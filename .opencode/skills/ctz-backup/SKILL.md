---
name: ctz-backup
description: Backup and restore workflows using ctz_backup_create/list/restore tools
---

# CTZ Backup Skill

## When to Use
- Creating backups of important files or directories
- Listing available backups
- Restoring data from previous backups

## Available Tools
- ctz_backup_create: Create a new backup of specified path
- ctz_backup_list: List all available backups
- ctz_backup_restore: Restore data from a backup

## Workflow
1. Determine what needs to be backed up
2. Use ctz_backup_create with source path
3. Verify backup creation with ctz_backup_list
4. When needed, restore using ctz_backup_restore with backup ID

## Examples
- "user request" → "Backup my project" → ctz_backup_create with project directory
- "user request" → "Show me my backups" → ctz_backup_list
- "user request" → "Restore yesterday's backup" → ctz_backup_restore with specific backup ID

## Notes
- Backups are stored with timestamps
- Restore overwrites current files
- Large directories may take time to backup