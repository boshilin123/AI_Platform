---
name: git-publish-workflow
description: Review, validate, stage, commit, push, and optionally open a pull request for BLUEDOT AI capability platform changes. Use when the user asks for Git status, staging, commits, publishing, syncing, pushing, or preparing repository changes for review.
---

# Git Publish Workflow

1. Inspect branch, remote, status, staged diff and unstaged diff.
2. Read all new files and separate unrelated topics.
3. Scan for API keys, tokens, passwords, private keys, `.env`, databases, resumes and generated artifacts.
4. Validate changed areas:
   - backend: `pytest` and `compileall`
   - frontend: `npm run build`
   - skills: run `quick_validate.py`
   - deployment: `docker compose config`
5. Stage explicit files; avoid `git add .` when unrelated changes exist.
6. Use Conventional Commits with a concise Chinese subject.
7. Push only when explicitly requested.
8. Report commit hash, branch, validation and intentionally uncommitted files.

Never reset, force-push, discard user changes, commit `.env`, or publish secrets.
