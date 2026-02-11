#!/usr/bin/env python3
"""
Categorize existing videos in the database
Run this to auto-assign categories to all existing videos
"""

import sqlite3
import re
import os

DB_PATH = '/home/ubuntu/.openclaw/workspace/stash_bot/stash.db'

# Domain to category mapping
DOMAIN_CATEGORIES = {
    'brazzers': 'Brazzers',
    'brazzer': 'Brazzers',
    'pornhub': 'Pornhub',
    'ph': 'Pornhub',
    'xvideos': 'XVideos',
    'xnxx': 'XNXX',
    'youporn': 'YouPorn',
    'redtube': 'RedTube',
    'tube8': 'Tube8',
    'spankbang': 'SpankBang',
    'chaturbate': 'Chaturbate',
    'onlyfans': 'OnlyFans',
    'of': 'OnlyFans',
    'manyvids': 'ManyVids',
    'clips4sale': 'Clips4Sale',
    'c4s': 'Clips4Sale',
    'realitykings': 'Reality Kings',
    'rk': 'Reality Kings',
    'bangbros': 'BangBros',
    'naughtyamerica': 'Naughty America',
    'na': 'Naughty America',
    'digitalplayground': 'Digital Playground',
    'dp': 'Digital Playground',
    'mofos': 'Mofos',
    'teamskeet': 'TeamSkeet',
    'fakehub': 'FakeHub',
    'vixen': 'Vixen',
    'tushy': 'Tushy',
    'blacked': 'Blacked',
    'blackedraw': 'Blacked Raw',
    'deeper': 'Deeper',
    'julesjordan': 'Jules Jordan',
    'evilangel': 'Evil Angel',
    'brazzersexxtra': 'Brazzers Exxtra',
    'milf': 'MILF',
    'milfs': 'MILF',
    'stepmom': 'Step Mom',
    'stepsis': 'Step Sister',
    'step': 'Step Family',
    'anal': 'Anal',
    'lesbian': 'Lesbian',
    'threesome': 'Threesome',
    'gangbang': 'Gangbang',
    'blowjob': 'Blowjob',
    'creampie': 'Creampie',
    'interracial': 'Interracial',
    'ebony': 'Ebony',
    'latina': 'Latina',
    'asian': 'Asian',
    'teen': 'Teen',
    'amateur': 'Amateur',
    'homemade': 'Homemade',
    'webcam': 'Webcam',
    'casting': 'Casting',
    'massage': 'Massage',
    'yoga': 'Yoga',
    'gym': 'Gym',
    'office': 'Office',
    'public': 'Public',
    'car': 'Car',
    'outdoor': 'Outdoor',
    'beach': 'Beach',
    'pool': 'Pool',
    'shower': 'Shower',
    'bathroom': 'Bathroom',
    'kitchen': 'Kitchen',
    'bedroom': 'Bedroom',
    'hotel': 'Hotel',
}

def extract_category_from_title(title):
    """Extract category from video title based on domains/keywords"""
    if not title:
        return None
    
    title_lower = title.lower()
    
    # Check for domain patterns
    patterns = [
        r'\[([^\]]+)\]',
        r'\(([^\)]+)\)',
        r'www\.([a-z0-9]+)',
        r'([a-z0-9]+)\.com',
        r'([a-z0-9]+)\.net',
        r'([a-z0-9]+)\.org',
        r'([a-z0-9]+)\.tv',
        r'([a-z0-9]+)\.xxx',
        r'([a-z0-9]+)_',
        r'_([a-z0-9]+)',
        r'-([a-z0-9]+)-',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, title_lower)
        for match in matches:
            clean_match = match.strip().replace('.', '').replace('-', '').replace('_', '')
            if clean_match in DOMAIN_CATEGORIES:
                return DOMAIN_CATEGORIES[clean_match]
    
    # Direct keyword matching
    for keyword, category in DOMAIN_CATEGORIES.items():
        if keyword in title_lower:
            return category
    
    return None

def categorize_all_videos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all videos without categories
    c.execute("SELECT id, title, category FROM videos")
    videos = c.fetchall()
    
    updated = 0
    already_categorized = 0
    no_category_found = 0
    
    print(f"🍑💦 Categorizing {len(videos)} videos...\n")
    
    for video_id, title, existing_category in videos:
        # Skip if already has a category
        if existing_category:
            already_categorized += 1
            continue
        
        # Extract category from title
        category = extract_category_from_title(title)
        
        if category:
            c.execute("UPDATE videos SET category = ? WHERE id = ?", (category, video_id))
            updated += 1
            if updated % 100 == 0:
                print(f"✅ Categorized {updated} videos...")
        else:
            no_category_found += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Done!")
    print(f"✅ Newly categorized: {updated}")
    print(f"📁 Already had category: {already_categorized}")
    print(f"❓ No category found: {no_category_found}")

if __name__ == "__main__":
    categorize_all_videos()
