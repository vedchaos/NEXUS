---
name: ctz-data-analysis
description: CSV/JSON data analysis workflows using ctz_data_csv_*/json_* tools
---

# CTZ Data Analysis Skill

## When to Use
- Analyzing CSV files for insights
- Processing JSON data structures
- Generating summary statistics

## Available Tools
- ctz_data_csv_read: Read and parse CSV file
- ctz_data_csv_analyze: Perform statistical analysis on CSV
- ctz_data_json_read: Read and parse JSON file
- ctz_data_json_transform: Transform JSON data structure

## Workflow
1. Load data using appropriate read tool
2. Explore data structure and contents
3. Apply analysis or transformation
4. Extract insights or generate reports

## Examples
- "user request" → "Analyze sales data" → ctz_data_csv_read then ctz_data_csv_analyze
- "user request" → "Process API response" → ctz_data_json_read then ctz_data_json_transform
- "user request" → "Show summary stats" → ctz_data_csv_analyze with aggregation options

## Notes
- Supports common CSV delimiters
- JSON tools handle nested structures
- Large files may be processed in chunks