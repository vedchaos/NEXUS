---
name: ctz-docs
description: Documentation management using ctz_docs_read/search/list tools
---

# CTZ Docs Skill

## When to Use
- Reading documentation files
- Searching for specific content in docs
- Listing available documentation

## Available Tools
- ctz_docs_read: Read content of a documentation file
- ctz_docs_search: Search documentation by keyword or phrase
- ctz_docs_list: List all available documentation files

## Workflow
1. Use ctz_docs_list to see what docs are available
2. Search for relevant topics with ctz_docs_search
3. Read specific files with ctz_docs_read
4. Extract needed information

## Examples
- "user request" → "How do I use feature X?" → ctz_docs_search for "feature X"
- "user request" → "Show me the API docs" → ctz_docs_list then ctz_docs_read
- "user request" → "Find installation guide" → ctz_docs_search for "install"

## Notes
- Documentation may be in various formats (MD, TXT, etc.)
- Search supports partial matches
- Some docs may require authentication