---
name: ctz-translate
description: Translation workflows using ctz_translate_text/detect tools
---

# CTZ Translate Skill

## When to Use
- Translating text between languages
- Detecting language of input text
- Multi-language content processing

## Available Tools
- ctz_translate_text: Translate text to target language
- ctz_translate_detect: Detect language of input text

## Workflow
1. If language unknown, use ctz_translate_detect
2. Translate text with ctz_translate_text
3. Verify translation quality
4. Handle multiple languages if needed

## Examples
- "user request" → "Translate this to Spanish" → ctz_translate_text
- "user request" → "What language is this?" → ctz_translate_detect
- "user request" → "Translate to French and German" → ctz_translate_text twice
- "user request" → "Detect and translate" → ctz_translate_detect then ctz_translate_text

## Notes
- Supports major world languages
- Translation quality varies by language pair
- Can be combined with ctz-docs skill for document translation