================================================================================
HOMEWORK SUMMARY: DETERMINISTIC ATTENTION ENGINE
================================================================================

DATE: February 21, 2026
TOPIC: Simulated Self-Attention and Word Embeddings
LIBRARIES: numpy, hashlib, json, re

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment is to build an "Attention Engine" that simulates how 
models weight the importance of words. By using a 
focus word as a reference point, the system calculates which other words in a 
sentence deserve the most "focus" based on semantic similarity and linguistic 
rules.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- LOGIC ENGINES:
  * generate_attention.py: The core engine that tokenizes text, generates 
    hash-based embeddings, and calculates attention weights.
  * softmax.py: A standalone utility script used to test the Softmax 
    mathematical distribution logic.

- DATASETS:
  * sentences.txt: A collection of 10 test sentences involving subjects like 
    Christina’s cake, Nik’s book, and David’s laptop.

- OUTPUTS:
  * attention_XX.json: Individual result files (e.g., attention_01.json) 
    containing the sentence, the focus word, and the final calculated 
    attention weights.

--------------------------------------------------------------------------------
3. KEY LOGIC: THE ATTENTION PIPELINE
--------------------------------------------------------------------------------
- DETERMINISTIC EMBEDDINGS:
  The system uses SHA-256 hashing to create consistent, 64-dimension vectors 
  for every word, ensuring the same word always has the same "meaning" 
 .

- FOCUS SELECTION:
  The script automatically identifies a "Focus Word" by looking for 
  adjectives (words ending in -ing, -ed, -ous, etc.) or the longest 
  available content word.



- PENALTY & BOOST HEURISTICS:
  * Self-Penalty: The focus word is penalized (0.25x) so it doesn't 
    dominate the results.
  * Stopword Penalty: Common words (the, a, is) are heavily discounted 
    (0.35x).
  * Subject Boost: If the focus is an adjective, the system finds the 
    nearest subject to the left and triples (3.0x) its importance 
   .

- WEIGHT CAPPING:
  To ensure a balanced distribution, no single word can exceed a specific 
  attention cap (e.g., 0.15 for the focus word), with excess weight 
  redistributed to other words.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To process the sentences and generate the JSON reports:
    python generate_attention.py

To verify the softmax math independently:
    python softmax.py
================================================================================