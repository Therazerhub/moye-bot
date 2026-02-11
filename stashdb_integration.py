"""
StashDB/FansDB Integration Module
Handles caption formatting with metadata lookup
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

# GraphQL query for FansDB (uses queryScenes with SceneQueryInput)
FANSDB_SEARCH_QUERY = """
query SearchScenes($input: SceneQueryInput!) {
  queryScenes(input: $input) {
    scenes {
      id
      title
      date
      performers {
        performer {
          name
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

# GraphQL query for StashDB (uses searchScene)
STASHDB_SEARCH_QUERY = """
query SearchScenes($term: String!, $limit: Int = 5) {
  searchScene(
    term: $term
    limit: $limit
  ) {
    id
    title
    date
    performers {
      performer {
        name
        gender
      }
      as
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
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'query': query,
        'variables': variables or {}
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL errors from {url}: {data['errors']}")
            return None
            
        return data
    except Exception as e:
        print(f"API query error ({url}): {e}")
        return None


def search_fansdb(title: str, performer: str = None) -> Optional[dict]:
    """Search FansDB for a scene"""
    if not FANSDB_API_KEY:
        return None
    
    # Build input - use text search which searches title, performer, etc
    search_text = f"{performer} {title}" if performer else title
    
    result = query_api(FANSDB_GRAPHQL_URL, FANSDB_API_KEY, FANSDB_SEARCH_QUERY, 
                      {'input': {'text': search_text, 'per_page': 5}})
    
    if not result or 'data' not in result:
        return None
    
    scenes = result['data'].get('queryScenes', {}).get('scenes', [])
    
    if isinstance(scenes, list) and len(scenes) > 0:
        return scenes[0]
    
    return None


def search_stashdb(title: str, performer: str = None) -> Optional[dict]:
    """Search StashDB for a scene"""
    if not STASHDB_API_KEY:
        return None
    
    if performer:
        search_term = f"{performer} {title}"
    else:
        search_term = title
    
    result = query_api(STASHDB_GRAPHQL_URL, STASHDB_API_KEY, STASHDB_SEARCH_QUERY, {'term': search_term, 'limit': 5})
    
    if not result or 'data' not in result:
        return None
    
    scenes = result['data'].get('searchScene', [])
    
    if isinstance(scenes, list) and len(scenes) > 0:
        return scenes[0]
    
    return None


def parse_filename(filename: str) -> tuple:
    """Parse filename to extract performer and scene title"""
    name = os.path.splitext(filename)[0]
    name = name.replace('.', ' ').replace('_', ' ')
    
    if ' - ' in name:
        parts = name.split(' - ', 1)
        performer = parts[0].strip()
        title = parts[1].strip()
        return performer, title
    
    words = name.split()
    if len(words) >= 4:
        performer = ' '.join(words[:2])
        title = ' '.join(words[2:])
        return performer, title
    
    return None, name


def format_performer_name(performers: List[dict]) -> str:
    """Format performer names"""
    if not performers:
        return "Unknown"
    
    names = []
    for p in performers:
        performer = p.get('performer', {}) if isinstance(p, dict) else {}
        name = performer.get('name', '') if isinstance(performer, dict) else str(performer)
        if name:
            names.append(name)
    
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} & {names[1]}"
    elif len(names) > 2:
        return f"{names[0]}, {names[1]} & {len(names)-2} more"
    
    return "Unknown"


def format_tags(tags: List[dict], max_tags: int = 10) -> List[str]:
    """Format tags for hashtags"""
    formatted = []
    for tag in tags[:max_tags]:
        if isinstance(tag, dict):
            tag_name = tag.get('name', '')
        else:
            tag_name = str(tag)
        if tag_name:
            clean_tag = re.sub(r'[^\w]', '', tag_name.lower())
            if clean_tag:
                formatted.append(clean_tag)
    return formatted


def generate_caption(scene_data: dict, original_filename: str = None) -> str:
    """Generate formatted caption"""
    performers = scene_data.get('performers', [])
    performer_name = format_performer_name(performers)
    
    title = scene_data.get('title', '')
    if not title and original_filename:
        _, title = parse_filename(original_filename)
    if not title:
        title = "Scene"
    
    caption = f"🔥🎬 <b>{performer_name} - {title}</b> ✨"
    
    studio = scene_data.get('studio', {})
    if isinstance(studio, dict) and studio.get('name'):
        caption += f"\n📺 {studio['name']}"
    
    tags = scene_data.get('tags', [])
    if tags:
        tag_list = format_tags(tags, max_tags=10)
        if tag_list:
            hashtag_line = ' '.join([f'#{tag}' for tag in tag_list])
            caption += f"\n\n{hashtag_line}"
    
    if len(caption) > 1024:
        caption = caption[:1020] + "..."
    
    return caption


def process_video_caption(filename: str) -> Optional[str]:
    """
    Main function: Search both databases and return formatted caption
    Priority: FansDB first (unrestricted), then StashDB, then filename fallback
    """
    # Parse filename first (always available)
    performer, title = parse_filename(filename)
    
    # Try FansDB first (unrestricted)
    try:
        scene = search_fansdb(title, performer)
        if scene:
            print(f"✅ Found in FansDB: {filename[:50]}")
            return generate_caption(scene, filename)
    except Exception as e:
        print(f"FansDB error: {e}")
    
    # Fallback to StashDB
    try:
        scene = search_stashdb(title, performer)
        if scene:
            print(f"✅ Found in StashDB: {filename[:50]}")
            return generate_caption(scene, filename)
    except Exception as e:
        print(f"StashDB error: {e}")
    
    # Final fallback: format filename nicely
    if performer:
        fallback = f"🔥🎬 <b>{performer} - {title}</b> ✨"
    else:
        fallback = f"🔥🎬 <b>{title}</b> ✨"
    
    return fallback


# Test function
if __name__ == '__main__':
    test_files = [
        "Jia Lissa - Midnight Ride.mp4",
        "Ariana Marie - Call Me.mp4",
        "Vixen.23.01.15.Alice.Visby.XXX.1080p.mp4"
    ]
    
    for filename in test_files:
        print(f"\n{'='*60}")
        print(f"Processing: {filename}")
        print('='*60)
        caption = process_video_caption(filename)
        if caption:
            print(f"✅ Caption:\n{caption}")
        else:
            print("❌ No match found in either database")
