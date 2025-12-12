"""
Fusion Add-in that provides HTTP API for MCP communication
Communicates with the Go MCP proxy server
"""

import traceback
import adsk.core
import adsk.fusion
from .server.mcp_server import start_mcp_server, stop_mcp_server#, example_tools, example_resources
from .mcp_primitives.registry import get_tools, get_resources
from .server.task_manager import TaskManager
# Import tools and resources to register them
from . import tools
from . import resources

# Global variables
app = adsk.core.Application.get()
ui = app.userInterface
mcp = None
server = None
thread = None

HOST = 'localhost'
PORT = 9100

# Fusion Add-in Entry Points
def run(context):
    """Called when add-in starts"""

    try:
        global app, mcp, server, thread, ui

        TaskManager.start()

        # tools = example_tools()
        # resources = example_resources()    
        tools = get_tools()
        resources = get_resources()
        mcp, server, thread = start_mcp_server(
            host=HOST,
            port=PORT,
            tools=tools,
            resources=resources
        )

        # Start HTTP server with integrated ThreadExecutor
        if mcp:
            app.log(
                f"Fusion MCP Add-in started successfully!\n\n"
                f"MCP server running on {HOST}:{PORT}\n"
                f"You can now connect to Fusion."
            )
        else:
            if ui:
                ui.messageBox("Failed to start Fusion MCP Add-in")
            if app:
                app.log("Failed to start Fusion MCP Add-in")
    except Exception:
        app.log(f'Failed to start Fusion MCP Add-in:\n{traceback.format_exc()}')


def stop(context):
    """Called when add-in stops"""

    try:
        TaskManager.stop()

        if stop_mcp_server(server, thread):
            if app:
                app.log("Fusion MCP Add-in stopped successfully.")
        else:
            if app:
                app.log("Error stopping Fusion MCP Add-in")

    except Exception:
        if app:
            app.log(f"Error stopping Fusion MCP Add-in:\n{traceback.format_exc()}")
