import json
import os
from pathlib import Path

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:4b"
)


def load_evidence():
    evidence_path = (
        Path(__file__).parent
        / "pria_evidence.json"
    )

    with open(
        evidence_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def build_prompt(evidence):
    evidence_json = json.dumps(
        evidence,
        indent=2
    )

    prompt = f"""
You are PRIA:
Partner API Regression Investigator Agent.

Your job is to investigate software regression failures.

IMPORTANT RULES:

1. Use ONLY the evidence provided.
2. Do not invent PRs, files, tests, commits, or causes.
3. Clearly separate evidence from assumptions.
4. Identify the most probable root cause.
5. Explain why the code change is related to the failed test.
6. If evidence is insufficient, say so.
7. Give a confidence level: High, Medium, or Low.

Analyze this investigation evidence:

{evidence_json}

Return the investigation report in this exact format:

PRIA ROOT CAUSE REPORT

Failed Test:
<test name>

Expected:
<expected result>

Actual:
<actual result>

Suspected PR:
<PR number and title>

Suspected File:
<file>

Probable Root Cause:
<clear explanation>

Evidence:
- <evidence 1>
- <evidence 2>
- <evidence 3>

Confidence:
<High / Medium / Low>

Recommended Action:
<what developer should investigate or change>

Do not include information that is not supported by the evidence.
"""

    return prompt


def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["response"]


def save_report(report):
    output_path = (
        Path(__file__).parent
        / "pria_report.md"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(report)

    return output_path


def main():

    print(
        "\n========== PRIA AI ANALYSIS ==========\n"
    )

    evidence = load_evidence()

    print("Evidence loaded successfully.")

    prompt = build_prompt(evidence)

    print(
        f"Sending evidence to Ollama model: {MODEL}"
    )

    report = call_ollama(prompt)

    print(
        "\n========== ROOT CAUSE REPORT ==========\n"
    )

    print(report)

    output_path = save_report(report)

    print(
        "\n----------------------------------------"
    )

    print(
        "PRIA report saved:"
    )

    print(output_path)

    print(
        "----------------------------------------"
    )


if __name__ == "__main__":
    main()
