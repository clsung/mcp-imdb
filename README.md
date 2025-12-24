# mcp-imdb MCP server

A Model Context Protocol (MCP) server for accessing IMDB data.
Original author: [Cheng-Lung Sung](https://github.com/clsung/mcp-imdb)

## Components

### Resources

The server implements a simple note storage system with:
- Custom note:// URI scheme for accessing individual notes
- Each note resource has a name, description and text/plain mimetype

### Prompts

The server provides a single prompt:
- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

### Tools

The server implements one tool:
- add-note: Adds a new note to the server
  - Takes "name" and "content" as required string arguments
  - Updates server state and notifies clients of resource changes

## Configuration

[TODO: Add configuration details specific to your implementation]

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-imdb": {
      "command": "uv",
      "args": [
        "--directory",
        "<dir_to>/git/mcp-imdb",
        "run",
        "mcp-imdb"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-imdb": {
      "command": "uvx",
      "args": [
        "mcp-imdb"
      ]
    }
  }
  ```
</details>

## Docker

You can run the server as an HTTP SSE (Server-Sent Events) server using Docker.

### Building the Docker Image

```bash
docker build -t mcp-imdb .
```

### Running the Docker Image

```bash
docker run -p 8000:8000 mcp-imdb
```

The server will be available at `http://localhost:8000/sse` for SSE connections and `http://localhost:8000/messages/` for POST messages.

### Docker Compose

You can also use Docker Compose to run the server. Create a `docker-compose.yml` file:

```yaml
services:
  mcp-imdb:
    image: ghcr.io/juanmandev/mcp-imdb:latest
    build: .
    ports:
      - "8000:8000"
    restart: always
```

Then run:
```bash
docker-compose up -d
```

### Connecting VS Code GitHub Copilot to Docker

Once the server is running via Docker, add the following to your VS Code `settings.json`:

```json
{
  "github.copilot.chat.mcpServers": {
    "mcp-imdb": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory <dir_to>/git/mcp-imdb run mcp-imdb
```
Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
