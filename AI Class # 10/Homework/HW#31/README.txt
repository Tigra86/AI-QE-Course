================================================================================
PROJECT SUMMARY: AI ALIGNMENT TESTING ENGINE
================================================================================
DATE:    March 27, 2026
PROJECT: HW#31 - Alignment Testing
SYSTEM:  Python (Intent Classifier & Rule Engine)
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* train.py: 
  The training script updated to use 'utf-8-sig' to prevent BOM errors and 
  [cite_start]configured with 'general' and 'safety' thresholds to avoid RuntimeErrors[cite: 24, 25].
* ai_31.json: 
  A dataset containing 12 refined test cases designed to evaluate model 
  [cite_start]behavior against blocked keywords and disallowed rules[cite: 7, 8, 9].
* model.pkl: 
  The serialized model pack containing the vectorizer, trained classifier, 
  [cite_start]and alignment logic[cite: 1, 3].

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- ALIGNMENT VERIFICATION: 
  Ensures actual behavior is consistent with intended goals and safety 
  [cite_start]constraints, not just technical correctness[cite: 1].
- TEST CATEGORIES: 
  * [cite_start]BLOCKED_KEYWORDS: Prevents terms like 'kill', 'hack', or 'kys'[cite: 4, 7].
  * [cite_start]DISALLOWED_RULES: Overrides intent for topics like 'poison' or 'bomb'[cite: 5, 8].
  * [cite_start]LEXICON FILTERING: Handles profane or abusive language contextually[cite: 6, 9].
- PERFORMANCE REQUIREMENT: 
  The system must achieve a Macro-F1 score of at least 0.65 to pass 
  validation requirements.

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To train the alignment model:
    python train.py

To evaluate the test cases:
    Ensure the JSON metadata 'domain' matches your config (e.g., 'other')[cite: 7].

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- [cite_start]SHELL: Optimized for the Bash environment on your Mac mini[cite: 23].
- ENVIRONMENT: Uses 'python' and 'pip' aliases as configured in your 
  [cite_start]local system settings[cite: 24].
- ENCODING: Switched to 'utf-8-sig' to resolve Unexpected UTF-8 BOM 
  [cite_start]decoding errors[cite: 25].

================================================================================
END OF SUMMARY
================================================================================