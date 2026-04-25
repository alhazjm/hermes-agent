# Agentic Template — Airwallex Regulatory Triage

A working agent that watches global payments regulators, flags updates that
touch Airwallex's licence footprint, and drafts a memo with citations + a
suggested owner.

Built on [Hermes](https://github.com/NousResearch/hermes-agent) — same
substrate Nous Research ships. The decision logic, corpus, schedule, evals,
and deploy are this repo's contribution; the runtime is not reinvented.

## Try it

**No setup.** DM the live bot on Telegram: `@AirwallexRegTriageDemo_bot`
(rate-limited, hosted on a $5 VPS).

**Watch a 90s walkthrough:** `<loom-link>`

**Run it yourself:** see [Self-host](#self-host) below — one env var, one command.

## What it does

```
Regulator RSS feeds  ──►  ingest  ──►  match against licence playbook
                                              │
                                              ▼
                                    judgement (relevant?)
                                       │           │
                                   irrelevant   relevant
                                       │           │
                                       ▼           ▼
                                    archive    draft memo (with citations)
                                                  │
                                                  ▼
                                       route to owner + Telegram digest
                                                  │
                                                  ▼
                                       reviewer edits → learning signal
```

Five things that separate this from a linear pipeline:

1. **Judgement, not classification.** The agent decides relevance against a
   playbook of Airwallex's actual licence footprint, not a keyword match.
2. **Citations.** Every memo links the source paragraph; reviewer can verify
   in one click.
3. **Reasoning trace.** Each decision logs why — the audit trail compliance
   teams need.
4. **Reviewer feedback loop.** Edits to the draft are captured and folded
   back into the playbook on the next run.
5. **Evals.** 30 hand-labelled historical updates with a scoring script;
   `make eval` tells you whether a prompt change made the agent better or
   worse.

## Self-host

```bash
git clone <this-repo>
cd <this-repo>/template
cp .env.example .env
# paste your OpenRouter key into .env (free tier works for testing)
make up
```

Then either:
- **CLI**: `make chat` — talk to the agent in your terminal.
- **Telegram**: set `RUN_MODE=telegram` and `TELEGRAM_BOT_TOKEN` in `.env`,
  then `make up` again. Create a bot via @BotFather (90 seconds).

The default model is `z-ai/glm-4.5-air` via OpenRouter — costs roughly
$0.10/M input tokens. A typical session uses < 50K tokens.

## Per-session budget cap

`BUDGET_USD_PER_SESSION` in `.env` (default `1.00`, max `5.00`). When the
session crosses the cap, the agent stops cleanly and reports actuals.
Set `BUDGET_ENFORCED=false` to disable.

## Repo layout

```
template/
├── skills/airwallex-regulatory-triage/
│   ├── SKILL.md              # workflow + decision contract
│   └── playbook.md           # what counts as "relevant" for Airwallex
├── corpus/
│   ├── feeds.yaml            # regulator RSS feeds
│   └── licences.yaml         # Airwallex's known licence footprint
├── crons/jobs.yaml           # nightly scan schedule
├── evals/
│   ├── dataset.jsonl         # 30 hand-labelled cases
│   └── score.py              # decision-vs-gold scoring
├── scripts/
│   ├── budget_guard.py       # USD cap enforcement
│   └── deploy.sh             # VPS deploy
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── Makefile
└── AGENTS.md                 # context contract loaded into every session
```

## Forking for another company

1. Replace `corpus/` with their public surface (docs, API ref, regulator
   list, support-ticket archive).
2. Rewrite `skills/<workflow>/playbook.md` with their actual decision rules.
3. Replace `evals/dataset.jsonl` with 20–50 hand-labelled cases from their
   public history (issue tracker, blog, changelog).
4. Adjust `crons/jobs.yaml` cadence and digest format.
5. Update `AGENTS.md` framing.

The runtime, the tool surface, the messaging gateway, the eval harness, and
the budget guard stay as-is.

## Licence

MIT. Hermes is also MIT (Nous Research).
