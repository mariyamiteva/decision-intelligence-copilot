from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from openai import OpenAI

from app.config import CHROMA_DIR, COLLECTION_NAME, DOCS_DIR, EMBEDDING_MODEL
from app.data_loader import list_document_files, read_document


@dataclass
class RetrievedChunk:
    chunk_id: str
    title: str
    text: str
    score: float


class DocumentRetriever:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma.get_or_create_collection(name=COLLECTION_NAME)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> Iterable[str]:
        text = " ".join(text.split())
        start = 0
        while start < len(text):
            end = start + chunk_size
            yield text[start:end]
            if end >= len(text):
                break
            start = end - overlap

    @staticmethod
    def _stable_id(title: str, chunk: str) -> str:
        digest = hashlib.sha1(f"{title}:{chunk}".encode("utf-8")).hexdigest()[:12]
        return f"src_{digest}"

    def index_documents(self, directory: Path = DOCS_DIR) -> int:
        files = list_document_files(directory)
        if not files:
            return 0

        existing_ids = set(self.collection.get(include=[]).get("ids", []))
        new_ids: list[str] = []
        new_docs: list[str] = []
        new_meta: list[dict] = []

        for path in files:
            text = read_document(path)
            title = path.stem.replace("_", " ").title()
            for chunk in self._chunk_text(text):
                chunk_id = self._stable_id(title, chunk)
                if chunk_id in existing_ids:
                    continue
                new_ids.append(chunk_id)
                new_docs.append(chunk)
                new_meta.append({"title": title, "path": str(path)})

        if new_docs:
            embeddings = self._embed(new_docs)
            self.collection.add(ids=new_ids, documents=new_docs, metadatas=new_meta, embeddings=embeddings)

        return len(new_docs)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_embedding = self._embed([query])[0]
        result = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    title=meta.get("title", "Unknown"),
                    text=doc,
                    score=float(distance) if distance is not None else 0.0,
                )
            )
        return chunks
