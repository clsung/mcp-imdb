import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from mcp.server.sse import SseServerTransport
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp_imdb.server import server

def create_app():
    # Create the SSE server transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        """Handle SSE connections."""
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            read_stream, write_stream = streams
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-imdb",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        return Response()

    async def health_check(request: Request):
        """Health check endpoint."""
        return JSONResponse({"status": "ok", "server": "mcp-imdb"})

    # Starlette routes
    routes = [
        Route("/", endpoint=health_check, methods=["GET"]),
        Route("/health", endpoint=health_check, methods=["GET"]),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ]

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    return Starlette(debug=True, routes=routes, middleware=middleware)

app = create_app()

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
