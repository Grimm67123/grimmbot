"""
Persistent RAG memory with TF-IDF semantic search.
"""

import os
import json
import math
import hashlib
import logging
import base64
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import Counter

import numpy as np
from cryptography.fernet import Fernet

logger = logging.getLogger("memory")


@dataclass
class MemoryConfig:
    enabled: bool = True
    max_entries: int = 100
    keep_after_summary: int = 20
    memory_file: str = "data/memory.json"

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        return cls(
            enabled=os.getenv("MEMORY_ENABLED", "true").lower() == "true",
            max_entries=int(os.getenv("MEMORY_MAX_ENTRIES", "100")),
            keep_after_summary=int(os.getenv("MEMORY_KEEP_AFTER_SUMMARY", "20")),
            memory_file=os.getenv("MEMORY_FILE", "data/memory.json"),
        )


@dataclass
class MemoryEntry:
    id: str
    timestamp: str
    task_summary: str
    result_summary: str
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryEntry":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})

    def to_text(self) -> str:
        return f"[{self.timestamp}] Task: {self.task_summary} | Result: {self.result_summary}"


class TextEmbedder:
    """Lightweight TF-IDF with character n-grams for semantic search."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.idf_scores: dict[str, float] = {}
        self.document_count = 0

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower().strip()
        words = []
        current = []
        for char in text:
            if char.isalnum():
                current.append(char)
            else:
                if current:
                    words.append("".join(current))
                    current = []
        if current:
            words.append("".join(current))

        tokens = list(words)
        for word in words:
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    tokens.append(f"#{word[i:i+3]}#")
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")
        return tokens

    def _hash_token(self, token: str) -> int:
        return int(hashlib.sha256(token.encode()).hexdigest(), 16) % self.dim

    def update_idf(self, documents: list[str]):
        self.document_count = len(documents)
        doc_freq: Counter = Counter()
        for doc in documents:
            for token in set(self._tokenize(doc)):
                doc_freq[token] += 1
        self.idf_scores = {
            token: math.log((self.document_count + 1) / (freq + 1)) + 1
            for token, freq in doc_freq.items()
        }

    def embed(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dim
        tf = Counter(tokens)
        max_tf = max(tf.values())
        vector = np.zeros(self.dim, dtype=np.float64)
        for token, count in tf.items():
            normalized_tf = 0.5 + 0.5 * (count / max_tf)
            idf = self.idf_scores.get(token, 1.0)
            weight = normalized_tf * idf
            idx = self._hash_token(token)
            sign = 1 if int(hashlib.md5(token.encode()).hexdigest(), 16) % 2 == 0 else -1
            vector[idx] += sign * weight
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_np, b_np = np.array(a), np.array(b)
    dot = np.dot(a_np, b_np)
    norm_a, norm_b = np.linalg.norm(a_np), np.linalg.norm(b_np)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


# Encryption removed as requested for host-based readable storage.



class MemoryStore:
    """Per-profile persistent memory with TF-IDF search."""

    def __init__(self, profile: str, config: Optional[MemoryConfig] = None):
        self.profile = profile
        self.config = config or MemoryConfig.from_env()
        self.entries: list[MemoryEntry] = []
        self.summaries: list[str] = []
        self.embedder = TextEmbedder(dim=512)
        self._pending_summarization = False
        self._memory_file = Path(self.config.memory_file)
        self._load()

    def _ensure_dir(self):
        if self._memory_file.parent:
            self._memory_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self._memory_file.exists():
            return
        try:
            full_data = json.loads(self._memory_file.read_text())
            data = full_data.get(self.profile, {})
            if data:
                self.entries = [MemoryEntry.from_dict(e) for e in data.get("entries", [])]
                self.summaries = data.get("summaries", [])
                self._rebuild_idf()
        except Exception as exc:
            logger.error("Failed to load memory for '%s': %s", self.profile, exc)

    def _save(self):
        try:
            full_data = {}
            if self._memory_file.exists():
                try:
                    full_data = json.loads(self._memory_file.read_text())
                except:
                    pass
            
            full_data[self.profile] = {
                "entries": [e.to_dict() for e in self.entries],
                "summaries": self.summaries,
            }
            self._memory_file.write_text(json.dumps(full_data, indent=2))
        except Exception as exc:
            logger.error("Failed to save memory: %s", exc)

    def _rebuild_idf(self):
        if self.entries:
            documents = [f"{e.task_summary} {e.result_summary}" for e in self.entries]
            self.embedder.update_idf(documents)
            for entry in self.entries:
                entry.embedding = self.embedder.embed(
                    f"{entry.task_summary} {entry.result_summary}"
                )

    @property
    def needs_summarization(self) -> bool:
        return len(self.entries) >= self.config.max_entries

    def add(self, task: str, result: str, tags: Optional[list[str]] = None):
        if not self.config.enabled:
            return
        entry = MemoryEntry(
            id=hashlib.md5(
                f"{task}{result}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12],
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            task_summary=task[:200],
            result_summary=result[:500],
            tags=tags or [],
        )
        self.entries.append(entry)
        self._rebuild_idf()
        if self.needs_summarization:
            self._pending_summarization = True
        self._save()

    def request_summarization(self) -> str:
        if not self._pending_summarization:
            return "No summarization needed."
        if len(self.entries) <= self.config.keep_after_summary:
            self._pending_summarization = False
            return "Not enough entries to summarize."

        to_summarize = self.entries[:-self.config.keep_after_summary]
        self.entries = self.entries[-self.config.keep_after_summary:]

        parts = [f"- {e.task_summary}: {e.result_summary[:100]}" for e in to_summarize]
        summary = (
            f"[Summary of {len(to_summarize)} tasks from "
            f"{to_summarize[0].timestamp} to {to_summarize[-1].timestamp}]:\n"
            + "\n".join(parts[:20])
        )
        if len(parts) > 20:
            summary += f"\n...and {len(parts) - 20} more tasks."

        self.summaries.append(summary)
        if len(self.summaries) > 5:
            self.summaries = self.summaries[-5:]

        self._rebuild_idf()
        self._pending_summarization = False
        self._save()
        return f"Summarized {len(to_summarize)} entries. {len(self.entries)} remain."

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        if not self.entries:
            return []
        query_embedding = self.embedder.embed(query)
        scored = []
        for entry in self.entries:
            if entry.embedding:
                score = cosine_similarity(query_embedding, entry.embedding)
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored[:top_k] if score > 0.05]

    def get_context(self, current_task: str, max_chars: int = 2000) -> str:
        if not self.config.enabled:
            return ""
        parts = []
        if self.summaries:
            parts.append("=== Historical Context ===")
            for summary in self.summaries[-2:]:
                parts.append(summary)
        relevant = self.search(current_task, top_k=5)
        if relevant:
            parts.append("\n=== Relevant Past Tasks ===")
            for entry in relevant:
                parts.append(entry.to_text())
        context = "\n".join(parts)
        if len(context) > max_chars:
            context = context[:max_chars] + "\n[...truncated...]"
        return context

    def get_all(self) -> list[MemoryEntry]:
        return self.entries.copy()

    def list_entries(self) -> list[MemoryEntry]:
        return self.entries.copy()

    def clear(self):
        self.reset()

    def reset(self):
        self.entries = []
        self.summaries = []
        self._pending_summarization = False
        self.embedder = TextEmbedder(dim=512)
        self._save()

    def stats(self) -> dict:
        return {
            "profile": self.profile,
            "entries": len(self.entries),
            "summaries": len(self.summaries),
            "enabled": self.config.enabled,
            "max_entries": self.config.max_entries,
            "pending_summarization": self._pending_summarization,
        }


_memory_stores: dict[str, MemoryStore] = {}


def get_memory(profile: str = "default") -> MemoryStore:
    if profile not in _memory_stores:
        _memory_stores[profile] = MemoryStore(profile)
    return _memory_stores[profile]


def reset_memory(profile: str = "default"):
    get_memory(profile).reset()