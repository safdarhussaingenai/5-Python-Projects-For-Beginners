import json
import os
import re
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

OWNER = "safdarhussaingenai"
REPO = "5-Python-Projects-For-Beginners"
PR_NUMBER = 1

BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


# ============================================================
# GITHUB API HELPERS
# ============================================================

def get_headers():
    headers = {
        "Accept": "application/vnd.github+json"
    }

    token = os.getenv("GITHUB_TOKEN")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def github_get(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# PULL REQUEST DATA
# ============================================================

def get_pull_request():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}"

    return github_get(url)


def get_changed_files():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}/files"

    return github_get(url)


def get_commits():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}/commits"

    return github_get(url)


# ============================================================
# WORKFLOW DATA
# ============================================================

def get_workflow_runs():
    url = f"{BASE_URL}/actions/runs"

    return github_get(
        url,
        params={
            "event": "pull_request",
            "branch": "bug/partner-validation",
        },
    )


def get_failed_regression_run(workflow_runs):
    """
    Find the failed GitHub Actions workflow associated
    with our regression Pull Request.
    """

    for run in workflow_runs.get("workflow_runs", []):
        if run.get("conclusion") == "failure":
            return run

    return None


def get_failed_job(run_id):
    """
    Find the failed job inside the failed workflow run.
    """

    url = f"{BASE_URL}/actions/runs/{run_id}/jobs"

    data = github_get(url)

    for job in data.get("jobs", []):
        if job.get("conclusion") == "failure":
            return job

    return None


def get_job_logs(job_id):
    """
    Download logs for the failed GitHub Actions job.
    """

    url = f"{BASE_URL}/actions/jobs/{job_id}/logs"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ============================================================
# FAILED TEST ANALYSIS
# ============================================================

def parse_failed_test(log_text):
    """
    Extract the failed pytest test name and the
    actual/expected values from the GitHub Actions log.
    """

    failed_test = {
        "name": None,
        "expected": None,
        "actual": None
    }

    # Example pytest output:
    #
    # FAILED test_subscription.py::test_create_subscription_returns_201

    test_match = re.search(
        r"FAILED\s+.*::([A-Za-z0-9_]+)",
        log_text
    )

    if test_match:
        failed_test["name"] = test_match.group(1)

    # Example pytest assertion:
    #
    # assert 400 == 201
    #
    # Left side = actual
    # Right side = expected

    assertion_match = re.search(
        r"assert\s+(\d+)\s*==\s*(\d+)",
        log_text
    )

    if assertion_match:
        failed_test["actual"] = int(
            assertion_match.group(1)
        )

        failed_test["expected"] = int(
            assertion_match.group(2)
        )

    return failed_test


# ============================================================
# CREATE STRUCTURED PRIA EVIDENCE
# ============================================================

def create_evidence():

    # --------------------------------------------------------
    # Step 1: Collect PR information
    # --------------------------------------------------------

    pr = get_pull_request()

    files = get_changed_files()

    commits = get_commits()

    workflow_runs = get_workflow_runs()

    # --------------------------------------------------------
    # Step 2: Find failed regression workflow
    # --------------------------------------------------------

    failed_run = get_failed_regression_run(
        workflow_runs
    )

    # Default values

    failed_test = {
        "name": None,
        "expected": None,
        "actual": None
    }

    # --------------------------------------------------------
    # Step 3: Find failed job and read test logs
    # --------------------------------------------------------

    if failed_run:

        failed_job = get_failed_job(
            failed_run["id"]
        )

        if failed_job:

            logs = get_job_logs(
                failed_job["id"]
            )

            failed_test = parse_failed_test(
                logs
            )

    # --------------------------------------------------------
    # Step 4: Prepare changed-file information
    # --------------------------------------------------------

    changed_files = []

    for file in files:

        changed_files.append(
            {
                "filename": file.get(
                    "filename"
                ),
                "status": file.get(
                    "status"
                ),
                "additions": file.get(
                    "additions"
                ),
                "deletions": file.get(
                    "deletions"
                ),
                "patch": file.get(
                    "patch",
                    ""
                ),
            }
        )

    # --------------------------------------------------------
    # Step 5: Prepare commit information
    # --------------------------------------------------------

    commit_list = []

    for commit in commits:

        commit_list.append(
            {
                "sha": commit.get(
                    "sha"
                ),
                "message": commit[
                    "commit"
                ].get(
                    "message"
                ),
            }
        )

    # --------------------------------------------------------
    # Step 6: Create final structured evidence
    # --------------------------------------------------------

    evidence = {

        "repository":
            f"{OWNER}/{REPO}",

        "pull_request": {

            "number":
                pr.get("number"),

            "title":
                pr.get("title"),

            "source_branch":
                pr["head"].get("ref"),

            "target_branch":
                pr["base"].get("ref"),

            "state":
                pr.get("state"),
        },

        "changed_files":
            changed_files,

        "commits":
            commit_list,

        "regression": {

            "workflow_name": (
                failed_run.get("name")
                if failed_run
                else None
            ),

            "workflow_status": (
                failed_run.get("status")
                if failed_run
                else None
            ),

            "workflow_conclusion": (
                failed_run.get("conclusion")
                if failed_run
                else None
            ),

            "head_branch": (
                failed_run.get(
                    "head_branch"
                )
                if failed_run
                else None
            ),

            "run_id": (
                failed_run.get("id")
                if failed_run
                else None
            ),
        },

        "failed_test":
            failed_test,
    }

    return evidence


