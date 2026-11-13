# Skills in this kit

Every skill below is copied into `~/.claude/skills/`. Descriptions come from each SKILL.md.

| Skill | What it does |
|---|---|
| `agent-reach` |  Use to READ content from platforms that WebFetch/WebSearch cannot reach: Reddit, Twitter/X, Facebook, Instagram posts, XiaoHongShu, LinkedIn, V2EX, Xueqiu, podcasts, RSS feeds. Triggers: a link to one of those platforms... |
| `anatomy` | Build crafted, highly detailed, interactive isometric SVG figures that explain a technical idea as a real physical object (a test rig, a dial gauge, a cabinet of drawers, a plotter, a lock), with many small precise solid... |
| `ask-matt` | Ask which skill or flow fits your situation. A router over the skills in this repo. |
| `auto-run` | Run a long task unattended across fresh contexts - this session plans chunks into a Brain run note, then a background loop runs one headless worker per chunk until the run stops or finishes. Use when a task is large (3+ ... |
| `brag-slim` | Turn a project directory or a website URL into a short, shareable launch video with music, motion, and share copy. One file, no bundled assets — built entirely by the model with the tools already on the machine. Use when... |
| `brain` | {{NAME}}'s long-term memory vault ({{HOME}}\Brain). Use to recall past projects, decisions, people, preferences or lessons; to save something worth remembering across sessions; or to write the daily note when {{NAME}} wr... |
| `code-video` | Make animated promo, explainer or motion-graphics videos as code (canvas scenes + synthesised sound effects) and export MP4, optionally synced to a voiceover. Use when {{NAME}} wants a promo, explainer, pitch video, moti... |
| `codebase-design` | Shared vocabulary for designing deep modules. Use when the user wants to design or improve a module's interface, find deepening opportunities, decide where a seam goes, make code more testable or AI-navigable, or when an... |
| `council` | Convene an LLM council - 5 Sonnet advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) answer a decision independently, peer-review each other anonymously, then Opus gives the chairman's verdict. Use... |
| `delegate` | Hand a build ticket to the sonnet-coder worker - when to delegate vs build inline, the brief, the acceptance check. Use when /implement starts a ticket, or {{NAME}} says delegate or sonnet. |
| `design-motion-principles` | Motion and interaction design expert based on Emil Kowalski, Jakub Krehel, and Jhey Tompkins' techniques. Two modes — build interactive components with purposeful motion, or audit existing animations to catch AI-slop mot... |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow. |
| `domain-modeling` | Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a GLOSSARY.md, or recording or editing an ADR. |
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used w... |
| `finishing-a-development-branch` | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work |
| `grill-me` | A relentless interview to sharpen a plan or design. |
| `grill-with-docs` | A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `impeccable` | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing page... |
| `implement` | Implement a piece of work based on a spec or set of tickets. |
| `improve-codebase-architecture` | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick. |
| `improve-system` | Mine {{NAME}}'s recent Claude Code session transcripts for repeated mistakes, missing context, skill candidates and automation candidates, then propose fixes. Use when {{NAME}} says /improve-system, "improve my setup", "... |
| `new-project-setup` | Set up a new project's Claude configuration. Invoke when a project has no .claude/ directory, or when the user says "set up Claude for this project". Scans all installed global skills and plugins, detects the project sta... |
| `night-shift-approve` | Act on {{NAME}}'s picks from a Night Shift review - "approve 1, 2b" against a `Brain/Inbox/Night Shift <date>.md` note. Use when he replies "approve <ids>" to a Night Shift review, or asks to install or save something it... |
| `no-ai-slop` | Edit drafts into sharper, more human writing while preserving the writer's personal voice, or detect AI-slop patterns without rewriting. Use when the user wants a draft clearer, more direct, more opinionated, or less AI-... |
| `ponytail` |  Forces the laziest solution that actually works, simplest, shortest, most minimal. Channels a senior dev who has seen everything: question whether the task needs to exist at all (YAGNI), reach for the standard library b... |
| `pr` | Use when writing a PR body. |
| `prototype` | Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like. |
| `receiving-code-review` | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind ... |
| `research` | Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork done and writt... |
| `retro` | Conduct a retrospective on a coding session. |
| `reverse-engineer-anything` | Reverse engineer native, managed, Electron/JavaScript, packaged, firmware, and browser targets with REA. Use shipped-artifact or requested runtime evidence to explain features, compare versions, decompile code, or guide ... |
| `review-changes` | Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating iss... |
| `scroll-sites` | Use when building a website, landing page, or one-page site whose visuals move with scroll (scroll-scrubbed scenes, Apple-style image-sequence animation, scroll storytelling, parallax depth) using AI-generated images or ... |
| `security-checklist` | Security checklist to follow WHILE building, for Next.js + Supabase + Netlify apps (e.g. Traksy, multi-tenant, student data). Use when adding or changing auth, sessions, roles, Server Actions, route handlers/API endpoint... |
| `setup-matt-pocock-skills` | Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills. |
| `skill-builder` | Automatically detect source types and build AI skills using Skill Seekers. Use when the user wants to create skills from documentation, repos, PDFs, videos, or other knowledge sources. |
| `skill-inspector` | Review AI agent skills before installation using NVIDIA SkillSpector and source-aware semantic review. Use when asked whether a skill or downloaded skill folder is safe, trustworthy, installable, over-permissioned, or ma... |
| `tdd` | Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests. |
| `teach` | Teach the user a new skill or concept, within this workspace. |
| `to-questionnaire` | Turn a decision you can't fully answer into a questionnaire for someone else to fill in. |
| `to-spec` | Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed. |
| `to-tickets` | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blockin... |
| `triage` | Move issues and external PRs through a state machine of triage roles, categorise, verify, grill if needed, and write agent-ready briefs. |
| `ux-feel` | Checklist of 20 small UX details (skeletons, optimistic updates, undo toasts, command menu, tabular numbers, safe areas, OTP autofill, idempotency, etc.) plus the Doherty 400ms rules, for making an app feel fast and expe... |
| `verification-before-completion` | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions a... |
| `wait-what` | Stop. That last message did not land: re-pitch it. |
| `watch-video` | Watch a video for {{NAME}} - what it says (caption, speech), what's on screen (frame sheets), and what applies to him. Use when he shares a YouTube, Instagram reel, TikTok or other video link or file and asks to watch it... |
| `wayfinder` | Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear. |
| `web-design-guidelines` | Final UI audit against Vercel's Web Interface Guidelines (accessibility, focus states, forms, motion, copy, edge cases), reporting terse file:line findings. Use only when {{NAME}} asks for "web interface guidelines", "ve... |
| `web-visual-fx` | Implementation toolkit for premium visual effects on websites - 3D scenes (React Three Fiber), liquid/Apple-style glass UI (liquid-glass-js), animated shader gradient backgrounds (ShaderGradient), and liquid/chrome anima... |
| `wizard` | Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or runn... |
| `writing-for-agents` | Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. |

