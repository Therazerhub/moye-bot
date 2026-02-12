# Match Feedback Loop System

A self-improving performer matching system that learns from user corrections.

## Overview

The feedback loop tracks when users correct performer names in video captions, then uses these corrections to improve future matching accuracy. This creates a continuously learning system that gets better over time.

## Example Flow

1. Bot guesses "Rylee Reid" for a filename
2. User edits caption to correct it to "Riley Reid"
3. System stores: filename pattern → "Riley Reid"
4. Next time the same pattern appears → suggests "Riley Reid" first

## Components

### 1. feedback_db.py

Database module for storing and retrieving corrections.

#### Functions

**`record_correction(filename, original_match, user_correction, correction_type, user_id, confidence)`**
- Records a user correction to the database
- Updates alias mappings and filename patterns
- Parameters:
  - `filename`: The filename that was corrected
  - `original_match`: System's original guess
  - `user_correction`: User's corrected value
  - `correction_type`: Type of correction (default: 'performer_name')
  - `user_id`: Telegram user ID (optional)
  - `confidence`: Confidence score 0.0-1.0 (default: 1.0)

**`apply_learned_corrections(filename, performer_guess)`**
- Checks if a performer guess should be corrected based on learned patterns
- Returns: `(corrected_performer, confidence_score)`
- If no correction found, returns original guess with 0.0 confidence

**`get_correction_stats(days=30)`**
- Returns statistics about corrections and learning progress
- Includes most corrected performers, learned aliases, daily trends

**`generate_weekly_report()`**
- Generates a formatted weekly report of learned corrections
- Suggests new aliases to add to the system

**`detect_caption_change(original_caption, new_caption)`**
- Detects what changed between original and edited captions
- Returns change details or None if no performer change detected

### 2. Database Schema

#### corrections table
```sql
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    filename_pattern TEXT,
    original_performer TEXT,
    corrected_performer TEXT NOT NULL,
    correction_type TEXT,
    timestamp TIMESTAMP,
    user_id INTEGER,
    confidence_score REAL
);
```

#### performer_aliases table
```sql
CREATE TABLE performer_aliases (
    id INTEGER PRIMARY KEY,
    performer_name TEXT NOT NULL,
    alias TEXT NOT NULL,
    correction_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_used TIMESTAMP,
    confidence_score REAL,
    UNIQUE(performer_name, alias)
);
```

#### filename_patterns table
```sql
CREATE TABLE filename_patterns (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL UNIQUE,
    corrected_performer TEXT NOT NULL,
    match_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_used TIMESTAMP
);
```

### 3. Updated matching_utils.py

The `enhanced_performer_match()` function now:
1. Checks learned corrections FIRST (before algorithm matching)
2. If a correction is found, compares corrected name to DB performer
3. Boosts match score based on confidence if corrected name matches
4. Falls back to standard fuzzy + phonetic matching if no correction

### 4. Updated bot.py

New admin commands:
- `/feedbackstats` - Show learning statistics
- `/feedbackreport` - Generate weekly report
- `/suggestaliases` - Show suggested aliases to add

New handlers:
- Edited message handler detects caption changes
- Stores original captions for comparison
- Records corrections when performer names change

## Admin Commands

### /feedbackstats
Shows feedback learning statistics (admin only):
- Total corrections recorded
- Recent corrections (last 30 days)
- Most corrected performer mappings
- Learned aliases with high confidence

### /feedbackreport
Generates a detailed weekly report (admin only):
- Corrections activity
- Most common mistakes
- Ready-to-add aliases
- Daily activity trend

### /suggestaliases
Shows aliases that should be added to the system (admin only):
- Minimum 2 corrections required for suggestion
- Sorted by correction count
- Shows mapping: alias → correct name

## How It Works

### Filename Pattern Extraction

The system extracts patterns from filenames for matching:
- Removes extensions (.mp4, .mkv, etc.)
- Removes dates (2023-01-15, 20230115)
- Removes part numbers (part1, .part001)
- Removes episode/scene numbers
- Removes resolution (1080p, 4k)
- Removes hashes
- Converts to lowercase with underscores

Example: `Brazzers - Riley Reid - Scene 1.mp4` → `brazzers_riley_reid_scene`

### Correction Learning

1. When a caption is edited, the system compares original vs new
2. If performer name changed, records the correction
3. Updates alias mappings (both directions)
4. Updates filename pattern → performer mapping

### Match Application

1. When matching a new file, system first checks:
   - Filename pattern in learned patterns table
   - Performer alias in aliases table
2. If found, applies correction before algorithm matching
3. Boosts confidence score for matches with learned corrections

## Configuration

No additional configuration required. The system:
- Auto-initializes database on first use
- Stores data in `feedback.db` (SQLite)
- Works alongside existing stash.db

## Testing

Run the feedback module directly to test:

```bash
cd /home/ubuntu/.openclaw/workspace/stash_bot
python3 feedback_db.py
```

This will:
1. Initialize the database
2. Record a test correction
3. Apply the learned correction
4. Display statistics and weekly report

## Integration with Existing System

The feedback loop integrates seamlessly:
- `matching_utils.py` checks corrections before fuzzy matching
- `bot.py` detects edits and records corrections automatically
- Database is separate from main stash.db (no conflicts)
- All changes are backward compatible

## Benefits

1. **Self-Improving**: Gets better with every user correction
2. **Pattern Learning**: Learns filename patterns, not just aliases
3. **Confidence Scoring**: Tracks accuracy of learned corrections
4. **Admin Insights**: Reports show what the system has learned
5. **No Manual Work**: Fully automatic after initial setup

## Future Enhancements

Potential improvements:
- Machine learning model training on correction patterns
- Automatic alias suggestion approval after N corrections
- Cross-user learning (if multiple users correct the same pattern)
- Integration with main database for permanent alias storage
