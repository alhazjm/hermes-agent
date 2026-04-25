---
name: airwallex-regulatory-triage
description: Triage daily regulatory updates from global payments regulators against Airwallex's licence footprint. Decide flag-vs-ignore against a documented playbook, draft a memo with citations, route to the right legal owner, and capture reviewer corrections as a learning signal.
version: 0.1.0
author: <your-name>
license: MIT
metadata:
  hermes:
    tags: [Compliance, RegTech, Payments, Triage, Legal]
prerequisites:
  commands: [blogwatcher-cli]
  skills: [blogwatcher]
---

# Airwallex Regulatory Triage

A judgement skill, not a classifier. The agent reads the day's regulatory
updates, decides which ones matter to Airwallex, and produces an auditable
memo with citations.

## Inputs

- `corpus/feeds.yaml` — regulator RSS/Atom feeds (FCA, MAS, FinCEN, RBA, …)
- `corpus/licences.yaml` — Airwallex's known licence footprint per jurisdiction
- `playbook.md` — what counts as relevant; updated by reviewer feedback

## Workflow

1. **Ingest.** Use the `blogwatcher` skill to pull unread items from each
   feed in `corpus/feeds.yaml`. Mark read after processing.
2. **Filter.** For each item, check the title + summary against the
   jurisdictions in `corpus/licences.yaml`. Drop items outside the footprint
   (saves model cost; logged but not memoed).
3. **Decide.** For each surviving item, fetch the full article. Apply the
   playbook in `playbook.md`. Output the JSON decision contract from
   `AGENTS.md`.
4. **Draft memo.** If `decision == "flag"`, write a memo to
   `out/memos/<update_id>.md` using the template below.
5. **Route.** Map `affected_licences` → owner via the table in `playbook.md`.
   Append the memo path + summary to the daily digest.
6. **Deliver.** When all items processed, send the digest via the configured
   `RUN_MODE` channel (CLI stdout, Telegram, Slack).
7. **Learn.** When the reviewer edits a memo, capture the diff to
   `out/feedback/<update_id>.diff`. The next run loads recent diffs as
   few-shot examples.

## Memo template

```markdown
# {update_title}

**Decision:** flag — affects {affected_licences}
**Source:** {source_url} ({regulator}, {publish_date})
**Suggested owner:** {suggested_owner}

## Why this matters

{one-paragraph rationale, citing the licence rule}

## Key citations

> {verbatim quote 1}
— [{source_url}#para-{n}]

> {verbatim quote 2}
— [{source_url}#para-{m}]

## Suggested next step

{one bullet — file response, brief counsel, monitor, etc.}
```

## Stop conditions

- Session USD budget exhausted (see `scripts/budget_guard.py`).
- No new feed items since last run (exit cleanly with "nothing today").
- Reviewer-only ambiguity flag set on > 3 items in one run (escalate
  rather than guess).

## How to extend

- **New regulator**: add to `corpus/feeds.yaml`. No code change.
- **New licence**: add to `corpus/licences.yaml`. No code change.
- **Tighter rules**: edit `playbook.md`. Run `make eval` to confirm the
  change improves precision/recall on the dataset.
- **New owner mapping**: edit the routing table in `playbook.md`.
