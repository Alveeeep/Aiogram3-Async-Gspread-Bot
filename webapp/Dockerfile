FROM python:3.13-slim

# Копируем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Создаем пользователя заранее
RUN useradd -m -u 1001 app && \
    mkdir -p /home/app/.cache/uv && \
    chown -R app:app /home/app

WORKDIR /app

COPY --chown=app:app pyproject.toml uv.lock ./
COPY --chown=app:app webapp/pyproject.toml ./webapp/

COPY --chown=app:app webapp/ ./webapp/
COPY --chown=app:app shared/ ./shared/

RUN uv venv
RUN uv sync --no-dev

ENV PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/home/app/.cache/uv \
    PATH="/app/.venv/bin:${PATH}"

USER app

CMD ["uv", "run", "uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]