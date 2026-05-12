================================================================================
PROJECT SUMMARY: MULTILINGUAL SENTENCE VALIDATOR
================================================================================
DATE:    March 9, 2026 [cite: 13]
PROJECT: HW#28 - Syntactic Analysis & NLP Validation [cite: 13]
SYSTEM:  Python (spaCy ML Engine) [cite: 13]
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* spacy_ml.py: 
  The core validation engine using spaCy models (en_core_web_sm and 
  ru_core_news_sm) to perform deep syntactic analysis. [cite: 14]
* input.txt: 
  The source file containing raw sentences (one per line) used to 
  test the validator's accuracy across English and Russian. [cite: 1, 7]
* report.html: 
  The data summary. An interactive, color-coded report that parses 
  validation results into PASS, WARN, and FAIL categories. [cite: 17]

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- VALIDATION THRESHOLDS: 
  Strictly monitored for sentence length. [cite: 18]
  * MIN_LEN: 3 tokens (Short phrases trigger WARN). [cite: 22]
  * MAX_LEN: 40 tokens (Long sentences trigger WARN). [cite: 22]
  * EXTREME_LEN: 80 tokens (Excessive length triggers FAIL). [cite: 22]

- DETERMINISTIC RULES: 
  The system follows a fixed priority for evaluation: [cite: 20]
  1. Empty/Math Check (Immediate FAIL if only symbols/numbers). [cite: 4, 14]
  2. Grammatical Check (Verification of Subject, Verb, and Predicate). [cite: 2, 3]
  3. Punctuation Check (Verification of terminal '.', '!', or '?'). [cite: 5, 15]

- MULTILINGUAL SUPPORT: 
  Uses a language detection heuristic to switch between English 
  and Russian NLP pipelines automatically. [cite: 1, 7]

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To run a standard validation:
    python3.10 spacy_ml.py input.txt [cite: 21]

To run with automatic language detection:
    python3.10 spacy_ml.py input.txt -l auto [cite: 21]

To generate the visual HTML report:
    python3.10 spacy_ml.py input.txt --html report.html [cite: 21]

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- SEVERITY: Uses a mapping dictionary to alert when sentences 
  reach specific error capacities (WARN/FAIL). [cite: 22]
- ENVIRONMENT: Uses the 'python' alias as configured in your 
  local system settings. [cite: 23]

================================================================================
END OF SUMMARY
================================================================================