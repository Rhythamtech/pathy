FROM astral-sh/uv:python3.12-alpine AS builder

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install python dependencies using uv
RUN uv sync --frozen --no-dev

# Final runtime image
FROM python:3.12-alpine

WORKDIR /app

# Copy virtualenv and application files
COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Enable virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose backend port
EXPOSE 7777

# Set default env variables for Docker
ENV HOST=0.0.0.0
ENV PORT=7777
ENV DEBUG=false

CMD ["python", "server.py"]
