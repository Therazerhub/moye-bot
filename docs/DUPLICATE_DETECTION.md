# Duplicate Detection System (pHash)

This module implements perceptual hashing (pHash) to detect duplicate videos even with different filenames or quality.

## Features

- **Perceptual Hashing**: Uses imagehash library with pHash algorithm
- **Multi-frame Sampling**: Samples 5 frames per video (10%, 30%, 50%, 70%, 90%) for robust matching
- **Hamming Distance**: Compares videos using Hamming distance (threshold: 10)
- **Metadata Matching**: Uses duration and file size for quick duplicate checks
- **Database Integration**: Stores hashes in the existing SQLite database

## Files

### 1. `duplicate_detector.py` - Core Module

Main module providing duplicate detection functionality:

```python
from duplicate_detector import (
    calculate_video_hash,      # Calculate multi-frame hash for a video
    hamming_distance,          # Compare two hashes
    is_duplicate,              # Check if two hashes match
    find_duplicates,           # Search DB for similar videos
    init_duplicate_columns     # Initialize DB schema
)
```

**Key Functions:**

- `calculate_phash(image_path)` - Extract pHash from image
- `calculate_video_hash(video_path)` - Multi-frame hash using ffmpeg
- `hamming_distance(hash1, hash2)` - Compare two perceptual hashes
- `hamming_distance_video(hash1, hash2)` - Compare multi-frame video hashes
- `is_duplicate(hash1, hash2, threshold=10)` - Returns True if distance < threshold
- `find_duplicates(video_hash, exclude_id, threshold=10)` - Search DB for similar videos

### 2. `detect_duplicates.py` - CLI Script

Command-line tool for duplicate detection:

```bash
# Initialize database schema
python detect_duplicates.py --init-db

# Calculate hashes for all videos without them (requires local video files)
python detect_duplicates.py --scan-all

# Find and report all duplicate groups
python detect_duplicates.py --find-duplicates

# Generate full duplicate report
python detect_duplicates.py --report

# Check a specific video for duplicates
python detect_duplicates.py --check <video_id>

# Show database statistics
python detect_duplicates.py --stats

# Generate SQL to mark duplicates
python detect_duplicates.py --export-sql

# Adjust threshold (lower = stricter)
python detect_duplicates.py --report --threshold 5
```

### 3. Database Schema Updates

Adds the following columns to the `videos` table in `stash.db`:

```sql
ALTER TABLE videos ADD COLUMN phash TEXT;
ALTER TABLE videos ADD COLUMN video_hash TEXT;
ALTER TABLE videos ADD COLUMN duration INTEGER;
ALTER TABLE videos ADD COLUMN file_size INTEGER;

CREATE INDEX idx_video_hash ON videos(video_hash);
CREATE INDEX idx_phash ON videos(phash);
```

## Integration with Bot

### bot.py Updates

When a video is uploaded, the bot now:

1. **Quick Duplicate Check**: Compares duration and file_size against existing videos
2. **Warning Display**: If similar video found, shows:
   - ⚠️ Possible duplicate warning
   - Original video title
   - "✅ Save Anyway" button
   - "🗑️ Skip Duplicate" button
   - "📊 View Original" button

3. **User Decision**: User can choose to save anyway or skip the duplicate

### organize_channel.py Updates

The organizer now:

1. **Checks for Duplicates**: Before processing, checks for videos with similar duration (±5s) and size (±10%)
2. **Duplicate Handling**:
   - By default: Skips forwarding duplicates (just marks them)
   - Optional: Forwards to `DUPLICATE_CHANNEL_ID` for review
3. **Tracking**: Stores duplicate information in `organize.db` with `duplicate_of` reference

## Configuration

### Environment Variables

No additional env vars required, but you can configure:

```python
# In organize_channel.py
CHECK_DUPLICATES = True                    # Enable/disable duplicate checking
DUPLICATE_DURATION_TOLERANCE = 5           # ±5 seconds
DUPLICATE_SIZE_TOLERANCE = 0.1             # ±10%
DUPLICATE_CHANNEL_ID = -100xxxxxxxxxx      # Channel for duplicate review
```

### Thresholds

- **Hamming Distance Threshold**: Default is 10 (0-64 range)
  - 0-5: Very high confidence duplicate (same video)
  - 5-10: Likely duplicate (different quality/encoding)
  - 10-15: Possible duplicate (different cuts/edits)
  - 15+: Probably different videos

## Usage Examples

### Check if a video is a duplicate

```python
from duplicate_detector import calculate_video_hash, find_duplicates

# Calculate hash
video_hash = calculate_video_hash("/path/to/video.mp4")

# Find duplicates
duplicates = find_duplicates(video_hash, threshold=10)
for dup in duplicates:
    print(f"Duplicate: {dup['title']} (distance: {dup['distance']})")
```

### Process videos and skip duplicates

```python
from organize_channel import process_single_video

# Process with duplicate skipping enabled
status = await process_single_video(client, message, skip_duplicates=True)
# Returns: "duplicate" if skipped, otherwise "clean", "review", "unsorted", or "error"
```

### Mark duplicates in database

```bash
# Generate SQL commands
python detect_duplicates.py --export-sql

# Output:
-- Duplicate cleanup SQL
UPDATE videos SET category = 'DUPLICATE' WHERE id = 123;
UPDATE videos SET category = 'DUPLICATE' WHERE id = 456;
```

## Requirements

```
imagehash>=4.3.1      # Perceptual hashing
Pillow>=10.0.0        # Image processing
ffmpeg                # Frame extraction (system package)
```

Note: ffmpeg must be installed on the system. The script uses ffmpeg/ffprobe for video processing instead of opencv for better compatibility.

## Limitations

1. **Requires Local Files**: Video hashing requires access to the actual video files. Videos stored as Telegram file_ids cannot be hashed without downloading first.

2. **Processing Time**: Hashing a video takes a few seconds (needs to extract 5 frames via ffmpeg).

3. **Memory**: Frame extraction uses memory proportional to video resolution.

## Future Enhancements

- [ ] Background task to download and hash Telegram videos
- [ ] Web UI for duplicate review
- [ ] Automatic deletion of lower-quality duplicates
- [ ] Fuzzy matching for near-duplicates (different cuts)
- [ ] Integration with StashDB for cross-reference
