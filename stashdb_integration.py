"""
StashDB/FansDB Integration Module
Handles caption formatting with metadata lookup - CLEAN & SIMPLE
"""

import os
import re
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

# Both APIs
STASHDB_API_KEY = os.getenv('STASHDB_API_KEY')
STASHDB_GRAPHQL_URL = os.getenv('STASHDB_GRAPHQL_URL', 'https://stashdb.org/graphql')

FANSDB_API_KEY = os.getenv('FANSDB_API_KEY')
FANSDB_GRAPHQL_URL = os.getenv('FANSDB_GRAPHQL_URL', 'https://fansdb.cc/graphql')

# GraphQL query for FansDB
FANSDB_SEARCH_QUERY = """
query SearchScenes($input: SceneQueryInput!) {
  queryScenes(input: $input) {
    scenes {
      id
      title
      performers {
        performer {
          name
          gender
        }
      }
      studio {
        name
      }
      tags {
        name
      }
    }
  }
}
"""

# GraphQL query for StashDB
STASHDB_SEARCH_QUERY = """
query SearchScenes($term: String!, $limit: Int = 5) {
  searchScene(term: $term, limit: $limit) {
    id
    title
    performers {
      performer {
        name
        gender
      }
    }
    studio {
      name
    }
    tags {
      name
    }
  }
}
"""


def query_api(url: str, api_key: str, query: str, variables: dict = None) -> Optional[dict]:
    """Make a GraphQL query to an API"""
    if not api_key:
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'ApiKey': api_key  # StashDB/FansDB use ApiKey header, not Bearer
    }
    
    payload = {'query': query, 'variables': variables or {}}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL errors: {data['errors']}")
            return None
            
        return data
    except Exception as e:
        print(f"API error: {e}")
        return None


def search_fansdb(title: str, performer: str = None) -> Optional[dict]:
    """Search FansDB for a scene"""
    if not FANSDB_API_KEY:
        return None
    
    search_text = f"{performer} {title}" if performer else title
    
    result = query_api(FANSDB_GRAPHQL_URL, FANSDB_API_KEY, FANSDB_SEARCH_QUERY, 
                      {'input': {'text': search_text, 'per_page': 5}})
    
    if result and 'data' in result:
        scenes = result['data'].get('queryScenes', {}).get('scenes', [])
        if scenes:
            return scenes[0]
    return None


def search_stashdb(title: str, performer: str = None) -> Optional[dict]:
    """Search StashDB for a scene"""
    if not STASHDB_API_KEY:
        return None
    
    search_term = f"{performer} {title}" if performer else title
    
    result = query_api(STASHDB_GRAPHQL_URL, STASHDB_API_KEY, STASHDB_SEARCH_QUERY, 
                      {'term': search_term, 'limit': 5})
    
    if result and 'data' in result:
        scenes = result['data'].get('searchScene', [])
        if scenes:
            return scenes[0]
    return None


def parse_filename(filename: str) -> tuple:
    """Parse filename to extract performer and title"""
    name = os.path.splitext(filename)[0]
    name = name.replace('.', ' ').replace('_', ' ')
    
    if ' - ' in name:
        parts = name.split(' - ', 1)
        return parts[0].strip(), parts[1].strip()
    
    words = name.split()
    if len(words) >= 4:
        return ' '.join(words[:2]), ' '.join(words[2:])
    
    return None, name


def get_female_performer_names(performers: List[dict]) -> str:
    """Get only female performer names (max 2)"""
    if not performers:
        return None
    
    female_names = []
    
    for p in performers:
        if not isinstance(p, dict):
            continue
            
        performer = p.get('performer', {})
        if not isinstance(performer, dict):
            continue
            
        name = performer.get('name', '')
        gender = performer.get('gender', '')
        
        # Only include if female (FEMALE or empty/unknown)
        if name and (not gender or gender.upper() in ['FEMALE', 'F', '']):
            female_names.append(name)
            if len(female_names) >= 2:  # Max 2 performers
                break
    
    if len(female_names) == 1:
        return female_names[0]
    elif len(female_names) == 2:
        return f"{female_names[0]} & {female_names[1]}"
    
    return None


