# Server Package

This package provides an MCP server implementation and thread-safe execution utilities for Fusion 360.

## Components

### ThreadExecutor

Provides thread-safe execution of Fusion API calls from background threads using Fusion's custom event system.

### MCP Server (`server/mcp_server.py`)

Lightweight, Fusion-compatible MCP server over HTTP with no external dependencies.

- `start_mcp_server(host='localhost', port=9100, tools=None, resources=None)`
- `stop_mcp_server(http_server, server_thread, timeout=5)`

#### Quick Start

```python
from server.mcp_server import start_mcp_server, stop_mcp_server

def hello_world(name: str = "World") -> str:
    return f"Hello, {name}!"

tools = {
    "hello_world": {
        "function": hello_world,
        "description": "Say hello"
    }
}

mcp, http_server, thread = start_mcp_server(host='localhost', port=9100, tools=tools)

# ... later
stop_mcp_server(http_server, thread)
```

#### Registering Tools and Resources

```python
def add_numbers(a: int, b: int) -> int:
    return a + b

def get_status() -> dict:
    return {"status": "running"}

tools = {
    "add_numbers": {"function": add_numbers, "description": "Add two numbers"}
}

resources = {
    "server://status": {"function": get_status, "description": "Server status"}
}

start_mcp_server(tools=tools, resources=resources)
```

#### Supported MCP Methods

- initialize
- tools/list
- tools/call
- resources/list
- resources/read

Responses follow JSON-RPC 2.0 with MCP-compatible payloads.

## Thread Safety

- HTTP requests are handled in separate threads
- Fusion API calls should be executed in the main thread via `ThreadExecutor`
- Resource cleanup is performed on shutdown

## Error Handling

Errors are returned in a consistent JSON-RPC error format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {"code": -32603, "message": "Error description"}
}
```

## Manually Testing Tools

### Start MCP Server Outside
python mcp_server.py

### Health check
curl http://localhost:9100/health

### Initialize MCP connection
curl -X POST http://localhost:9100/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}'

### List tools
curl -X POST http://localhost:9100/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}'

### Call a tool
curl -X POST http://localhost:9100/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "id": 3, "params": {"name": "hello_world", "arguments": {"name": "Fusion"}}}'

### List resources
curl -X POST http://localhost:9100/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/list"
  }'

### List resource templates
curl -X POST http://localhost:9100 \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 1,
    \"method\": \"resources/templates/list\",
    \"params\": {}
  }"

### Read resource template
curl -X POST http://localhost:9100 \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 1,
    \"method\": \"resources/read\",
    \"params\": {
      \"uri\": \"fusion://screenshot?view=current^&width=100^&height=100\"
    }
  }"

### Read a specific resource
curl -X POST http://localhost:9100/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "resources/read",
    "params": {
      "uri": "server://status"
    }
  }'

### Read a resource template
curl -X POST http://localhost:9100 \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 1,
    \"method\": \"resources/read\",
    \"params\": {
    \"uri\": \"fusion://screenshot?view=current\"
    }
  }"