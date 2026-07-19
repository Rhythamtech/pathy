FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install python dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Final runtime image
FROM python:3.12-alpine

# Create a non-root user and setup directory permissions
RUN addgroup -S appgroup && adduser -S appuser -G appgroup \
 && mkdir /app && chown appuser:appgroup /app

WORKDIR /app

# Copy virtualenv and application files with ownership set to non-root user
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --chown=appuser:appgroup . /app

# Enable virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose backend port
EXPOSE 7777

# Set default env variables for Docker
ENV HOST=0.0.0.0
ENV PORT=7777
ENV DEBUG=false

# Switch to non-root user
USER appuser

# Healthcheck to verify the server status
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://0.0.0.0:7777/status || exit 1

CMD ["python", "server.py"]
