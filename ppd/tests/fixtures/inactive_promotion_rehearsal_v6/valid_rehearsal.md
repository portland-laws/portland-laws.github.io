# Inactive Guardrail Promotion Rehearsal v6

Mode: inactive rehearsal only. No active activation is requested or implied.

## Release Readiness References

- Release readiness reference: ppd://guardrails/release-readiness/inactive-v6
- Evidence reference: ppd://sources/freshness/report-2026-05-08

## Inactive Promotion Candidate Rows

| inactive promotion candidate | bundle | status |
| --- | --- | --- |
| inactive promotion candidate | guardrail-bundle-devhub-readonly | rehearsal only |

## Reviewer-Controlled Signoff Placeholders

| reviewer-controlled signoff | placeholder |
| --- | --- |
| PP&D source reviewer | pending placeholder |
| Guardrail reviewer | pending placeholder |

## Source Freshness Clearance Prerequisites

Source freshness clearance is a prerequisite before any later human promotion review. Clearance requires current public-source hashes and no stale DevHub guidance alerts.

## Unresolved Hold Propagation

Unresolved hold propagation must carry every hold into the candidate status table and block promotion review until a reviewer clears it.

## Rollback Checkpoint Rows

| rollback checkpoint | owner | expected state |
| --- | --- | --- |
| checkpoint before inactive rehearsal | guardrail reviewer | previous inactive bundle remains selected |

## Post-Promotion Smoke Replay Expectations

Post-promotion smoke replay expectations: after a separate reviewer-approved promotion, the team must replay read-only smoke checks against deterministic fixtures before any agent use.

## Agent API Compatibility Reminders

Agent API compatibility reminder: verify stable missing-information, blocked-action, and exact-confirmation response fields before reviewer signoff.

## Monitoring Handoff Rows

| monitoring handoff | owner | trigger |
| --- | --- | --- |
| source freshness monitor | PP&D source reviewer | changed official source hash |
| guardrail regression monitor | guardrail reviewer | failed deterministic smoke replay |

## Validation Commands

- python3 ppd/daemon/ppd_daemon.py --self-test
