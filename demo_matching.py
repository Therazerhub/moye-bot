#!/usr/bin/env python3
"""
Demo script showing matching improvements for StashDB integration
Compares old (difflib) vs new (rapidfuzz + phonetic + n-gram) matching
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import difflib
from matching_utils import (
    calculate_similarity,
    calculate_partial_similarity,
    calculate_token_similarity,
    phonetic_match,
    ngram_similarity,
    combined_similarity,
    enhanced_performer_match,
    normalize_single_char_name,
    handle_concatenated_title,
    RAPIDFUZZ_AVAILABLE,
    JELLYFISH_AVAILABLE,
)

def old_calculate_similarity(str1, str2):
    """Old method using difflib"""
    if not str1 or not str2:
        return 0.0
    import re
    clean1 = re.sub(r'[^\w\s]', '', str1.lower()).strip()
    clean2 = re.sub(r'[^\w\s]', '', str2.lower()).strip()
    return difflib.SequenceMatcher(None, clean1, clean2).ratio()


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_comparison(test_name, str1, str2):
    """Print before/after comparison for a test case"""
    print(f"\n📁 {test_name}")
    print(f"   String 1: '{str1}'")
    print(f"   String 2: '{str2}'")
    
    old_score = old_calculate_similarity(str1, str2)
    new_score = calculate_similarity(str1, str2)
    partial_score = calculate_partial_similarity(str1, str2)
    token_score = calculate_token_similarity(str1, str2)
    
    print(f"\n   BEFORE (difflib):        {old_score:.1%}")
    print(f"   AFTER (rapidfuzz):")
    print(f"     - WRatio:              {new_score:.1%}")
    print(f"     - Partial ratio:       {partial_score:.1%}")
    print(f"     - Token sort:          {token_score:.1%}")
    
    improvement = ((new_score - old_score) / old_score * 100) if old_score > 0 else 0
    if new_score > old_score:
        print(f"   🚀 Improvement: +{improvement:.0f}%")


def print_phonetic_comparison(name1, name2):
    """Print phonetic matching comparison"""
    print(f"\n🔊 Phonetic Test: '{name1}' vs '{name2}'")
    
    old_score = old_calculate_similarity(name1, name2)
    new_fuzzy = calculate_similarity(name1, name2)
    phonetic_score = phonetic_match(name1, name2)
    enhanced = enhanced_performer_match(name1, name2)
    
    print(f"   BEFORE (difflib):        {old_score:.1%}")
    print(f"   AFTER (fuzzy only):      {new_fuzzy:.1%}")
    if JELLYFISH_AVAILABLE:
        print(f"   AFTER (phonetic only):   {phonetic_score:.1%}")
        print(f"   AFTER (combined):        {enhanced:.1%}")
        if phonetic_score > new_fuzzy:
            print(f"   ✅ Phonetic matching helped!")
    else:
        print(f"   ⚠️  jellyfish not installed - phonetic matching unavailable")


def print_ngram_comparison(str1, str2):
    """Print n-gram comparison for concatenated words"""
    print(f"\n🔗 N-gram Test: '{str1}' vs '{str2}'")
    
    old_score = old_calculate_similarity(str1, str2)
    new_score = calculate_similarity(str1, str2)
    bigram = ngram_similarity(str1, str2, n=2)
    trigram = ngram_similarity(str1, str2, n=3)
    combined, details = combined_similarity(str1, str2, debug=True)
    
    print(f"   BEFORE (difflib):        {old_score:.1%}")
    print(f"   AFTER (rapidfuzz):       {new_score:.1%}")
    print(f"   Bigram similarity:       {bigram:.1%}")
    print(f"   Trigram similarity:      {trigram:.1%}")
    print(f"   Combined score:          {combined:.1%}")
    
    if combined > old_score:
        improvement = ((combined - old_score) / old_score * 100) if old_score > 0 else 0
        print(f"   🚀 Improvement: +{improvement:.0f}%")


def print_edge_case(filename, expected_performer=None, expected_title=None):
    """Print edge case analysis"""
    print(f"\n📄 Edge Case: {filename}")
    
    # Test single-char name normalization
    if "JMac" in filename or "J Mac" in filename:
        normalized = normalize_single_char_name("JMac")
        print(f"   JMac → '{normalized}'")
    
    # Test concatenated title handling
    if "BigTitsAtWork" in filename:
        split = handle_concatenated_title("BigTitsAtWork")
        print(f"   BigTitsAtWork → '{split}'")
    
    # Test phonetic matching
    if "Caitlyn" in filename:
        print(f"   Caitlyn vs Kaitlyn: {phonetic_match('Caitlyn', 'Kaitlyn'):.1%}")


def main():
    print_header("STASH BOT MATCHING IMPROVEMENTS DEMO")
    print(f"\n📚 Libraries available:")
    print(f"   rapidfuzz: {'✅' if RAPIDFUZZ_AVAILABLE else '❌'}")
    print(f"   jellyfish: {'✅' if JELLYFISH_AVAILABLE else '❌'}")
    
    # ========================================================================
    # 1. Basic similarity comparisons
    # ========================================================================
    print_header("1. BASIC SIMILARITY IMPROVEMENTS")
    
    print_comparison(
        "Standard match",
        "Riley Reid Massage",
        "Riley Reid Massage"
    )
    
    print_comparison(
        "Case insensitive",
        "Riley Reid",
        "riley reid"
    )
    
    print_comparison(
        "Special chars",
        "Riley-Reid",
        "Riley Reid"
    )
    
    # ========================================================================
    # 2. Token/order independent matching
    # ========================================================================
    print_header("2. ORDER-INDEPENDENT MATCHING")
    
    print_comparison(
        "Word order reversed",
        "Riley Reid - Massage",
        "Massage - Riley Reid"
    )
    
    print_comparison(
        "Studio at end vs start",
        "Riley Reid - Massage - Brazzers",
        "Brazzers - Riley Reid - Massage"
    )
    
    # ========================================================================
    # 3. Phonetic matching
    # ========================================================================
    print_header("3. PHONETIC MATCHING (Caitlyn vs Kaitlyn)")
    
    print_phonetic_comparison("Caitlyn", "Kaitlyn")
    print_phonetic_comparison("Sofia", "Sophia")
    print_phonetic_comparison("Stephen", "Steven")
    print_phonetic_comparison("Smith", "Smyth")
    
    # ========================================================================
    # 4. N-gram similarity for concatenated words
    # ========================================================================
    print_header("4. N-GRAM SIMILARITY (Concatenated Words)")
    
    print_ngram_comparison(
        "BigTitsAtWork",
        "Big Tits At Work"
    )
    
    print_ngram_comparison(
        "MyDadsHotGirlfriend",
        "My Dads Hot Girlfriend"
    )
    
    print_ngram_comparison(
        "BigTitsAtWork",
        "Big Boobs At Work"  # Different but similar
    )
    
    # ========================================================================
    # 5. Edge cases
    # ========================================================================
    print_header("5. EDGE CASES")
    
    test_files = [
        ("Brazzers - J Mac - Big Tits At Work.mp4", "J Mac", "Big Tits At Work"),
        ("NaughtyAmerica - Caitlyn Smith - My Dads Hot Girlfriend.mp4", "Caitlyn Smith", "My Dads Hot Girlfriend"),
        ("Brazzers_BigTitsAtWork_JMac.mp4", "J Mac", "Big Tits At Work"),
        ("Riley Reid - Massage - Brazzers.mp4", "Riley Reid", "Massage"),
    ]
    
    for filename, expected_perf, expected_title in test_files:
        print_edge_case(filename, expected_perf, expected_title)
    
    # ========================================================================
    # 6. Combined scoring example
    # ========================================================================
    print_header("6. COMBINED SCORING EXAMPLE")
    
    test_pairs = [
        ("Big Tits At Work", "BigTitsAtWork"),
        ("Riley Reid Massage", "Massage Riley Reid"),
        ("My Dads Hot Girlfriend", "My Dad's Hot Girlfriend"),
    ]
    
    for str1, str2 in test_pairs:
        score, details = combined_similarity(str1, str2, debug=True)
        print(f"\n   '{str1}' vs '{str2}':")
        print(f"   Final score: {score:.1%}")
        print(f"   Components:")
        for key, val in details.items():
            if key != 'final':
                print(f"     - {key}: {val:.1%}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_header("SUMMARY")
    print("""
✅ IMPROVEMENTS IMPLEMENTED:

1. rapidfuzz - 10-100x faster than difflib, better algorithms
   - WRatio: Weighted combination of multiple algorithms
   - Partial ratio: Good for substring matching
   - Token sort: Order-independent matching

2. Phonetic matching (jellyfish)
   - Handles Caitlyn/Kaitlyn, Sofia/Sophia, etc.
   - Uses Soundex, Metaphone, and NYSIIS algorithms

3. N-gram similarity
   - Great for concatenated words (BigTitsAtWork → Big Tits At Work)
   - 2-gram and 3-gram overlap measurement

4. Combined scoring
   - Weighted combination of all algorithms
   - More robust than any single method

5. Edge case handling
   - J Mac / JMac normalization
   - Concatenated word splitting
   - Single-letter first name handling

📦 NEW REQUIREMENTS:
   - rapidfuzz (installed: {})
   - jellyfish (installed: {})
""".format('✅' if RAPIDFUZZ_AVAILABLE else '❌',
           '✅' if JELLYFISH_AVAILABLE else '❌'))


if __name__ == '__main__':
    main()