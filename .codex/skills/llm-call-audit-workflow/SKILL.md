---
name: llm-call-audit-workflow
description: Implement or review OpenAI-compatible LLM calls for BLUEDOT AI capability platform, including error mapping, retry eligibility, Retry-After, timeouts, streaming boundaries, structured repair, Token accounting, content privacy, and business/upstream audit records. Use whenever changing model calls, prompts, retries, streaming, usage statistics, or audit behavior.
---

# LLM Call Audit Workflow

1. Trace the complete path from HTTP route through scenario, capability executor, LLM client and audit persistence.
2. Verify the real API Key remains server-only and never appears in logs, errors, responses or frontend state.
3. Classify failures:
   - retry network failures, timeouts, 429 and 5xx
   - do not retry 400, 401, 403, model errors or content rejection
4. Limit transport retries to configured delays and honor `Retry-After`.
5. Record every real upstream attempt, including failed calls and format repair.
6. Keep business request count separate from upstream call count.
7. Sum usage from all attempts that return usage; do not invent usage for failures.
8. Treat structured format repair as a separate attempt type.
9. Never retry a stream transparently after response bytes were emitted.
10. Store only content hash and length in audit metadata.
11. Test success, 429 recovery, timeout exhaustion, non-retryable auth errors, malformed JSON repair and final failure.
