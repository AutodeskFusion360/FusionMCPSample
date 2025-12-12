"""
Execute API Script Tool

This module defines a tool for executing Fusion API Python scripts.
"""

import os
import re
import tempfile
import traceback
from ..mcp_primitives.tool import Tool
from ..mcp_primitives.item import Item
from ..mcp_primitives.registry import register
import adsk.core

app = adsk.core.Application.get()


def handler(script: str) -> dict:
    """
    Handler function for executing Fusion API Python scripts.
    
    Args:
        arguments: JSON string containing the script to execute
        
    Returns:
        JSON string containing the execution result
    """

    # The script should have a "run" function that takes a single argument.
    run_function_match = re.search(r'def\s+run\s*\(\s*(\w+)\s*\):', script)
    if not run_function_match:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Script does not have a run function that takes a single argument"
                }
            ],
            "isError": True,
            "message": "Script does not have a run function that takes a single argument",
        }

    # Create temporary file for the script
    temp_file = None
    transaction_started = False
    transacted_doc = None
    try:
        # When using Python.Run, we have to call the 'run' function directly.
        script += "\nrun(None)"

        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', prefix='script', suffix='.py', delete=False) as f:
            f.write(script)
            temp_file = f.name

        # Start a transaction to ensure the script is executed in a single transaction
        try:
            transacted_doc = app.activeDocument
        except:
            app.log("No active document to transact")
        if transacted_doc:
            app.executeTextCommand('PTransaction.Start "Execute Prompt Script"')
            transaction_started = True

        # res = app.executeTextCommand(f'Python.RunScript "{temp_file}"')
        res = app.executeTextCommand(f'Python.Run "{temp_file}"')

        if transaction_started and transacted_doc.isValid:
            current_doc = app.activeDocument
            if current_doc is transacted_doc:
                app.executeTextCommand('PTransaction.Commit')
            else:
                app.log("Active document has changed since transaction started")
                transacted_doc.activate()
                app.executeTextCommand('PTransaction.Commit')
                current_doc.activate()

        result = {
            "isError": False,
            "message": "Script executed successfully"
        }
        if res:
            result["content"] = [
                {
                    "type": "text",
                    "text": res
                }
            ]
        return result
    except Exception as e:
        if transaction_started and transacted_doc.isValid:
            try:
                current_doc = app.activeDocument
                if current_doc is transacted_doc:
                    app.executeTextCommand('PTransaction.Abort')
                else:
                    app.log("Active document has changed since transaction started")
                    transacted_doc.activate()
                    app.executeTextCommand('PTransaction.Abort')
                    current_doc.activate()
            except Exception:
                pass  # If abort fails, we can't do much about it
        res = traceback.format_exc()
        app.log(f"Error executing script: {e}:\n{res}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": res
                }
            ],
            "isError": True,
            "message": "Script execution failed"
        }
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass  # If cleanup fails, we can't do much about it


# Create the tool definition

def_file_path = os.path.realpath(os.path.join(app.applicationFolders.defaultPathForScriptsAndAddIns, 'Python/defs/adsk'))

TOOL_DESCRIPTION = \
f"""Execute Fusion API Python script source code.

IMPORTANT! DO NOT present any UI with a `messageBox`.
IMPORTANT! DO NOT catch any errors unless you want to ignore an error. Or use a `print()` statment with the specific error so you can determine what the error is.
DO take a screenshot before editing an existing document to understand the model.
DO take a screenshot after making changes to ensure the changes worked as expected.
DO use `print()` statements to return any information or values from the script through the `result` field in the response.

MAKE SURE the script defines a "run" function that will be run. For example:
    ```python
    def run(context):
        print("result value")
    ```

IMPORTANT! DO NOT handle exceptions. Let them be raised to Fusion so that changes already made in the script are aborted, and so the error message and location is returned to the agent.

DO refer to the documentation of the Fusion API by searching in the Python module files located in the "{def_file_path}" folder.
"""

SCRIPT_ARG_DESCRIPTION = \
"""Fusion API Python script source code to execute."""

tool = Tool.create_with_string_input(
    name="execute_api_script",
    description=TOOL_DESCRIPTION,
    input_param_name="script", # must match the keyword argument in the handler function
    input_param_description=SCRIPT_ARG_DESCRIPTION
)

# Create the item with handler
item = Item.create_tool_item(
    tool=tool,
    handler=handler
)

# Register the tool in the registry
register(item)
