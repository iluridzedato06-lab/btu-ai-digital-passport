# BTU AI Skills Digital Passport — common tasks (Windows: use scripts/*.ps1 instead)
.PHONY: up down reset logs ps demo summary sync-once confirm-demo test test-backend test-chain test-frontend e2e chain-build deploy-contract template prod

up:            ## build and start everything (http://localhost:3000)
	@test -f .env || cp .env.example .env
	docker compose up -d --build
	@echo "Site: http://localhost:3000   Mail: http://localhost:8025   API: http://localhost:8000/api/health"

down:
	docker compose down

reset:         ## wipe database, chain state and local sheet, then start fresh
	docker compose down -v
	rm -f data/local_sheet/passport_sheet.xlsx chain/deployments/31337.json
	$(MAKE) up

logs:
	docker compose logs -f web worker

ps:
	docker compose ps

summary:       ## list passports and their verification links
	docker compose exec web python manage.py demo_summary

sync-once:
	docker compose exec web python manage.py sync_once

confirm-demo:  ## simulate the passport office confirming a new skill for the showcase student Giorgi
	docker compose exec web python manage.py demo_confirm AW-DEMO-0013

demo: up       ## start, wait for the first sync, print links
	@sleep 25
	docker compose exec web python manage.py demo_summary

deploy-contract:
	docker compose exec web python manage.py deploy_contract

template:      ## regenerate data/sheet_template
	docker compose exec web python manage.py build_sheet_template

test: test-chain test-backend test-frontend

test-backend:
	docker compose run --rm --no-deps web python -m pytest -q -p no:cacheprovider

test-chain:
	docker run --rm -v "$(CURDIR)/chain:/work" -w /work --entrypoint sh ghcr.io/foundry-rs/foundry:stable -c "forge test"

test-frontend:
	cd frontend && npm ci && npm test

e2e:           ## browser end-to-end test against the running stack (needs: pip install playwright)
	python scripts/e2e_smoke.py

chain-build:   ## recompile the contract and refresh the committed artifacts
	docker run --rm -v "$(CURDIR)/chain:/work" -w /work --entrypoint sh ghcr.io/foundry-rs/foundry:stable -c "forge build"
	python scripts/export_artifact.py

prod:
	docker compose --profile prod up -d --build
