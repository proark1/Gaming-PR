"""
Content deduplication using SimHash.

Detects near-duplicate articles across different outlets (e.g., same press release
published on IGN, GameSpot, and Kotaku). Stores a 64-bit fingerprint per article
for fast comparison.
"""
import hashlib
import re
from typing import Optional


def compute_simhash(text: str) -> int:
    """
    Compute a 64-bit SimHash fingerprint for text.

    SimHash preserves similarity: similar documents produce similar hashes.
    Hamming distance between two SimHashes correlates with text similarity.
    """
    if not text:
        return 0

    tokens = _tokenize(text)
    if not tokens:
        return 0

    v = [0] * 64

    for token in tokens:
        token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit:
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """Count the number of differing bits between two hashes."""
    return bin(hash1 ^ hash2).count("1")


def is_duplicate(hash1: int, hash2: int, threshold: int = 10) -> bool:
    """
    Check if two SimHashes indicate duplicate content.

    A hamming distance of <= 10 out of 64 bits indicates ~85% similarity.
    """
    return hamming_distance(hash1, hash2) <= threshold


def similarity_score(hash1: int, hash2: int) -> float:
    """Return a 0.0 to 1.0 similarity score between two SimHashes."""
    dist = hamming_distance(hash1, hash2)
    return 1.0 - (dist / 64.0)


def _tokenize(text: str) -> list[str]:
    """Tokenize text into shingles (3-grams of words) for SimHash."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < 3:
        return words

    # Use 3-word shingles for better similarity detection
    shingles = []
    for i in range(len(words) - 2):
        shingles.append(f"{words[i]}_{words[i+1]}_{words[i+2]}")
    return shingles
