
import asyncio
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from mcp.server.sse import SseServerTransport
from mcp_imdb.server import server

def create_app():
    # Create the SSE server transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as streams:
            read_stream, write_stream = streams
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    # Starlette routes
    routes = [
        Mount("/sse", app=handle_sse),
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

    return Starlette(routes=routes, middleware=middleware)

app = create_app()

def main():
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
