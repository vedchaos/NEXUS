---
name: ctz-browser-automation
description: Browser automation — open pages, scrape content, navigate links, run JS, take screenshots. Use when user wants to browse, scrape, or automate web interactions.
---

# CHAOS TYPE ZERO Browser Automation Skill

Simulated browser automation for reconnaissance, data gathering, and web interaction.

## Capabilities
- **Open & Navigate** — Load URLs, follow redirects, manage tabs
- **Click & Type** — Interact with links and form fields
- **Scrape** — Extract text, links, images from any page
- **Evaluate** — Run JS-like queries (querySelector, title, body text)
- **Screenshot** — Save text snapshots of pages for review
- **Wait** — Poll for elements with configurable timeout

## Tools
| Tool | Purpose |
|------|---------|
| `ctz_browser_open` | Open URL, return page info |
| `ctz_browser_navigate` | Navigate active tab to URL |
| `ctz_browser_click` | Click a link by text or selector |
| `ctz_browser_type` | Type into a form field |
| `ctz_browser_screenshot` | Save page snapshot |
| `ctz_browser_scrape` | Extract text/links/images |
| `ctz_browser_tabs` | List open tabs |
| `ctz_browser_close` | Close a tab |
| `ctz_browser_evaluate` | Run JS on page |
| `ctz_browser_wait` | Wait for element or timeout |

## Workflows

### Reconnaissance Scan
1. `ctz_browser_open` target URL
2. `ctz_browser_scrape` with mode=links to enumerate endpoints
3. `ctz_browser_scrape` with mode=text for content analysis
4. `ctz_browser_screenshot` for documentation

### Form Interaction
1. `ctz_browser_open` login/form page
2. `ctz_browser_type` to fill fields
3. `ctz_browser_click` submit button
4. `ctz_browser_screenshot` result

### Multi-page Scrape
1. `ctz_browser_open` seed URL
2. Loop: `ctz_browser_scrape` links, `ctz_browser_click` each, scrape again
3. Aggregate results

## Commands
- "website kholo" → ctz_browser_open
- "page scrape karo" → ctz_browser_scrape
- "link pe click karo" → ctz_browser_click
- "form fill karo" → ctz_browser_type + click
- "screenshot le lo" → ctz_browser_screenshot
- "page ka JS run karo" → ctz_browser_evaluate
