================================================================================
PROJECT SUMMARY
================================================================================
DATE:    March 7, 2026
PROJECT: HW#27 - Context Window & Memory Management (Testing Edition)
SYSTEM:  Mac mini (Bash)
================================================================================

1. COMPONENT FILES
--------------------------------------------------------------------------------
* cw.py: 
  The original engine. Implements the core Message dataclasses and uses 
  tiktoken (cl100k_base) for precision token counting.

* cw_with_test.py: 
  The enhanced testing version. Includes the complete logic from the 
  original script plus a built-in 'run_eviction_test' suite to verify 
  system behavior under high-token stress.

* overflow_events.jsonl: 
  The "Input Auditor." Records exact JSON snapshots of every overflow event, 
  tracking which tokens were evicted to maintain the 100-token limit.
 

* overflow_events.csv: 
  The "Data Summary." A parsed version of the logs used to analyze 
  pre-trim vs. post-trim efficiency across multiple sessions.
 

2. KEY CONCEPTS & LOGIC
--------------------------------------------------------------------------------
- TOKEN THRESHOLD: 
  Strictly capped at 100 tokens. Uses 'cl100k_base' encoding to match 
  modern LLM tokenization standards.

- DETERMINISTIC EVICTION: 
  Instead of random deletion, the system follows a fixed priority:
  1. System & Memory Summary (Protected)
  2. Latest User Input (Protected)
  3. Historical Messages (Evicted from oldest to newest)



- REGEX MEMORY: 
  Maintains a "Gold Standard" memory summary by scanning for Name, Age, 
  Location, and Hobbies using Case-Insensitive patterns.

3. SETUP & EXECUTION
--------------------------------------------------------------------------------
To run the standard interaction loop:
    python cw.py

To run the version with the new test suite:
    python cw_with_test.py

To trigger the automated eviction test inside the program:
    Type: /test

4. CONFIGURATION NOTES
--------------------------------------------------------------------------------
- Overhead: Set to 4 tokens per message for metadata.
- Warning Level: Includes a 'WARN_AT' variable (0.8) to alert when 
  context is reaching 80% capacity.
- Environment: Uses the 'python' alias as configured in your .bashrc. 
 
================================================================================
END OF SUMMARY
================================================================================