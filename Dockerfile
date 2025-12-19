# Use a Python image with uv pre-installed
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Expose the port
EXPOSE 8000

# Run the application.
CMD ["/app/.venv/bin/uvicorn", "mcp_imdb.sse_server:app", "--host", "0.0.0.0", "--port", "8000"]
