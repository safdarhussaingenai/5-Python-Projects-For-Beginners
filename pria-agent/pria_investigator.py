import json
from pathlib import Path

import requests


OWNER = "safdarhussaingenai"
REPO = "5-Python-Projects-For-Beginners"
PR_NUMBER = 1

BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


def github_get(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_pull_request():
    return github_get(f"{BASE_URL}/pulls/{PR_NUMBER}")


def get_changed_files():
    return github_get(f"{BASE_URL}/pulls/{PR_NUMBER}/files")


def get_commits():
    return github_get(f"{BASE_URL}/pulls/{PR_NUMBER}/commits")


def get_workflow_runs():
    return github_get(
        f"{BASE_URL}/actions/runs",
        params={
            "event": "pull_request",
            "branch": "bug/partner-validation",
        },
    )


def get_failed_regression_run(workflow_runs):
    for run in workflow_runs.get("workflow_runs", []):
        if run.get("conclusion") == "failure":
            return run

    return None


def create_evidence():
    pr = get_pull_request()
    files = get_changed_files()
    commits = get_commits()
    workflow_runs = get_workflow_runs()

    failed_run = get_failed_regression_run(workflow_runs)

    changed_files = []

    for file in files:
        changed_files.append(
            {
                "filename": file.get("filename"),
                "status": file.get("status"),
                "additions": file.get("additions"),
                "deletions": file.get("deletions"),
                "patch": file.get("patch", ""),
            }
        )

    commit_list = []

    for commit in commits:
        commit_list.append(
            {
                "sha": commit.get("sha"),
                "message": commit["commit"].get("message"),
            }
        )

    evidence = {
        "repository": f"{OWNER}/{REPO}",
        "pull_request": {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "source_branch": pr["head"].get("ref"),
            "target_branch": pr["base"].get("ref"),
            "state": pr.get("state"),
        },
        "changed_files": changed_files,
        "commits": commit_list,
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
                failed_run.get("head_branch")
                if failed_run
                else None
            ),
            "run_id": (
                failed_run.get("id")
                if failed_run
                else None
            ),
        },

        # We will populate these in the NEXT step
        # by reading the failed test logs.
        "failed_test": {
            "name": None,
            "expected": None,
            "actual": None,
        },
    }

    return evidence


def save_evidence(evidence):
    output_path = (
        Path(__file__).parent / "pria_evidence.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            evidence,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


def investigate():
    print("\n========== PRIA INVESTIGATION ==========\n")

    evidence = create_evidence()

    pr = evidence["pull_request"]

    print("PR NUMBER:", pr["number"])
    print("TITLE:", pr["title"])
    print("SOURCE BRANCH:", pr["source_branch"])
    print("TARGET BRANCH:", pr["target_branch"])

    print("\n---------- CHANGED FILES ----------")

    for file in evidence["changed_files"]:
        print("\nFile:", file["filename"])
        print("Status:", file["status"])
        print("Additions:", file["additions"])
        print("Deletions:", file["deletions"])

        if file["patch"]:
            print("\nCode Diff:")
            print(file["patch"])

    print("\n---------- COMMITS ----------")

    for commit in evidence["commits"]:
        print(
            commit["sha"][:7],
            "-",
            commit["message"],
        )

    print("\n---------- REGRESSION ----------")

    regression = evidence["regression"]

    print(
        "Workflow:",
        regression["workflow_name"],
    )

    print(
        "Conclusion:",
        regression["workflow_conclusion"],
    )

    output_path = save_evidence(evidence)

    print("\n----------------------------------")
    print("Evidence JSON created:")
    print(output_path)
    print("----------------------------------")


if __name__ == "__main__":
    investigate()