## Not copied (install from upstream, pinned)

| Name | Source | Pin | Why not copied |
|---|---|---|---|
| `notebooklm` skill | github.com/PleasePrompto/notebooklm-skill | `eea5cb2` | Its `data/` folder holds a logged-in Google browser profile; never ship it. Clone, then `pip install -r requirements.txt` in a venv. |
| `claude-seo` plugin | github.com/AgricIDaniel/claude-seo | `ff87fce` | Plugin, installed as a local marketplace. Delete its `hooks/hooks.json` if you do not want a schema check on every html/tsx edit. |
| `floorplan` plugin | github.com/haydenschmitty/floorplan | `59a12f4` | Plugin, local marketplace. Set `FLOORPLAN_NO_PROMPTS=1` to hide its email waitlist prompt. |
| `ui-ux-pro-max` plugin | github.com/nextlevelbuilder/ui-ux-pro-max-skill | 2.5.0 | GitHub marketplace (in settings template). |
| `claude-hud` plugin | github.com/jarrodwatts/claude-hud | 0.8.0 | GitHub marketplace, ships disabled (checkpoint-band replaced it). |
| `caveman` plugin | github.com/JuliusBrussee/caveman | `655b7d9` | GitHub marketplace, ships disabled. |
| `playwright`, `frontend-design` | claude-plugins-official | latest | Official marketplace. |
| context7 MCP | upstash/context7 | latest | Library docs lookup the CLAUDE.md tells Claude to use. |
| rtk | rtk (Rust Token Killer) CLI | - | Binary the `rtk-rewrite.sh` hook needs; the installer skips that hook if `rtk` is not on PATH. |
| SkillSpector | github.com/NVIDIA/skillspector | `c7958a3` | Scanner used by `skill-inspector`: `uv tool install git+https://github.com/NVIDIA/skillspector.git@c7958a3`. |
