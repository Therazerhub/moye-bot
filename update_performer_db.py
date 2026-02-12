#!/usr/bin/env python3
"""
Update Performer Database Script
Standalone script to refresh the local StashDB performer database.
Should be run weekly via cron to keep the database up to date.

Usage:
    python update_performer_db.py           # Full update
    python update_performer_db.py --init    # Initialize database first
    python update_performer_db.py --stats   # Show database statistics
    python update_performer_db.py --search "Name"  # Test search
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from performer_db import PerformerDB, init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def update_database(db_path: str = None, force_full: bool = False):
    """
    Update the performer database by fetching all performers from StashDB.
    
    Args:
        db_path: Path to the database file (optional)
        force_full: Force a full refresh even if recently updated
    """
    logger.info("=" * 60)
    logger.info("StashDB Performer Database Updater")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Initialize database connection
    db = PerformerDB(db_path)
    
    # Check if database exists and is initialized
    db_file = Path(db.db_path)
    if not db_file.exists():
        logger.info("Database not found, initializing...")
        db.init_db()
    
    # Get current stats before update
    try:
        stats_before = db.get_stats()
        logger.info(f"Database before update:")
        logger.info(f"  Performers: {stats_before.get('total_performers', 0):,}")
        logger.info(f"  Aliases: {stats_before.get('total_aliases', 0):,}")
        logger.info(f"  Images: {stats_before.get('total_images', 0):,}")
        logger.info(f"  Size: {stats_before.get('db_size_mb', 0):.2f} MB")
        logger.info(f"  Last sync: {stats_before.get('last_sync', 'Never')}")
    except Exception as e:
        logger.warning(f"Could not get stats (database may not be initialized): {e}")
        logger.info("Initializing database...")
        db.init_db()
        stats_before = {'total_performers': 0, 'total_aliases': 0, 'total_images': 0}
    
    logger.info("\nFetching performers from StashDB API...")
    logger.info("(This may take a few minutes for large databases)")
    
    try:
        # Fetch all performers from StashDB
        performers = db.fetch_all_performers_from_stashdb(batch_size=100)
        
        if not performers:
            logger.error("No performers fetched from StashDB. Check your API key.")
            return False
        
        logger.info(f"\nFetched {len(performers):,} performers from StashDB")
        
        # Update local database
        logger.info("\nUpdating local database...")
        db.update_local_db(performers)
        
        # Get stats after update
        stats_after = db.get_stats()
        
        performers_added = stats_after.get('total_performers', 0) - stats_before.get('total_performers', 0)
        aliases_added = stats_after.get('total_aliases', 0) - stats_before.get('total_aliases', 0)
        
        elapsed_time = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("Update Complete!")
        logger.info("=" * 60)
        logger.info(f"Database after update:")
        logger.info(f"  Performers: {stats_after.get('total_performers', 0):,} ({performers_added:+,})")
        logger.info(f"  Aliases: {stats_after.get('total_aliases', 0):,} ({aliases_added:+,})")
        logger.info(f"  Images: {stats_after.get('total_images', 0):,}")
        logger.info(f"  Size: {stats_after.get('db_size_mb', 0):.2f} MB")
        logger.info(f"  Last sync: {stats_after.get('last_sync', 'Unknown')}")
        logger.info(f"\nElapsed time: {elapsed_time:.1f} seconds")
        logger.info(f"Rate: {len(performers) / elapsed_time:.1f} performers/second")
        
        return True
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False
    finally:
        db._close()


def show_stats(db_path: str = None):
    """Show database statistics"""
    logger.info("=" * 60)
    logger.info("Database Statistics")
    logger.info("=" * 60)
    
    db = PerformerDB(db_path)
    
    try:
        stats = db.get_stats()
        
        print(f"\nDatabase location: {db.db_path}")
        print(f"Total performers: {stats.get('total_performers', 0):,}")
        print(f"Total aliases: {stats.get('total_aliases', 0):,}")
        print(f"Total images: {stats.get('total_images', 0):,}")
        print(f"Database size: {stats.get('db_size_mb', 0):.2f} MB")
        print(f"Last sync: {stats.get('last_sync', 'Never')}")
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        print(f"\nDatabase may not be initialized yet.")
        print(f"Run: python update_performer_db.py --init")
    finally:
        db._close()


def test_search(query: str, db_path: str = None):
    """Test performer search functionality"""
    logger.info("=" * 60)
    logger.info(f"Testing Search: '{query}'")
    logger.info("=" * 60)
    
    db = PerformerDB(db_path)
    
    try:
        stats = db.get_stats()
        if stats.get('total_performers', 0) == 0:
            logger.error("Database is empty. Run update first.")
            return
        
        print(f"\nSearching for: '{query}'")
        print(f"Total performers in database: {stats.get('total_performers', 0):,}")
        
        start_time = time.time()
        results = db.search_performer(query, limit=10, min_score=0.3)
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"\nSearch completed in {elapsed_ms:.1f}ms")
        print(f"Found {len(results)} matches:\n")
        
        for i, (performer, score) in enumerate(results, 1):
            print(f"{i}. {performer.name}")
            print(f"   Score: {score:.2%}")
            print(f"   StashDB ID: {performer.id}")
            if performer.gender:
                print(f"   Gender: {performer.gender}")
            if performer.aliases:
                print(f"   Aliases: {', '.join(performer.aliases[:5])}")
            print()
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db._close()


def main():
    parser = argparse.ArgumentParser(
        description='Update StashDB performer local database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database (run once)
  python update_performer_db.py --init
  
  # Update database with latest performers
  python update_performer_db.py
  
  # Show database statistics
  python update_performer_db.py --stats
  
  # Test search functionality
  python update_performer_db.py --search "Riley Reid"
        """
    )
    
    parser.add_argument(
        '--db-path',
        help='Path to the database file (default: performers.db in script directory)'
    )
    
    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize the database (create tables)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    parser.add_argument(
        '--search',
        metavar='QUERY',
        help='Test search functionality with the given query'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force full update even if recently updated'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute requested action
    if args.init:
        logger.info("Initializing database...")
        init_database(args.db_path)
        logger.info("Database initialized successfully!")
        print(f"\nDatabase created at: {Path(args.db_path).absolute() if args.db_path else PerformerDB().db_path.absolute()}")
        print("\nNext step: Run 'python update_performer_db.py' to populate it.")
        
    elif args.stats:
        show_stats(args.db_path)
        
    elif args.search:
        test_search(args.search, args.db_path)
        
    else:
        # Default: update database
        success = update_database(args.db_path, force_full=args.force)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
