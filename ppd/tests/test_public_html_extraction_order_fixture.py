from html.parser import HTMLParser
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "public_html_extraction_order" / "synthetic_guidance.html"


class OrderedVisibleContentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._stack = []
        self._capture = None
        self._buffer = []
        self._hidden_depth = 0
        self._ol_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        hidden = self._is_hidden(tag, attrs_dict)
        self._stack.append((tag, hidden))
        if hidden:
            self._hidden_depth += 1

        if self._hidden_depth:
            return

        if tag == "ol":
            self._ol_stack.append(0)
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._start_capture(f"heading:{tag}")
        elif tag == "li" and self._ol_stack:
            self._ol_stack[-1] += 1
            self._start_capture(f"step:{self._ol_stack[-1]}")
        elif tag == "aside" or "callout" in attrs_dict.get("class", "").split():
            self._start_capture("callout")
        elif tag == "caption":
            self._start_capture("table:caption")
        elif tag in {"th", "td"}:
            self._start_capture(f"table:{tag}")
        elif tag == "a" and self._in_related_links():
            self._start_capture("related-link")
        elif tag == "time" or "updated" in attrs_dict.get("class", "").split():
            self._start_capture("updated")

    def handle_endtag(self, tag):
        if self._capture and self._capture[0] == tag:
            text = " ".join("".join(self._buffer).split())
            if text:
                self.items.append((self._capture[1], text))
            self._capture = None
            self._buffer = []

        if tag == "ol" and self._ol_stack and not self._hidden_depth:
            self._ol_stack.pop()

        if self._stack:
            _open_tag, hidden = self._stack.pop()
            if hidden:
                self._hidden_depth -= 1

    def handle_data(self, data):
        if self._capture and not self._hidden_depth:
            self._buffer.append(data)

    def _start_capture(self, kind):
        if not self._capture:
            self._capture = (self._stack[-1][0], kind)
            self._buffer = []

    def _is_hidden(self, tag, attrs):
        style = attrs.get("style", "").replace(" ", "").lower()
        return (
            tag in {"script", "style", "template"}
            or "hidden" in attrs
            or attrs.get("aria-hidden") == "true"
            or "display:none" in style
        )

    def _in_related_links(self):
        for tag, _hidden in reversed(self._stack):
            if tag in {"nav", "section"}:
                return True
        return False


def test_public_guidance_fixture_preserves_visible_content_order():
    parser = OrderedVisibleContentParser()
    parser.feed(FIXTURE.read_text(encoding="utf-8"))

    assert parser.items == [
        ("heading:h1", "Commercial Solar Permits"),
        ("updated", "Updated May 8, 2026"),
        ("heading:h2", "Before You Apply"),
        ("step:1", "Confirm the property address and permit type."),
        ("step:2", "Prepare plan sheets and engineering documents."),
        ("callout", "Permit review may take longer for historic resources."),
        ("heading:h2", "Fees and Review Targets"),
        ("table:caption", "Review targets"),
        ("table:th", "Permit type"),
        ("table:th", "Target"),
        ("table:td", "Commercial solar"),
        ("table:td", "10 business days"),
        ("heading:h2", "After Approval"),
        ("step:1", "Print the issued permit."),
        ("step:2", "Schedule required inspections."),
        ("related-link", "Solar permit application"),
        ("related-link", "Electrical inspections"),
    ]
