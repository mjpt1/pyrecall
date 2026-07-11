"""Stdio JSON-RPC tool bridge for compatible coding tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pyrecall import __version__
from pyrecall.harvest import harvest_docs
from pyrecall.learner import learn_correction, parse_correction_blob
from pyrecall.models import Memory, MemoryKind
from pyrecall.packs import install_pack
from pyrecall.paths import find_project_root
from pyrecall.retriever import format_context, search
from pyrecall.store import Store

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "search_memory",
        "description": (
            "Search local project memory and learned skills for relevant guidance. "
            "Call this before editing Python code in this repository."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What you need to recall"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tag filter (match any)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_context",
        "description": (
            "REQUIRED before editing Python in this repository: return a ready-to-use "
            "context block of project conventions and correction-derived skills for "
            "the given task. Includes why each hit matched. Call this first."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 6},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tag filter (match any)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "add_memory",
        "description": "Store a durable project note, decision, or convention.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "kind": {
                    "type": "string",
                    "enum": ["decision", "convention", "note", "doc"],
                    "default": "note",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["python"],
                },
            },
            "required": ["title", "body"],
        },
    },
    {
        "name": "learn_correction",
        "description": (
            "REQUIRED when the user rejects an approach and states a preferred one: "
            "record the correction and distill it into a reusable skill so the same "
            "mistake is not repeated. Call this in the same turn as the correction."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "rejected": {
                    "type": "string",
                    "description": "Approach or snippet to avoid",
                },
                "preferred": {
                    "type": "string",
                    "description": "Approach or snippet to prefer",
                },
                "context": {"type": "string", "default": ""},
                "reason": {"type": "string", "default": ""},
                "blob": {
                    "type": "string",
                    "description": "Optional free-form 'avoid => prefer' text",
                },
            },
        },
    },
    {
        "name": "list_skills",
        "description": "List active learned skills for this project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "install_pack",
        "description": (
            "Install an optional skill pack: fastapi, django, sqlalchemy, or ruff."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "enum": ["fastapi", "django", "sqlalchemy", "ruff"],
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "harvest_docs",
        "description": (
            "Re-read README / CONTRIBUTING / AGENTS style docs and store convention "
            "bullets as durable memories. Call after the user updates project docs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "keep": {
                    "type": "boolean",
                    "default": False,
                    "description": "Keep previous harvested entries",
                },
            },
        },
    },
    {
        "name": "project_stats",
        "description": "Show counts of memories, corrections, and skills.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class BridgeServer:
    def __init__(self, root: Path | None = None) -> None:
        self.root = find_project_root(root)

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        if "method" not in message:
            return self._error(message.get("id"), -32600, "Invalid Request")

        method = message["method"]
        msg_id = message.get("id")
        params = message.get("params") or {}

        # Notifications have no id
        if msg_id is None and method.startswith("notifications/"):
            return None

        try:
            if method == "initialize":
                result = self._initialize(params)
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                result = self._call_tool(params)
            elif method == "ping":
                result = {}
            elif method == "resources/list":
                result = {"resources": []}
            elif method == "prompts/list":
                result = {"prompts": []}
            else:
                return self._error(msg_id, -32601, f"Method not found: {method}")
        except Exception as exc:  # noqa: BLE001 — bridge must never crash the host
            return self._error(msg_id, -32000, str(exc))

        if msg_id is None:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "pyrecall",
                "version": __version__,
            },
        }

    def _call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "search_memory":
            tags = arguments.get("tags") or None
            hits = search(
                arguments["query"],
                limit=int(arguments.get("limit") or 8),
                tags=tags,
                root=self.root,
            )
            payload = [h.model_dump() for h in hits]
            return self._text(json.dumps(payload, ensure_ascii=False, indent=2))

        if name == "get_context":
            tags = arguments.get("tags") or None
            hits = search(
                arguments["query"],
                limit=int(arguments.get("limit") or 6),
                tags=tags,
                root=self.root,
            )
            return self._text(format_context(hits, show_why=True))

        if name == "add_memory":
            kind = MemoryKind(arguments.get("kind") or "note")
            memory = Memory(
                kind=kind,
                title=arguments["title"],
                body=arguments["body"],
                tags=list(arguments.get("tags") or ["python"]),
            )
            Store(self.root).upsert_memory(memory)
            return self._text(json.dumps({"id": memory.id, "title": memory.title}))

        if name == "learn_correction":
            rejected = arguments.get("rejected") or ""
            preferred = arguments.get("preferred") or ""
            context = arguments.get("context") or ""
            reason = arguments.get("reason") or ""
            blob = arguments.get("blob") or ""
            if blob and (not rejected or not preferred):
                parsed_r, parsed_p, parsed_reason = parse_correction_blob(blob)
                rejected = rejected or parsed_r
                preferred = preferred or parsed_p
                reason = reason or parsed_reason
            if not preferred:
                raise ValueError("preferred (or blob) is required")
            result = learn_correction(
                rejected or "(unspecified)",
                preferred,
                context=context,
                reason=reason,
                root=self.root,
            )
            return self._text(json.dumps(result, ensure_ascii=False, indent=2))

        if name == "list_skills":
            limit = int(arguments.get("limit") or 50)
            skills = Store(self.root).list_skills(active_only=True)[:limit]
            payload = [
                {
                    "id": s.id,
                    "name": s.name,
                    "rule": s.rule,
                    "tags": s.tags,
                    "hit_count": s.hit_count,
                }
                for s in skills
            ]
            return self._text(json.dumps(payload, ensure_ascii=False, indent=2))

        if name == "install_pack":
            result = install_pack(Store(self.root), arguments["name"])
            return self._text(
                json.dumps({"pack": arguments["name"], **result}, ensure_ascii=False)
            )

        if name == "harvest_docs":
            result = harvest_docs(self.root, replace=not bool(arguments.get("keep")))
            return self._text(json.dumps(result, ensure_ascii=False, indent=2))

        if name == "project_stats":
            return self._text(json.dumps(Store(self.root).stats(), indent=2))

        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def _text(text: str) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": text}], "isError": False}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }


def serve_stdio(root: Path | None = None) -> None:
    server = BridgeServer(root)
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        line = stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            # Content-Length framed messages
            header = line.decode("utf-8", errors="ignore")
            if header.lower().startswith("content-length:"):
                length = int(header.split(":", 1)[1].strip())
                # consume remaining headers
                while True:
                    hdr = stdin.readline()
                    if hdr in (b"\r\n", b"\n", b""):
                        break
                body = stdin.read(length)
                message = json.loads(body.decode("utf-8"))
            else:
                continue

        response = server.handle(message)
        if response is None:
            continue
        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
        # Prefer Content-Length framing for broader client compatibility
        frame = (
            f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload
        )
        stdout.write(frame)
        stdout.flush()
