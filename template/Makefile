.PHONY: help up down chat logs eval verify-feeds telegram-chat-id deploy clean

help:
	@echo "make up               - build + start the agent (background)"
	@echo "make chat             - attach a CLI session"
	@echo "make logs             - tail container logs"
	@echo "make down             - stop and remove the container"
	@echo "make eval             - run the eval suite"
	@echo "make verify-feeds     - HEAD-check every feed in corpus/feeds.yaml"
	@echo "make telegram-chat-id - print the chat ID of the next Telegram message"
	@echo "make deploy           - deploy to REMOTE host (see scripts/deploy.sh)"
	@echo "make clean            - remove ./out artefacts"

up:
	docker compose up -d --build

chat:
	docker compose exec agent hermes

logs:
	docker compose logs -f --tail=200

down:
	docker compose down

eval:
	docker compose exec agent python /app/evals/score.py --report
	@echo "Report at evals/report.md"

verify-feeds:
	@python -c "import yaml, urllib.request; \
data = yaml.safe_load(open('corpus/feeds.yaml')); \
[print(f\"{f['name']:30s} {urllib.request.urlopen(f['url'], timeout=5).status}\") \
 for f in data['feeds']]"

telegram-chat-id:
	docker compose exec agent hermes gateway telegram chat-id

deploy:
	./scripts/deploy.sh

clean:
	rm -rf out/memos out/feedback out/digest out/session_budget.json
