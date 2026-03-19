from __future__ import annotations

from pathlib import Path
from datetime import datetime

from app.config import EXPORTS_DIR
from app.schemas import DecisionOutput


def export_memo(case_name: str, result: DecisionOutput) -> Path:
    safe_name = case_name.lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORTS_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(result.memo_markdown, encoding="utf-8")
    return path
