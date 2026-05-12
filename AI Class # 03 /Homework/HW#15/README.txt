================================================================================
HOMEWORK SUMMARY: API AUTOMATION & DATA PERSISTENCE
================================================================================

DATE: February 13, 2026
TOPIC: Programmatic API Interaction and Response Logging
LIBRARIES: requests, json, os

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment was to move away from manual chat interfaces and 
build an automated pipeline for AI interactions. You created scripts that 
read questions from a file, send them to the GPT-3.5-Turbo model multiple 
times (for consistency testing), and log the output for further analysis.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- AUTOMATION SCRIPTS:
  * chat_in_out.py: The basic execution script. It uses a hardcoded API key 
    to send prompts and append the text responses to a file.
  * chat_in_out_ev.py: An improved version of the script that utilizes 
    Environmental Variables (os.environ.get) for the API Key, following 
    security best practices.

- DATA INPUTS & OUTPUTS:
  * prompts.txt: A bilingual collection of sports-related trivia questions 
    (English and Russian) used as the batch input.
  * content.txt: A raw text log of all AI responses, useful for quick 
    human review of the answers.
  * responses.jsonl: A structured "JSON Lines" log containing the full API 
    metadata, including timestamps, model versions, and token usage for 
    every iteration.

--------------------------------------------------------------------------------
3. KEY LOGIC: BATCH PROCESSING
--------------------------------------------------------------------------------
- ITERATION LOGIC: 
  The scripts include an 'iterate' variable (set to 3), which forces the system 
  to ask the same question three times to observe variations in AI responses.

- SECURITY (Environment Variables): 
  By using 'os.environ.get', you ensured that sensitive API keys are not 
  leaked in the source code—a critical step for professional development.

- DATA FORMATTING: 
  The use of 'utf-8-sig' and 'append' mode ('a') ensures that multilingual 
  characters are preserved and no data is overwritten during long runs.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To run the secure version of the script:
    export OPENAI_API_KEY='your_key_here'
    python chat_in_out_ev.py

To install the necessary networking library:
    pip install requests
================================================================================