# Unlocking the Power of Fusion MCP

Given the rising popularity of MCP servers in product design and manufacturing, Autodesk's Fusion API team has made a basic server sample available for developers who want to experiment with them.

This document offers some insights that we hope will be useful to these developers.

## Server Sample

The Fusion MCP add-in is a reference implementation that demonstrates how an MCP server can connect agent workflows to Fusion’s Python API with a small, pragmatic toolset designed for iterative validation. It provides basic tools for context loading, API documentation lookups, script execution in Fusion, and screenshot-based validation.

**The Fusion MCP add-in is a functional sample, not a product. It’s intentionally minimal and intended to illustrate patterns and enable experimentation. It does not aim to provide all the features and guarantees required for a production-ready MCP server.** It's intended to provide a working baseline to explore patterns, prove concepts, and make it easier to start developing a Fusion MCP server project.

### What can it do?

When people think of MCP servers in the context of CAD/CAM, they often imagine an AI independently creating full components and assemblies from scratch. We're not exactly there yet. As MCPs use APIs to interact with applications, not everything that can be done by hand can be done by an MCP. Drawing sketches to build components is often out of scope.

What this MCP is particularly good at is things like:
- Retrieving and analyzing information from designs
- Editing properties of existing components
- Helping developers create add-ins

You *can* still do some automation magic, but you'll have to push this MCP to its limits. The second part of this document has tips and prompt examples for that.

### Provided Tools

MCP tools are named capabilities (basically functions) that AI agents can use to either retrieve information or execute an action. Good tools replace some of the guesswork AIs often do by allowing agents to add relevant data to context and providing them with ways to verify results.

The Fusion MCP server provides a few foundational tools. Notably, it provides a core tool that allows AI to execute scripts inside Fusion. In addition, the MCP server provides a lengthy list of best practices and a tool to access it. Finally, it also provides a way to capture Fusion's viewport and a way to search the Fusion API documentation, both exposed by MCP tools.

These tools cover a lot of ground. However, if you want to build on top of this sample, most of your development time will probably go to the creation of tools adapted to your specific workflows and use-cases.

1. #### get_best_practices
    Pulls `best_practices.md` file, containing consolidated instructions on how to use Fusion and its API, and adds it to context. This file is a bit like a rule file (think `claude.md`) that has been pre-written specifically for Fusion MCP. Use it at the beginning of a prompt to make sure the AI agent loads the necessary context.

    I like integrating it as the first line of my go-to prompt structure:

    ```
    ## CONTEXT
    Use get_best_practices to establish context, your role and the basic rules to follow.
    ```

    It can also be useful to make an explicit call to this tool if the AI starts "drifting" in longer chat sessions.

2. #### get_api_documentation 
    This tool lets the agent search Fusion's Python API for a given term and type of information (classes by default). The top 3 results will be added to the model's context. A namespace can be used to search for classes and members. The AI is instructed to use the namespace if it knows it.

    The AI agent *should* use this tool (per its best practices instructions) when it's not sure of a class or member name, needs a function’s exact signature, or wants to confirm the existence of a property. It'll start broad with class-name searches that may not return anything but will narrow it down iteratively.

    I suggest calling this tool explicitly in your prompt when you know that a specific class or function should be used. You'll see how I use this a bit later on with complete prompt examples.

3. #### execute_api_script

    Takes a Fusion API Python script as a string parameter and executes it in the Fusion environment. The AI agent interacts with Fusion with the help of API scripts. This tool gives it the ability to execute them.

    AI agents are usually consistent with this one. It's a good idea, however, to make it clear in your prompts that the agent must not run scripts that open modal windows. Open windows pause script execution so the AI has no way to interact with Fusion when one is open. It's in the best practices documentation, but you really don't want it to forget that one.
    
    If you're using an IDE like Cursor that supports it, I'd suggest creating a rule for it.

4. #### get_screenshot ####

    Takes a viewport name, a height, and a width as parameters to capture a screenshot of a viewport and add it to context. This allows the AI to produce an image it can analyze to see the results of a task.

    Again, the agent should know to use this often since it's described in the best practices. I'd still suggest explicitly specifying when the key moments are to take screenshots and visually validate the work.

