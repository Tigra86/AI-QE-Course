================================================================================
HOMEWORK SUMMARY: SEMANTIC VECTOR EMBEDDINGS
================================================================================

DATE: February 14, 2026
TOPIC: Text Vectorization and High-Dimensional Semantic Mapping
LIBRARIES: openai

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment was to experiment with 'text-embedding-3-small', 
OpenAI's model for converting text into numerical vectors. You explored how 
individual words and full sentences are translated into a 1536-dimensional 
space, allowing for mathematical comparisons of "meaning."

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- LOGIC SCRIPT:
  * embedding.py: The primary script that interfaces with the OpenAI API. It 
    sends text strings to the embedding endpoint and retrieves the resulting 
    floating-point array.

- VECTOR OUTPUTS (The 1536-D Maps):
  * Individual Words: Who.txt, won.txt, Stanley.txt, Cup.txt, 2025.txt, ?.txt. 
    These files store the raw vector arrays for single tokens.
  * Full Sentence: Who won Stanley Cup 2025?.txt. This file contains the 
    consolidated vector for the entire query, demonstrating how context 
    shifts the numerical representation.

--------------------------------------------------------------------------------
3. KEY LOGIC: VECTOR DIMENSIONALITY
--------------------------------------------------------------------------------
- DIMENSIONS: 
  Every piece of text, regardless of length, is converted into a vector of 
  exactly 1536 numbers. This fixed size allows different strings to be 
  compared using Cosine Similarity.

- SEMANTIC SEARCH: 
  By converting text to vectors, you've created the foundation for a 
  search engine that understands "concepts" rather than just "keywords." 
  For example, the vector for "won" and "victory" would be mathematically 
  closer than "won" and "apple."

--------------------------------------------------------------------------------
4. EXECUTION
--------------------------------------------------------------------------------
To generate a new embedding:
    python embedding.py

To install the official OpenAI library:
    pip install openai
================================================================================