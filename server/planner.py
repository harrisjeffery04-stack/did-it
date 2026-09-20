"""Planners — turn a natural-language task into a list of {action, args} steps.

Two planners ship:
- LocalPlanner   — deterministic, offline, rule-based. Always available.
- BedrockPlanner — AWS Builder mini-challenge path: uses Amazon Bedrock
  (Anthropic Claude) to plan free-text tasks. Enabled automatically when
  AWS credentials are present. See docs/AWS_BUILDER.md.

Every planner output is JSON-safe and validated against the executor list.
"""
import json
import os
import re

from .executors import EXECUTORS

_ALLOWED = sorted(EXECUTORS)


def _url_from_text(text):
    m = re.search(r"https?://\S+", text)
    return m.group(0).rstrip(".,;:!?") if m else None


class LocalPlanner:
    """Rule-based planner: fast, offline, and honest about what it can't do."""

    name = "local"

    def plan(self, task: str) -> list[dict]:
        t = task.lower()
        url = _url_from_text(task)
        if "backup" in t or "copy" in t:
            m = re.search(r"backup (.+?) to (.+)", t)
            if m:
                return [{"action": "file_backup",
                         "args": {"source_dir": m.group(1), "dest_dir": m.group(2)}}]
        if url:
            return [{"action": "web_check",
                     "args": {"url": url}}]
        if "organize" in t or "tidy" in t or "sort" in t:
            m = re.search(r"(?:organize|tidy|sort) (.+)", t)
            if m:
                return [{"action": "file_organize", "args": {"source_dir": m.group(1)}}]
        if "check" in t and "disk" in t or "space" in t:
            return [{"action": "sys_check", "args": {}}]
        # Honest fallback: no confident plan.
        return []


class BedrockPlanner:
    """Plan free-text tasks with Amazon Bedrock (Claude).

    Requires AWS credentials (env/config) and boto3. Enabled automatically by
    get_planner() when credentials are detected; nothing about the receipt
    pipeline changes — the plan is still executed by the same verified
    executors.
    """

    name = "bedrock"

    def __init__(self, model_id: str | None = None):
        import boto3  # optional dependency
        self._client = boto3.client("bedrock-runtime")
        self.model_id = model_id or os.environ.get(
            "PROVENDONE_BEDROCK_MODEL", "us.anthropic.claude-3-5-haiku-20241022-v1:0")

    def plan(self, task: str) -> list[dict]:
        prompt = (
            "You plan personal-ops tasks for a verification-first assistant. "
            f"Available actions: {json.dumps(_ALLOWED)}. "
            "Reply ONLY with a JSON array of steps, each {\"action\":..., \"args\":{...}}. "
            f"Task: {task}"
        )
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        })
        resp = self._client.invoke_model(modelId=self.model_id, body=body)
        out = json.loads(resp["body"].read())["content"][0]["text"]
        steps = json.loads(out)
        assert isinstance(steps, list) and all(
            isinstance(s, dict) and s.get("action") in EXECUTORS for s in steps), "bad plan from Bedrock"
        return steps


def get_planner():
    """Pick Bedrock when credentials exist; otherwise the local planner."""
    try:
        import botocore.session  # noqa
        sess = botocore.session.get_session()
        if sess.get_credentials() is not None:
            return BedrockPlanner()
    except ImportError:
        pass
    return LocalPlanner()