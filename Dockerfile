FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --chown=app:app pyproject.toml uv.lock ./

RUN uv venv
RUN uv sync --locked

RUN useradd -m -u 1001 app && \
    mkdir -p /home/app/.cache/uv && \
    chown -R app:app /home/app

ENV PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/home/app/.cache/uv \
    PATH="/home/app/.local/bin:${PATH}"

COPY --chown=app:app . /app

WORKDIR /app

USER app

CMD ["uv", "run", "bot.py"]