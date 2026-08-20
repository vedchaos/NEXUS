---
name: ctz-vault
description: Secure credential management using ctz_vault_set/get/delete tools
---

# CTZ Vault Skill

## When to Use
- Storing sensitive credentials securely
- Retrieving stored passwords or tokens
- Managing API keys and secrets

## Available Tools
- ctz_vault_set: Store credential with name and value
- ctz_vault_get: Retrieve credential by name
- ctz_vault_delete: Remove stored credential

## Workflow
1. Store new credential with ctz_vault_set
2. Retrieve when needed with ctz_vault_get
3. Update if changed with ctz_vault_set again
4. Remove if no longer needed with ctz_vault_delete

## Examples
- "user request" → "Save API key" → ctz_vault_set with name and key
- "user request" → "Get my password" → ctz_vault_get with credential name
- "user request" → "Delete old token" → ctz_vault_delete
- "user request" → "Update GitHub token" → ctz_vault_set with new value

## Notes
- Credentials are encrypted at rest
- Never log or display credential values
- Access controlled by system permissions