"""
retriever.py -- Knowledge base search for the local troubleshooting chatbot.
Loads knowledge_base.json, indexes it with TF-IDF, and finds the closest
matching entries for a given question. No external API calls.
"""

import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeBaseRetriever:
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.entries = []
        self.vectorizer = None
        self.matrix = None
        self._load()

    def _load(self):
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)
        else:
            self.entries = []
        self._reindex()

    def _reindex(self):
        if not self.entries:
            self.vectorizer = None
            self.matrix = None
            return
        corpus = [
            f"{e.get('category','')} {e.get('issue','')} {e.get('symptoms','')} {e.get('solution','')}"
            for e in self.entries
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 3):
        if not self.entries or self.vectorizer is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        ranked_idx = scores.argsort()[::-1][:top_k]
        results = []
        for i in ranked_idx:
            if scores[i] <= 0:
                continue
            entry = dict(self.entries[i])
            entry["score"] = round(float(scores[i]), 3)
            results.append(entry)
        return results

    def add_entry(self, category: str, issue: str, symptoms: str, solution: str):
        new_id = f"kb-{len(self.entries) + 1:04d}"
        entry = {
            "id": new_id,
            "category": category,
            "issue": issue,
            "symptoms": symptoms,
            "solution": solution,
        }
        self.entries.append(entry)
        self._save()
        self._reindex()
        return entry

    def _save(self):
        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2)
