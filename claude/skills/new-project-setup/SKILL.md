---
name: new-project-setup
description: Set up a new project's Claude configuration. Invoke when a project has no .claude/ directory, or when the user says "set up Claude for this project". Scans all installed global skills and plugins, detects the project stack, and wires the most relevant ones into the project.
---

# New Project Setup

Detect the project stack, scan installed skills/plugins, and wire the right ones into this project.

## Steps

### 1. Detect Project Stack

Run these checks to understand the project:

```bash
# Package managers / language
ls package.json pyproject.toml Cargo.toml go.mod pom.xml requirements.txt 2>/dev/null
cat package.json 2>/dev/null | head -60

# Framework signals
grep -r "react\|vue\|angular\|next\|express\|fastapi\|django\|flask\|rails\|laravel" package.json pyproject.toml 2>/dev/null | head -20

# Existing Claude config
ls .claude/ CLAUDE.md 2>/dev/null

# Project structure
ls src/ app/ lib/ tests/ components/ pages/ api/ 2>/dev/null
```

### 2. Inventory All Available Skills & Plugins

Use Glob to find all `SKILL.md` files:
- `{{HOME}}\.claude\skills\**\SKILL.md` (global skills)
- `{{HOME}}\.claude\plugins\**\SKILL.md` (plugin skills)

Read each one's `name` and `description` frontmatter.

### 3. Match Skills to Project

Based on the detected stack, select the most relevant skills:

| Signal | Relevant Skills/Plugins |
|--------|------------------------|
| Any repo | Matt Pocock flow: /setup-matt-pocock-skills first (local tracker), then grill-with-docs, to-spec, to-tickets, implement, review-changes |
| Next.js + Supabase | security-checklist |
| Frontend | impeccable, web-visual-fx (CLAUDE.md Frontend rule) |

### 4. Create Project Claude Config

Create the following structure in the current directory:

```
.claude/
  CLAUDE.md           ← project-level instructions
  skills/             ← project-specific skills (if any)
```

**CLAUDE.md content to generate:**

```markdown
# [Project Name]: Claude config

## Stack
[detected stack summary]

## Active Skills (from global)
[list the matched global skills with their invocation commands]

## Project-Specific Notes
[any project-specific conventions Claude should follow]
```

### 5. MCP servers

context7, playwright and Supabase are already connected globally. Recommend a project-scoped MCP only when the stack needs one that is not, and install it through the global install rule.

### 6. Output Summary

Print a summary of what was configured and what commands the user should run next.
