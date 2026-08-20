---
name: ctz-reporting
description: Report generation using ctz_report_system/memory/project tools
---

# CTZ Reporting Skill

## When to Use
- Generating system performance reports
- Creating memory usage summaries
- Producing project status reports

## Available Tools
- ctz_report_system: Generate system health/performance report
- ctz_report_memory: Create memory usage report
- ctz_report_project: Generate project status report

## Workflow
1. Identify type of report needed
2. Use appropriate ctz_report_* tool
3. Review generated report
4. Share or archive as needed

## Examples
- "user request" → "System report" → ctz_report_system
- "user request" → "Memory report" → ctz_report_memory
- "user request" → "Project status" → ctz_report_project
- "user request" → "Weekly summary" → ctz_report_system + ctz_report_memory

## Notes
- Reports can be exported to various formats
- Include visualizations where possible
- Schedule reports via ctz-scheduler skill