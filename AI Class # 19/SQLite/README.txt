# Language Model Evaluation Framework

## Overview
This framework provides a localized, structured system for automated benchmarking, logging, and grading of Language Model text outputs. It acts as an isolation test suite by reading raw local test definitions, interacting with the model API, and recording itemized scoring histories inside a relational SQLite database.

---

## Directory Structure
The workspace contains the following files and directories:

.
├── eval_pipeline.py      # The execution engine containing core script logic.
├── eval_pipeline.db      # The local SQLite database storing evaluation metrics.
└── jsons/                # Directory containing the standalone test profiles.
    ├── test_001.json     # Q001: Mathematics (Basic Arithmetic Multiplication)
    ├── test_002.json     # Q002: Mathematics (Algebra Variable Extraction)
    ├── test_003.json     # Q003: Programming (Python Dictionary Mapping)
    ├── test_004.json     # Q004: Programming (File I/O Append Mode Character)
    ├── test_005.json     # Q005: Geography (Landmark Country Lookup)
    ├── test_006.json     # Q006: Geography (Deepest Ocean Body Identification)
    ├── test_007.json     # Q007: Science (Chemical Element Abbreviation)
    ├── test_008.json     # Q008: Science (Cellular Biology Component Definition)
    ├── test_009.json     # Q009: Linguistics (Grammar Conjunction Part of Speech)
    └── test_010.json     # Q010: Systems (CLI Shell Working Directory Command)

---

## Framework Architecture

### 1. Database Schema
The relational database engine (`eval_pipeline.db`) handles data state isolation across three tables:
* **test_cases**: Tracks unique query identifiers (Q001–Q010), target category tags, benchmark intent strings, raw question prompts, and custom regular expressions.
* **eval_runs**: Holds metadata records tracking individual benchmark execution parameters (target model string, strict timestamps, aggregations of passed vs. failed tasks, and calculated average scores).
* **eval_results**: Logs itemized text outputs, error flags, and binary matching properties for every prompt processed during evaluation.

### 2. Tiered Evaluation Grading System
Model responses are automatically scored across three tiered validation checkpoints:
* **Score 1.0 (Exact Match)**: Triggered when the stripped, lowercased model output string exactly aligns with the ground-truth benchmark.
* **Score 0.8 (Regex Match)**: Triggered when the model answer matches a custom regular expression pattern configured for that specific test item.
* **Score 0.6 (Contains Substring)**: Fallback rule triggered if the expected standalone string is present anywhere within a broader conversational model text response.
* **Score 0.0 (Fail)**: Applied if none of the above validation patterns are detected.

---

## Command Line Operational Instructions

All execution subcommands are initiated using standard environment configurations:

### Phase 1: Initialize the Work Environment
Creates the schema constraints and optimizations inside the SQLite database engine:
`python eval_pipeline.py --db eval_pipeline.db init`

### Phase 2: Bulk Data Ingestion
Scans the local source directory and writes test constraints directly to the tables:
`python eval_pipeline.py --db eval_pipeline.db load --source jsons`

### Phase 3: Run Evaluation Benchmarks
Queries the targeted language model with dataset prompts and commits metrics to the logs:
`python eval_pipeline.py --db eval_pipeline.db run --model gpt-5.2`

### Phase 4: Output Historical Performance Summary
Generates a complete console diagnostic report detailing text outputs using a specific Run ID:
`python eval_pipeline.py --db eval_pipeline.db report --run-id <run-id-uuid>`