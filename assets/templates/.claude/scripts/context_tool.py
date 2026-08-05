#!/usr/bin/env python3
"""CTX404 context helper using only the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_TOPIC_FIELDS = (
    "id", "type", "schema-version", "revision", "created-at", "updated-at", "status", "summary", "keywords"
)
VALID_TOPIC_STATUS = {"active", "draft", "superseded", "archived"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def project_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    candidate = Path.cwd().resolve()
    for path in (candidate, *candidate.parents):
        if (path / ".claude" / "context" / "index.json").is_file():
            return path
    return candidate


def context_root(root: Path) -> Path:
    return root / ".claude" / "context"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative_path_is_safe(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and not re.match(r"^[A-Za-z]:", value)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value.startswith("["):
        return json.loads(value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value.strip('"')


def parse_topic(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter marker")
    try:
        closing = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("missing closing frontmatter marker") from exc
    metadata: dict[str, Any] = {}
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line {line_number}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in metadata:
            raise ValueError(f"duplicate frontmatter key: {key}")
        metadata[key] = parse_scalar(value)
    body = "\n".join(lines[closing + 1 :]).strip() + "\n"
    return metadata, body


def topic_errors(metadata: dict[str, Any]) -> list[str]:
    errors = [f"missing frontmatter field: {field}" for field in REQUIRED_TOPIC_FIELDS if field not in metadata]
    topic_id = metadata.get("id")
    if not isinstance(topic_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic_id):
        errors.append("id must use lowercase letters, digits, and hyphens")
    if metadata.get("type") != "context-topic":
        errors.append("type must be context-topic")
    if metadata.get("schema-version") != 1:
        errors.append("schema-version must be 1")
    if not isinstance(metadata.get("revision"), int) or metadata.get("revision", 0) < 1:
        errors.append("revision must be a positive integer")
    if metadata.get("status") not in VALID_TOPIC_STATUS:
        errors.append("status must be active, draft, superseded, or archived")
    summary = metadata.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary is required")
    elif len(summary) > 200:
        errors.append("summary exceeds 200 characters")
    keywords = metadata.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
        errors.append("keywords must be an inline JSON array of strings")
    elif len(keywords) > 10:
        errors.append("keywords exceeds 10 items")
    return errors


def body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def render_topic(metadata: dict[str, Any], body: str) -> str:
    ordered = [
        f"id: {metadata['id']}",
        f"type: {metadata['type']}",
        f"schema-version: {metadata['schema-version']}",
        f"revision: {metadata['revision']}",
        f"created-at: {metadata['created-at'] or 'null'}",
        f"updated-at: {metadata['updated-at'] or 'null'}",
        f"status: {metadata['status']}",
        f"summary: {metadata['summary']}",
        f"keywords: {json.dumps(metadata['keywords'], ensure_ascii=False)}",
    ]
    return "---\n" + "\n".join(ordered) + "\n---\n\n" + body


def topic_files(root: Path) -> list[Path]:
    topics = context_root(root) / "topics"
    return sorted(path for path in topics.rglob("*.md") if path.is_file())


def validation(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ctx = context_root(root)
    index_path = ctx / "index.json"
    current_path = ctx / "current.json"
    schema_path = ctx / "schema.json"
    history_path = ctx / "history.jsonl"
    for path in (index_path, current_path, schema_path, history_path):
        if not path.is_file():
            errors.append(f"Missing required file: {path.relative_to(root)}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}
    try:
        index = load_json(index_path)
        current = load_json(current_path)
        load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "errors": [str(exc)], "warnings": warnings}
    if not isinstance(index.get("ctx404Version"), str):
        errors.append("index.json ctx404Version is required")
    if index.get("schemaVersion") != 1 or current.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    topics = index.get("topics")
    if not isinstance(topics, list):
        errors.append("index.json topics must be an array")
        topics = []
    ids: set[str] = set()
    for position, topic in enumerate(topics):
        if not isinstance(topic, dict):
            errors.append(f"topics[{position}] must be an object")
            continue
        topic_id = topic.get("id")
        if not isinstance(topic_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic_id):
            errors.append(f"topics[{position}].id is invalid")
        elif topic_id in ids:
            errors.append(f"Duplicate topic id: {topic_id}")
        else:
            ids.add(topic_id)
        if not isinstance(topic.get("summary"), str) or not topic["summary"].strip():
            errors.append(f"topics[{position}].summary is required")
        if not isinstance(topic.get("keywords"), list) or not all(isinstance(k, str) for k in topic.get("keywords", [])):
            errors.append(f"topics[{position}].keywords must be an array of strings")
        topic_path = topic.get("path")
        if not isinstance(topic_path, str) or not relative_path_is_safe(topic_path):
            errors.append(f"topics[{position}].path must be relative")
        elif not (root / topic_path).is_file():
            errors.append(f"Indexed topic path does not exist: {topic_path}")
    for name, value in index.get("entrypoints", {}).items():
        if not isinstance(value, str) or not relative_path_is_safe(value):
            errors.append(f"Invalid entrypoint path: {name}")
        elif not (root / value).is_file():
            errors.append(f"Entrypoint does not exist: {value}")
    active = current.get("activeTopics", [])
    if not isinstance(active, list):
        errors.append("current.json activeTopics must be an array")
    else:
        unknown = sorted(set(active) - ids)
        if unknown:
            errors.append(f"Unknown active topic ids: {', '.join(unknown)}")
    if current.get("updatedAt"):
        try:
            datetime.fromisoformat(current["updatedAt"])
        except (TypeError, ValueError):
            errors.append("current.json updatedAt must be ISO 8601 or null")
    try:
        for line_number, line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict) or not all(key in event for key in ("at", "type", "summary", "refs")):
                errors.append(f"history.jsonl line {line_number} has an invalid event")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid history.jsonl: {exc}")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "topicCount": len(topics)}


def sync_topics(root: Path) -> dict[str, Any]:
    index_path = context_root(root) / "index.json"
    index = load_json(index_path)
    old_by_id = {item["id"]: item for item in index.get("topics", []) if isinstance(item, dict) and "id" in item}
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    changed: list[str] = []
    timestamp = now_iso()
    for path in topic_files(root):
        metadata, body = parse_topic(path)
        errors = topic_errors(metadata)
        if errors:
            raise ValueError(f"{path.relative_to(root)}: {'; '.join(errors)}")
        topic_id = metadata["id"]
        if topic_id in seen:
            raise ValueError(f"duplicate topic id: {topic_id}")
        seen.add(topic_id)
        digest = body_hash(body)
        previous = old_by_id.get(topic_id)
        if previous is None:
            metadata["revision"] = max(1, metadata["revision"])
            metadata["created-at"] = metadata["created-at"] or timestamp
            metadata["updated-at"] = metadata["updated-at"] or timestamp
            changed.append(topic_id)
        elif previous.get("bodySha256") != digest:
            metadata["revision"] = max(metadata["revision"], int(previous.get("revision", 0))) + 1
            metadata["updated-at"] = timestamp
            changed.append(topic_id)
        path.write_text(render_topic(metadata, body), encoding="utf-8", newline="\n")
        entries.append({
            "id": topic_id,
            "summary": metadata["summary"],
            "keywords": metadata["keywords"],
            "path": path.relative_to(root).as_posix(),
            "status": metadata["status"],
            "revision": metadata["revision"],
            "updatedAt": metadata["updated-at"],
            "bodySha256": digest,
        })
    index["topics"] = sorted(entries, key=lambda item: item["id"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "topicCount": len(entries), "changedTopics": changed}


def doctor(root: Path) -> dict[str, Any]:
    check = validation(root)
    issues = list(check.get("errors", []))
    warnings = list(check.get("warnings", []))
    index = load_json(context_root(root) / "index.json") if not issues else {}
    claude_path = root / "CLAUDE.md"
    instructions_path = root / ".claude" / "ctx404-instructions.md"
    definition_path = context_root(root) / "project-definition.md"
    rule_path = root / ".claude" / "rules" / "ctx404-context.md"
    if not claude_path.is_file():
        issues.append("CLAUDE.md is missing")
    else:
        content = claude_path.read_text(encoding="utf-8")
        starts = re.findall(r'<!-- ctx404:governance:start version="([^"]+)" schema="([^"]+)" -->', content)
        if len(starts) != 1 or content.count("<!-- ctx404:governance:end -->") != 1:
            issues.append("CTX404 governance markers are missing or duplicated")
        elif starts[0][0] != index.get("ctx404Version"):
            issues.append("CLAUDE.md governance version differs from index.json")
        else:
            # The stub is inert unless both imports survive; a broken import fails silently otherwise.
            for target in ("@.claude/ctx404-instructions.md", "@.claude/context/project-definition.md"):
                if target not in content:
                    issues.append(f"CLAUDE.md is missing the {target} import")
    if not instructions_path.is_file():
        issues.append(".claude/ctx404-instructions.md is missing")
    else:
        instructions = instructions_path.read_text(encoding="utf-8")
        marker = re.search(r'<!-- ctx404:instructions:start version="([^"]+)"', instructions)
        if not marker:
            issues.append(".claude/ctx404-instructions.md has no CTX404 version marker")
        elif marker.group(1) != index.get("ctx404Version"):
            issues.append(".claude/ctx404-instructions.md version differs from index.json")
    if not definition_path.is_file():
        issues.append(".claude/context/project-definition.md is missing")
    if not rule_path.is_file():
        issues.append(".claude/rules/ctx404-context.md is missing")
    indexed = {item.get("id"): item for item in index.get("topics", []) if isinstance(item, dict)}
    discovered: set[str] = set()
    for path in topic_files(root):
        try:
            metadata, body = parse_topic(path)
            errors = topic_errors(metadata)
            if errors:
                issues.append(f"{path.relative_to(root)}: {'; '.join(errors)}")
                continue
            topic_id = metadata["id"]
            discovered.add(topic_id)
            entry = indexed.get(topic_id)
            if not entry:
                issues.append(f"Unindexed topic: {path.relative_to(root)}")
            elif entry.get("bodySha256") != body_hash(body):
                issues.append(f"Topic content changed without sync: {topic_id}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"{path.relative_to(root)}: {exc}")
    for topic_id in sorted(set(indexed) - discovered):
        issues.append(f"Indexed topic not discovered: {topic_id}")
    return {"ok": not issues, "issues": issues, "warnings": warnings, "ctx404Version": index.get("ctx404Version")}


def status(root: Path) -> dict[str, Any]:
    check = validation(root)
    if not check["ok"]:
        return {"ok": False, "validation": check}
    current = load_json(context_root(root) / "current.json")
    index = load_json(context_root(root) / "index.json")
    return {
        "ok": True,
        "ctx404Version": index.get("ctx404Version"),
        "project": index.get("project"),
        "current": current,
        "availableTopics": [
            {"id": topic["id"], "summary": topic["summary"], "path": topic["path"]}
            for topic in index["topics"]
        ],
    }


def find_topics(root: Path, query: str, limit: int) -> dict[str, Any]:
    index = load_json(context_root(root) / "index.json")
    terms = [term.casefold() for term in re.findall(r"[\w-]+", query)]
    matches: list[dict[str, Any]] = []
    for topic in index.get("topics", []):
        haystack = " ".join([topic.get("id", ""), topic.get("summary", ""), *topic.get("keywords", [])]).casefold()
        score = sum(3 if term in topic.get("id", "").casefold() else 1 for term in terms if term in haystack)
        if score:
            matches.append({"id": topic["id"], "summary": topic["summary"], "path": topic["path"], "score": score})
    matches.sort(key=lambda item: (-item["score"], item["id"]))
    return {"ok": True, "query": query, "matches": matches[:limit]}


def list_topics(root: Path) -> dict[str, Any]:
    return {"ok": True, "topics": load_json(context_root(root) / "index.json").get("topics", [])}


def snapshot(root: Path) -> dict[str, Any]:
    files = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size}
        for path in sorted(path for path in context_root(root).rglob("*") if path.is_file())
    ]
    return {"ok": True, "root": str(root), "files": files, "validation": validation(root)}


def history(root: Path, limit: int, event_type: str | None) -> dict[str, Any]:
    path = context_root(root) / "history.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if event_type:
        events = [event for event in events if event.get("type") == event_type]
    return {"ok": True, "events": list(reversed(events))[:limit]}


def topic_write(
    root: Path,
    topic_id: str,
    summary: str,
    keywords: list[str],
    status_value: str,
    body: str,
) -> dict[str, Any]:
    """Write a topic body deterministically.

    Claude decides the content; this builds the frontmatter and syncs the index. Writing through
    the helper also keeps topic files reachable in non-interactive sessions, where the built-in
    file tools are blocked from `.claude/` by the sensitive-path gate.
    """
    body = body.strip()
    if not body:
        raise ValueError("body must not be empty")

    topics_dir = context_root(root) / "topics"
    path = topics_dir / f"{topic_id}.md"
    existed = path.is_file()
    metadata: dict[str, Any] = {
        "id": topic_id,
        "type": "context-topic",
        "schema-version": 1,
        "revision": 1,
        "created-at": None,
        "updated-at": None,
        "status": status_value,
        "summary": summary.strip(),
        "keywords": keywords,
    }
    if existed:
        # Preserve provenance; sync_topics owns the revision bump and timestamps.
        previous, _ = parse_topic(path)
        metadata["created-at"] = previous.get("created-at")
        metadata["revision"] = previous.get("revision", 1)

    errors = topic_errors(metadata)
    if errors:
        raise ValueError("; ".join(errors))

    topics_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(render_topic(metadata, body + "\n"), encoding="utf-8", newline="\n")
    return {
        "ok": True,
        "id": topic_id,
        "path": path.relative_to(root).as_posix(),
        "created": not existed,
        "topicSync": sync_topics(root),
    }


def read_body(source: str) -> str:
    return sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")


def complete(
    root: Path,
    summary: str,
    next_step: str,
    status_value: str,
    topic_ids: list[str],
    refs: list[str],
    event_type: str,
) -> dict[str, Any]:
    summary = summary.strip()
    next_step = next_step.strip()
    event_type = event_type.strip()
    if not summary:
        raise ValueError("summary must not be empty")
    if not next_step:
        raise ValueError("next-step must not be empty")
    if not event_type or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", event_type):
        raise ValueError("event-type must use lowercase letters, digits, and hyphens")
    if status_value not in {"not-defined", "active", "blocked", "complete", "paused"}:
        raise ValueError("status must be not-defined, active, blocked, complete, or paused")
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic_id) for topic_id in topic_ids):
        raise ValueError("topic ids must use lowercase letters, digits, and hyphens")
    if any(not relative_path_is_safe(ref) for ref in refs):
        raise ValueError("refs must be safe relative paths")

    before = validation(root)
    if not before["ok"]:
        raise ValueError("context is invalid before completion: " + "; ".join(before["errors"]))

    sync_result = sync_topics(root)
    index = load_json(context_root(root) / "index.json")
    available = {item["id"] for item in index.get("topics", [])}
    unknown = sorted(set(topic_ids) - available)
    if unknown:
        raise ValueError(f"unknown topic ids: {', '.join(unknown)}")

    current_path = context_root(root) / "current.json"
    history_path = context_root(root) / "history.jsonl"
    current = load_json(current_path)
    timestamp = now_iso()
    event = {
        "at": timestamp,
        "type": event_type,
        "summary": summary,
        "refs": refs,
    }
    with history_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    current.update({
        "revision": int(current.get("revision", 0)) + 1,
        "updatedAt": timestamp,
        "status": status_value,
        "lastCompleted": summary,
        "nextStep": next_step,
        "activeTopics": topic_ids,
    })
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    doctor_result = doctor(root)
    if not doctor_result["ok"]:
        raise ValueError("context completion failed doctor: " + "; ".join(doctor_result["issues"]))
    return {
        "ok": True,
        "completedAt": timestamp,
        "currentRevision": current["revision"],
        "topicSync": sync_result,
        "doctor": doctor_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "doctor", "sync", "status", "list-topics", "check-paths", "snapshot"):
        command = sub.add_parser(name)
        command.add_argument("--root")
    find_command = sub.add_parser("find")
    find_command.add_argument("query")
    find_command.add_argument("--limit", type=int, default=5)
    find_command.add_argument("--root")
    history_command = sub.add_parser("history")
    history_command.add_argument("--limit", type=int, default=10)
    history_command.add_argument("--type")
    history_command.add_argument("--root")
    topic_command = sub.add_parser("topic-write")
    topic_command.add_argument("--id", required=True)
    topic_command.add_argument("--summary", required=True)
    topic_command.add_argument("--keyword", action="append", default=[])
    topic_command.add_argument("--status", default="active")
    topic_command.add_argument("--body-file", default="-", help="Body source; '-' reads stdin")
    topic_command.add_argument("--root")
    complete_command = sub.add_parser("complete")
    complete_command.add_argument("--summary", required=True)
    complete_command.add_argument("--next-step", required=True)
    complete_command.add_argument("--status", default="active")
    complete_command.add_argument("--topic", action="append", default=[])
    complete_command.add_argument("--ref", action="append", default=[])
    complete_command.add_argument("--event-type", default="change")
    complete_command.add_argument("--root")
    args = parser.parse_args()
    root = project_root(args.root)
    try:
        if args.command in ("validate", "check-paths"):
            payload = validation(root)
        elif args.command == "doctor":
            payload = doctor(root)
        elif args.command == "sync":
            payload = sync_topics(root)
        elif args.command == "status":
            payload = status(root)
        elif args.command == "find":
            payload = find_topics(root, args.query, max(1, min(args.limit, 20)))
        elif args.command == "list-topics":
            payload = list_topics(root)
        elif args.command == "history":
            payload = history(root, max(1, min(args.limit, 100)), args.type)
        elif args.command == "topic-write":
            payload = topic_write(
                root,
                args.id,
                args.summary,
                args.keyword,
                args.status,
                read_body(args.body_file),
            )
        elif args.command == "complete":
            payload = complete(
                root,
                args.summary,
                args.next_step,
                args.status,
                args.topic,
                args.ref,
                args.event_type,
            )
        else:
            payload = snapshot(root)
        return emit(payload, 0 if payload.get("ok") else 1)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        return emit({"ok": False, "error": str(exc)}, 1)


if __name__ == "__main__":
    raise SystemExit(main())
