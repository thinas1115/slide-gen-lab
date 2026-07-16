"""公開diagramスキーマの構成図サンプルを回帰検証する。"""
from copy import deepcopy
import json

from diagram_layout import ICON_SIZE, Layout
from diagram_specs import AWS_MULTIAZ_EXAMPLE, AWS_SIMPLE_EXAMPLE
from layout_fit import FitError
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
    invalid["slides"][0]["diagram"]["nodes"]["user"]["icon"] = (
        "fluent/not_defined.png")
    errors = validate(invalid)
    assert any("diagram.area" in error for error in errors)
    assert any(".pad" in error for error in errors)
    assert any("assets/ にありません" in error for error in errors)

    rows = [f"r{i}" for i in range(5)]
    nodes = {
        f"n{i}": {
            "col": "main", "row": row, "icon": "fluent/app.png",
            "title": f"Node {i}", **({"sub": "sub"} if i < 2 else {}),
        }
        for i, row in enumerate(rows)
    }
    dense = {
        "cols": ["main"], "rows": rows, "nodes": nodes,
        "containers": [], "channels": {}, "edges": [],
    }
    gap_only = deepcopy(dense)
    gap_only["nodes"]["n0"].pop("sub")
    gap_only["nodes"]["n1"].pop("sub")
    compact_gap = Layout(gap_only)
    assert compact_gap.fit_stage == "gap"
    assert compact_gap.icon_size == ICON_SIZE

    compact = Layout(dense)
    assert compact.fit_stage == "icon"
    assert compact.icon_size < ICON_SIZE

    for node in dense["nodes"].values():
        node["sub"] = "sub"
    try:
        Layout(dense)
    except FitError as e:
        assert "アイコン縮小" in str(e), str(e)
        assert "行数を減らす" in str(e), str(e)
    else:
        raise AssertionError("最小アイコンでも収まらないdiagramを拒否しませんでした")
    print("OK: 2 inline diagram examples passed schema, layout, and routing checks")


if __name__ == "__main__":
    main()
