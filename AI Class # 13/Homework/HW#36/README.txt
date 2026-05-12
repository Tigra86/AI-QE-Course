================================================================================
PROJECT SUMMARY: DETERMINISTIC SCHEMA VALIDATION REGRESSION TEST
================================================================================
DATE:    April 13, 2026
PROJECT: HW #36 - Planning CS Regression Test
SYSTEM:  Python (AI QE / Deterministic Validation Suite)
================================================================================

1. COMPONENT FILES & DESCRIPTIONS
--------------------------------------------------------------------------------
* call.py:
  Initializes the OpenAI client to request data from gpt-5.2. It captures 
  the model's response and saves it as a timestamped JSON file for testing.

* local.py:
  The primary local testing script. It compares a single 'response.json' 
  against 'schema2.json' using standard validation. It stops and reports 
  the first error it encounters.

* local_multi.py:
  An advanced local validator that uses Draft7Validator. Instead of stopping 
  at one error, it identifies and lists every single structural violation 
  found in the local file at once.

* online.py:
  A "live" testing script that performs an API call and immediately 
  validates the response against 'schema.json' before saving. It ensures 
  the data is valid before it even hits the disk.

* online_multi.py:
  The most comprehensive test tool. It performs a live API call and 
  runs a multi-error validation pass, reporting all schema discrepancies 
  directly in the terminal.

* response.json / response_raw.json:
  The data objects being tested. These contain the full API response 
  envelope, including model ID, usage statistics, and the generated text.

* schema.json / schema2.json:
  The "Contracts." These files define exactly what the JSON must look like. 
  Updated to include flexible logic for null values and the 'phase' field.

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
* REGRESSION TESTING:
  Determines if specific structural patterns that previously worked have 
  stopped functioning following system updates.
* SCHEMA VALIDATION:
  Verifies that system outputs conform to a predefined structural "contract" 
  (e.g., ensuring 'temperature' is a number or 'id' is a string).
* DETERMINISTIC:
  Rule-based validation focusing on fixed, binary Pass/Fail evaluation of 
  the JSON envelope and data types.

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
Execution Commands (using custom Bash aliases):
- Live multi-validation:   python online_multi.py
- Local multi-validation:  python local_multi.py
- Generate response only:  python call.py

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- SHELL: Optimized for the Bash environment on the Mac mini.
- ENVIRONMENT: Uses 'python' (aliased) in the local Alex Academy directory.
- SUBJECT LINE: For submission, use "Re: [AI] Homework # 36" when 
  emailing these assets to alex@alex.academy.
================================================================================
END OF SUMMARY
================================================================================