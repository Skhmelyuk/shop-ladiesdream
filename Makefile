.PHONY: help up down restart logs ps \
        run migrate migrations shell collectstatic \
        install freeze lint clean

ifeq ($(OS),Windows_NT)
PYTHON  = venv/Scripts/python
PIP     = venv/Scripts/pip
else
PYTHON  = venv/bin/python
PIP     = venv/bin/pip
endif
MANAGE  = $(PYTHON) manage.py

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────────────────
up: ## Запустити PostgreSQL та Redis у фоні
	docker compose up -d

down: ## Зупинити та видалити контейнери
	docker compose down

restart: ## Перезапустити контейнери
	docker compose restart

logs: ## Показати логи контейнерів (Ctrl+C для виходу)
	docker compose logs -f

ps: ## Показати статус контейнерів
	docker compose ps

# ── Django ────────────────────────────────────────────────────────────────────
run: ## Запустити сервер розробки
	$(MANAGE) runserver

migrate: ## Застосувати міграції
	$(MANAGE) migrate

migrations: ## Створити нові міграції
	$(MANAGE) makemigrations

shell: ## Відкрити Django shell
	$(MANAGE) shell

collectstatic: ## Зібрати статику
	$(MANAGE) collectstatic --noinput

worker: ## Запустити Celery Worker
	venv/bin/celery -A shop worker -l info

beat: ## Запустити Celery Beat (планувальник)
	venv/bin/celery -A shop beat -l info

# ── CSS ───────────────────────────────────────────────────────────────────────
css: ## Зібрати CSS один раз
	npm run css:build

css-watch: ## Слідкувати за змінами CSS
	npm run css:watch

# ── Python залежності ─────────────────────────────────────────────────────────
install: ## Встановити залежності з requirements.txt
	$(PIP) install -r requirements.txt

freeze: ## Оновити requirements.txt з поточного venv
	$(PIP) freeze > requirements.txt

# ── Очистка ───────────────────────────────────────────────────────────────────
clean: ## Видалити кеш Python, міграції __pycache__ тощо
	find . -type d -name "__pycache__" -not -path "./.venv/*" -not -path "./venv/*" | xargs rm -rf
	find . -name "*.pyc" -not -path "./.venv/*" -not -path "./venv/*" -delete

clean-docker: ## Видалити контейнери, volumes та образи проекту
	docker compose down -v --rmi local --remove-orphans

clean-all: clean clean-docker ## Повна очистка (Python кеш + Docker)
