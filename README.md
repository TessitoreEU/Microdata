# JSON Section Checker

A Streamlit web app that runs LLM-based checks against sections of an uploaded JSON document
and reports the results.

## How it works

1. **Upload** a JSON file whose content is organized into a numbered section tree (`1`, `1.1`,
   `2`, `2.1`, ...). See `sample_data/MICRODATA18822_hierarchical.json` for a real example: a
   nested dict keyed by section id, where each section can carry a `title` plus either a
   `content` string, a `tables` list of `{"label", "value"}` rows, or nothing but nested
   sub-sections. Non-numeric top-level keys (e.g. `_metadata`) are ignored as metadata, not
   sections. A flat `{"1": "text", "1.1": "text"}` dict or a list of `{"id", "title", "content"}`
   objects are also accepted.
2. **Checks** live as JSON files in the `checks/` directory (every `*.json` file there is loaded
   automatically). A checks file mirrors the shape of the section tree it targets: any section
   entry can carry an `elements_to_be_included_or_confirmed` list, and each item's `text` becomes
   one check run against that section id. See `checks/sample_checks.json`:
   ```json
   {
     "6": {
       "6.2": {
         "title": "Anonymisation of results",
         "elements_to_be_included_or_confirmed": [
           {"text": "The specific confidentiality thresholds ... will be applied."},
           {"text": "No confidential information can be inferred ..."}
         ]
       }
     }
   }
   ```
3. **Run**: for every check, the app builds a prompt from the required element's text and the
   content of its target section, and asks an OpenAI chat model (standard OpenAI API) to respond
   with a `PASS` / `FAIL` / `NA` verdict plus a short explanation. Results are appended to
   `results/results.json`. If a check's target section isn't present in the uploaded file, it's
   recorded as an `ERROR` row instead of being silently skipped.
4. **Report** tab: pick a run (or view all runs), see pass/fail/NA/error counts, filter the table
   by status, and download it as CSV.

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # or paste it into the sidebar at runtime
streamlit run app.py
```

Streamlit serves the GUI at `http://localhost:8501` by default; point a reverse proxy at it (or
use `streamlit run app.py --server.port ... --server.address 0.0.0.0`) to host it on a server.

## Adding your own checks

Drop a new file into `checks/`, nesting it to match the section(s) it targets:

```json
{
  "1": {
    "1.1": {
      "elements_to_be_included_or_confirmed": [
        {"text": "What must be true about section 1.1"}
      ]
    }
  }
}
```

## Project layout

```
app.py                   Streamlit GUI (upload, run, report tabs)
core/data_loader.py      Parses the uploaded JSON into Section objects
core/checks_loader.py    Loads check definitions from checks/*.json
core/section_ids.py      Shared helper for recognising section-id keys vs. metadata
core/llm_runner.py       Builds the prompt and calls the OpenAI API
core/results_store.py    Appends/reads results/results.json
core/report.py           Summary stats + table formatting for the Report tab
```

## Notes / assumptions

- The original request was cut off at "Produce a report based on results file and show...", so
  the report tab implements a reasonable default: summary counts, a filterable/sortable table,
  and CSV export. Let me know if you had a specific report format (PDF, charts, grouped by
  section, etc.) in mind and I'll adjust.
- Results accumulate across runs in `results/results.json`; the Report tab lets you look at a
  single run or all runs combined.
- The example check files provided (`Checks1.json` / `Checks2.json`) had a JSON syntax error (an
  extra `}` before the closing `]` of the `elements_to_be_included_or_confirmed` array) — fixed in
  `checks/sample_checks.json`.
