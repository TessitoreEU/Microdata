"""Streamlit GUI: upload a sectioned JSON file, run LLM-based checks against it, view a report.

Run with:  streamlit run app.py
"""
import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from openai import OpenAI

from core.checks_loader import load_checks
from core.data_loader import parse_sections
from core.llm_runner import missing_section_result, run_check
from core.report import summarize, to_table_rows
from core.results_store import load_all, save_run

CHECKS_DIR = "checks"

st.set_page_config(page_title="JSON Section Checker", layout="wide")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input(
        "OpenAI API key",
        value=os.environ.get("OPENAI_API_KEY", ""),
        type="password",
        help="Read from the OPENAI_API_KEY environment variable by default. Never stored to disk.",
    )
    model = st.selectbox(
        "Model", ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini", "gemma4-26b-moe"], index=0
    )
    base_url = st.text_input(
        "Base URL (optional)",
        value=os.environ.get("OPENAI_BASE_URL", ""),
        help="Only needed for non-OpenAI, OpenAI-compatible endpoints (e.g. gemma4-26b-moe).",
    )
    st.caption(f"Checks are loaded from `{CHECKS_DIR}/*.json`.")

tab_run, tab_report = st.tabs(["Run Checks", "Report"])

with tab_run:
    st.subheader("1. Load a JSON file")
    uploaded_file = st.file_uploader("Section data (JSON)", type="json")

    sections = {}
    if uploaded_file is not None:
        try:
            sections = parse_sections(uploaded_file.getvalue().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not parse JSON file: {exc}")

        if sections:
            st.success(f"Loaded {len(sections)} section(s): {', '.join(sorted(sections.keys()))}")

    st.subheader("2. Checks to run")
    try:
        checks = load_checks(CHECKS_DIR)
    except ValueError as exc:
        checks = []
        st.error(str(exc))

    if not checks:
        st.warning(f"No checks found in `{CHECKS_DIR}/`. Add check-definition JSON files there.")
    else:
        st.dataframe(
            pd.DataFrame(
                [{"ID": c.id, "Name": c.name, "Section": c.section, "Source": c.source_file} for c in checks]
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("3. Run")
    run_disabled = not sections or not checks or not api_key
    if st.button("Run checks", type="primary", disabled=run_disabled):
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        results = []
        progress = st.progress(0.0, text="Running checks...")
        for i, check in enumerate(checks):
            section = sections.get(check.section)
            if section is None:
                results.append(missing_section_result(check, model, run_id, timestamp))
            else:
                results.append(run_check(client, check, section, model, run_id, timestamp))
            progress.progress((i + 1) / len(checks), text=f"Ran {i + 1}/{len(checks)} checks")
        progress.empty()

        save_run(results)
        st.session_state["last_run_id"] = run_id
        st.success(f"Run `{run_id}` complete: {len(results)} check(s) evaluated. See the Report tab.")
        st.dataframe(pd.DataFrame(to_table_rows(results)), use_container_width=True, hide_index=True)

    if run_disabled:
        missing = []
        if not sections:
            missing.append("a JSON file")
        if not checks:
            missing.append("check definitions")
        if not api_key:
            missing.append("an OpenAI API key")
        st.caption(f"Waiting on: {', '.join(missing)}.")

with tab_report:
    st.subheader("Results report")
    all_results = load_all()

    if not all_results:
        st.info("No results yet. Run some checks in the first tab.")
    else:
        run_ids = sorted({r.run_id for r in all_results}, reverse=True)
        selected_run = st.selectbox("Run", ["All runs"] + run_ids)
        filtered = all_results if selected_run == "All runs" else [r for r in all_results if r.run_id == selected_run]

        stats = summarize(filtered)
        cols = st.columns(5)
        cols[0].metric("Total", stats["total"])
        cols[1].metric("Pass", stats["pass"])
        cols[2].metric("Fail", stats["fail"])
        cols[3].metric("N/A", stats["na"])
        cols[4].metric("Error", stats["error"])

        table = pd.DataFrame(to_table_rows(filtered))
        status_filter = st.multiselect("Filter by status", ["PASS", "FAIL", "NA", "ERROR"])
        if status_filter:
            table = table[table["Status"].isin(status_filter)]

        st.dataframe(table, use_container_width=True, hide_index=True)
        st.download_button(
            "Download as CSV",
            data=table.to_csv(index=False).encode("utf-8"),
            file_name=f"report_{selected_run}.csv",
            mime="text/csv",
        )
