"""Runs a single check against a section's text using the OpenAI Chat Completions API."""
import json

from openai import OpenAI

from core.models import Check, CheckResult, Section

SYSTEM_PROMPT = (
    "You are a meticulous compliance and quality-assurance reviewer. "
    "You will be given a document section and a required element that must be included in, "
    "or confirmed by, that section. "
    "Respond ONLY with a JSON object of the form "
    '{"status": "PASS" | "FAIL" | "NA", "explanation": "<one or two sentence justification>"}. '
    "PASS means the section clearly includes or confirms the required element. "
    "FAIL means the section contradicts it or omits it despite otherwise being on topic. "
    "Use NA only if the section does not contain enough information to evaluate the element."
)


def build_user_prompt(check: Check, section: Section) -> str:
    return (
        f"Section {section.id} - {section.title}\n"
        f"---\n{section.content}\n---\n\n"
        f"Required element to be included or confirmed (check {check.id}):\n{check.text}"
    )


def run_check(
    client: OpenAI,
    check: Check,
    section: Section,
    model: str = "gpt-4o-mini",
    run_id: str = "",
    timestamp: str = "",
) -> CheckResult:
    user_prompt = build_user_prompt(check, section)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        status = str(parsed.get("status", "ERROR")).upper()
        explanation = parsed.get("explanation", "")
    except Exception as exc:  # noqa: BLE001 - surface any failure as an ERROR result row
        raw = None
        status = "ERROR"
        explanation = f"LLM call failed: {exc}"

    return CheckResult(
        run_id=run_id,
        timestamp=timestamp,
        check_id=check.id,
        check_name=check.name,
        section_id=section.id,
        section_found=True,
        model=model,
        status=status,
        explanation=explanation,
        raw_response=raw,
    )


def missing_section_result(check: Check, model: str, run_id: str, timestamp: str) -> CheckResult:
    return CheckResult(
        run_id=run_id,
        timestamp=timestamp,
        check_id=check.id,
        check_name=check.name,
        section_id=check.section,
        section_found=False,
        model=model,
        status="ERROR",
        explanation=f"Section {check.section} not found in the uploaded JSON file.",
        raw_response=None,
    )
