FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.8.21 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Copy only dependency files first for better layer caching
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install dependencies only (no project package to install)
WORKDIR /app/backend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy application code
WORKDIR /app
COPY backend ./backend

FROM python:3.13-slim AS runtime

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/app/backend/.venv/bin:$PATH"

RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /app -s /bin/false appuser

WORKDIR /app

# Copy only what's needed from build stage
COPY --from=build --chown=appuser:appgroup /app/backend ./backend

# Copy frontend directly (no build needed for static files)
COPY --chown=appuser:appgroup frontend ./frontend

USER appuser

# Change to backend directory so relative paths work
WORKDIR /app/backend

ENTRYPOINT ["python", "main.py"]