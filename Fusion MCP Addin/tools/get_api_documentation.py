"""
Get API Documentation Tool

This module defines a tool for searching for documentation in the Fusion API.

curl -X POST http://localhost:9100/ -H "Content-Type: application/json" -d "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {\"name\": \"get_api_documentation\", \"arguments\": {\"search_term\": \"Application\", \"category\": \"class_name\"}}}"
"""

import inspect
import json
import re
import traceback
from types import ModuleType, FunctionType
from ..mcp_primitives.tool import Tool
from ..mcp_primitives.item import Item
from ..mcp_primitives.registry import register
import adsk
import adsk.core

app = adsk.core.Application.get()

MAX_RESULTS = 3

def get_short_description(member: property | FunctionType, member_name: str) -> dict:
    return {
        "name": member_name,
        "doc": member.__doc__[:member.__doc__.find('.')].strip() if member.__doc__ else ""
    }

def get_class_doc(class_obj: type, namespace_name: str) -> str:
    result = {
        "type": "class",
        "name": class_obj.__name__,
        "namespace": f'adsk.{namespace_name}',
        "doc": class_obj.__doc__
    }
    properties = []
    functions = []
    for member_name, member in class_obj.__dict__.items():
        if member_name.startswith("_"):
            continue
        if member_name in ["thisown", "cast"]:
            continue
        if isinstance(member, property):
            properties.append(get_short_description(member, member_name))
        elif isinstance(member, FunctionType):
            functions.append(get_short_description(member, member_name))
    if properties:
        result['properties'] = properties
    if functions:
        result['functions'] = functions
    return json.dumps(result)

def get_property_doc(prop: property, prop_name: str, class_name: str, namespace_name: str) -> str:
    result = {
        "type": "property",
        "name": prop_name,
        "class": class_name,
        "namespace": f'adsk.{namespace_name}',
        "doc": prop.__doc__
    }
    if prop.fset is None:
        result['readonly'] = True
    return json.dumps(result)

def get_function_doc(func: FunctionType, class_name: str, namespace_name: str) -> str:
    result = {
        "type": "function",
        "name": func.__name__,
        "class": class_name,
        "namespace": f'adsk.{namespace_name}',
        "doc": func.__doc__
    }
    signature_str = str(inspect.signature(func))

    # Remove 'self' parameter if present
    if signature_str.startswith('(self'):
        signature_str = signature_str.replace('(self, ', '(').replace('(self)', '()')

    # Remove quotes and replace :: with .
    signature_str = signature_str.replace("'", "")
    signature_str = signature_str.replace("::", ".")

    # Remove adsk::core::Ptr<> wrapper
    signature_str = re.sub(r'adsk\.core\.Ptr<([^>]+)>', r'\1', signature_str)

    result['signature'] = signature_str
    return json.dumps(result)

