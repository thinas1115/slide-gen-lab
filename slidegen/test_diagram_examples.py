"""公開diagramスキーマの構成図サンプルを回帰検証する。"""
from copy import deepcopy
import json

from diagram_layout import Layout
from diagram_specs import AWS_MULTIAZ_EXAMPLE, AWS_SIMPLE_EXAMPLE
from validate_content import validate


def _assert_no_layout_fields(diagram):
    assert "area" not in diagram
    for container in diagram.get("containers", []):
        assert "pad" not in container
        assert "pad_x" not in container


def main():
    examples = [AWS_SIMPLE_EXAMPLE, AWS_MULTIAZ_EXAMPLE]
    for diagram in examples:
        _assert_no_layout_fields(diagram)
        layout = Layout(diagram)
        edges = diagram["edges"]
        routed = layout.route_edges(edges)
        layout.validate_edges(edges, routed)

    deck = {
        "meta": {
            "title": "diagram examples",
            "footer": "diagram examples",
            "date": "2026-07",
            "author": "test",
        },
        "slides": [
            {
                "type": "diagram",
                "kicker": "simple",
                "title": "simple architecture",
                "diagram": AWS_SIMPLE_EXAMPLE,
            },
            {
                "type": "diagram",
                "kicker": "dense",
                "title": "dense architecture",
                "diagram": AWS_MULTIAZ_EXAMPLE,
            },
        ],
    }
    json_roundtrip = json.loads(json.dumps(deck, ensure_ascii=False))
    errors = validate(json_roundtrip)
    assert not errors, "\n".join(errors)

    invalid = deepcopy(json_roundtrip)
    invalid["slides"][0]["diagram"]["area"] = [0, 0, 1, 1]
    invalid["slides"][0]["diagram"]["containers"][0]["pad"] = 0.1
    errors = validate(invalid)
    assert any("diagram.area" in error for error in errors)
    assert any(".pad" in error for error in errors)
    print("OK: 2 inline diagram examples passed schema, layout, and routing checks")


if __name__ == "__main__":
    main()
