---
name: ai-platform-onboarding
description: Load the current BLUEDOT AI capability platform context and route work to the correct backend, frontend, LLM, audit, recruitment, documentation, or deployment paths. Use when starting or resuming project work, analyzing the repository, locating implementation ownership, or deciding the next development step.
---

# AI Platform Onboarding

1. Read the repository `AGENTS.md` and any nearer `AGENTS.md`.
2. Read `AI-chat-history/CURRENT_PROJECT_STATE.md` completely.
3. Read `AI-chat-history/INDEX.md` completely.
4. Inspect Git branch, short HEAD and worktree status.
5. Route the task:
   - LLM calls, retries and streaming: `backend/app/infrastructure/llm/`
   - reusable AI execution: `backend/app/capabilities/`
   - recruitment: `backend/app/scenarios/recruitment/`
   - audits: `backend/app/modules/audits/`
   - dashboard and settings: `backend/app/modules/`
   - UI: `frontend/src/`
   - deployment: `deploy/`
6. Read only task-relevant code, tests, docs and dated histories.
7. Treat current code as authoritative and call out stale history explicitly.
8. Never print environment secrets or resume content while onboarding.

Return the current behavior, affected paths, gaps, risks, smallest sensible next step, and available validation.
