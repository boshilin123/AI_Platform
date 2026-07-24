---
name: fastapi-module-workflow
description: Implement or review BLUEDOT AI capability platform FastAPI modules with consistent router, service, repository, schema, dependency, error, documentation, and test boundaries. Use for new backend endpoints, business modules, refactors, API contract changes, or FastAPI diagnostics.
---

# FastAPI Module Workflow

1. Read root and nearest `AGENTS.md`.
2. Confirm the owning layer: infrastructure, capability, scenario or management module.
3. Keep `router.py` limited to HTTP input, dependencies and response conversion.
4. Put orchestration in `service.py`, persistence in `repository.py`, and Pydantic contracts in `schemas.py`.
5. Use typed dependencies and `AsyncSession`; do not call synchronous network or database clients from async routes.
6. Return the standard success envelope and raise typed `AppError` failures.
7. Update OpenAPI-visible schemas and `docs/api-contract.md` for contract changes.
8. Add focused unit or integration tests for success, validation, authorization and failure behavior.
9. Run `pytest` and `compileall`, then inspect the diff for secrets and unrelated changes.
