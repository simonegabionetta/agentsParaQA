"""
Cliente GitHub para o Ultron.
Busca detalhes de PRs e diffs via API REST do GitHub.
"""

import os
import requests
from dataclasses import dataclass


@dataclass
class PRData:
    number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    diff: str
    files_changed: list[dict]
    commits: list[str]


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str, repo: str):
        self.repo = repo
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_pr(self, pr_number: int, base_branch: str = "") -> PRData:
        pr = self._get(f"/repos/{self.repo}/pulls/{pr_number}")

        resolved_base = base_branch or pr["base"]["ref"]

        files = self._get(f"/repos/{self.repo}/pulls/{pr_number}/files")
        commits_raw = self._get(f"/repos/{self.repo}/pulls/{pr_number}/commits")

        diff = self._get_diff(pr_number)
        files_changed = [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": f.get("patch", ""),
            }
            for f in files
        ]
        commits = [c["commit"]["message"].splitlines()[0] for c in commits_raw]

        return PRData(
            number=pr_number,
            title=pr["title"],
            description=pr.get("body") or "",
            author=pr["user"]["login"],
            base_branch=resolved_base,
            head_branch=pr["head"]["ref"],
            diff=diff,
            files_changed=files_changed,
            commits=commits,
        )

    def _get(self, path: str) -> dict | list:
        resp = self._session.get(f"{self.BASE}{path}")
        resp.raise_for_status()
        return resp.json()

    def _get_diff(self, pr_number: int) -> str:
        resp = self._session.get(
            f"{self.BASE}/repos/{self.repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.diff"},
        )
        resp.raise_for_status()
        return resp.text
