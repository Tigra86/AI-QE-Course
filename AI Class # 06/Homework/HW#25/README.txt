================================================================================
HOMEWORK SUMMARY: AI GATEWAY, ALIGNMENT, AND FINE-TUNING
================================================================================

DATE: March 1, 2026
TOPIC: Safety Guardrails, Policy Enforcement, and Model Specialization
LIBRARIES: sklearn, numpy, re, dataclasses

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
This final phase of the project focuses on the "Guardrail" layer and model 
specialization. It ensures the chatbot remains safe, adheres to usage policies, 
and is fine-tuned to recognize specific technical and local intents.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- SAFETY GATEWAY & MODERATION:
  * ai_gateway.py: The central controller that sequences profanity checks, 
    alignment logic, and intent classification.
  * profanity.py: Detects abusive language while allowing academic exceptions.
  * alligment.py: Enforces hard-blocks on illegal activities (hacking) and 
    restricted topics (weapons).

- MODEL IMPROVEMENT:
  * fine-tuning.py: Combines pre-training data with a specialized dataset to 
    improve accuracy for specific technical queries.

- DATASETS:
  * alligment_input.txt / profanity_input.txt / fine-tuning_input.txt: 
    Test cases used to validate safety filters and model predictions.

--------------------------------------------------------------------------------
3. SAFETY LOGIC & ARCHITECTURE
--------------------------------------------------------------------------------
The system utilizes a multi-layered defense strategy:

- LAYER 1: PROFANITY FILTRATION
  Calculates an alignment score. If "Academic Terms" are present, the system 
  permits the use of potentially flagged words for scholarly discussion.



- LAYER 2: ALIGNMENT & POLICY
  Scans for "Blocked Keywords" (e.g., trojan, bypass) and "Restricted Topics" 
  (e.g., explosives). Matches here trigger immediate refusals.

- LAYER 3: SPECIALIZED INFERENCE
  Uses a fine-tuned Logistic Regression pipeline to categorize the validated 
  input into intents like 'technical_how_to' or 'product_specs'.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To train and test the fine-tuned model:
    python fine-tuning.py

To run the full integrated safety gateway:
    python ai_gateway.py

To test the alignment or profanity filters individually:
    python alligment.py
    python profanity.py
================================================================================