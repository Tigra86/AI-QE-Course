================================================================================
PROJECT SUMMARY: LLM EVALUATION & DATASET VALIDATION WORKFLOW
================================================================================
DATE:    April 16, 2026
PROJECT: HW #37 - Dataset Correction & Partial-Match Evaluation
SYSTEM:  Python (AI QE / Partial-Match Validation Suite)
================================================================================

1. COMPONENT FILES & DESCRIPTIONS
--------------------------------------------------------------------------------
* capitals_other_eval.jsonl:
  Geography dataset corrected for accurate capital city mappings. Specifically 
  fixed cross-contamination between UK and France capital associations.

* email_support_government_eval.jsonl:
  Government contact dataset. Updated with specific regex patterns to properly 
  validate email address formats in the model output.

* global_metrics_science_eval.jsonl:
  Science metric dataset. Cleaned of generic '.*' patterns and replaced with 
  targeted factual values (e.g., Mount Everest height, world population).

* partial_match_api_test.py:
  The primary validation script. It checks if the specific 'regex' keyword 
  defined in the dataset is present within the model's response string.

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
* PARTIAL-MATCH VALIDATION:
  Rule-based validation ensuring core factual tokens (like "Paris") are 
  present in the response, regardless of surrounding conversational text.

* DATASET CLEANING:
  The systematic replacement of generic wildcards (.*) with specific factual 
  keys to ensure the evaluation reports reflect true model accuracy.

* REGEX NORMALIZATION:
  The process of escaping special characters (like . or @) to ensure they are 
  treated as literal characters during the validation phase.

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
Execution Commands:
- Run partial-match test:   python partial_match_api_test.py
- Review HTML report:       Review 'partial_match_report.html' to analyze 
                            the Pass/Fail distribution.

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- ENVIRONMENT: Optimized for the local Alex Academy Python environment.
- REGEX: Specific factual tokens must be used in the 'regex' field to 
  prevent false failures in the partial-match report.
- SUBJECT LINE: For final submission, use "Re: [AI] Homework # 37" when 
  emailing these assets to alex@alex.academy.
================================================================================
END OF SUMMARY
================================================================================