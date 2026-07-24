# Frontend contribution guide

This directory contains the Vue 3 administration console.

## Boundaries

- Keep API calls in `src/api`; views must not call `fetch` directly.
- Keep shared transport types in `src/types`.
- Never display, request, persist, or log the upstream GPT API key.
- Use black for primary actions, green for healthy/success states, and red only for errors.
- Keep recruitment features under `views/RecruitmentView.vue`; future scenarios should get their own route and view.

## Verification

Run `npm run type-check` and `npm run build` before handing off changes.