def handler(search_term: str, category: str = "class") -> dict:
    """
    Handler function for searching the API documentation.
    
    Args:
        search_term: The text to search for.
    
    Returns:
        JSON string containing the documentation of the results.
    """

    try:
        app.log(f"Searching documentation: term: {search_term}, type: {category}")

        # convert the search term to lowercase to make the search case insensitive
        search_term = search_term.lower()

        # remove the "adsk."" namespace prefix if it exists
        if search_term.startswith('adsk.'):
            search_term = search_term[5:]

        # split the namespace prefix from the search term if it exists
        if '.' in search_term:
            namespace_prefix, search_term = search_term.split('.', 1)
        else:
            namespace_prefix = None

        # split the class name from the search term if it exists
        if '.' in search_term:
            class_name_prefix, search_term = search_term.split('.', 1)
        else:
            class_name_prefix = None

        if category != "description":
            parts = re.split(r'\s', search_term, 1)
            search_term = parts[0] if parts else ""
            ignored_term = parts[1] if len(parts) > 1 else ""
        else:
            ignored_term = None

        if not search_term:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "empty search_term"
                    }
                ],
                "isError": True
            }

        app.log(f"namespace_prefix: {namespace_prefix}, class_name_prefix: {class_name_prefix}, search_term: {search_term}, ignored_term: {ignored_term}")

        # enumerate all the classes in the adsk module's dictionary
        exact_matches = []
        matches = []
        for namespace_name, namespace in adsk.__dict__.items():
            if namespace_name.startswith("_") or not isinstance(namespace, ModuleType):
                continue
            if namespace_prefix and namespace_prefix != namespace_name:
                continue

            app.log(f"searching namespace: {namespace_name}")

            for class_name, class_obj in namespace.__dict__.items():
                if class_name.startswith("_") or not isinstance(class_obj, type):
                    continue
                class_name = class_name.lower()
                if class_name_prefix and class_name_prefix != class_name:
                    continue

                app.log(f"searching class: {class_name}")

                if category == "class_name" or category == "all":
                    if search_term == class_name:
                        exact_matches.append((namespace_name, class_obj, None))
                    elif search_term in class_name:
                        matches.append((namespace_name, class_obj, None))
                if category == "description" or category == "all":
                    class_doc = class_obj.__doc__.lower() if class_obj.__doc__ else ""
                    if search_term in class_doc:
                        matches.append((namespace_name, class_obj, None))

                if category == "member_name" or category == "description" or category == "all":
                    for member_name, member_obj in class_obj.__dict__.items():
                        if member_name.startswith("_") or not isinstance(member_obj, (property, FunctionType)):
                            continue
                        member_name = member_name.lower()
                        if member_name in ["thisown", "cast"]:
                            continue

                        if category == "member_name" or category == "all":
                            if search_term == member_name:
                                exact_matches.append((namespace_name, class_obj, member_obj))
                            elif search_term in member_name:
                                matches.append((namespace_name, class_obj, member_obj))
                        if category == "description" or category == "all":
                            member_doc = member_obj.__doc__.lower() if member_obj.__doc__ else ""
                            if search_term in member_doc:
                                matches.append((namespace_name, class_obj, member_obj))
                        if len(exact_matches) >= MAX_RESULTS:
                            break

                if len(exact_matches) >= MAX_RESULTS:
                    break

            if len(exact_matches) >= MAX_RESULTS:
                break

        # Dump the summary of the exact matches first, then matches
        results = []
        for namespace_name, class_obj, member_obj in (exact_matches + matches)[:MAX_RESULTS]:
            class_name = class_obj.__name__
            if not member_obj: # class
                results.append(get_class_doc(class_obj, namespace_name))
            elif isinstance(member_obj, property):
                # Find the property name from the class
                prop_name = None
                for name, member in class_obj.__dict__.items():
                    if member is member_obj:
                        prop_name = name
                        break
                results.append(get_property_doc(member_obj, prop_name or "unknown", class_name, namespace_name))
            elif isinstance(member_obj, FunctionType):
                results.append(get_function_doc(member_obj, class_name, namespace_name))

        contents = []
        for result in results:
            contents.append({
                "type": "text",
                "text": result
            })

        if ignored_term:
            contents.append({
                "type": "text",
                "text": f"(ignored: \"{ignored_term}\" portion of the search_term following whitespace)"
            })
        return {
            "content": contents,
            "isError": False,
            "message": f"found {len(contents)} result{'s' if len(contents) > 1 else ''}",
        }
    except Exception as e:
        app.log(f"Error searching documentation: {e}\n{traceback.format_exc()}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(e)
                }
            ],
            "isError": True,
            "message": "Error searching documentation"
        }


# Create the documentation tool definition

TOOL_DESCRIPTION = \
f"""Search the Fusion API documentation.
Searches are case insensitive.
Use the `search_term` param to search for a specific term.
Use the `category` param to search for a specific type of documentation.

Returns the top {MAX_RESULTS} results from the search.
DO limit the search to a namespace, if known, with a "namespace." prefix, for example "fusion.SEARCH_TERM".
DO limit the search to a class, if known, with a "namespace.class_name." prefix, for example "fusion.Application.SEARCH_TERM".
IMPORTANT! If you are unsure of the exact namespace of a class, leave it off. For example, search for "SurfaceEvaluator" if unsure what namespace it is in.
IMPORTANT! If you are unsure of the exact member names, get the list of members from class first with the "class_name" category. And then get the description of the exact member name and the "member_name" category.
"""

SEARCH_TERM_ARG_DESCRIPTION = \
"""The term to search for.

For the "class_name", "member_name" or "all" category types, the search term should be the name of a single class or member.
The search term can optionally be prefixed with namespace if known (e.g., "fusion.Application") or class if known (e.g., "core.Application.activeDocument").
When searching for a class or member name, a partial name can be used. For example, "extrude" will find "ExtrudeFeatures", "ExtrudeFeatureInput", any class or member that contains the word "extrude" in its description, etc....
Only the first name will be used. Anything after the first whitespace will be ignored.

For the "description" category type, the exact search term will be searched for in class and member descriptions (case insensitive).
For example, "loft feature" will find "loftFeatures" property, "LoftFeature" class, etc....
"""

CATEGORY_ARG_DESCRIPTION = \
"""The category type of documentation to search for.

class_name: searches all class names.
member_name: searches all property and function names.
description: searches all class, property, and function doc strings.
all: searches all categories."""

tool = Tool.create_simple(
    name="get_api_documentation",
    description=TOOL_DESCRIPTION
).add_input_property(
    "search_term",
    {
        "description": SEARCH_TERM_ARG_DESCRIPTION,
        "type": "string"
    }
).add_input_property(
    "category",
    {
        "description": CATEGORY_ARG_DESCRIPTION,
        "type": "string",
        "enum": ["class_name", "member_name", "description", "all"]
    }
).add_required_input("search_term")

# Create the tool item with handler
item = Item.create_tool_item(
    tool=tool,
    handler=handler
)

# Register the tool in the registry
register(item)
