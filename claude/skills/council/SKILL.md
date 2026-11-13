---
name: council
description: Convene an LLM council - 5 Sonnet advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) answer a decision independently, peer-review each other anonymously, then Opus gives the chairman's verdict. Use when {{NAME}} says "council", "/council", "run it past the council", "pressure-test this", or wants a decision challenged instead of agreed with. Not for factual lookups or code changes.
---

# Council

Kills yes-man answers on decisions worth a few minutes: plans, trade-offs, "should I X or Y". Opus (you) is the chairman. Advisors are `council-advisor` subagents (Sonnet). They see only the brief, never this conversation.

## 1. Brief

Write one brief, max ~200 words:

```
QUESTION: <the decision, one line>
CONTEXT: <only facts that change the answer: goals, constraints, numbers, what's been tried>
OPTIONS: <if known>
SUCCESS LOOKS LIKE: <what a good outcome is>
FILES: <paths, only if an advisor must read them>
```

No conversation history, no Brain dumps, no preamble. If the question is too vague to brief (no goal, no constraint), ask {{NAME}} one question first.

## 2. Round 1: advise (5 parallel calls, one message)

Launch 5 `Agent` calls with `subagent_type: council-advisor`, `run_in_background: false`, all in a single message. Each prompt = role card + brief + format:

| Seat | Role card |
|---|---|
| Contrarian | Find the fatal flaw. Assume this fails; say why. Attack the strongest-looking option hardest. |
| First Principles | Strip assumptions. What is actually being solved? Rebuild the answer from the base facts; flag any premise that is wrong. |
| Expansionist | Look for the bigger upside being missed. What would make this 10x better, or a better option nobody listed? |
| Outsider | You know nothing about this field. Point at what looks odd, overcomplicated or jargon-hidden to a smart newcomer. |
| Executor | Only cares what happens Monday. Is it doable with these resources? First 3 concrete steps, and where it stalls. |

Format line to append: `Answer in max 150 words: POSITION (one line), REASONING, BIGGEST RISK.`

## 3. Round 2: peer review (5 parallel calls, one message)

Shuffle the 5 answers and label them A to E (drop seat names). Launch 5 more `council-advisor` calls, one per seat, each with: its role card, the QUESTION line, the 5 labelled answers, and:

`Review as your seat, max 100 words: STRONGEST (letter + why), WEAKEST (letter + the flaw), WHAT ALL MISSED.`

Skip round 2 only if {{NAME}} asks for a quick council.

## 4. Chairman's verdict (you, inline)

Map letters back to seats. Weigh arguments, not votes; a lone advisor can be right. Then reply:

```
## Council: <question>
**Verdict:** <the call, one or two lines>

**The seats** - one line each: Contrarian / First Principles / Expansionist / Outsider / Executor
**Where they agree:** ...
**Where they clash:** ... and which side wins, why
**What the council caught:** blind spots from round 2 you would have missed
**Recommendation:** concrete next steps
**Confidence:** high / medium / low, and what would change it
```

Then the plain-English **Summary:** per {{NAME}}'s profile. Disagree with the council if your own reasoning beats it, and say so.

## Rules
- Advisors get the brief only. Never paste transcript, CLAUDE.md or Brain notes into prompts.
- Do not show raw advisor outputs unless {{NAME}} asks; the verdict is the deliverable.
- One council per decision. No re-running until it agrees with you.
