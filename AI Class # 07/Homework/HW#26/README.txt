================================================================================
AI PROMPTOPS PIPELINE SUMMARY
================================================================================

DATE: March 2, 2026
ENVIRONMENT: Mac Mini (Bash)
COMMANDS: python, pip

--------------------------------------------------------------------------------
1. COMPONENT SCRIPTS
--------------------------------------------------------------------------------
- prompts.py: 
  The "Executor." Connects to OpenAI API (gpt-4o-mini) and processes 
  prompts.json into response files.
  
- prompt_drift.py: 
  The "Input Auditor." Compares current prompts against prompts_baseline.json 
  to see if instructions have changed.

- response_drift.py: 
  The "Output Auditor." Compares new AI answers against a baseline response 
  file to detect changes in AI behavior or model performance.

- run_pipeline.py: 
  The "Orchestrator." Runs all scripts in sequence and handles system paths.

--------------------------------------------------------------------------------
2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- BASELINES: 
  You define the "Gold Standard" files. The system only knows what is "correct" 
  based on the baseline files you provide.

- SEMANTIC SIMILARITY: 
  Uses the 'all-MiniLM-L6-v2' model to calculate "Cosine Similarity." 
  This measures if the MEANING of the text is the same, even if the 
  words are slightly different.

- DRIFT TYPES:
  * SEMANTIC DRIFT: The core intent or answer has changed.
  * STRUCTURAL DRIFT: The format or length has changed significantly.

--------------------------------------------------------------------------------
3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To install requirements:
    pip install openai sentence-transformers numpy

To run the full pipeline:
    python run_pipeline.py

--------------------------------------------------------------------------------
4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- Similarity Threshold: Currently set between 0.90 and 0.92. 
- Normalization: The response script can ignore punctuation to reduce 
  false alarms.
- Orchestrator Logic: Uses sys.executable to ensure the sub-scripts use the 
  correct environment path.
================================================================================