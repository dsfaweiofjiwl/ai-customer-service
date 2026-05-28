import os
import re
from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import config


class RAGEngine:
    def __init__(self):
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.chunks: List[str] = []
        self.sources: List[str] = []
        self.index: faiss.IndexFlatIP | None = None

    def _split_markdown(self, text: str, source_name: str) -> List[Tuple[str, str, str]]:
        """Split markdown by ## headings. Returns [(chunk, source_label), ...]."""
        sections = re.split(r"\n(?=## )", text)
        results = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            lines = sec.split("\n")
            title = lines[0].replace("#", "").strip()
            body = "\n".join(lines[1:]).strip()
            if len(body) < 20:
                continue
            label = f"{source_name} - {title}"
            results.append((body, label))
        return results

    def load_knowledge_dir(self, directory: str):
        all_items = []
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith((".md", ".json", ".txt")):
                continue
            fpath = os.path.join(directory, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
            if fname.endswith(".json"):
                items = self._parse_json(text, fname)
            else:
                items = self._split_markdown(text, fname.replace(".md", ""))
            all_items.extend(items)
        self._build_index(all_items)

    def _parse_json(self, text: str, fname: str) -> List[Tuple[str, str]]:
        import json
        data = json.loads(text)
        items = []
        for entry in data:
            q = entry.get("question", "")
            a = entry.get("answer", "")
            if q and a:
                items.append((a, f"{fname} - {q}"))
        return items

    def _build_index(self, items: List[Tuple[str, str]]):
        if not items:
            return
        self.chunks = [item[0] for item in items]
        self.sources = [item[1] for item in items]
        embeddings = self.model.encode(self.chunks, normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        q_emb = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(np.array(q_emb, dtype=np.float32), top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            if score < config.SIMILARITY_THRESHOLD:
                continue
            results.append((self.chunks[idx], self.sources[idx], float(score)))
        return results


rag_engine = RAGEngine()
