================================================================================
HOMEWORK SUMMARY: HYBRID HALLUCINATION DETECTION SUITE
================================================================================

DATE: February 15, 2026
TOPIC: Automated Model Evaluation and HTML Reporting
LIBRARIES: openai, numpy, csv, statistics

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment was to create a "Judge" for AI responses. By 
comparing model outputs against a "Ground Truth" dataset, you built a system 
that identifies factual errors and "nonexistent" hallucinations (when an AI 
confidently describes something that doesn't exist).

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- EVALUATION ENGINES:
  * ai_tests.py: The core logic. It runs prompts through GPT-4.1, retrieves 
    embeddings to calculate semantic similarity, and applies heuristic rules 
    (like checking for "denial" phrases) to flag hallucinations.
  * ai_reporting.py: A post-processing script that reads the test results 
    and generates a professional, styled dashboard.

- DATASETS:
  * ai_tests.csv: 50 test cases divided into 'factual' (real-world knowledge) 
    and 'nonexistent' (fictional concepts like the "Ninth Moon of Venus").
  * ai_results.csv: The raw data dump of the evaluation, including similarity 
    scores and True/False hallucination flags.

- THE DASHBOARD:
  * ai_results.html: A clean, user-friendly HTML report with summary cards 
    for hallucination rates and color-coded tables for "Pass/Fail" results.

--------------------------------------------------------------------------------
3. KEY LOGIC: HYBRID SCORING
--------------------------------------------------------------------------------
- SEMANTIC SIMILARITY: 
  The system uses Cosine Similarity between the model output and the ground 
  truth. For factual queries, you set a high bar (0.85), while fictional 
  queries have a lower bar (0.75) to allow for varied "I don't know" phrasing.

- RULE-BASED CHECKING: 
  Even if similarity is low, a response might be "Correct" if it includes a 
  denial. Your script looks for patterns like "does not exist" or "fictional" 
  to ensure the AI isn't penalized for correctly identifying a fake prompt.



--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To run the full test suite:
    python ai_tests.py

To generate the visual report:
    python ai_reporting.py
================================================================================