# ============================================================
# SAVE JSON FILE
# ============================================================

def save_evidence(evidence):

    output_path = (
        Path(__file__).parent
        / "pria_evidence.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            evidence,
            file,
            indent=2,
            ensure_ascii=False
        )

    return output_path


# ============================================================
# DISPLAY INVESTIGATION
# ============================================================

def investigate():

    print(
        "\n========== PRIA INVESTIGATION ==========\n"
    )

    evidence = create_evidence()

    # --------------------------------------------------------
    # PR INFORMATION
    # --------------------------------------------------------

    pr = evidence["pull_request"]

    print(
        "PR NUMBER:",
        pr["number"]
    )

    print(
        "TITLE:",
        pr["title"]
    )

    print(
        "SOURCE BRANCH:",
        pr["source_branch"]
    )

    print(
        "TARGET BRANCH:",
        pr["target_branch"]
    )

    # --------------------------------------------------------
    # CHANGED FILES
    # --------------------------------------------------------

    print(
        "\n---------- CHANGED FILES ----------"
    )

    for file in evidence["changed_files"]:

        print(
            "\nFile:",
            file["filename"]
        )

        print(
            "Status:",
            file["status"]
        )

        print(
            "Additions:",
            file["additions"]
        )

        print(
            "Deletions:",
            file["deletions"]
        )

        if file["patch"]:

            print(
                "\nCode Diff:"
            )

            print(
                file["patch"]
            )

    # --------------------------------------------------------
    # COMMITS
    # --------------------------------------------------------

    print(
        "\n---------- COMMITS ----------"
    )

    for commit in evidence["commits"]:

        print(
            commit["sha"][:7],
            "-",
            commit["message"]
        )

    # --------------------------------------------------------
    # REGRESSION INFORMATION
    # --------------------------------------------------------

    print(
        "\n---------- REGRESSION ----------"
    )

    regression = evidence["regression"]

    print(
        "Workflow:",
        regression["workflow_name"]
    )

    print(
        "Status:",
        regression["workflow_status"]
    )

    print(
        "Conclusion:",
        regression["workflow_conclusion"]
    )

    print(
        "Branch:",
        regression["head_branch"]
    )

    # --------------------------------------------------------
    # FAILED TEST INFORMATION
    # --------------------------------------------------------

    print(
        "\n---------- FAILED TEST ----------"
    )

    failed_test = evidence["failed_test"]

    print(
        "Test:",
        failed_test["name"]
    )

    print(
        "Expected:",
        failed_test["expected"]
    )

    print(
        "Actual:",
        failed_test["actual"]
    )

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    output_path = save_evidence(
        evidence
    )

    print(
        "\n----------------------------------"
    )

    print(
        "Evidence JSON created:"
    )

    print(
        output_path
    )

    print(
        "----------------------------------"
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    investigate()
