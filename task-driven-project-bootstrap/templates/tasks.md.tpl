# __PROJECT_NAME__ - Tasks

Last updated: __DATE__

Source docs:

- `__PLAN_PATH__`
- `__PROGRESS_FILE__`

Execution rule:

- complete one task at a time unless the user explicitly asks for a batch
- respect dependencies
- run verification before marking a task done
- update `__PROGRESS_FILE__` after each completed task

## Batch 1: Discovery and Contract

- [ ] `T01` Audit the real input shape or existing implementation baseline.
  Acceptance: key formats, constraints, and edge cases are documented.
- [ ] `T02` Lock the v1 contract for the core data model or API surface.
  Depends on: `T01`
  Acceptance: target fields and required behaviors are explicit.
- [ ] `T03` Create the implementation plan for the first real feature batch.
  Depends on: `T02`
  Acceptance: files, tests, and verification steps are known.

## Batch 2: First Functional Slice

- [ ] `T04` Add tests for the first real slice.
  Depends on: `T03`
  Acceptance: tests fail for the intended reason before implementation.
- [ ] `T05` Implement the first real slice.
  Depends on: `T04`
  Acceptance: the feature works and the tests pass.
- [ ] `T06` Add or update E2E coverage for the critical flow.
  Depends on: `T05`
  Acceptance: the core user flow is exercised end to end.

## Batch 3: Hardening

- [ ] `T07` Handle the most important error and empty states.
  Depends on: `T05`
  Acceptance: failures are explicit, not silent.
- [ ] `T08` Remove temporary scaffolding or mocks that the real slice replaced.
  Depends on: `T05`
  Acceptance: stale fallback paths are deleted or clearly isolated.

## Suggested Stop Points

- Stop after Batch 1 to confirm the contract.
- Stop after Batch 2 to review the first end-to-end slice.
- Stop after Batch 3 before expanding scope.
