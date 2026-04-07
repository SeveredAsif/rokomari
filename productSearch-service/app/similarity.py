"""
similarity.py
-------------
Computes cosine similarity between search queries and product names.

Why cosine similarity?
---------------------
Cosine similarity measures how "similar" two pieces of text are by:
  1. Converting each text to a vector of numbers (TF-IDF vectorization)
  2. Computing the angle between those vectors (cosine distance)
  3. Returning a score from 0 to 1 (0 = completely different, 1 = identical)

Example:
  query = "history of bangladesh"
  product_1 = "A history of bangladesh"     → similarity_score = 0.95 ✓ very similar
  product_2 = "cooking recipes"             → similarity_score = 0.02 ✗ very different

Why not full-text search (LIKE / ILIKE)?
-----------------------------------------
LIKE is exact matching:
  - "history of" does NOT match "bangladesh history" (word order matters)
  - "history" does NOT match "historic" (no stemming)

Cosine similarity is semantic matching:
  - "history of bangladesh" matches "bangladesh's history" (word order doesn't matter)
  - "history" matches "historic" (after stemming)

Node.js equivalent:
-------------------
In Node.js you'd use the 'natural' or 'compromise' library:
    const natural = require('natural')
    const tokenizer = new natural.WordTokenizer()
    const tfidf = new natural.TfIdf()

Here we use scikit-learn, Python's most popular ML library for text vectorization.
"""

import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _normalize_token(token: str) -> str:
    # Very light stemming/singularization without extra dependencies.
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    tokens = [_normalize_token(tok) for tok in text.split() if tok]
    return " ".join(tokens)


def compute_cosine_similarities(query: str, candidates: list[str]) -> np.ndarray:
    """
    Compute cosine similarity between a query and a list of candidate strings.

    Args:
        query: the search keyword (e.g., "history of bangladesh")
        candidates: list of product names to compare against

    Returns:
        numpy array of shape (len(candidates),) with similarity scores in [0, 1]

    Example:
        >>> compute_cosine_similarities(
        ...     "history book",
        ...     ["A history of bangladesh", "cooking recipes", "history novels"]
        ... )
        array([0.8, 0.1, 0.75])
    """
    if not candidates:
        return np.array([])

    # Normalize both query and candidates to improve plural/singular matching
    # (e.g. "graphics" vs "graphic") and punctuation differences.
    normalized_query = _normalize_text(query)
    normalized_candidates = [_normalize_text(c) for c in candidates]

    # Build a hybrid similarity score:
    # 1) word-level TF-IDF for semantics
    # 2) char-level TF-IDF for morphology/typos
    texts = [normalized_query] + normalized_candidates

    try:
        word_vectorizer = TfidfVectorizer(
            lowercase=False,
            stop_words="english",
            ngram_range=(1, 3),
            max_features=5000,
            sublinear_tf=True,
        )
        word_matrix = word_vectorizer.fit_transform(texts)
        word_sim = cosine_similarity(word_matrix[0], word_matrix[1:])[0]
    except ValueError:
        # Empty vocabulary can happen for degenerate inputs.
        word_sim = np.zeros(len(candidates), dtype=float)

    try:
        char_vectorizer = TfidfVectorizer(
            lowercase=False,
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=8000,
            sublinear_tf=True,
        )
        char_matrix = char_vectorizer.fit_transform(texts)
        char_sim = cosine_similarity(char_matrix[0], char_matrix[1:])[0]
    except ValueError:
        char_sim = np.zeros(len(candidates), dtype=float)

    similarities = 0.7 * word_sim + 0.3 * char_sim

    # Small overlap boost for multi-token queries like "graphics books".
    query_tokens = set(normalized_query.split())
    if query_tokens:
        for i, candidate_text in enumerate(normalized_candidates):
            candidate_tokens = set(candidate_text.split())
            overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens), 1)
            similarities[i] = min(1.0, similarities[i] + 0.15 * overlap)

    return similarities


def rank_by_similarity(similarities: np.ndarray, products: list[dict]) -> list[dict]:
    ranked = []
    for product, score in zip(products, similarities):
        product_with_score = product.copy()
        product_with_score["similarity_score"] = float(score)
        ranked.append(product_with_score)
    ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
    return ranked


def filter_by_threshold(
    similarities: np.ndarray,
    products: list[dict],
    threshold: float = 0.1
) -> list[dict]:
    """
    Filter and rank products by similarity score.

    Args:
        similarities: numpy array of similarity scores (output from compute_cosine_similarities)
        products: list of product dicts to filter
        threshold: minimum similarity score to include (0.0 to 1.0)

    Returns:
        List of product dicts with similarity_score attached, sorted descending by score.
        Only products with score >= threshold are included.

    Example:
        >>> products = [
        ...     {"id": 1, "name": "A history of bangladesh"},
        ...     {"id": 2, "name": "cooking recipes"},
        ...     {"id": 3, "name": "history novels"}
        ... ]
        >>> similarities = np.array([0.8, 0.1, 0.75])
        >>> filter_by_threshold(similarities, products, threshold=0.2)
        [
            {"id": 1, "name": "A history of bangladesh", "similarity_score": 0.8},
            {"id": 3, "name": "history novels", "similarity_score": 0.75}
        ]
    """
    ranked = rank_by_similarity(similarities, products)
    return [item for item in ranked if item["similarity_score"] >= threshold]