def get_top_tags(tags: List[dict], max_tags: int = 5) -> List[str]:
    """Get top tags, cleaned and limited"""
    if not tags:
        return []
    
    formatted = []
    for tag in tags[:max_tags]:
        if isinstance(tag, dict):
            tag_name = tag.get('name', '')
        else:
            tag_name = str(tag)
        
        if tag_name:
            # Clean tag: lowercase, remove special chars
            clean = re.sub(r'[^\w\s]', '', tag_name.lower())
            clean = clean.replace(' ', '')
            if clean and len(clean) > 2:  # Skip short tags
                formatted.append(clean)
    
    return formatted[:max_tags]


def generate_clean_caption(scene_data: dict, original_filename: str = None, source: str = "local") -> str:
    """Generate clean caption: Title + Studio + Female Performer(s) + 5 Tags + Source indicator"""
    
    # Get title
    title = scene_data.get('title', '')
    if not title and original_filename:
        _, title = parse_filename(original_filename)
    if not title:
        title = "Scene"
    
    # Get studio
    studio = scene_data.get('studio', {})
    studio_name = studio.get('name', '') if isinstance(studio, dict) else ''
    
    # Get female performer(s)
    performers = scene_data.get('performers', [])
    performer_str = get_female_performer_names(performers)
    
    # Get top 5 tags
    tags = scene_data.get('tags', [])
    tag_list = get_top_tags(tags, max_tags=5)
    
    # Build caption
    lines = []
    
    # Source indicator emoji
    source_emoji = "🌐" if source in ("stashdb", "fansdb") else "📁"
    
    # Title line with studio
    if performer_str and studio_name:
        lines.append(f"{source_emoji} <b>{performer_str} — {title}</b>")
        lines.append(f"📺 {studio_name}")
    elif performer_str:
        lines.append(f"{source_emoji} <b>{performer_str} — {title}</b>")
    elif studio_name:
        lines.append(f"{source_emoji} <b>{title}</b>")
        lines.append(f"📺 {studio_name}")
    else:
        lines.append(f"{source_emoji} <b>{title}</b>")
    
    # Tags line (max 5)
    if tag_list:
        tags_str = ' '.join([f'#{tag}' for tag in tag_list])
        lines.append(f"\n{tags_str}")
    
    caption = '\n'.join(lines)
    
    # Truncate if too long
    if len(caption) > 1024:
        caption = caption[:1020] + "..."
    
    return caption


def process_video_caption(filename: str) -> tuple:
    """
    Main function: Search databases and return clean caption with source
    Returns: (caption, source)
    """
    # Parse filename
    performer, title = parse_filename(filename)
    
    # Try FansDB first
    try:
        scene = search_fansdb(title, performer)
        if scene:
            print(f"✅ FansDB: {filename[:50]}")
            return generate_clean_caption(scene, filename, source="fansdb"), "fansdb"
    except Exception as e:
        print(f"FansDB error: {e}")
    
    # Fallback to StashDB
    try:
        scene = search_stashdb(title, performer)
        if scene:
            print(f"✅ StashDB: {filename[:50]}")
            return generate_clean_caption(scene, filename, source="stashdb"), "stashdb"
    except Exception as e:
        print(f"StashDB error: {e}")
    
    # Fallback: just format filename
    if performer:
        return f"📁 <b>{performer} — {title}</b>", "local"
    return f"📁 <b>{title}</b>", "local"


# Test
if __name__ == '__main__':
    test_files = [
        "Jia Lissa - Midnight Ride.mp4",
        "Ariana Marie - Call Me.mp4",
    ]
    
    for filename in test_files:
        print(f"\n{'='*50}")
        print(f"File: {filename}")
        caption = process_video_caption(filename)
        if caption:
            print(f"Caption:\n{caption}")
        else:
            print("No match found")
