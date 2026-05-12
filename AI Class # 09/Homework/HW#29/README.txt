================================================================================
PROJECT SUMMARY: MULTILINGUAL INTENT CLASSIFIER
================================================================================
DATE:    March 19, 2026 [cite: 13]
PROJECT: HW#29 - Training Data & Bayesian Inference [cite: 13]
SYSTEM:  Python (Log-Likelihood & Softmax Engine) [cite: 13]
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* training_data.py: 
  The core classification engine utilizing Naive Bayes mathematics and 
  Softmax functions to calculate intent probabilities. [cite: 4, 14]

* training_data.txt: 
  The expanded training dataset containing categorized "look-alike" 
  examples for BILLING, TECH_SUPPORT, ACCOUNT, and SECURITY. [cite: 6, 1, 7]

* tests.txt: 
  The source file containing raw user inquiries used to validate the 
  engine's prediction accuracy and escalation logic. [cite: 6, 1, 7]

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- CONFIDENCE THRESHOLDS: 
  Strictly monitored for automated decision making. [cite: 8]
  * MIN_CONFIDENCE: 0.70 (70%). [cite: 9]
  * UNDER_THRESHOLD: Triggers 'ESCALATE_TO_HUMAN'. [cite: 16]

- DETERMINISTIC PIPELINE: 
  The system follows a fixed priority for evaluation:
  1. Tokenization (Text normalization and lower-case splitting). [cite: 12, 14]
  2. Log-Likelihood Calculation (Applying Laplace Smoothing +1). [cite: 13, 2, 3]
  3. Softmax Normalization (Converting raw scores to 0-100% scale). [cite: 13, 2, 3]

- MULTILINGUAL SUPPORT: 
  Processes English and Russian tokens interchangeably to support 
  international user inquiries. [cite: 15, 1, 7]

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To run the standard classification:
    python training_data.py

To update the training vocabulary:
    Modify training_data.txt and re-run the engine.

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- ENCODING: Uses 'utf-8-sig' to ensure compatibility with Russian 
  characters across different operating systems. [cite: 16]
- ENVIRONMENT: Uses the 'python' alias as configured in your 
  local Mac mini system settings.

================================================================================
END OF SUMMARY
================================================================================