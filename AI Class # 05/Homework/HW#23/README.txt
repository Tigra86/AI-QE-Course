================================================================================
HOMEWORK SUMMARY: AUTOMATED API PERFORMANCE EVALUATION
================================================================================

DATE: February 26, 2026 
TOPIC: Batch Testing and Automated HTML Reporting
LIBRARIES: Flask, requests, rapidfuzz, csv, statistics

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment is to automate the evaluation of the Hybrid Chatbot 
Engine. By feeding a batch of test questions into the API, the system compares 
the actual chatbot responses against expected "ground truth" answers, 
calculating accuracy metrics and generating a visual dashboard for analysis.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- TESTING SUITE:
  * api_test.py: Automation script. Reads test cases, pings the chatbot API, 
    calculates similarity scores, and generates an HTML report.
  * api_test.csv: Input dataset containing IDs, questions, and expected answers.

- CHATBOT ENGINE (Target):
  * app.py / query.py / train.py: The underlying chatbot system being evaluated.
  * system.config: Configuration for model paths and API settings.

- OUTPUTS:
  * api_output.csv: Data dump of every test case and similarity percentage.
  * api_report.html: A styled dashboard with summary statistics and results.

--------------------------------------------------------------------------------
3. EXECUTION
--------------------------------------------------------------------------------
To train the model:
    python train.py

To run the chatbot server:
    python app.py

To install dependencies:
    pip install -r requirements.txt

To execute the test suite and generate the dashboard:
    python api_test.py

--------------------------------------------------------------------------------
4. KEY LOGIC: AUTOMATED EVALUATION
--------------------------------------------------------------------------------
- BATCH API INTEGRATION:
  The script iterates through a CSV, sending each question to the Flask 
  endpoint. It handles timeouts to ensure the batch completes reliably.

- FUZZY SIMILARITY SCORING:
  Uses "token_sort_ratio" to compare actual and expected answers. This allows 
  for slight variations in phrasing while still validating the core content.

- PASS/FAIL THRESHOLDING:
  A configurable threshold (70%) determines if a response is a "PASS", 
  providing an objective metric for model performance.
================================================================================