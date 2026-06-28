# Fixture-First Source Refresh Runbook Candidate

Status: candidate
Scope: Portland PP&D public source refresh preparation
Mode: metadata-only, fixture-first, no live URL fetches

## Inputs

This runbook candidate consumes only committed or reviewer-supplied metadata artifacts:

1. Public source recrawl dry-run command plan
2. Source registry coverage gap packet
3. Post-release monitoring plan

The refresh coordinator must not fetch URLs, invoke document processors, mutate schedules, write raw crawl output, or create authenticated automation state while following this candidate.

## Ordered Refresh Steps

1. Confirm fixture set
   - Verify the dry-run command plan, registry gap packet, and monitoring plan are present as metadata fixtures.
   - Record fixture names, checksums, and reviewer initials in the refresh notes.
   - Abort if any input is missing, stale, or derived from an unapproved live fetch.

2. Build source inventory delta
   - Compare the dry-run command plan source list with the registry coverage gap packet.
   - Classify each source as covered, newly proposed, missing evidence, policy blocked, or needs reviewer decision.
   - Do not add, remove, or reorder live schedules.

3. Assign allowlisted batches
   - Group only sources with complete registry metadata and robots or policy evidence references.
   - Keep batch size small enough for manual review before execution.
   - Exclude sources with missing policy evidence, unclear ownership, CAPTCHA, authentication, payment, or submission requirements.

4. Attach robots and policy evidence
   - For every candidate source, reference existing robots, terms, policy, or public access evidence by fixture path or registry identifier.
   - Prefer dated evidence captured during approved review.
   - Do not retrieve robots.txt or policy pages during this runbook candidate.

5. Define rate-limit windows
   - Assign conservative metadata-only execution windows for future live runs.
   - Include maximum request rate, quiet hours, and retry limits as proposed values only.
   - Mark any source without explicit rate guidance for reviewer approval.

6. Reviewer checkpoint A: source eligibility
   - Reviewer confirms each source is public, in-scope for PP&D, and represented in the registry.
   - Reviewer rejects sources with unclear legal, policy, or operational status.

7. Reviewer checkpoint B: batch readiness
   - Reviewer confirms each allowlisted batch has source IDs, evidence references, proposed rate windows, and abort criteria.
   - Reviewer confirms no batch requires authentication, CAPTCHA handling, payment, upload, certification, account creation, or form submission.

8. Reviewer checkpoint C: release monitoring alignment
   - Compare proposed batches with the post-release monitoring plan.
   - Ensure each batch has monitoring expectations, owner, rollback note, and escalation channel.
   - Do not create or mutate monitoring schedules from this candidate.

9. Produce metadata-only handoff packet
   - Emit a reviewer-facing packet containing ordered steps, allowlisted batches, policy evidence references, proposed rate windows, checkpoints, and abort notes.
   - Label the packet as not executable until a separate approved implementation task authorizes live crawling.

## Allowlisted Batch Template

Each proposed batch should contain:

- batch_id
- source_ids
- source_registry_refs
- dry_run_plan_refs
- coverage_gap_refs
- robots_policy_evidence_refs
- proposed_rate_limit_window
- reviewer_checkpoint
- abort_conditions
- escalation_contact_or_role
- monitoring_plan_refs

## Abort Conditions

Abort the candidate refresh preparation if any of the following occur:

- A required fixture is missing, unsigned, or inconsistent with the registry.
- A source requires authentication, CAPTCHA, MFA, account creation, payment, submission, upload, cancellation, or certification.
- Robots, terms, policy, or public access evidence is absent or ambiguous.
- A proposed batch includes a source outside Portland PP&D scope.
- The run would fetch URLs, invoke processors, mutate schedules, write raw crawl output, or create private session state.
- Reviewer approval is missing at any checkpoint.

## Escalation Notes

Escalate to the PP&D maintainer before live execution when:

- Registry coverage conflicts with the dry-run plan.
- Monitoring expectations are undefined or incompatible with proposed batches.
- Rate-limit guidance is unavailable for a high-volume source.
- A public source changes access policy or introduces interactive barriers.

This runbook candidate is intentionally non-executable. It prepares metadata for review and later implementation only.
