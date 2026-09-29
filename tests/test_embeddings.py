"""Tests for cosine similarity and top_k. No real model or network is needed."""

import math

from app.embeddings import cosine_similarity, get_embeddings, top_k


def test_identical_vectors_score_one():
    assert math.isclose(cosine_similarity([1, 2, 3], [1, 2, 3]), 1.0)


def test_opposite_vectors_score_minus_one():
    assert math.isclose(cosine_similarity([1, 0], [-1, 0]), -1.0)


def test_perpendicular_vectors_score_zero():
    assert math.isclose(cosine_similarity([1, 0], [0, 1]), 0.0)


def test_zero_vector_does_not_crash():
    assert cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0


def test_similarity_ignores_vector_length_only_direction_matters():
    # [2,0] points the same direction as [1,0], just "louder" -> still perfect similarity.
    assert math.isclose(cosine_similarity([1, 0], [2, 0]), 1.0)


def test_top_k_returns_the_closest_items_first():
    items = [
        {"label": "far", "vector": [0, 1]},
        {"label": "close", "vector": [1, 0.01]},
        {"label": "exact", "vector": [1, 0]},
    ]
    result = top_k([1, 0], items, k=2)
    assert [entry["label"] for entry in result] == ["exact", "close"]
    assert result[0]["score"] > result[1]["score"]


def test_top_k_never_returns_more_than_k():
    items = [{"vector": [1, 0]}, {"vector": [0, 1]}, {"vector": [1, 1]}]
    assert len(top_k([1, 0], items, k=1)) == 1


def test_get_embeddings_batches_requests():
    calls = []

    def fake_post(url, body):
        calls.append(body["input"])
        return {"embeddings": [[1.0, 0.0] for _ in body["input"]]}

    vectors = get_embeddings([f"text{i}" for i in range(10)], http_post=fake_post, batch_size=4)
    assert len(vectors) == 10
    assert len(calls) == 3  # 4 + 4 + 2
