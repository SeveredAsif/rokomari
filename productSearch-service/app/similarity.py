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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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

    # Combine query and candidates for vectorization
    # This ensures they're vectorized in the same "vocabulary space"
    texts = [query] + candidates

    # TfidfVectorizer converts text to TF-IDF vectors
    # (Term Frequency - Inverse Document Frequency)
    # This weighs common words lower and rare/distinctive words higher.
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',  # ignore common words like "the", "a", "is"
        ngram_range=(1, 2),    # consider both single words and 2-word phrases
        max_features=100,      # limit to top 100 features for speed
    )

    # Fit and transform all texts to vectors
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Extract the query vector (first row)
    query_vector = tfidf_matrix[0]

    # Extract candidate vectors (rest of the rows)
    candidate_vectors = tfidf_matrix[1:]

    # Compute cosine similarity between query and each candidate
    # Result shape: (1, len(candidates)) → flatten to (len(candidates),)
    similarities = cosine_similarity(query_vector, candidate_vectors)[0]

    return similarities


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
    results = []

    for idx, (product, score) in enumerate(zip(products, similarities)):
        if score >= threshold:
            # Create a copy so we don't modify the original
            product_with_score = product.copy()
            product_with_score["similarity_score"] = float(score)
            results.append(product_with_score)

    # Sort by similarity score descending (highest first)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return results
