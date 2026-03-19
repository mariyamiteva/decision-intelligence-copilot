from __future__ import annotations

import json
from typing import Iterable

from openai import OpenAI

from app.config import MAX_RETRIEVED_CHUNKS, OPENAI_MODEL
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas import DecisionOutput
from app.retriever import DocumentRetriever, RetrievedChunk


class DecisionEngine:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.retriever = DocumentRetriever(api_key=api_key)

    @staticmethod
    def _build_query(case_data: dict) -> str:
        return json.dumps(case_data, ensure_ascii=False)

    @staticmethod
    def _format_context(chunks: Iterable[RetrievedChunk]) -> str:
        parts = []
        for chunk in chunks:
            parts.append(
                f"SOURCE_ID: {chunk.chunk_id}\n"
                f"TITLE: {chunk.title}\n"
                f"CONTENT: {chunk.text}\n"
            )
        return "\n---\n".join(parts)

    def analyze(self, case_data: dict) -> tuple[DecisionOutput, list[RetrievedChunk]]:
        self.retriever.index_documents()
        chunks = self.retriever.retrieve(self._build_query(case_data), top_k=MAX_RETRIEVED_CHUNKS)
        context = self._format_context(chunks)
        prompt = build_user_prompt(case_data, context)

        completion = self.client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            text_format=DecisionOutput,
        )

        parsed = completion.output_parsed
        if parsed is None:
            raise ValueError("Model did not return a parsable structured response.")
        return parsed, chunks
