================================================================================
HOMEWORK SUMMARY: DATA INTEGRATION & PARSING (HTML + JS + PYTHON)
================================================================================

DATE: February 6, 2026
TOPIC: Data Embedding, DOM Manipulation, and JSON Parsing
LANGUAGES: HTML, JavaScript, Python

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment was to demonstrate how data travels between different 
environments. You practiced embedding JSON data directly into HTML documents 
using <script type="application/json"> tags and then fetching that data using 
both JavaScript (for web display) and Python (for logic processing).

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- WEB INTEGRATION (HTML + JS):
  * HTML + JSON - Single Level.html: Parses a flat JSON object and populates 
    static ID spans in the browser.
  * HTML + JSON - Double-nested.html: Demonstrates accessing deeper object 
    properties (data.user.name) to update the UI.
  * HTML + JSON - Array.html: Uses a .forEach loop to dynamically create 
    new <div> elements for multiple users in a list.

- DATA PROCESSING (Python):
  * Python:JSON - Single Level.py: Demonstrates loading a flat JSON string 
    into a dictionary.
  * Python:JSON - Double nested.py: Shows multi-level dictionary indexing 
    to retrieve specific nested values.
  * Python:JSON - Array.py: Iterates through a list of dictionaries to 
    extract and print specific attributes.

--------------------------------------------------------------------------------
3. KEY LOGIC: THE BRIDGE
--------------------------------------------------------------------------------
- JSON.parse() vs. json.loads(): 
  The core mechanism for converting "text" into "objects" or "dictionaries" 
  in both JavaScript and Python environments.

- OPTIONAL CHAINING (??): 
  Used in the JavaScript files to handle missing data gracefully by 
  providing an "Unknown" fallback value.

- DOM MANIPULATION: 
  The HTML files use document.getElementById and innerHTML/textContent to 
  manually map data values to visual elements.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To run the logic scripts:
    python "Python:JSON - Single Level.py"

To install any necessary formatting tools:
    pip install autopep8
================================================================================