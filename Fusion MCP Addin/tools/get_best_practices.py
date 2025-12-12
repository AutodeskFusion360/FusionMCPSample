"""
Get Best Practices Tool

This module defines a tool for getting best practices for using the Fusion API.

curl -X POST http://localhost:9100/ -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {\"name\": \"get_best_practices\"}}"
"""

import traceback
import os
from ..mcp_primitives.tool import Tool
from ..mcp_primitives.item import Item
from ..mcp_primitives.registry import register
import adsk.core

app = adsk.core.Application.get()


def handler() -> dict:
    """
    Handler function for getting the best practices for using the Fusion API.
    
    Returns:
        JSON RPC result dictionary
    """

    try:
        app.log(f"Getting design best practices")

        tools_dir = os.path.dirname(os.path.abspath(__file__))
        text_file = os.path.join(tools_dir, "best_practices.md")

        if not os.path.exists(text_file):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Best practices file not found at {text_file}\n\n💡 The best_practices.md file should be in the tools directory."
                    }
                ],
                "isError": True
            }

        # Read the content of the best practices file
        with open(text_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add header and formatting
        text = "🎯 **FUSION 360 DESIGN BEST PRACTICES**\n\n"
        text += "📚 **Source**: best_practices.md\n"
        text += f"📄 **Length**: {len(content.splitlines())} lines\n\n"
        text += "---\n\n"
        text += content
        text += "\n\n---\n\n"
        text += "✅ **Tip**: Keep these best practices in mind when designing in Fusion 360!\n"
        text += "🔄 **Updated**: This guide reflects learnings from real design projects"

        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ],
            "isError": False
        }
    except Exception as e:
        app.log(f"Error getting best practices: {e}\n{traceback.format_exc()}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(e)
                }
            ],
            "isError": True,
            "message": "Error getting best practices"
        }


# Create the screenshot tool definition

TOOL_DESCRIPTION = \
"""Get Fusion 360 design best practices and guidelines

Returns comprehensive best practices for Fusion 360 design including:
    - Coordinate system fundamentals
    - Body naming strategies
    - Construction plane techniques
    - Script execution guidelines
    - Advanced geometry creation
    - Material application
    - Problem-solving approaches"""

tool = Tool.create_simple(
    name="get_best_practices",
    description=TOOL_DESCRIPTION
)

# Create the tool item with handler
item = Item.create_tool_item(
    tool=tool,
    handler=handler
)

# Register the tool in the registry
register(item)
