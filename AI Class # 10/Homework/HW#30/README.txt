================================================================================
PROJECT SUMMARY: SPORTS DATA VALIDATION ENGINE
================================================================================
DATE:    March 24, 2026
PROJECT: HW#30 - ML Data
SYSTEM:  Python (JSON Validator & Metadata Checker)
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* validate_data.py: 
  The core validation tool designed to enforce strict schema rules, 
  ensuring metadata integrity and answer logic consistency.

* multiple.json: 
  A dataset containing 500 sports-themed questions where each entry 
  provides a list of multiple correct answers (expected_answers).

* single.json: 
  A dataset containing 500 sports-themed questions where each entry 
  provides exactly one correct answer (expected_answer).

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- METADATA INTEGRITY: 
  Strictly monitors that 'total_questions' matches the actual count.
  * REQUIRED_KEYS: product, domain, version, total_questions.
  * ALLOWED_DOMAINS: local_information, product_specs, technical_how_to, other.

- ANSWER NORMALIZATION: 
  The system enforces a specific logic for response formats:
  1. expected_answer: Must be a non-empty string.
  2. expected_answers: Must be a non-empty list of strings.
  3. MUTUALLY EXCLUSIVE: A question cannot use both formats.

- BILINGUAL CAPABILITY: 
  Engineered to support tokens in both English and Russian to align with 
  academic and technical project requirements.

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To validate a single dataset:
    python validate_data.py single.json

To validate all JSON files in the data folder:
    python validate_data.py data/

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- SHELL: Optimized for the Bash environment on your Mac mini.
- ENVIRONMENT: Uses the 'python' and 'pip' aliases as specifically 
  configured in your local system settings.
- ENCODING: Uses 'utf-8' to ensure compatibility with international 
  character sets across datasets.

================================================================================
END OF SUMMARY
================================================================================