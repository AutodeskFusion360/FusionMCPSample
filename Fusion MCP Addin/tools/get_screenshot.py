"""
Get Screenshot Tool

This module defines a tool for getting screenshots of the current Fusion 360 view.

curl -X POST http://localhost:9100/ -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {\"name\": \"get_screenshot\", \"arguments\": {\"view\": \"current\", \"width\": 512, \"height\": 512}}}"
"""

import base64
import traceback
import time
import tempfile
import os
from ..mcp_primitives.tool import Tool
from ..mcp_primitives.item import Item
from ..mcp_primitives.registry import register
import adsk.core
from adsk.core import ViewOrientations

app = adsk.core.Application.get()


def handler(view: str = "current", width: int = 512, height: int = 512) -> dict:
    """
    Handler function for getting a screenshot of the current Fusion 360 view.
    
    Args:
        view: Camera orientation - "current", ... (default: "current")
    
    Returns:
        JSON string containing the screenshot result with base64 image data
    """

    try:
        app.log(f"Getting screenshot: view: {view}, width: {width}, height: {height}")

        # Convert string parameters to appropriate types
        try:
            width = int(width) if isinstance(width, str) else width
        except (ValueError, TypeError):
            width = 512
        try:
            height = int(height) if isinstance(height, str) else height
        except (ValueError, TypeError):
            height = 512

        orientation_map = {
            'top': ViewOrientations.TopViewOrientation,
            'bottom': ViewOrientations.BottomViewOrientation,
            'front': ViewOrientations.FrontViewOrientation,
            'back': ViewOrientations.BackViewOrientation,
            'left': ViewOrientations.LeftViewOrientation,
            'right': ViewOrientations.RightViewOrientation,
            'iso-top-left': ViewOrientations.IsoTopLeftViewOrientation,
            'iso-top-right': ViewOrientations.IsoTopRightViewOrientation,
            'iso-bottom-left': ViewOrientations.IsoBottomLeftViewOrientation,
            'iso-bottom-right': ViewOrientations.IsoBottomRightViewOrientation,
        }
        orientation = orientation_map.get(view, ViewOrientations.IsoTopLeftViewOrientation)
        viewport = app.activeViewport

        # Set orientation
        if view and view != "current":
            camera = viewport.camera
            camera.viewOrientation = orientation
            viewport.camera = camera

            # Small delay to ensure viewport is fully refreshed
            start_time = time.time()
            while time.time() - start_time < 1.0:
                adsk.doEvents()

            camera = viewport.camera
            camera.isFitView = True
            viewport.camera = camera

        # Create temporary file with unique name to avoid caching
        timestamp = str(int(time.time() * 1000))  # milliseconds for uniqueness
        with tempfile.NamedTemporaryFile(prefix=f'mcp_screenshot_{timestamp}_', suffix='.png',
                                         delete=False) as temp_file:
            image_path = os.path.abspath(temp_file.name)

        # Take the screenshot
        success = viewport.saveAsImageFile(image_path, width, height)

        if not success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Failed to save screenshot"
                    }
                ],
                "isError": True,
                "message": "Failed to save screenshot"
            }

        # Verify file was created and has content
        if not os.path.exists(image_path):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Screenshot file not created: {image_path}"
                    }
                ],
                "isError": True,
                "message": f"Screenshot file not created: {image_path}"
            }

        file_size = os.path.getsize(image_path)
        if file_size == 0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Screenshot file is empty"
                    }
                ],
                "isError": True,
                "message": "Screenshot file is empty"
            }

        # Read the image file and encode as base64
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

        # Clean up the temporary file
        try:
            os.unlink(image_path)
        except:
            pass  # Ignore cleanup errors

        # Dummy placeholder: 1x1 pixel transparent PNG
        # This is a minimal PNG file (89 bytes) representing a single transparent pixel
        # width = 1
        # height = 1
        # dummy_png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        # base64_image = base64.b64encode(dummy_png_data).decode('utf-8')

        return {
            "content": [
                {
                    "type": "image",
                    "data": base64_image,
                    "mimeType": 'image/png',
                    "width": width,
                    "height": height,
                    "view": view
                }
            ],
            "isError": False,
            "message": "Screenshot captured"
        }
    except Exception as e:
        app.log(f"Error getting screenshot: {e}\n{traceback.format_exc()}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(e)
                }
            ],
            "isError": True,
            "message": "Error getting screenshot"
        }


# Create the screenshot tool definition

TOOL_DESCRIPTION = \
"""Get a screenshot of the current Fusion view.
Use the `view` param to get a specific view orientation.

DO take a screenshot before editing an existing document to understand the current state.
DO take a screenshot after executing a script to make changes to ensure the changes are what you expect."""

tool = Tool.create_simple(
    name="get_screenshot",
    description=TOOL_DESCRIPTION
).add_input_property(
    "view",
    {
        "description": "Sets the camera orientation to use.",
        "type": "string",
        "enum": ["current", "top", "bottom", "front", "back", "left", "right", "iso-top-left", "iso-top-right", "iso-bottom-left", "iso-bottom-right"],
        "default": "current"
    }
).add_input_property(
    "width",
    {
        "description": "The width of the screenshot in pixels.",
        "type": "integer",
        "minimum": 1,
        "maximum": 4096,
        "default": 512
    }
).add_input_property(
    "height",
    {
        "description": "The height of the screenshot in pixels.",
        "type": "integer",
        "minimum": 1,
        "maximum": 4096,
        "default": 512
    }
)

# Create the tool item with handler
item = Item.create_tool_item(
    tool=tool,
    handler=handler
)

# Register the tool in the registry
register(item)
