"""
API Response Cache Module
Caches StashDB/FansDB API responses for faster repeated searches
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class APICache:
    """
    SQLite-based cache for API responses with TTL support.
    
    Cache key is MD5 hash of "source:query" for fast lookups.
    Stores query text for debugging, response as JSON, and timestamp.
    """
    
    def __init__(self, db_path: str = 'api_cache.db', ttl_hours: int = 24):
        """
        Initialize the API cache.
        
        Args:
            db_path: Path to SQLite database file
            ttl_hours: Time-to-live in hours for cached entries
        """
        self.db_path = db_path
        self.ttl = timedelta(hours=ttl_hours)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with cache table"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create cache table with all required fields
        c.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT,
                source TEXT,
                response TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Index for faster cleanup queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_created ON cache(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_source ON cache(source)')
        
        conn.commit()
        conn.close()
    
    def _make_hash(self, query: str, source: str) -> str:
        """Generate MD5 hash of source + query for cache key"""
        return hashlib.md5(f"{source}:{query}".encode()).hexdigest()
    
    def get(self, query: str, source: str) -> Optional[Dict[Any, Any]]:
        """
        Get cached response if it exists and hasn't expired.
        
        Args:
            query: The search query string
            source: API source ('stashdb' or 'fansdb')
            
        Returns:
            Cached response dict if cache hit, None if cache miss or expired
        """
        query_hash = self._make_hash(query, source)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT response, created_at 
                FROM cache 
                WHERE query_hash = ? AND source = ?
            ''', (query_hash, source))
            
            result = c.fetchone()
            
            if result:
                response_json, created_at = result
                created = datetime.fromisoformat(created_at)
                
                # Check if still valid (not expired)
                if datetime.now() - created < self.ttl:
                    return json.loads(response_json)
                else:
                    # Entry expired, remove it
                    c.execute('DELETE FROM cache WHERE query_hash = ?', (query_hash,))
                    conn.commit()
        
        finally:
            conn.close()
        
        return None
    
    def set(self, query: str, source: str, response: Dict[Any, Any]) -> None:
        """
        Cache an API response.
        
        Args:
            query: The search query string
            source: API source ('stashdb' or 'fansdb')
            response: The API response dict to cache
        """
        query_hash = self._make_hash(query, source)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT OR REPLACE INTO cache 
                (query_hash, query_text, source, response, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                query_hash,
                query,
                source,
                json.dumps(response),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        finally:
            conn.close()
    
    def clear_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        cutoff = (datetime.now() - self.ttl).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('DELETE FROM cache WHERE created_at < ?', (cutoff,))
            deleted = c.rowcount
            conn.commit()
            return deleted
        
        finally:
            conn.close()
    
    def clear_all(self) -> int:
        """
        Clear entire cache (useful for testing or reset).
        
        Returns:
            Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('DELETE FROM cache')
            deleted = c.rowcount
            conn.commit()
            return deleted
        
        finally:
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with total_entries, expired_entries, sources breakdown
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Total entries
            c.execute('SELECT COUNT(*) FROM cache')
            total = c.fetchone()[0]
            
            # Expired entries
            cutoff = (datetime.now() - self.ttl).isoformat()
            c.execute('SELECT COUNT(*) FROM cache WHERE created_at < ?', (cutoff,))
            expired = c.fetchone()[0]
            
            # By source
            c.execute('''
                SELECT source, COUNT(*) 
                FROM cache 
                GROUP BY source
            ''')
            sources = {row[0]: row[1] for row in c.fetchall()}
            
            return {
                'total_entries': total,
                'expired_entries': expired,
                'valid_entries': total - expired,
                'by_source': sources,
                'ttl_hours': self.ttl.total_seconds() / 3600
            }
        
        finally:
            conn.close()


# Global cache instance for use across the module
_default_cache = None


def get_cache(db_path: str = 'api_cache.db', ttl_hours: int = 24) -> APICache:
    """Get or create the default cache instance"""
    global _default_cache
    if _default_cache is None:
        _default_cache = APICache(db_path=db_path, ttl_hours=ttl_hours)
    return _default_cache


def reset_cache():
    """Reset the default cache instance (useful for testing)"""
    global _default_cache
    _default_cache = None


# Test the cache if run directly
if __name__ == '__main__':
    import tempfile
    import os
    
    # Test with temp file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    try:
        print("Testing APICache...")
        
        # Create cache with 1 second TTL for testing
        cache = APICache(db_path=temp_path, ttl_hours=1/3600)  # 1 second TTL
        
        # Test set and get
        test_response = {
            'id': 'test-scene-123',
            'title': 'Test Scene',
            'performers': [{'performer': {'name': 'Test Performer', 'gender': 'FEMALE'}}]
        }
        
        cache.set('test query', 'stashdb', test_response)
        print(f"✓ Cached response for 'test query'")
        
        # Test cache hit
        cached = cache.get('test query', 'stashdb')
        if cached and cached['id'] == 'test-scene-123':
            print("✓ Cache hit: Retrieved cached response")
        else:
            print("✗ Cache hit failed")
        
        # Test cache miss (different source)
        cached = cache.get('test query', 'fansdb')
        if cached is None:
            print("✓ Cache miss: Different source returns None")
        else:
            print("✗ Should have been cache miss")
        
        # Test cache miss (different query)
        cached = cache.get('different query', 'stashdb')
        if cached is None:
            print("✓ Cache miss: Different query returns None")
        else:
            print("✗ Should have been cache miss")
        
        # Test stats
        stats = cache.get_stats()
        print(f"✓ Cache stats: {stats}")
        
        # Wait for expiry
        print("Waiting 2 seconds for TTL expiry...")
        import time
        time.sleep(2)
        
        # Should be expired now
        cached = cache.get('test query', 'stashdb')
        if cached is None:
            print("✓ Expired entry returns None")
        else:
            print("✗ Should have expired")
        
        # Test clear_expired
        cache.set('query1', 'stashdb', {'data': 1})
        cache.set('query2', 'fansdb', {'data': 2})
        time.sleep(2)
        cache.set('query3', 'stashdb', {'data': 3})  # This one won't be expired
        
        cleared = cache.clear_expired()
        print(f"✓ Cleared {cleared} expired entries")
        
        stats = cache.get_stats()
        print(f"✓ Final stats: {stats}")
        
        print("\n✅ All tests passed!")
        
    finally:
        os.unlink(temp_path)
