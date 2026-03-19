from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.config import CASES_DIR, OPENAI_API_KEY
from app.data_loader import list_case_files, load_case
from app.memo_generator import export_memo
from app.reasoning import DecisionEngine
from app.schemas import DecisionOutput


DECISION_DESCRIPTIONS = {
    "Option A": "Strong fit / preferred path",
    "Option B": "Viable but with trade-offs",
    "Option C": "Alternative path worth considering",
    "Needs Review": "Insufficient or conflicting information",
    "Not Recommended": "Current evidence does not support proceeding",
}


def render_sidebar() -> Path | None:
    st.sidebar.header("Demo case")
    case_files = list_case_files(CASES_DIR)
    if not case_files:
        st.sidebar.warning("No sample cases found.")
        return None

    labels = {path.stem.replace("_", " ").title(): path for path in case_files}
    selected = st.sidebar.selectbox("Select a sample case", list(labels.keys()))
    st.sidebar.caption("You can also edit the JSON in the main panel before analysis.")
    return labels[selected]


def render_result(result: DecisionOutput, export_path: Path | None) -> None:
    st.subheader("Decision")
    st.metric("Recommendation", result.decision, DECISION_DESCRIPTIONS.get(result.decision, ""))
    st.progress(min(max(result.confidence, 0.0), 1.0), text=f"Confidence: {result.confidence:.0%}")

    st.subheader("Executive summary")
    st.write(result.executive_summary)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Reasoning")
        for item in result.reasoning:
            st.markdown(f"- {item}")

        st.subheader("Risks")
        if result.risks:
            for item in result.risks:
                st.markdown(f"- {item}")
        else:
            st.caption("No material risks highlighted.")

    with col2:
        st.subheader("Missing information")
        if result.missing_information:
            for item in result.missing_information:
                st.markdown(f"- {item}")
        else:
            st.caption("No missing information flagged.")

        st.subheader("Recommended next steps")
        for item in result.recommended_next_steps:
            st.markdown(f"- {item}")

    st.subheader("Evidence")
    for item in result.evidence:
        with st.expander(f"{item.source_title} · {item.source_id}"):
            st.caption(item.relevance)
            st.write(item.excerpt)

    st.subheader("Generated memo")
    st.markdown(result.memo_markdown)

    if export_path:
        st.success(f"Memo exported to: {export_path}")
        st.download_button(
            label="Download memo",
            data=export_path.read_text(encoding="utf-8"),
            file_name=export_path.name,
            mime="text/markdown",
        )


def run_app() -> None:
    st.set_page_config(page_title="Decision Intelligence Copilot", layout="wide")
    st.title("Decision Intelligence Copilot")
    st.caption("Explainable multi-source reasoning with structured outputs and grounded evidence.")

    if not OPENAI_API_KEY:
        st.error("Missing OPENAI_API_KEY. Copy .env.example to .env and add your key.")
        st.stop()

    selected_case = render_sidebar()
    default_case = load_case(selected_case) if selected_case else {}

    st.subheader("Case input")
    raw_case = st.text_area(
        "Edit or paste JSON case data",
        value=json.dumps(default_case, indent=2, ensure_ascii=False),
        height=380,
    )

    analyze = st.button("Analyze case", type="primary")

    if analyze:
        try:
            case_data = json.loads(raw_case)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            st.stop()

        with st.spinner("Retrieving sources and generating structured decision..."):
            engine = DecisionEngine(api_key=OPENAI_API_KEY)
            result, _ = engine.analyze(case_data)
            export_path = export_memo(case_data.get("case_name", "decision_case"), result)

        render_result(result, export_path)
