---
name: ctz-file-management
description: File operations workflows using ctz_file_read/write/search/grep tools
---

# CTZ File Management Skill

## When to Use
- Reading file contents
- Writing or modifying files
- Searching for files by pattern
- Searching within files for text

## Available Tools
- ctz_file_read: Read content of a file
- ctz_file_write: Write content to a file
- ctz_file_search: Search files by name pattern
- ctz_file_grep: Search within files for text patterns

## Workflow
1. Locate files with ctz_file_search
2. Read files with ctz_file_read
3. Modify content with ctz_file_write
4. Find specific content with ctz_file_grep

## Examples
- "user request" → "Show me config.txt" → ctz_file_read
- "user request" → "Find all .log files" → ctz_file_search for *.log
- "user request" → "Search for error in logs" → ctz_file_grep for "error"
- "user request" → "Update settings" → ctz_file_write with new content

## Notes
- Supports absolute and relative paths
- Grep uses regular expressions
- Write creates file if doesn't exist