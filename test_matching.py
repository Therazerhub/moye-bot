#!/usr/bin/env python3
"""Test script for matching_utils.py"""

from matching_utils import (
    ngram_similarity, combined_similarity, calculate_similarity,
    enhanced_performer_match, calculate_match_confidence, phonetic_match
)
from rapidfuzz import fuzz

print('=' * 60)
print('N-GRAM SIMILARITY EXAMPLES')
print('=' * 60)
print()
print("BigTitsAtWork vs 'Big Tits At Work' (n=2): " + str(round(ngram_similarity('BigTitsAtWork', 'Big Tits At Work', 2) * 100, 2)) + "%")
print("BigTitsAtWork vs 'Big Tits At Work' (n=3): " + str(round(ngram_similarity('BigTitsAtWork', 'Big Tits At Work', 3) * 100, 2)) + "%")
print("Riley Reid vs 'RileyReid' (n=2): " + str(round(ngram_similarity('Riley Reid', 'RileyReid', 2) * 100, 2)) + "%")
print("Caitlyn vs 'Kaitlyn' (n=2): " + str(round(ngram_similarity('Caitlyn', 'Kaitlyn', 2) * 100, 2)) + "%")
print()

print('=' * 60)
print('COMBINED SIMILARITY vs OLD SIMILARITY')
print('=' * 60)
print()

tests = [
    ('BigTitsAtWork', 'Big Tits At Work'),
    ('RileyReid - Massage', 'Riley Reid - Massage'),
    ('Massage - Riley Reid', 'Riley Reid - Massage'),
    ('JMac.Big.Tits.At.Work', 'J Mac - Big Tits At Work'),
]

for s1, s2 in tests:
    old = calculate_similarity(s1, s2)
    new = combined_similarity(s1, s2)
    diff = new - old
    print(s1[:30].ljust(32) + " | Old: " + str(round(old * 100, 2)).rjust(6) + "% | New: " + str(round(new * 100, 2)).rjust(6) + "% | Diff: " + ("+" if diff >= 0 else "") + str(round(diff * 100, 2)) + "%")

print()
print('=' * 60)
print('ENHANCED PERFORMER MATCH (with phonetic)')
print('=' * 60)
print()

pairs = [('Caitlyn', 'Kaitlyn'), ('Sophia', 'Sofia'), ('Riley', 'Rylee'), ('Riley Reid', 'Riley Reid')]
for s1, s2 in pairs:
    fuzzy = fuzz.WRatio(s1, s2) / 100.0
    phonetic = phonetic_match(s1, s2)
    enhanced = enhanced_performer_match(s1, s2)
    print(s1 + " vs " + s2 + ":")
    print("  Fuzzy:    " + str(round(fuzzy * 100, 2)).rjust(6) + "%")
    print("  Phonetic: " + str(round(phonetic * 100, 2)).rjust(6) + "%")
    print("  Enhanced: " + str(round(enhanced * 100, 2)).rjust(6) + "%")
    print()

print('=' * 60)
print('CONFIDENCE SCORING OUTPUT FORMAT')
print('=' * 60)
print()

scene = {
    'title': 'Big Tits At Work',
    'studio': {'name': 'Brazzers'},
    'performers': [{'performer': {'name': 'Riley Reid', 'gender': 'FEMALE'}}]
}
result = calculate_match_confidence(
    filename='test.mp4',
    scene_data=scene,
    parsed_performer='Riley Reid',
    parsed_title='Big Tits At Work',
    detected_studio='Brazzers'
)

print("Sample match confidence (with studio match):")
print("  title_similarity:     " + str(round(result['title_similarity'] * 100, 2)) + "%")
print("  performer_similarity: " + str(round(result['performer_similarity'] * 100, 2)) + "%")
studio_str = 'Bonus!' if result['studio_match'] else 'No match'
print("  studio_match:         " + str(round(result['studio_match'] * 100, 2)) + "% (" + studio_str + ")")
print("  final_score:          " + str(round(result['final_score'] * 100, 2)) + "%")
print("  strong_match_bonus:   " + str(result.get('strong_match_bonus', False)))
print()

# Test without studio match
print("Sample match confidence (without studio match):")
result2 = calculate_match_confidence(
    filename='test.mp4',
    scene_data=scene,
    parsed_performer='Riley Reid',
    parsed_title='Big Tits At Work',
    detected_studio=None
)
print("  title_similarity:     " + str(round(result2['title_similarity'] * 100, 2)) + "%")
print("  performer_similarity: " + str(round(result2['performer_similarity'] * 100, 2)) + "%")
print("  studio_match:         " + str(round(result2['studio_match'] * 100, 2)) + "%")
print("  final_score:          " + str(round(result2['final_score'] * 100, 2)) + "%")
print()

print('=' * 60)
print('ALL TESTS COMPLETED SUCCESSFULLY!')
print('=' * 60)
