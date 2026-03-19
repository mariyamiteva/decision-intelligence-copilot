from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = DATA_DIR / "documents"
CASES_DIR = DATA_DIR / "cases"
CHROMA_DIR = BASE_DIR / ".chroma"
EXPORTS_DIR = BASE_DIR / "exports"

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "decision_copilot_docs"
MAX_RETRIEVED_CHUNKS = 5

EXPORTS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
