================================================================================
HOMEWORK SUMMARY: LLM DECODING STRATEGIES ANALYSIS
================================================================================

DATE: February 28, 2026
TOPIC: Probabilistic Word Selection and Sampling Techniques
LIBRARIES: math, random, csv, json

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
This project explores how Large Language Models (LLMs) choose the next word in 
a sequence based on output logits. By implementing various decoding 
algorithms—ranging from deterministic "greedy" search to stochastic sampling—
we can observe how different configurations affect the creativity and 
consistency of the generated text.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- LOGIC & EXECUTION:
  * decoding.py: Core script implementing Softmax, Greedy search, Random 
    sampling, Temperature scaling, Top-K, and Top-P (Nucleus) filtering.

- DATASETS:
  * sentences.csv: Input sentence templates with placeholders (e.g., "I am 
    planning a trip to ||").
  * candidates.jsonl: Logit data for each sentence ID, representing the model's 
    raw "confidence" scores for various candidate words.

- OUTPUTS:
  * decoding_report.html: A comprehensive visual report showing the 
    resulting word selections for each strategy, color-coded for clarity.

--------------------------------------------------------------------------------
3. EXECUTION
--------------------------------------------------------------------------------
To process the logits and generate the HTML report:
    python decoding.py

--------------------------------------------------------------------------------
4. DECODING STRATEGIES IMPLEMENTED
--------------------------------------------------------------------------------
- GREEDY SEARCH:
  Always selects the word with the highest logit. Stable but repetitive.

- TEMPERATURE SCALING:
  Adjusts the probability distribution. Lower T (< 1.0) makes the model more 
  confident; higher T (> 1.0) increases "randomness" and variety.

- TOP-K SAMPLING:
  Limits the selection to the top 'K' most likely words, preventing the model 
  from choosing highly improbable "garbage" words.

- TOP-P (NUCLEUS) SAMPLING:
  Selects from the smallest set of words whose cumulative probability exceeds 
  threshold 'P'. This allows the vocabulary size to dynamically shift based 
  on the model's actual confidence.



- SOFTMAX NORMALIZATION:
  The mathematical backbone that converts raw logits into a valid probability 
  distribution (summing to 1.0).
================================================================================