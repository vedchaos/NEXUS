---
name: ctz-api-testing
description: REST API testing workflows using ctz_api_get/post/put/delete tools
---

# CTZ API Testing Skill

## When to Use
- Testing REST endpoints (GET, POST, PUT, DELETE)
- Validating API responses and status codes
- Automated API health checks

## Available Tools
- ctz_api_get: Send GET request to API endpoint
- ctz_api_post: Send POST request with JSON body
- ctz_api_put: Send PUT request to update resources
- ctz_api_delete: Send DELETE request to remove resources

## Workflow
1. Identify target API endpoint and method
2. Prepare request headers and body if needed
3. Use appropriate ctz_api_* tool
4. Check response status and content
5. Handle errors or retry if needed

## Examples
- "user request" → "Check if API is up" → ctz_api_get with health endpoint
- "user request" → "Create new user" → ctz_api_post with user data
- "user request" → "Update profile" → ctz_api_put with changes
- "user request" → "Delete item" → ctz_api_delete with item ID

## Notes
- All tools return status code, headers, and response body
- Supports JSON and form data
- Include auth tokens in headers if required