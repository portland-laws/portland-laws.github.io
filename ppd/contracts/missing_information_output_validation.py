"""Fixture-scoped validation for PP&D missing-information output.

This module is intentionally small and syntax-first. It validates only the
committed four-requested-items fixture shape used to recover the blocked
missing-information output validator task.
"""

from urllib.parse import urlparse


MODULE_STATUS = "syntax_first_import_ready"

EXPECTED_SCHEMA_VERSION = 1
EXPECTED_FIXTURE_ID = "missing-information-output-four-requested-items"
EXPECTED_ITEM_KINDS = ("fact", "file", "acknowledgment", "decision")
EXPECTED_ACTION_BY_KIND = {
    "fact": "read_only",
    "file": "draft_edit",
    "acknowledgment": "consequential_confirmation_required",
    "decision": "consequential_confirmation_required",
}
ALLOWED_REDACTION_TOKEN = "[REDACTED]"

PRIVATE_KEY_MARKERS = (
    "authorization",
    "auth_state",
    "authstate",
    "bearer",
    "client_secret",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "private_value",
    "raw_body",
    "raw_content",
    "raw_html",
    "raw_response",
    "refresh_token",
    "secret",
    "session_cookie",
    "screenshot",
    "storage_state",
    "token",
    "trace",
    "username",
)

PRIVATE_VALUE_MARKERS = (
    "bearer ",
    "password=",
    "private devhub",
    "session cookie",
    "storage_state",
    "storage-state",
    "trace.zip",
    "raw response body",
    "raw_response_body",
    "raw-response-body",
    "screenshot.png",
    "screenshot.jpg",
    "screenshot.jpeg",
    "screenshot.webp",
    "downloaded private document",
    "ppd/data/private",
    "devhub/session",
    "devhub/sessions",
)

REQUIRED_TOP_LEVEL_KEYS = (
    "schemaVersion",
    "fixtureId",
    "processId",
    "userCaseId",
    "generatedAt",
    "redactionPolicy",
    "requestedItems",
)

REQUIRED_ITEM_KEYS = (
    "id",
    "kind",
    "label",
    "prompt",
    "requestedValue",
    "actionClassification",
    "sourceBacked",
    "evidence",
)

REQUIRED_EVIDENCE_KEYS = (
    "requirementId",
    "sourceUrl",
    "sourceTitle",
    "retrievedAt",
    "summary",
)


def validate_missing_information_output(data):
    """Return a list of validation error strings for the fixture-like object."""

    errors = []
    if not isinstance(data, dict):
        return ["output must be a JSON object"]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append("missing top-level key: " + key)

    if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")
    if data.get("fixtureId") != EXPECTED_FIXTURE_ID:
        errors.append("fixtureId must be " + EXPECTED_FIXTURE_ID)
    if not _is_non_empty_string(data.get("processId")):
        errors.append("processId is required")
    if not _is_non_empty_string(data.get("userCaseId")):
        errors.append("userCaseId is required")
    if not _is_utc_timestamp(data.get("generatedAt")):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    errors.extend(_validate_redaction_policy(data.get("redactionPolicy")))

    items = data.get("requestedItems")
    if not isinstance(items, list):
        errors.append("requestedItems must be a list")
        items = []
    if len(items) != 4:
        errors.append("requestedItems must contain exactly four items")

    seen_ids = set()
    seen_kinds = []
    for index, item in enumerate(items):
        path = "requestedItems[" + str(index) + "]"
        if not isinstance(item, dict):
            errors.append(path + " must be an object")
            continue
        errors.extend(_validate_requested_item(item, path, seen_ids))
        kind = item.get("kind")
        if isinstance(kind, str):
            seen_kinds.append(kind)

    if tuple(seen_kinds) != EXPECTED_ITEM_KINDS:
        errors.append("requestedItems kinds must be fact, file, acknowledgment, decision in order")

    errors.extend(_validate_no_private_values(data))
    return errors


def validate_missing_information_output_fixture(data):
    """Compatibility wrapper for tests that name the fixture explicitly."""

    return validate_missing_information_output(data)


