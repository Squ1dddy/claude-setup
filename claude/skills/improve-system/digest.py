"""Build a compact digest of recent Claude Code sessions for /improve-system.

Reads ~/.claude/projects/**/*.jsonl locally, keeps only what {{NAME}} typed plus
friction signals (corrections, interrupts, denials, tool errors), redacts
anything that looks like a secret, and writes one Markdown file.

Usage: python digest.py [--days 7] [--root PATH] [--out PATH]
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CORRECTION = re.compile(
    r"\b(no[,.!]|nope|wrong|that's not|thats not|not what i|i said|i asked|"
    r"don't|dont|stop|undo|revert|again\?|why did you|you forgot|you missed|"
    r"actually|instead|should have|shouldn't|still (broken|wrong|not))\b",
    re.I,
)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+|"
    r"(?:api[_-]?key|token|secret|password)\s*[:=]\s*\S+|[A-Za-z0-9_-]{40,})",
    re.I,
)
NOISE = ("<system-reminder>", "<command-message>", "<local-command", "Caveat:",
         "<task-notification>", "<ci-monitor-event>", "This session is being continued")
DENIAL = ("denied", "doesn't want to proceed", "user rejected", "was rejected")


def redact(text: str) -> str:
    return SECRET.sub("[REDACTED]", text)


def clip(text: str, n: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + "..."


def user_text(content) -> str | None:
    """Return text {{NAME}} typed, or None for tool results / injected noise."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [c.get("text", "") for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        if not parts:
            return None
        text = "\n".join(parts)
    else:
        return None
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S).strip()
    if not text or text.startswith(NOISE):
        return None
    return text


def tool_results(content):
    if not isinstance(content, list):
        return
    for c in content:
        if isinstance(c, dict) and c.get("type") == "tool_result":
            body = c.get("content")
            if isinstance(body, list):
                body = " ".join(b.get("text", "") for b in body if isinstance(b, dict))
            yield bool(c.get("is_error")), str(body or "")


def parse_ts(raw):
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    root = Path(args.root)
    sessions = []
    slash = Counter()
    tools = Counter()
    denials, errors = [], Counter()

    for f in sorted(root.rglob("*.jsonl")):
        if "subagents" in f.parts:
            continue
        if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < cutoff:
            continue
        project, prompts, corrections, interrupts = f.parent.name, [], [], 0
        prev_assistant = ""
        for line in f.open(encoding="utf-8", errors="replace"):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = parse_ts(e.get("timestamp", ""))
            if ts and ts < cutoff:
                continue
            msg = e.get("message") or {}
            content = msg.get("content")
            if e.get("type") == "assistant" and isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        tools[c.get("name", "?")] += 1
                    elif isinstance(c, dict) and c.get("type") == "text":
                        prev_assistant = c.get("text", "")
                continue
            if e.get("type") != "user" or e.get("isMeta"):
                continue
            for is_err, body in tool_results(content):
                low = body.lower()
                if any(d in low for d in DENIAL):
                    denials.append(clip(redact(body), 200))
                elif is_err:
                    errors[clip(redact(body.splitlines()[0] if body else ""), 120)] += 1
            text = user_text(content)
            if text is None:
                continue
            if "[Request interrupted by user" in text:
                interrupts += 1
                continue
            m = re.match(r"<command-name>/?([\w:-]+)</command-name>", text)
            if m:
                slash[m.group(1)] += 1
                continue
            text = redact(text)
            prompts.append(clip(text))
            if CORRECTION.search(text) and prompts and len(prompts) > 1:
                corrections.append((clip(redact(prev_assistant), 200), clip(text)))
        if prompts:
            sessions.append((project, f.stem[:8], prompts, corrections, interrupts))

    out = [f"# Session digest (last {args.days} days, {len(sessions)} sessions)\n"]
    out.append("## Slash commands used\n" + ", ".join(f"{k} x{v}" for k, v in slash.most_common()) + "\n")
    out.append("## Tool use\n" + ", ".join(f"{k} x{v}" for k, v in tools.most_common(25)) + "\n")
    out.append("## Recurring tool errors (2+)\n" + "\n".join(
        f"- x{v}: {k}" for k, v in errors.most_common(20) if v > 1) + "\n")
    out.append("## Permission denials\n" + "\n".join(f"- {d}" for d in denials[:30]) + "\n")

    by_project = defaultdict(list)
    for s in sessions:
        by_project[s[0]].append(s)
    out.append("## Corrections (Claude said -> {{NAME}} replied)\n")
    for project, items in by_project.items():
        for _, sid, _, corr, intr in items:
            for said, reply in corr:
                out.append(f"- [{project} {sid}] Claude: {said}\n  {{NAME}}: {reply}")
            if intr:
                out.append(f"- [{project} {sid}] interrupted x{intr}")
    out.append("\n## Opening prompts and follow-ups by project\n")
    for project, items in by_project.items():
        out.append(f"### {project}")
        for _, sid, prompts, _, _ in items:
            out.append(f"- {sid}: " + " | ".join(prompts[:6]))
    Path(args.out).write_text("\n".join(out), encoding="utf-8")
    print(f"{len(sessions)} sessions -> {args.out} ({Path(args.out).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
