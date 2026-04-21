"""
Cliente de gerenciador de projetos para o Ultron.
Suporta: Jira, Linear, GitHub Issues.
"""

import os
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CardData:
    id: str
    title: str
    description: str
    url: str


class PMClient(ABC):
    @abstractmethod
    def get_card(self, card_id: str) -> CardData:
        ...

    @abstractmethod
    def post_comment(self, card_id: str, body: str) -> str:
        """Posta comentário e retorna URL do comentário."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Jira
# ──────────────────────────────────────────────────────────────────────────────

class JiraClient(PMClient):
    def __init__(self, base_url: str, email: str, api_token: str):
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.auth = (email, api_token)
        self._session.headers.update({"Content-Type": "application/json"})

    def get_card(self, card_id: str) -> CardData:
        resp = self._session.get(f"{self._base}/rest/api/3/issue/{card_id}")
        resp.raise_for_status()
        data = resp.json()
        fields = data["fields"]

        desc = ""
        if fields.get("description"):
            desc = _jira_adf_to_text(fields["description"])

        return CardData(
            id=card_id,
            title=fields["summary"],
            description=desc,
            url=f"{self._base}/browse/{card_id}",
        )

    def post_comment(self, card_id: str, body: str) -> str:
        # API v2 aceita string simples — renderiza formatação corretamente no Jira
        resp = self._session.post(
            f"{self._base}/rest/api/2/issue/{card_id}/comment",
            json={"body": body},
        )
        resp.raise_for_status()
        comment_id = resp.json()["id"]
        return f"{self._base}/browse/{card_id}?focusedCommentId={comment_id}"


def _jira_adf_to_text(node: dict, depth: int = 0) -> str:
    if node.get("type") == "text":
        return node.get("text", "")
    parts = [_jira_adf_to_text(c, depth + 1) for c in node.get("content", [])]
    sep = "\n" if node.get("type") in {"paragraph", "heading", "listItem"} else ""
    return sep.join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# Linear
# ──────────────────────────────────────────────────────────────────────────────

class LinearClient(PMClient):
    GQL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str):
        self._headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    def _gql(self, query: str, variables: dict) -> dict:
        resp = requests.post(
            self.GQL,
            json={"query": query, "variables": variables},
            headers=self._headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"Linear GraphQL error: {data['errors']}")
        return data["data"]

    def get_card(self, card_id: str) -> CardData:
        query = """
        query GetIssue($id: String!) {
          issue(id: $id) {
            id
            title
            description
            url
          }
        }
        """
        data = self._gql(query, {"id": card_id})
        issue = data["issue"]
        return CardData(
            id=card_id,
            title=issue["title"],
            description=issue.get("description") or "",
            url=issue["url"],
        )

    def post_comment(self, card_id: str, body: str) -> str:
        mutation = """
        mutation CreateComment($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) {
            success
            comment {
              id
              url
            }
          }
        }
        """
        data = self._gql(mutation, {"issueId": card_id, "body": body})
        return data["commentCreate"]["comment"]["url"]


# ──────────────────────────────────────────────────────────────────────────────
# GitHub Issues
# ──────────────────────────────────────────────────────────────────────────────

class GitHubIssuesClient(PMClient):
    BASE = "https://api.github.com"

    def __init__(self, token: str, repo: str):
        self._repo = repo
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_card(self, card_id: str) -> CardData:
        number = card_id.lstrip("#")
        resp = self._session.get(f"{self.BASE}/repos/{self._repo}/issues/{number}")
        resp.raise_for_status()
        issue = resp.json()
        return CardData(
            id=card_id,
            title=issue["title"],
            description=issue.get("body") or "",
            url=issue["html_url"],
        )

    def post_comment(self, card_id: str, body: str) -> str:
        number = card_id.lstrip("#")
        resp = self._session.post(
            f"{self.BASE}/repos/{self._repo}/issues/{number}/comments",
            json={"body": body},
        )
        resp.raise_for_status()
        return resp.json()["html_url"]


# ──────────────────────────────────────────────────────────────────────────────
# Factory
# ──────────────────────────────────────────────────────────────────────────────

def build_pm_client(env: dict) -> PMClient:
    provider = env.get("PM_PROVIDER", "github").lower()

    if provider == "jira":
        base_url   = _require(env, "JIRA_BASE_URL")
        email      = _require(env, "JIRA_EMAIL")
        api_token  = _require(env, "JIRA_API_TOKEN")
        return JiraClient(base_url, email, api_token)

    if provider == "linear":
        api_key = _require(env, "LINEAR_API_KEY")
        return LinearClient(api_key)

    if provider == "github":
        token = _require(env, "GITHUB_TOKEN")
        repo  = _require(env, "GITHUB_REPO")
        return GitHubIssuesClient(token, repo)

    raise ValueError(f"PM_PROVIDER '{provider}' não reconhecido. Use: jira | linear | github")


def _require(env: dict, key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não encontrada: {key}")
    return value