def assert_missing_information_output(data):
    """Raise AssertionError when the fixture-like output is invalid."""

    errors = validate_missing_information_output(data)
    if errors:
        raise AssertionError("; ".join(errors))
    return True


def assert_valid_missing_information_output(data):
    """Compatibility alias for assertion-style validation."""

    return assert_missing_information_output(data)


def _validate_redaction_policy(policy):
    errors = []
    if not isinstance(policy, dict):
        return ["redactionPolicy must be an object"]
    if policy.get("fixtureValuesAreRedacted") is not True:
        errors.append("redactionPolicy.fixtureValuesAreRedacted must be true")
    if policy.get("privateFixtureValuesAllowed") is not False:
        errors.append("redactionPolicy.privateFixtureValuesAllowed must be false")
    if policy.get("redactionToken") != ALLOWED_REDACTION_TOKEN:
        errors.append("redactionPolicy.redactionToken must be [REDACTED]")
    return errors


def _validate_requested_item(item, path, seen_ids):
    errors = []
    for key in REQUIRED_ITEM_KEYS:
        if key not in item:
            errors.append(path + " missing key: " + key)

    item_id = item.get("id")
    if not _is_non_empty_string(item_id):
        errors.append(path + ".id is required")
    elif item_id in seen_ids:
        errors.append(path + ".id duplicates " + item_id)
    else:
        seen_ids.add(item_id)

    kind = item.get("kind")
    if kind not in EXPECTED_ACTION_BY_KIND:
        errors.append(path + ".kind must be one of fact, file, acknowledgment, decision")
    else:
        expected_action = EXPECTED_ACTION_BY_KIND[kind]
        if item.get("actionClassification") != expected_action:
            errors.append(path + ".actionClassification must be " + expected_action)

    for text_key in ("label", "prompt"):
        if not _is_non_empty_string(item.get(text_key)):
            errors.append(path + "." + text_key + " is required")

    if item.get("requestedValue") != ALLOWED_REDACTION_TOKEN:
        errors.append(path + ".requestedValue must be [REDACTED]")
    if item.get("sourceBacked") is not True:
        errors.append(path + ".sourceBacked must be true")

    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(path + ".evidence must be a non-empty list")
    else:
        for index, evidence_item in enumerate(evidence):
            evidence_path = path + ".evidence[" + str(index) + "]"
            errors.extend(_validate_evidence(evidence_item, evidence_path))

    return errors


def _validate_evidence(evidence, path):
    errors = []
    if not isinstance(evidence, dict):
        return [path + " must be an object"]
    for key in REQUIRED_EVIDENCE_KEYS:
        if key not in evidence:
            errors.append(path + " missing key: " + key)
    for key in ("requirementId", "sourceTitle", "summary"):
        if not _is_non_empty_string(evidence.get(key)):
            errors.append(path + "." + key + " is required")
    if not _is_https_url(evidence.get("sourceUrl")):
        errors.append(path + ".sourceUrl must be an https URL")
    if not _is_utc_timestamp(evidence.get("retrievedAt")):
        errors.append(path + ".retrievedAt must be an ISO UTC timestamp ending in Z")
    return errors


def _validate_no_private_values(value):
    errors = []
    for path, key, leaf in _walk(value, "$"):
        key_text = _normalize(key)
        if key_text in PRIVATE_KEY_MARKERS:
            errors.append(path + " uses private key " + str(key))
            continue
        if isinstance(leaf, str):
            if leaf == ALLOWED_REDACTION_TOKEN:
                continue
            leaf_text = leaf.lower()
            for marker in PRIVATE_VALUE_MARKERS:
                if marker in leaf_text:
                    errors.append(path + " contains private marker " + marker)
                    break
    return errors


def _walk(value, path):
    if isinstance(value, dict):
        for key in sorted(value.keys(), key=str):
            child_path = path + "." + str(key)
            child = value[key]
            yield child_path, key, child
            for item in _walk(child, child_path):
                yield item
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = path + "[" + str(index) + "]"
            yield child_path, "", child
            for item in _walk(child, child_path):
                yield item


def _normalize(value):
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _is_utc_timestamp(value):
    return _is_non_empty_string(value) and value.endswith("Z") and "T" in value


def _is_https_url(value):
    if not _is_non_empty_string(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)
