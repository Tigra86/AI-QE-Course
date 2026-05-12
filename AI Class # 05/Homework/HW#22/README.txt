================================================================================
HOMEWORK SUMMARY: EMBEDDING SIMILARITY AND DISTANCE EVALUATION
================================================================================

DATE: February 26, 2026 
TOPIC: Geometric and Semantic Text Comparison Metrics
LIBRARIES: sentence_transformers, numpy, rapidfuzz, tabulate

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment is to evaluate different mathematical methods for 
measuring how "similar" two pieces of text are. By using various Transformer 
models (ranging from 384 to 4096 dimensions), the system compares semantic 
meaning against raw character-level fuzzy matching.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- METRIC SCRIPTS:
  * cosine.py: Measures the cosine of the angle between two vectors. It is 
    the standard for semantic similarity as it focuses on orientation rather 
    than magnitude.
  * dot.py: Calculates the raw dot product. Unlike cosine similarity, this 
    metric is sensitive to vector magnitude and "unnormalized" model 
    embeddings.
  * euclid.py: Measures the straight-line "geometric" distance between two 
    points in high-dimensional space.
  * fuzz.py: A non-neural approach using the Levenshtein-based 
    "token_sort_ratio" to compare character sequences rather than 
    meaning.

- INTEGRATED ANALYSIS:
  * all3.py: A comprehensive testing suite that runs 10 specific word pairs 
    (e.g., "apple/pear", "machine learning/AI") through all metrics 
    simultaneously to compare results across different model sizes.

--------------------------------------------------------------------------------
3. KEY LOGIC: MEASUREMENT DIMENSIONS
--------------------------------------------------------------------------------
- SEMANTIC ALIGNMENT (Cosine):
  Captures meaning even when words share no letters. For example, it identifies 
  that "machine learning" and "AI" are highly related despite different 
  spellings.

- GEOMETRIC DISTANCE (Euclidean):
  Provides the physical distance between embeddings. Lower scores indicate 
  closer conceptual proximity.



- STRING OVERLAP (Fuzz):
  Useful for catching typos (e.g., "Python" vs "Pytho") where a semantic model 
  might see two different concepts, but a fuzzy matcher sees nearly 
  identical strings.

- DIMENSIONAL SCALING:
  The project tests these metrics across multiple model architectures, 
  including MiniLM (384-dim) and GTR-T5-XXL (4096-dim), to observe how 
  vector density affects similarity scores.

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To run individual metric tests:
    python cosine.py
    python dot.py
    python euclid.py
    python fuzz.py

To generate the full comparison table across all models:
    python all3.py
================================================================================