#### Tip

Tools can also be called explicitly as you prompt by naming them and passing parameters in natural language. For example, if you have a tool called **get_api_documentation** that takes one argument, you can call it by simply writing something like this:

    call get_api_documentation for [argument].

This is particularly useful if you're using the MCP server as a development tool in your IDE, as it becomes a much faster way to consult API documentation (among other things).

### Choice of an AI Model

There's no model that is *de facto* the best choice for this MCP server. You should be able to achieve good results with both GPT‑5.1 and Claude 4.5. 

> **Note:** The one thing I would advise against is using Cursor's auto model. This one consistently gave me poor results.


## Getting Results (use cases, best practices and examples)

Now that we went over the Fusion MCP Server and its tools, it's time to look into how to get the best out of all of this.

### General Guidelines

Working with Fusion MCP mostly follows the same general guidelines as doing anything with AI: be specific, structure your intent, and validate as you go (or demand recurring validation if you're trying to get the agent to work independently).

If you’re a software developer, approach Fusion MCP as you would approach a programming task using AI: break the work into small, verifiable steps, lean on documentation, and iterate with feedback loops.

Here's a list of good practices tailored for Fusion MCP:

- Think programmatically
- Use an effective prompt structure
- Deconstruct complex tasks
- Force API documentation lookups
- Demand validation and be clear about visual validation
- Explicitly allow for iteration and recovery
- Be extremely specific about units and dimensions

These tips apply broadly, but they’re most important when using the Fusion MCP for full creative work. We’ll explore them in detail while walking through the last (more complex) use case below.

### Fetching and Analysing Information from Designs

This is the easiest kind of task for an AI agent. These tasks need less complex prompts and can often be done almost in natural language.

Of course, it's still always a good idea to follow the usual good practices, even if it's done implicitly.

Here is an example where the AI has to analyze a scene to return information:

```
## CONTEXT
Use get_best_practices to establish context, your role and the basic rules to follow.

## OBJECTIVE
Identify all the components that are made of metal in the current design and list their names in chat.

## REQUIREMENTS
-IMPORTANT: Never use modal dialogs or windows.
-IMPORTANT: Do not do any error handling.
```

AIs are so efficient at these tasks that, for a small request like this, the ```context``` and ```requirements``` sections become a bit superfluous. It's still a good idea to keep them for consistency, however.

Speaking of consistency, while this prompt will return satisfying results, it would be a good idea to define (or provide a way to define) what a "metal" is to make it really reliable. That's especially true if there are any custom materials in a design. 

> Note: if you're using an IDE like Cursor, it's possible to add repetitive elements of the prompt, in this example: the context and the two requirements, as prompting **rules**. This would make sure that these elements are added by the IDE itself to each prompt and allow you to write simpler prompts. It's also possible (and extremely useful) to write MCP tools that generate these rules automatically.

### Editing Properties

Editing properties of existing designs and components is almost as simple as retrieving data. Here's an example:

```
## CONTEXT
Use get_best_practices to establish context, your role and the basic rules to follow.

## OBJECTIVE
Find all components that are made of metal and change their material to carbon fiber instead. Report the weight savings.

## REQUIREMENTS
- List all affected components in chat
- Output the difference in weight of the assembly in chat

## ADDITIONAL INSTRUCTIONS
- IMPORTANT: Never use modal dialogs or windows.
- IMPORTANT: Do not use exceptions for error handling; log issues instead.
```

### Assisting Add-in Development

The MCP can also help developers with Fusion add-in development just like it can assist in most programming tasks. As with the two previous use cases, if you plan on working iteratively and you don't want something too complex, you can let the AI figure out the steps.

```
## CONTEXT
Use get_best_practices to establish context, your role and the basic rules to follow.

## OBJECTIVE
Using the official Python add-in template, create a minimal Fusion add-in named "PlateTools" with one command "CreatePlate". The command should have options to add fastener holes in each corner of the plate.

## REQUIREMENTS
- The "CreatePlate" command has a UI that is opened via a button in the 'create' submenu
- The UI contains:
    - a field to enter the width of the plate in cm
    - a field to enter the height of the plate in cm
    - a field to enter the thickness of the plate in cm
    - a checkbox with the option to add fastener holes in the corner
    - a field to enter the distance of the fastener holes from their respective corner
    - a field to enter the diameter of the fastener holes

## ADDITIONAL INSTRUCTIONS
- IMPORTANT: Never use modal dialogs or windows.
- IMPORTANT: Do not use exceptions for error handling; log issues instead.
```

### Creative Work: Creating Components

While independently creating components from scratch is not one of the Fusion MCP server's best use cases, it's a fun challenge and the complexity of the task makes it a good showcase for the best practices mentioned earlier. 

> Note: The AI can still be a great and efficient assistant for these tasks even if it can't properly do them independently. If there's a specific step you're unsure about, the MCP allows the AI to analyze your project and do a customized and efficient search for you.

#### 1. **Think Programmatically**

When writing prompts, it's important to keep in mind that the AI interacts with Fusion by using its API. As such, any part of a prompt that can't reasonably be done by scripting will fail.

The most obvious example is complex sketch drawing and 3D modeling. 

Unless you can explicitly describe how to programmatically obtain a shape from basic primitives, you can presume the AI won't be able to draw it using Fusion's sketching or modeling tools.

>#### **Workaround for Sketches**
>
>There is an interesting workaround when it comes to sketching. Since Fusion can import .svg files as sketches, you can ask an AI agent to sketch something as a vector drawing in a .svg file and to import that file. 
>
>It's still not a miracle solution, but LLMs have significantly more knowledge on drawing vector images than they have on Fusion's sketching tools.


### 2. **Use an effective prompt structure**

Structure is extremely important for complex prompts. LLMs work best when the information they have to work with is well structured and logically organized. There are already thousands of templates available.

Here is the 'CORSA' prompt template I've been using specifically for the Fusion MCP:

```
# CONTEXT 
get_best_practices to establish context and your role as well as basic rules to follow for this prompt and the rest of the chat session after.

# OBJECTIVE
[High-level description of what you want the AI to do]
[If possible attach reference images and describe them here or explain where to find any]

# REQUIREMENTS
- [Enumerate the exact requirements for the end result]
- [e.g., dimensions, materials, how to output a result, etc.]

# STEPS [OPTIONAL]
[either detailed or a high-level guide of what to do with numerical steps]
1. [Subtask A]
    - Additional details for Subtask A (optional)
2. [Validation instructions for Subtask A]
3. [Subtask B]
    - Additional details for Subtask A (optional)
4. [Validation instructions for Subtask B]
5. ...

# ADDITIONAL INSTRUCTIONS [OPTIONAL]
- Use multiple small API scripts (at least one per step) so we can follow the progress better
- Call get_api_documentation before using any class outside of the Python Standard Library
- Refer back to CONSTRAINTS before every step
- Verify and validate your work often and restart steps as needed until results are correct
- When asked to validate visually use get_screenshot and compare your work with the references you were initially given
- [any other instructions on how to process the prompt, but try to limit them so as not to "dilute" other aspects of the prompt]
```

Note that if your requirements list becomes overly loaded, you can divide it into multiple categories: 

```
# REQUIREMENTS
    ## DIMENSIONS
    - ...
    ## MATERIALS
    - ...
    ## Etc.
    - ...
```

### 3. **Deconstruct Tasks in Small, Easy to Validate Steps**

As you can see from the template above, you should deconstruct tasks into as many small steps as you can. LLMs work best when you ask for small successive actions with verifiable results, as this prevents the AI from drifting away from the prompt and allows errors to be caught and fixed early—often by the agent. 

If you plan on using the AI interactively, you can simply write each task as a different prompt. 

When you want the AI to work as independently as possible, however, you'll need to be extremely detailed and precise about what needs to be done.

Well-defined small steps make it easier for the AI to accomplish tasks sequentially, and for you to supervise it from afar and intervene only if needed (and possible). 

Using numbered steps is helpful, as it makes it easier to refer to areas that need to be reworked.

```
# REQUIREMENTS:
- Component has a M4 fastener hole in each corner (4 in total)
- Fastener hole is counterbored and tapped
- Fastener hole is 1 cm away from both adjacent edges

[...]

# STEPS:
1. Create a first fastener hole
2. Make sure the hole meets all requirements after its created
```

### 4. **Force API Documentation Lookups**

Working with very specific APIs is not a strength of LLMs. Their training on the subject may be limited (if not non-existent) and often out of date. For this reason most MCPs, including this one, have tools to fetch relevant information from the API documentation. 

Newer LLMs are relatively good at figuring out what to search using these tools. However, you can maximize the AI's efficiency if you already know what it will need to look up. 


```
# REQUIREMENTS:
- Component has a M4 fastener hole in each corner (4 in total)
- Fastener hole is counterbored and tapped
- Fastener hole is 1 cm away from both adjacent edges

# ADDITIONAL CONSTRAINTS
- Call get_api_documentation every time you're about to use a class that is not part of Python Standard Library. Make sure the class exists

[...]

# STEPS
1. get_api_documentation on holeFeatures
2. Create a first fastener hole
3. Make sure the hole meets all requirements after its created
4. Create the other holes
```

### 5. **Demand Validation and Screenshot Verification**

When working in the viewport, explicitly request validation using the get_screenshot tool at key steps. Explain how and what to verify in a subsequent step.

```
[...]

# ADDITIONAL CONSTRAINTS
- Call get_api_documentation every time you're about to use a class that is not part of Python Standard Library. Make sure the class exists
- 

# STEPS
1. get_api_documentation on holeFeatures
2. Create a first fastener hole
3. Make sure the hole meets all requirements after its created
4. Create the other holes
5. Validate visually that the component meets the requirements
```

When you're not working iteratively, it can be important to explicitly tell the AI what "good enough" means. Otherwise the AI might fail a step and tell you afterward that it decided to continue.

```
# ADDITIONAL CONSTRAINTS
'Reasonably centered' is not good enough. The logo needs to be perfectly centered like in the reference image.
```

### 6. **Allow Iteration and Recovery**

In my experience, explicitly giving the AI permission to iterate helps achieve better results. Otherwise, it tends to accept poor results to avoid doing so.

```
# ADDITIONAL CONSTRAINTS
- Verify and validate your work often, and do it every time it is explicitly requested
- When results are not perfect, iterate. Restart steps as needed. Restart from scratch if needed.
```

### 7. **Be Extremely Specific About Units and Dimensions**

This one is pretty self-explanatory.

✅ GOOD:
```
# REQUIREMENTS

## DIMENSIONS:
- 10cm in length (X-axis)
- 10cm in width (Y-axis) 
- 1cm thick (Z-axis)
```

❌ BAD:
```
# REQUIREMENTS
- dimensions are 10 by 10 by 1
```

### Full Prompt Comparison

❌ BAD - Will give unpredictable results:
```
"Create a mounting plate with holes and a logo"
```
**Result:** AI guesses dimensions, hole types, logo size, placement. Likely to fail or produce something unusable. Even if it succeeds, the results will be wildly unpredictable. 

✅ BETTER - Will bring excellent results with a few human-guided iterations:
```
## OBJECTIVE
Create a square metal connector plate with four fastener holes and the Autodesk logo at its center.

## REQUIREMENTS
- Part measures 10cm x 10cm, 1cm thick
- Made of steel
- 4 M8 countersunk and tapped holes, 1.5cm from edges
- Autodesk logo engraved 0.2cm deep at center
- Use file: /Users/name/Desktop/autodesk-logo.svg at scale 0.05

## ADDITIONAL INSTRUCTIONS
- Use multiple small scripts (one per step minimum)
- VERY IMPORTANT: Use get_screenshot after every step
- IMPORTANT: Call get_api_documentation before using any Fusion API
- IMPORTANT: Iterate if results don't match expectations
- IMPORTANT: Re-read constraints before each step

REFERENCE: [Attached image showing expected result]
```
**Result:** AI creates mostly what you want, validates each step, catches errors early. However, the initial results will be somewhat unpredictable and it will take some chatting and iteration to get exactly what you wanted.

✅ EXCELLENT - Will get you what you want almost immediately, fully independently.
```
## CONTEXT
get_best_practices to establish context, your role and the basic rules to follow.

## OBJECTIVE
Using Fusion MCP, and using the attached draft as a reference, create a square metal connector plate with four fastener holes (one in each corner) and the Autodesk logo at its center. Refer to the steps below to get started. Keep in mind that these are mostly top-level steps; they are not exhaustive.

## CONSTRAINTS
- part measures 10cm in length and 10cm in width
- part is 1cm thick
- part is made of steel
- part has 4 fastener holes that are countersunk and tapped on its top face
- the top face of the component is the larger face that was highest along the Z-axis after the first extrusion
- fastener holes are for M8 screws
- fastener holes are 1.5 cm away from the sides (exterior profile of top face)
- there must be an Autodesk logo engraved in the center of the part
- engraving should be about 0.2 cm deep
- Use the 'autodesk-logo-alternate-rgb-black.svg' file on the desktop as the logo.

## STEPS
0. get_api_documentation 'timeline' to have it in context in case you need moveToBeginning and deleteAllAfterMarker to clean up the design
1. Start a sketch on the XY plane
2. Draw a square
3. Round the corners with fillets so they're smoothly beveled
4. Consult the documentation on the extrude features:
    4.1 get_api_documentation 'extrudeFeatures'
    4.2 get_api_documentation 'extrudeFeature'
    4.3 https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-CB1A2357-C8CD-474D-921E-992CA3621D04
5. Extrude the sketched profile as a new body
6. Consult the documentation on the hole feature:
    6.1 get_api_documentation 'holeFeatures'
    6.2 get_api_documentation 'holeFeature'
    6.3 https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-42731114-6082-46FB-B22C-78B07A8D6FA5
7. Create an M8 screw hole 1.5 cm away from the first corner
    7.1 Select the top face as the body for the hole
    7.2 Make a countersunk hole
    7.3 Once the hole is created, add the threads (tapping)
8. Create a screw hole 1.5 cm away from the second corner
9. Create a screw hole 1.5 cm away from the third corner
10. Create a screw hole 1.5 cm away from the fourth corner
11. Create a new sketch using the TOP FACE as the reference plane. Make sure this sketch is active and visible.
12. Import the SVG logo (at scale 0.2) into the new sketch using the sketch API and translate it by half its width in -X and half its height in +Y to center it properly.
13. Move the logo so it's perfectly centered on the component; the SVG anchor is not at its center, so account for that.
    - Important: DO NOT resize the logo; keep its current scale
    - Important: VALIDATE that the logo is VISUALLY at the center of the component's face. Compare with the reference image. Try again if it isn't correct. You may delete and recreate the sketch.
    - Important: "Reasonably centered" is not good enough. It needs to match the reference image.
14. Finish the sketch. Ensure it remains visible.
15. Extrude the logo by -0.2 cm
    15.1 Selection: choose all profiles inside the outer boundary that do not overlap the fastener holes. Exclude the three innermost profiles (letter cutouts in A, O, and D)
    15.2 VALIDATE VISUALLY using get_screenshot. The extrude may fail if the sketch isn't visible/active or is locked.
16. Change the part's physical material to steel
17. Set the viewport to the 'Home' named view and take the final screenshot.

## ADDITIONAL INSTRUCTIONS
- IMPORTANT: Use multiple small scripts (at least one per step) so I can visually see your progress and so you can validate your work visually.
- VERY IMPORTANT: Use get_screenshot after every step to validate results, compare the screenshot to the reference image, and try again if it's not close enough.
- CRITICAL: Iterate after any mistake. Start from scratch if necessary.
- CRITICAL: Never use exceptions for error handling in your scripts. Log them instead.
- CRITICAL: Call get_api_documentation every time you're about to use or access a class that is not part of the Python Standard Library. Make sure the class exists. The same goes for properties and member functions.
```

This last prompt is exceptionally long because we're asking for something that LLMs are still not very good at: create things to exact specs. It's definitely more of a fun exercise than it is a serious use case. 

However, if you can tolerate some variations, you can get away with much shorter prompts and still get interesting results.

In any case, if you do end up needing a prompt like this one, just remember that AIs are actually pretty good at writing prompts.