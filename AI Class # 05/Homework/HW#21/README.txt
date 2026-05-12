================================================================================
HOMEWORK SUMMARY: HYBRID INTENT-BASED CHATBOT ENGINE
================================================================================

DATE: February 24, 2026 
TOPIC: Machine Learning and Rule-Based NLP Integration
LIBRARIES: Flask, scikit-learn, joblib, rapidfuzz, numpy

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment is to develop a modular chatbot system that combines 
Machine Learning (ML) classification with a rule-based logic layer. This 
"Hybrid" approach ensures the model handles broad intents while providing 
precise answers for technical queries.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- LOGIC ENGINES:
  * train.py: The training pipeline. It vectorizes text using TF-IDF and trains 
    a Logistic Regression model to classify user intents.
  * query.py: The inference engine. It runs the ML model alongside a 
    fuzzy-matching algorithm to determine the best response.
  * app.py: A Flask-based web server that exposes the chatbot as an API and 
    allows for dynamic rule updates.

- CONFIGURATION & DATA:
  * system.config: Manages model paths, inference temperature, and 
    API settings.
  * fallback_messages.json: A library of "safety" responses for low-confidence 
    scenarios.

- MODEL ARTIFACTS:
  * model.pkl: A serialized pack containing the trained classifier, 
    vectorizer, and intent thresholds.

--------------------------------------------------------------------------------
3. KEY LOGIC: THE HYBRID PIPELINE
--------------------------------------------------------------------------------
- DUAL-LAYER CLASSIFICATION:
  The system first checks for "Fuzzy Overrides" (keyword matches > 70). If 
  found, it skips the ML prediction to ensure accuracy for specific product 
  names.

- INTENT THRESHOLDING:
  Each intent has a custom confidence bar (e.g., 0.45). If the ML probability 
  is too low, the system triggers a "low_confidence" fallback message 
 .

- DYNAMIC RULE MERGING:
  The system can evolve without retraining. app.py allows merging new rules 
  into the existing model pack at runtime.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To train the model:
    python train.py

To run the interactive CLI:
    python query.py

To launch the Web API:
    python app.py
================================================================================