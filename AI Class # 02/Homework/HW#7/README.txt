================================================================================
HOMEWORK SUMMARY: JSON DATA ARCHITECTURES
================================================================================

DATE: February 5, 2026
TOPIC: Flat vs. Nested vs. Array-based Data Modeling
FORMAT: JSON (JavaScript Object Notation)

--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
The goal of this assignment was to practice modeling various business entities 
(Users, Products, Site Configurations, and Sales) using different JSON patterns. 
This includes understanding when to use simple key-value pairs versus complex 
nested objects or lists of objects.

--------------------------------------------------------------------------------
2. FILE BREAKDOWN
--------------------------------------------------------------------------------
- SINGLE FILES (Flat Structures):
  * single_file1_users.json: A simple profile for a single user.
  * single_file2_settings.json: Global site configurations in a flat list.
  * single_file3_product.json: Core details for one inventory item.

- NESTED FILES (Categorized Structures):
  * nested_file1_user_profile.json: Separates user identity from metadata.
  * nested_file2_site_config.json: Groups site settings into 'site' vs 'limits'.
  * nested_file3_product_detail.json: Groups product specs vs warranty info.

- ARRAY FILES (Collection Structures):
  * array_file1_users_list.json: A list of multiple user objects.
  * array_file2_tags.json: A simple array of strings for categorization.
  * array_file3_sales.json: Numerical data for financial analysis.
  * array_file4_site_changes.json: A complex array of update logs containing 
    nested change-lists.

--------------------------------------------------------------------------------
3. KEY LOGIC: DATA MODELING
--------------------------------------------------------------------------------
- ABSTRACTION: 
  Nested structures help organize data logically (e.g., putting all 'limits' 
  under one umbrella) which makes the code more readable for large systems.

- SCALABILITY: 
  Array-based files allow for processing multiple records in a single loop 
  during data ingestion.

- DATA TYPES: 
  Demonstrates use of Booleans (active/inactive), Floats (prices), Integers 
  (IDs), and Strings (dates/names).

--------------------------------------------------------------------------------
4. EXECUTION & PARSING
--------------------------------------------------------------------------------
To parse these data structures in python:
    import json
    with open('array_file1_users_list.json') as f:
        users = json.load(f)

To validate the structure of these files:
    pip install check-jsonschema
================================================================================