# Local Performer Database

A high-performance SQLite-based cache of StashDB performers for instant lookups (0ms vs 2s API calls).

## Overview

The performer database provides:
- **Instant performer lookups** - Local SQLite queries instead of GraphQL API calls
- **Fuzzy + phonetic matching** - Find performers even with typos or variations
- **Full performer metadata** - Names, aliases, images, measurements, career info
- **Weekly auto-updates** - Cron job keeps the database synchronized with StashDB

## Files

| File | Description |
|------|-------------|
| `performer_db.py` | Main module with `PerformerDB` class |
| `update_performer_db.py` | Standalone script to refresh the database |
| `setup_cron.sh` | Sets up weekly automatic updates |
| `performers.db` | SQLite database file (created on first run) |

## Quick Start

### 1. Initialize the Database

```bash
cd stash_bot
python3 update_performer_db.py --init
```

### 2. Populate with StashDB Data

```bash
python3 update_performer_db.py
```

This will fetch all performers from StashDB and populate the local database. 
**First run may take 5-10 minutes** depending on the size of StashDB.

### 3. Set Up Weekly Updates

```bash
./setup_cron.sh
```

This adds a cron job that updates the database every Sunday at 3 AM.

## Usage

### Basic Search

```python
from performer_db import PerformerDB

db = PerformerDB()

# Search for performers (fuzzy + phonetic matching)
results = db.search_performer("Riley Reed", limit=5)  # Typo intentional!
for performer, score in results:
    print(f"{performer.name} (score: {score:.2%})")
    print(f"  Aliases: {', '.join(performer.aliases)}")
    print(f"  Images: {len(performer.images)}")

# Instant lookup by StashDB ID
performer = db.get_performer_by_id("abc-123-def")
if performer:
    print(performer.name)
```

### Integration with StashDB Search

The `stashdb_integration.py` module automatically uses the local database:

```python
from stashdb_integration import process_video_caption

# Local DB is checked first for performer matching (0ms lookup)
# Falls back to API only if not found locally
caption, source = process_video_caption("Riley Reid - Scene Title.mp4")
```

## Database Schema

### performers table
- `id` - Local auto-increment ID
- `stashdb_id` - StashDB UUID (unique)
- `name` - Performer name
- `gender` - Gender
- `birthdate`, `ethnicity`, `country` - Demographics
- `height`, `weight`, `measurements` - Physical stats
- `career_start_year`, `career_end_year` - Career dates
- `breast_type` - Breast type
- `created_at`, `updated_at` - StashDB timestamps
- `last_synced` - Local sync timestamp

### aliases table
- `performer_id` - Foreign key to performers
- `alias_name` - Alternative name

### images table
- `performer_id` - Foreign key to performers
- `image_url` - Image URL
- `is_default` - Whether this is the default image

## Command Line

### Update Script Options

```bash
# Full database update (fetch all from StashDB)
python3 update_performer_db.py

# Initialize database (create tables)
python3 update_performer_db.py --init

# Show statistics
python3 update_performer_db.py --stats

# Test search
python3 update_performer_db.py --search "Riley Reid"

# Verbose output
python3 update_performer_db.py -v

# Custom database path
python3 update_performer_db.py --db-path /path/to/custom.db
```

## Performance

| Operation | With Local DB | Without (API Only) |
|-----------|---------------|-------------------|
| Performer lookup | ~0-1ms | ~1500-3000ms |
| Fuzzy search | ~5-50ms | N/A (not possible) |
| Scene matching with performer | ~50-100ms | ~3000-5000ms |

## Matching Algorithm

The search uses multiple similarity algorithms combined:

1. **RapidFuzz WRatio** (35%) - Weighted Levenshtein distance
2. **Partial Ratio** (25%) - Substring matching
3. **Token Sort Ratio** (25%) - Word order independent
4. **Bigram Similarity** (10%) - Character pair matching
5. **Trigram Similarity** (5%) - Three-character sequences
6. **Phonetic Matching** (bonus) - Soundex/Metaphone for names that sound alike

## Troubleshooting

### Database is empty

```bash
python3 update_performer_db.py
```

### API key error

Ensure `STASHDB_API_KEY` is set in your `.env` file:

```bash
STASHDB_API_KEY=your_api_key_here
```

### Slow updates

First sync fetches all performers (~20,000+). Subsequent updates only sync changes and are much faster.

### Cron job not running

Check crontab:
```bash
crontab -l
```

Check logs:
```bash
tail -f logs/performer_db_update.log
```

## Architecture

```
┌─────────────────────┐
│   Scene Filename    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────┐
│  Parse Performer    │────▶│ Local DB Search  │◀──┐
└──────────┬──────────┘     │ (0ms lookup)     │   │
           │                └────────┬─────────┘   │
           │                         │             │
           │         ┌───────────────┘             │
           │         │         Not Found           │
           │         ▼                             │
           │    ┌──────────────────┐               │
           │    │  High Confidence │               │
           │    │    Match?        │               │
           │    └────────┬─────────┘               │
           │             │                         │
           │      Yes    │    No                   │
           │             │                         │
           ▼             ▼                         │
┌──────────────────────────────────┐              │
│   Use Confirmed Performer Name   │              │
│   for StashDB Scene Search       │              │
└──────────────────────────────────┘              │
                                                  │
           ┌──────────────────────────────────────┘
           │  API used to get scenes,
           │  not performer metadata
```

## Maintenance

### Manual Update

```bash
python3 update_performer_db.py
```

### Database Stats

```python
from performer_db import PerformerDB

db = PerformerDB()
stats = db.get_stats()
print(f"Performers: {stats['total_performers']:,}")
print(f"Last sync: {stats['last_sync']}")
print(f"DB size: {stats['db_size_mb']:.1f} MB")
```

### Reset Database

```bash
rm performers.db
python3 update_performer_db.py --init
python3 update_performer_db.py
```
