"""
Get Screenshot Resource

This module defines a resource for getting screenshots of the current Fusion 360 view.
"""

import base64
import json
import traceback
import time
import tempfile
import os
from ..mcp_primitives.resource import Resource
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
        camera = viewport.camera

        # Set orientation
        if view and view != "current":
            camera.viewOrientation = orientation
            camera.isFitView = True
            #camera.isSmoothTransition = False
            viewport.camera = camera
        viewport.refresh()

        # Small delay to ensure viewport is fully refreshed
        time.sleep(0.1)
        adsk.doEvents()

        # Create temporary file with unique name to avoid caching
        timestamp = str(int(time.time() * 1000))  # milliseconds for uniqueness
        with tempfile.NamedTemporaryFile(prefix=f'mcp_screenshot_{timestamp}_', suffix='.png',
                                         delete=False) as temp_file:
            image_path = os.path.abspath(temp_file.name)

        # Take the screenshot
        success = viewport.saveAsImageFile(image_path, width, height)

        if not success:
            return json.dumps({
                "status": "error",
                "message": "Failed to save screenshot"
            })

        # Verify file was created and has content
        if not os.path.exists(image_path):
            return json.dumps({
                "status": "error",
                "message": f"Screenshot file not created: {image_path}"
            })

        file_size = os.path.getsize(image_path)
        if file_size == 0:
            return json.dumps({
                "status": "error",
                "message": "Screenshot file is empty"
            })

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


# Create the screenshot resource definition
SCREENSHOT_DESCRIPTION = (
    "Get a screenshot of the current Fusion 360 view. Use the \"view\" parameter to specify "
    "the camera orientation of 'current' (default), 'top', 'bottom', 'front', 'back', "
    "'left', 'right', 'iso-top-left', 'iso-top-right', 'iso-bottom-left', or 'iso-bottom-right'."
    "Use the \"width\" and \"height\" parameters to specify the size (they both default to 512)."
)
get_screenshot_resource = Resource.create_json_resource(
    uri="fusion://screenshot",  # Empty URI for template resources
    name="get_screenshot",
    description=SCREENSHOT_DESCRIPTION
).set_uri_template("fusion://screenshot{?view,width,height}")

# Create the resource item with handler
get_screenshot_item = Item.create_resource_item(
    resource=get_screenshot_resource,
    handler=handler
)

# DISABLED FOR NOW. Using the tool version instead since Cursor did not seem able to use this as a resource from the agent.
# Register the resource in the registry
# register(get_screenshot_item)
