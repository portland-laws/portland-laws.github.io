from pathlib import Path

from ppd.devhub.permit_taxonomy import (
    MANUAL_HANDOFF_CATEGORIES,
    load_permit_type_routes,
    validate_permit_type_routes,
)


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "devhub" / "permit_type_taxonomy.json"
)


def test_permit_type_taxonomy_fixture_is_valid() -> None:
    routes = load_permit_type_routes(FIXTURE_PATH)

    errors = validate_permit_type_routes(routes)

    assert errors == []


def test_fixture_covers_required_path_categories() -> None:
    routes = load_permit_type_routes(FIXTURE_PATH)

    categories = {route.category for route in routes}

    assert "devhub_supported" in categories
    assert "devhub_unsupported" in categories
    assert "email_manual" in categories
    assert "public_reference_only" in categories


def test_unsupported_paths_always_force_manual_handoff() -> None:
    routes = load_permit_type_routes(FIXTURE_PATH)

    manual_routes = [
        route for route in routes if route.category in MANUAL_HANDOFF_CATEGORIES
    ]

    assert manual_routes
    for route in manual_routes:
        assert route.routing == "manual_handoff"
        assert route.browser_automation_allowed is False


def test_supported_paths_are_attended_not_final_actions() -> None:
    routes = load_permit_type_routes(FIXTURE_PATH)

    supported_routes = [route for route in routes if route.category == "devhub_supported"]

    assert supported_routes
    for route in supported_routes:
        assert route.browser_automation_allowed is True
        assert route.routing == "attended_devhub_draft"
        assert route.routing not in {"submit", "certify", "pay", "upload_final"}
