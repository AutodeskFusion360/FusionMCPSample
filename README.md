# Fusion MCP Add-in

A Fusion add-in that provides HTTP API functionality for Model Context Protocol (MCP) communication. MCP is a standardized protocol that enables AI assistants to interact with external tools and data sources. This add-in enables external applications (like Cursor) to interact with Fusion through a secure HTTP interface.

## Features

- **HTTP Server Management**: Create and manage HTTP servers within Fusion
- **Thread-Safe Execution**: Execute Fusion API calls safely from background threads
- **MCP Server**: Exposes a Model Context Protocol server for AI assistant integration
- **Resource Access**: Access design information, components, and viewport screenshots
- **Tool Execution**: Execute Fusion commands remotely

### Available Tools

- **execute_api_script**: Execute Python scripts using the Fusion API
- **get_screenshot**: Capture viewport screenshots with various camera orientations (current, top, bottom, front, back, left, right, isometric views)
- **get_api_documentation**: Search the Fusion API documentation for classes, methods, properties, and descriptions

> **Note on Tool Descriptions**: In MCP environments, well-crafted tool descriptions are critical for AI assistants to understand when and how to use each tool. This add-in includes detailed descriptions and parameter specifications to help AI assistants effectively interact with Fusion.

## Architecture

The add-in consists of three main components:

### 1. TaskManager (`task_manager.py`)

Provides thread-safe execution of Fusion API calls from background threads using Fusion's custom event system.

**Key Features:**

- Safe execution of Fusion API calls from HTTP request handlers
- Custom event-based communication between threads
- Error handling and result reporting

### 2. McpServer (`mcp_server.py`)

**Key Features:**

- Threaded HTTP server implementation
- Custom request handler support
- Integrated socketserver ThreadingMixIn for safe Fusion API access

### 3. Main Add-in (`Fusion MCP Addin.py`)

The main add-in that implements MCP-compatible HTTP endpoints for Fusion interaction.

**Key Features:**

- Health check and status endpoints
- Resource reading (design info, components)
- Tool execution (screenshots, environment info)
- JSON-based request/response handling

## Installation & More

[Installation instructions, troubleshooting, and more are found here](<Fusion MCP Addin/README.md>)