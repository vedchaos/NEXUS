---
name: ctz-database
description: SQLite database operations using ctz_db_query/execute/tables tools
---

# CTZ Database Skill

## When to Use
- Querying SQLite databases
- Executing SQL statements
- Managing database tables and schema

## Available Tools
- ctz_db_query: Run SELECT queries and return results
- ctz_db_execute: Execute INSERT, UPDATE, DELETE statements
- ctz_db_tables: List all tables in database
- ctz_db_schema: Show table schema and columns

## Workflow
1. Identify target database file
2. Use ctz_db_tables to see available tables
3. Query data with ctz_db_query
4. Modify data with ctz_db_execute
5. Verify changes with follow-up queries

## Examples
- "user request" → "Show all users" → ctz_db_query with SELECT statement
- "user request" → "Add new record" → ctz_db_execute with INSERT
- "user request" → "What tables exist?" → ctz_db_tables
- "user request" → "Update user email" → ctz_db_execute with UPDATE

## Notes
- Database files must be accessible
- Parameterized queries recommended for security
- Large result sets may be truncated