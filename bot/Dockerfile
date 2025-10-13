FROM python:3.13-slim

# Копируем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Создаем пользователя заранее
RUN useradd -m -u 1001 app && \
    mkdir -p /home/app/.cache/uv && \
    chown -R app:app /home/app

WORKDIR /app

COPY --chown=app:app pyproject.toml uv.lock ./
COPY --chown=app:app bot/pyproject.toml ./bot/

COPY --chown=app:app bot/ ./bot/
COPY --chown=app:app shared/ ./shared/

RUN uv lock
RUN uv venv
RUN uv sync --locked --package bot --no-dev

RUN mkdir -p /app/logs && chown -R app:app /app/logs

ENV PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/home/app/.cache/uv \
    PATH="/app/.venv/bin:${PATH}"

USER app

CMD ["uv", "run", "--package", "bot", "python", "-m", "bot.bot"]