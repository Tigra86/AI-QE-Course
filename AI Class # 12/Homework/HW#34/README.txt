================================================================================
PROJECT SUMMARY: DETERMINISTIC PARTIAL-MATCH REGRESSION TEST
================================================================================
DATE:    April 6, 2026
PROJECT: HW #34 - Planning Regression Test
SYSTEM:  Python (AI QE / Deterministic Validation Suite)
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* generate_assets.py:
  The core execution engine designed to process source QA JSON files into 
  training, eval, and rules datasets[cite: 8].
* capitals.json:
  The primary data suite containing 20 geography-based test cases with 
  unique metadata and multi-answer variations[cite: 7].
* outputs/:
  The destination directory where the system saves .jsonl datasets and 
  rule files for regression tracking[cite: 9, 10].

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- REGRESSION TESTING:
  Determines if features that previously worked have stopped functioning 
  following recent system changes[cite: 2].
* DETERMINISTIC: Rule-based validation including Exact, Partial, Regex, 
  and Schema validation[cite: 1, 3].
* PARTIAL-MATCH: A specific validation logic where the response must 
  simply contain the expected string (e.g., "Paris")[cite: 3, 6].

- DATASET GENERATION:
  The system transforms flat JSON data into structured assets[cite: 8, 9]:
  1. DATASETS: Maps question text to a specific domain label[cite: 10].
  2. RULES: Stores all valid answer variations for a given intent[cite: 10].
  3. EVALUATION: Generates unique SHA-256 hashes for every question/answer 
     pair to ensure data integrity during testing[cite: 11].

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To run the asset generation suite from your Mac mini:
    python generate_assets.py --source capitals.json

The script will scan the source file and generate step-by-step 
JSONL files used for AI Quality Engineering (QE) workflows[cite: 8, 9].

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- SHELL: Optimized for the Bash environment on your Mac mini.
- ENVIRONMENT: Uses 'python' as specifically configured in your 
  Alex Academy local directory (aliased without the '3').
- SUBJECT LINE: For submission, use "[AI] Homework # 34" when 
  emailing assets to alex@alex.academy.
================================================================================
END OF SUMMARY
================================================================================