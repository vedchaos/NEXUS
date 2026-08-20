---
name: ctz-testing
description: Test running and management using ctz_test_run/list/compile tools
---

# CTZ Testing Skill

## When to Use
- Running test suites
- Listing available tests
- Compiling test code

## Available Tools
- ctz_test_run: Execute specific test or test suite
- ctz_test_list: List all available tests
- ctz_test_compile: Compile test code before running

## Workflow
1. Use ctz_test_list to see available tests
2. Compile tests if needed with ctz_test_compile
3. Run specific tests with ctz_test_run
4. Analyze results and fix failures

## Examples
- "user request" → "Run all tests" → ctz_test_list then ctz_test_run
- "user request" → "Run unit tests" → ctz_test_run with test filter
- "user request" → "Compile tests" → ctz_test_compile
- "user request" → "What tests exist?" → ctz_test_list

## Notes
- Test results include pass/fail status
- Compile step may be required for some languages
- Parallel test execution available