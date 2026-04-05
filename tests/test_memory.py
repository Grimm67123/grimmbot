"""
Tests for memory.py — MemoryStore, TextEmbedder, encryption, search.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory import (
    MemoryConfig, MemoryEntry, MemoryStore, TextEmbedder,
    cosine_similarity, get_memory, reset_memory,
)


# ══════════════════════════════════════════════════════════════════════════════
# TextEmbedder
# ══════════════════════════════════════════════════════════════════════════════


class TestTextEmbedder:
    def test_embed_returns_correct_dimension(self):
        embedder = TextEmbedder(dim=256)
        vec = embedder.embed("Hello world")
        assert len(vec) == 256

    def test_embed_empty_string(self):
        embedder = TextEmbedder(dim=128)
        vec = embedder.embed("")
        assert len(vec) == 128
        assert all(v == 0.0 for v in vec)

    def test_embed_normalized(self):
        embedder = TextEmbedder(dim=512)
        vec = embedder.embed("Test normalization of embeddings")
        import numpy as np
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-6 or norm == 0.0

    def test_similar_texts_have_high_similarity(self):
        embedder = TextEmbedder(dim=512)
        embedder.update_idf(["cat sat on mat", "dog sat on rug", "fish in water"])
        v1 = embedder.embed("cat sat on mat")
        v2 = embedder.embed("cat sat on rug")
        sim = cosine_similarity(v1, v2)
        assert sim > 0.3  # should be reasonably similar

    def test_dissimilar_texts_have_low_similarity(self):
        embedder = TextEmbedder(dim=512)
        embedder.update_idf(["machine learning algorithms", "baking chocolate cake recipe"])
        v1 = embedder.embed("machine learning algorithms")
        v2 = embedder.embed("baking chocolate cake recipe")
        sim = cosine_similarity(v1, v2)
        assert sim < 0.5  # should be dissimilar

    def test_update_idf(self):
        embedder = TextEmbedder()
        embedder.update_idf(["hello world", "hello python", "foo bar"])
        assert embedder.document_count == 3
        assert len(embedder.idf_scores) > 0

    def test_tokenize_handles_special_chars(self):
        embedder = TextEmbedder()
        tokens = embedder._tokenize("Hello, world! Test-123")
        assert "hello" in tokens
        assert "world" in tokens


# ══════════════════════════════════════════════════════════════════════════════
# Cosine Similarity
# ══════════════════════════════════════════════════════════════════════════════


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.5, 0.3]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        assert abs(cosine_similarity(v1, v2)) < 1e-6

    def test_zero_vector(self):
        v1 = [0.0, 0.0]
        v2 = [1.0, 2.0]
        assert cosine_similarity(v1, v2) == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Encryption
# ══════════════════════════════════════════════════════════════════════════════


# Encryption removed as requested for host-based readable storage.



# ══════════════════════════════════════════════════════════════════════════════
# MemoryEntry
# ══════════════════════════════════════════════════════════════════════════════


class TestMemoryEntry:
    def test_to_dict_and_back(self):
        entry = MemoryEntry(
            id="abc123",
            timestamp="2026-04-03 12:00",
            task_summary="Test task",
            result_summary="Test result",
            tags=["test"],
            embedding=[0.1, 0.2, 0.3],
        )
        d = entry.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.id == "abc123"
        assert restored.task_summary == "Test task"
        assert restored.tags == ["test"]

    def test_to_text(self):
        entry = MemoryEntry(
            id="x", timestamp="2026-01-01",
            task_summary="Browse GitHub", result_summary="Found repos",
        )
        text = entry.to_text()
        assert "Browse GitHub" in text
        assert "Found repos" in text


# ══════════════════════════════════════════════════════════════════════════════
# MemoryStore
# ══════════════════════════════════════════════════════════════════════════════


class TestMemoryStore:
    @pytest.fixture
    def mem_config(self, tmp_path):
        return MemoryConfig(
            enabled=True,
            max_entries=5,
            keep_after_summary=2,
            memory_file=str(tmp_path / "memory.json"),
        )

    @pytest.fixture
    def store(self, mem_config):
        return MemoryStore("test_profile", mem_config)

    def test_add_entry(self, store):
        store.add("Open browser", "Browser opened")
        assert len(store.entries) == 1

    def test_search_finds_relevant(self, store):
        store.add("Navigate to GitHub", "Found repos")
        store.add("Write Python script", "Script created")
        store.add("Read documentation", "Docs summarized")

        results = store.search("GitHub navigation")
        assert len(results) > 0

    def test_search_empty_store(self, store):
        results = store.search("anything")
        assert results == []

    def test_get_context(self, store):
        store.add("Task 1", "Result 1")
        store.add("Task 2", "Result 2")
        ctx = store.get_context("Related query")
        assert isinstance(ctx, str)

    def test_get_context_disabled(self, mem_config):
        mem_config.enabled = False
        store = MemoryStore("disabled", mem_config)
        assert store.get_context("query") == ""

    def test_needs_summarization(self, store):
        for i in range(5):
            store.add(f"Task {i}", f"Result {i}")
        assert store.needs_summarization is True

    def test_request_summarization(self, store):
        for i in range(6):
            store.add(f"Task {i}", f"Result {i}")
        result = store.request_summarization()
        assert "Summarized" in result
        assert len(store.entries) == 2  # keep_after_summary

    def test_reset(self, store):
        store.add("Something", "Result")
        store.reset()
        assert len(store.entries) == 0
        assert len(store.summaries) == 0

    def test_persistence_save_and_load(self, mem_config):
        store1 = MemoryStore("persist_test", mem_config)
        store1.add("Persistent task", "Persistent result")
        del store1

        store2 = MemoryStore("persist_test", mem_config)
        assert len(store2.entries) == 1
        assert store2.entries[0].task_summary == "Persistent task"

    def test_stats(self, store):
        store.add("Task", "Result")
        stats = store.stats()
        assert stats["entries"] == 1
        assert stats["profile"] == "test_profile"

    def test_list_entries(self, store):
        store.add("A", "B")
        store.add("C", "D")
        entries = store.list_entries()
        assert len(entries) == 2

    def test_disabled_add_does_nothing(self, mem_config):
        mem_config.enabled = False
        store = MemoryStore("disabled", mem_config)
        store.add("Should not store", "Nothing")
        assert len(store.entries) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Module-level helpers
# ══════════════════════════════════════════════════════════════════════════════


class TestMemoryHelpers:
    def test_get_memory_returns_same_instance(self):
        m1 = get_memory("helper_test_profile")
        m2 = get_memory("helper_test_profile")
        assert m1 is m2

    def test_reset_memory(self):
        m = get_memory("reset_test_profile")
        m.add("task", "result")
        reset_memory("reset_test_profile")
        assert len(m.entries) == 0
