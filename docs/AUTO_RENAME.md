# Auto-Rename Feature Implementation Summary

## Overview
Implemented automatic renaming of video files when StashDB/FansDB match confidence is > 90%.

## Files Created

### 1. `auto_rename.py` - Core Auto-Rename Module
New module with the following functions:

- **`should_rename(match_score, match_source, threshold=None)`**
  - Returns True if score >= 90% AND source is StashDB or FansDB
  - Configurable threshold via AUTO_RENAME_THRESHOLD env variable

- **`generate_new_filename(scene_data, original_filename)`**
  - Generates filename in format: "Studio - Performer - Title [StashID].ext"
  - Handles special characters in performer/title names
  - Preserves original file extension
  - Falls back to original name if insufficient data

- **`rename_file(old_path, new_filename)`**
  - Safely renames files with collision handling
  - Adds number suffix (1), (2), etc. for duplicates
  - Returns (success: bool, result: str)

- **`move_to_organized_folder(filename, studio_name, base_folder=None)`**
  - Moves files to studio-organized subfolders
  - Creates studio folders as needed
  - Returns (success: bool, result: str)

- **`get_rename_suggestion(scene_data, original_filename)`**
  - Returns dict with rename details:
    - original: original filename
    - suggested: new filename
    - studio, performer, title, stash_id

- **`sanitize_filename(text)`**
  - Removes invalid filename characters
  - Collapses multiple spaces
  - Truncates very long names

- **`is_auto_rename_enabled()` / `is_organize_by_studio_enabled()`**
  - Check configuration from environment variables

### 2. `test_auto_rename.py` - Comprehensive Test Suite
Tests all functionality including:
- should_rename() logic
- sanitize_filename() edge cases
- generate_new_filename() with various data
- File rename with collision handling
- Studio folder organization
- Configuration options

## Files Modified

### 1. `stashdb_integration.py`
- Added imports from `auto_rename` module
- Created `_process_video_caption_impl()` - internal implementation
- Modified to return `(caption, source, metadata)` tuple
- `process_video_caption()` - backward-compatible wrapper
- `process_video_caption_with_metadata()` - enhanced version with full metadata
- Metadata includes:
  - original_filename
  - match_score
  - match_source
  - scene_data
  - should_rename (bool)
  - rename_suggestion (dict or None)

### 2. `bot.py`
- Added imports for auto-rename functionality
- Added `build_video_keyboard()` helper function
  - Shows "📝 Rename File" button when match > 90%
  - Button callback: `rename_<video_id>`
- Added `handle_rename_callback()` - shows rename confirmation dialog
- Added `handle_rename_confirm()` - performs the rename
- Updated `random_video()` to use metadata-enhanced caption function
- Added callback handlers to main() function

### 3. `.env`
Added new configuration options:
```
AUTO_RENAME_THRESHOLD=0.90
AUTO_RENAME_ENABLED=true
ORGANIZE_BY_STUDIO=false
ORGANIZED_FOLDER_PATH=
```

## Usage

### For Users
When a video has a high-confidence match (>90%) from StashDB or FansDB:
1. The video caption is shown with a "📝 Rename File" button
2. Clicking the button shows before/after filenames
3. User can confirm to rename (updates database title)

### For Developers
```python
from stashdb_integration import process_video_caption_with_metadata

caption, source, metadata = process_video_caption_with_metadata(filename)

if metadata['should_rename']:
    suggestion = metadata['rename_suggestion']
    print(f"Suggested: {suggestion['suggested']}")
```

## Testing
Run the test suite:
```bash
cd /home/ubuntu/.openclaw/workspace/stash_bot
python3 test_auto_rename.py
```

## Edge Cases Handled
- Filename collisions (adds number suffix)
- Special characters in names (sanitized)
- File extension preservation
- Missing/empty data fields
- Very long filenames (truncated)
- Non-existent files (graceful error)
- Invalid sources (local matches don't trigger rename)
- Multiple performers (shows up to 2 female performers)

## Future Enhancements
- Actual file system rename (currently updates DB title only)
- Automatic rename without confirmation (if AUTO_RENAME_ENABLED)
- Studio folder organization (if ORGANIZE_BY_STUDIO enabled)
- Undo rename functionality
- Rename history logging