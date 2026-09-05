import requests

OWNER = "safdarhussaingenai"
REPO = "5-Python-Projects-For-Beginners"
PR_NUMBER = 1

BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"


def get_pull_request():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_changed_files():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}/files"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_commits():
    url = f"{BASE_URL}/pulls/{PR_NUMBER}/commits"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_workflow_runs():
    url = f"{BASE_URL}/actions/runs"

    response = requests.get(
        url,
        params={
            "event": "pull_request",
            "branch": "bug/partner-validation"
        }
    )

    response.raise_for_status()
    return response.json()


def investigate():

    print("\n========== PRIA INVESTIGATION ==========\n")

    pr = get_pull_request()

    print("PR NUMBER:", pr["number"])
    print("TITLE:", pr["title"])
    print("SOURCE BRANCH:", pr["head"]["ref"])
    print("TARGET BRANCH:", pr["base"]["ref"])

    print("\n---------- CHANGED FILES ----------")

    files = get_changed_files()

    for file in files:
        print("\nFile:", file["filename"])
        print("Status:", file["status"])
        print("Additions:", file["additions"])
        print("Deletions:", file["deletions"])

        if "patch" in file:
            print("\nCode Diff:")
            print(file["patch"])

    print("\n---------- COMMITS ----------")

    commits = get_commits()

    for commit in commits:
        print(
            commit["sha"][:7],
            "-",
            commit["commit"]["message"]
        )

    print("\n---------- REGRESSION RUN ----------")

    runs = get_workflow_runs()

    for run in runs["workflow_runs"][:5]:

        print(
            run["name"],
            "|",
            run["head_branch"],
            "|",
            run["conclusion"]
        )


if __name__ == "__main__":
    investigate()
