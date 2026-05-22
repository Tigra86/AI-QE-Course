# MongoDB & NoSQL Class Reference Guide

This directory contains homework assignments, lecture materials, database shell scripts, and output logs for the AI Quality Engineering Course (Lecture #19: NoSQL & MongoDB).

## Core Reference Document

### kb_22_nosql.doc (Knowledge Base Cheat Sheet)
- Purpose: A comprehensive guide comparing SQL vs. NoSQL systems.
- Key Topics Covered:
  * Differences between relational models (Tables/Rows/Joins) and NoSQL structures (Collections/Documents/Embedding).
  * System setup protocols for installing, starting, and stopping MongoDB on macOS (Homebrew) and Windows.
  * Essential MongoDB Query Language (MQL) syntax examples including `$lookup` aggregations, regular expressions (`$regex`), collection operations, and record skipping/sorting.
  * A 15-question technical interview practice deck covering the CAP Theorem, eventual consistency, denormalization, and architecture decisions.

## Execution Scripts

### mongo_demo.py (Python Database Script)
- Purpose: A fully automated Python script utilizing the `pymongo` driver.
- Actions: Drops, builds, and seeds a local database (`demo_nosql`) with mockup users, products, and order data collections. It showcases multi-stage data aggregation pipelines calculating total orders and user revenue using `$lookup` and `$unwind`.

### input.js (MongoDB Shell Automation Script)
- Purpose: A lightweight script meant to be executed directly via the MongoDB shell (`mongosh`).
- Actions: Wipes an existing `users` collection to guarantee a fresh state, inserts sample profile data for "John Smith" and "Mike Loomis", and cleanly prints a structured result matching the user "Mike" using Extended JSON (`EJSON.stringify`).

## Output Logs & Exports

### output.txt / output.json / output2.json (Shell Query Results)
- Purpose: Production outputs exported straight from database shell operations.
- Contents: Structured document fragments representing a single query for user "Mike". These demonstrate how standard MongoDB `ObjectId` references are serialized into text format (`output.txt`) versus Extended JSON notation (`output.json` and `output2.json`).

## Database Backup Files

### test.gz/test (Binary Data Dump)
- Purpose: A compressed backup file generated via the standard utility command `mongodump`.
- Contents: Preserves raw collection metadata, default index configurations, unique system UUIDs, and underlying document snapshots for automated restoration using `mongorestore`.