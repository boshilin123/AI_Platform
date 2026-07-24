---
name: capture-discussion-summary
description: Save concise BLUEDOT AI capability platform decisions, implementation results, validation, errors, risks, and next steps into AI-chat-history. Use when preserving context for another session, recording a material development stage, or documenting a reusable incident or architectural decision.
---

# Capture Discussion Summary

1. Work from the repository root.
2. Create `AI-chat-history/YYYY-MM-DD-topic-summary.md` with an English hyphenated filename and Chinese title.
3. Record the goal, decisions, changed files, commands, validation, errors, current state, risks and next steps.
4. Do not paste transcripts, full prompts, resume content, API keys, tokens or connection strings.
5. Update `AI-chat-history/CURRENT_PROJECT_STATE.md` when architecture, implemented scope, risks or priorities changed.
6. Add the new record to `AI-chat-history/INDEX.md`.
7. Write with `apply_patch` and read the result back.

Prefer sections for discussion topic, key conclusions, completed changes, errors, validation, current state and follow-up.
