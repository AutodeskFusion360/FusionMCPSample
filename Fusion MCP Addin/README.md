## Installation

1. Copy the `Fusion MCP Addin` folder to your Fusion add-ins directory:
    - Windows: `%APPDATA%\Autodesk\Autodesk Fusion\API\AddIns\`
    - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion/API/AddIns/`

2. Start Fusion and go to the **Add-Ins** panel

3. Find "Fusion MCP Addin" in the list and click **Run**

4. The add-in will start an HTTP server on `localhost:9100` (port is configurable in the code if needed)

Or alternatively, work from the cloned repository directly by just adding the `Fusion MCP Addin` folder from the cloned source location in Fusion's **Add-Ins** panel.

## Configuring Cursor

To use this MCP server with Cursor, add it to your Cursor configuration:

```json
{
  "mcpServers": {
    "fusion-mcp-server": {
      "url": "http://localhost:9100/"
    }
  }
}
```

## Available Tools

Once the add-in is running, the following MCP tools are available:

### execute_api_script

Execute Python scripts using the Fusion API. The script runs in the Fusion context with full API access.

**Parameters:**
- `script` (string): Python script source code to execute

**Example usage from AI assistant:**
- "Create a 10cm cube at the origin"
- "List all components in the current design"
- "Extrude the selected sketch 5cm"

### get_screenshot

Capture a screenshot of the current Fusion viewport with optional camera orientation.

**Parameters:**
- `view` (string): Camera orientation - "current", "top", "bottom", "front", "back", "left", "right", "iso-top-left", "iso-top-right", "iso-bottom-left", "iso-bottom-right" (default: "current")
- `width` (integer): Screenshot width in pixels, 1-4096 (default: 512)
- `height` (integer): Screenshot height in pixels, 1-4096 (default: 512)

**Returns:** Base64-encoded PNG image data

### get_api_documentation

Search the Fusion API documentation to find classes, properties, methods, and their descriptions. This tool helps AI assistants discover and understand the Fusion API.

**Parameters:**
- `search_term` (string, required): The term to search for. Can be prefixed with namespace (e.g., "fusion.Application") or class (e.g., "core.Application.activeDocument")
- `category` (string): Search category - "class_name", "member_name", "description", or "all" (default behavior)

**Returns:** Top 3 results with documentation including class definitions, properties, methods, and their signatures

**Example searches:**
- "Application" - Find the Application class
- "fusion.Sketch.sketchCurves" - Find sketchCurves member of Sketch class
- "extrude" - Search for extrusion-related items

> **Note on Tool Descriptions**: This add-in uses detailed tool descriptions to help AI assistants understand when and how to use each tool. Clear descriptions with specific parameter constraints and usage examples significantly improve the effectiveness of MCP-based interactions.

## Troubleshooting

**Server won't start:**

- Check if port 9100 is already in use
- Verify Fusion has necessary permissions
- Check the Text Commands window for error messages

**Commands fail:**

- Check that Fusion API calls are valid for the current context
- Verify parameters are passed correctly

## License

This add-in is provided as-is for educational and development purposes. 
