README ADDENDUM 01 - Technical Orchestration Details

Core Purpose
These scripts (openai_currency_tool.py, openai_db_tool.py, openai_distance_tool.py, and openai_get_weather_tool.py) demonstrate OpenAI Tool Calling, which allows an Artificial Intelligence to interact with the real world. While AI is normally "frozen" in time based on its training data, these scripts give it the ability to perform live tasks, such as checking the weather, calculating current exchange rates, or querying a private database.

The Two-Step Workflow
Every script follows a specific "handshake" process to ensure the answer is accurate:

* The Request: You send a question to the AI along with a "Tool Definition." This tells the AI that a specific Python function exists (like a calculator or weather reporter) that it can use if it needs more information.
* The Decision: If the AI realizes it doesn't have the live data to answer you, it doesn't guess. Instead, it sends back a request for the script to run the specific tool.
* The Execution: The script runs the actual code locally—fetching data from a web API or a database—and gets a raw result (like "22°C" or "$1.10").
* The Final Answer: The script sends that result back to the AI, which then uses the data to write a natural, easy-to-read response for the user.

The Four Functions

* openai_currency_tool.py: Connects to a live exchange rate API to convert money without the AI having to do the math manually.
* openai_db_tool.py: Allows the AI to look up specific school records, such as student counts or average grades, from a private system.
* openai_distance_tool.py: Uses geographic coordinates and a mathematical formula to find the exact distance between two cities.
* openai_get_weather_tool.py: First finds the location coordinates and then pulls the current temperature from a weather station API.

Why This Matters
By using these scripts, the AI moves from being a simple chatbot to a functional assistant that provides factually accurate, up-to-the-minute information.