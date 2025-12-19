# Use a Python image with uv pre-installed
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application into the container.
WORKDIR /app
COPY pyproject.toml uv.lock /app/

# Install the application dependencies.
RUN uv sync --frozen --no-cache --no-install-project

COPY . /app
RUN uv sync --frozen --no-cache

# Expose the port
EXPOSE 8000

# Run the application.
CMD ["/app/.venv/bin/uvicorn", "mcp_imdb.sse_server:app", "--host", "0.0.0.0", "--port", "8000"]
