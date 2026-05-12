AI Quality Engineering: NLP Validation Ecosystem

This project is a high-precision framework designed to validate AI model responses against deterministic rules and semantic expectations[cite: 1]. It uses a structured pipeline to transform manual test cases into automated evaluation assets, ensuring consistency across product specifications and local information datasets[cite: 1].

-------------------------------------------------------------------------------
1. DIRECTORY STRUCTURE
-------------------------------------------------------------------------------

* config/: Contains system.config and fallback_messages.json for global environment settings[cite: 1].
* data/: The primary entry point containing manually curated .json test cases[cite: 1].
* datasets/: Distributed .jsonl files used for model querying and training[cite: 1].
* rules/: Deterministic validation logic extracted from test cases to define "Ground Truth"[cite: 1].
** manual_rules.json was created during the training of the model through Postman (both – via Body and via File). See RAG App.doc.
* eval/: Golden sets used to measure model accuracy and regression[cite: 1].
* reports/: Automated HTML and JSON outputs summarizing validation success/failure rates[cite: 1].
* static/ & templates/: A Flask-based web interface for visualizing complex validation reports[cite: 1].

-------------------------------------------------------------------------------
2. THE DATA PIPELINE (Step-by-Step)
-------------------------------------------------------------------------------

Step 1: Data Integrity (1_validate_data.py)
Before assets are generated, this script performs a structural audit of manual JSON files in the data/ folder[cite: 1]. It ensures every test case has the required fields before they enter the pipeline[cite: 1].

Step 2: Asset Generation & Distribution (2_generate_assets.py)
This is the "Engine" of the project[cite: 1]. When executed, it parses manual test cases and synchronizes three distinct layers[cite: 1]:
* Dataset Layer: Converts JSON to .jsonl for batch processing.
* Rule Layer: Generates specific rule sets that define what the model must or must not say.
* Evaluation Layer: Creates structured eval files mapping queries to verified answers.

Step 3: Training & Model Management (3_train.py)
Utilizes the generated datasets to refresh the model.pkl file[cite: 1]. It handles the logic for vectorization or fine-tuning based on updated content in the datasets/ folder[cite: 1].

Step 4: Querying (4_query.py)
Allows for direct model querying and response testing outside of the UI[cite: 1].

Step 4: The Validation Trilogy
The system evaluates AI performance across three specialized dimensions:
* Semantic Validation (6_semantic_validation.py): Verifies that the meaning of the AI response aligns with the expected intent[cite: 1].
* Partial Match (PM) Validation (7_pm_validation.py): A deterministic check to ensure key technical terms or "must-have" phrases are present[cite: 1].
* Sentence-Level Validation (8_sentence_validation.py): A granular audit checking for hallucinations or phrasing errors at the individual sentence level[cite: 1].

-------------------------------------------------------------------------------
3. WEB INTERFACE & MONITORING
-------------------------------------------------------------------------------

* 5_ui.py: A Flask application serving an interactive dashboard for triggers and real-time viewing of results[cite: 1].
* 9_chat_log_server.py: A specialized server for auditing chat_logs.jsonl, allowing engineers to review historical interactions[cite: 1].

-------------------------------------------------------------------------------
4. TECH STACK & ENVIRONMENT
-------------------------------------------------------------------------------

* Runtime: Python 3.10[cite: 1].
* Shell: Bash[cite: 1].
* Key Tools: Pydantic, Flask, JSONL, and Pickle[cite: 1].

-------------------------------------------------------------------------------
5. HOW TO RUN
-------------------------------------------------------------------------------

1. Validate your manual JSON source:
   python 1_validate_data.py data/

2. Generate the three synchronized assets (Datasets, Rules, Eval):
   python 2_generate_assets.py --source data/

3. Train the model:
   python 3_train.py

4. Query (Optional): 
   python 4_query.py 

5. Launch the UI:
   python 5_ui.py

6. Run validations:
   python 6_semantic_validation.py
   python 7_pm_validation.py
   ???python3.10 -m spacy download en_core_web_sm???
   ???python3.10 8_sentence_validation.py???