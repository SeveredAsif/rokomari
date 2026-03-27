"""
similarity.py
-------------
Everything related to cosine similarity lives here.

What IS cosine similarity?
--------------------------
Imagine you want to compare the search query "history book" against two products:
  - Product A: "World History: A Comprehensive Guide"
  - Product B: "Python Programming for Beginners"

To a computer, text is just characters — it can't understand meaning directly.
So we convert text into a list of numbers called a "vector". The idea is:
words that appear in common between two texts push their vectors closer together.

Cosine similarity measures the ANGLE between two vectors:
  - Score of 1.0  → identical meaning (angle = 0°)
  - Score of 0.0  → completely unrelated (angle = 90°)
  - Score of -1.0 → opposite meaning (rarely happens in text)

For "history book" vs product names:
  - vs "World History Guide" → score ≈ 0.7  ✅ above threshold
  - vs "Python Programming"  → score ≈ 0.05 ❌ below threshold

How we convert text to vectors (TF-IDF):
-----------------------------------------
TF-IDF stands for Term Frequency–Inverse Document Frequency.
In plain English:
  - Words that appear a lot in ONE document but rarely in ALL documents
    get a HIGH score (they are distinctive/meaningful).
  - Words like "the", "a", "is" appear everywhere, so they get a LOW score
    (they don't help us distinguish documents).

So "history" in "World History Guide" gets a high weight,
while "a" in the same string gets nearly zero weight.

scikit-learn's TfidfVectorizer does all of this automatically.

Node.js analogy:
----------------
There is no built-in equivalent in Node.js. You would need a library like
'natural' or 'compromise', or call an external ML API. Python's scikit-learn
makes this trivially easy.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import numpy as np


# Default threshold: only return products with similarity score above this.
# 0.1 is intentionally low for a skeleton — tune this upward (e.g. 0.3)
# as you test with real data.
DEFAULT_THRESHOLD = 0.1


def compute_cosine_similarities(query: str, candidates: List[str]) -> List[float]:
    """
    Given a single search query and a list of candidate strings (product names),
    returns a list of similarity scores — one score per candidate.

    Example:
        query      = "history of bangladesh"
        candidates = ["Bangladesh Liberation War", "Python Cookbook", "History of Rome"]
        returns    = [0.72, 0.02, 0.41]

    How it works step by step:
        1. We put the query AND all candidates together into one list.
        2. TfidfVectorizer converts every string into a numeric vector.
        3. cosine_similarity compares the query vector against every candidate vector.
        4. We return those scores as a plain Python list.

    Parameters:
        query      : the search keyword or product name to compare from
        candidates : list of product names (or any strings) to compare against

    Returns:
        List of float scores, same length as candidates.
        Each score is between 0.0 and 1.0.
    """
    if not candidates:
        return []

    # Step 1: combine query + candidates into one corpus
    # The query goes first so its vector is always at index 0
    corpus = [query] + candidates

    # Step 2: fit TF-IDF on the whole corpus, then transform each string
    # fit_transform learns the vocabulary from ALL strings, then vectorizes them
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Step 3: compare row 0 (the query) against rows 1..N (the candidates)
    # cosine_similarity returns a 2D array; we flatten it to a 1D list
    query_vector     = tfidf_matrix[0]           # shape: (1, vocab_size)
    candidate_matrix = tfidf_matrix[1:]          # shape: (N, vocab_size)

    scores = cosine_similarity(query_vector, candidate_matrix)
    # scores is shape (1, N) — squeeze it to a flat list
    return scores[0].tolist()


def filter_by_threshold(
    scores: List[float],
    candidates: List[dict],
    threshold: float = DEFAULT_THRESHOLD
) -> List[dict]:
    """
    Zips similarity scores with candidate dicts, filters out those below
    the threshold, then sorts by score descending (most similar first).

    Parameters:
        scores     : list of floats from compute_cosine_similarities()
        candidates : list of dicts (e.g. product rows as dicts), same order as scores
        threshold  : minimum score to include in results

    Returns:
        Filtered and sorted list of dicts, each with an added "similarity_score" key.

    Example:
        scores     = [0.72, 0.02, 0.41]
        candidates = [{"id":1,"name":"Bangladesh Liberation War"}, ...]
        threshold  = 0.3
        returns    = [
            {"id":1, "name":"Bangladesh Liberation War", "similarity_score": 0.72},
            {"id":3, "name":"History of Rome",           "similarity_score": 0.41},
        ]
    """
    results = []
    for score, candidate in zip(scores, candidates):
        if score >= threshold:
            results.append({**candidate, "similarity_score": round(score, 4)})

    # Sort so highest similarity appears first
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results
