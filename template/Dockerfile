# Thin layer over Hermes. The runtime is upstream; this image adds the
# template's skill, corpus, crons, evals, and budget guard.

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "hermes-agent[telegram]"

WORKDIR /app
COPY skills/   /app/skills/
COPY corpus/   /app/corpus/
COPY crons/    /app/crons/
COPY evals/    /app/evals/
COPY scripts/  /app/scripts/
COPY AGENTS.md /app/AGENTS.md

RUN mkdir -p /app/out/memos /app/out/feedback /app/out/digest

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "/app/scripts/entrypoint.py"]
