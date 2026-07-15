"""表紙・フッター設定の単体検証。"""
import json
import tempfile
from pathlib import Path

from pptx.dml.color import RGBColor

from cover_footer import (
    load_cover_footer_config,
    parse_cover_footer_config,
    render_footer,
)


def _must_fail(data, expected):
    try:
        parse_cover_footer_config(data)
    except ValueError as e:
        assert expected in str(e), str(e)
    else:
        raise AssertionError(f"ValueErrorになりませんでした: {data}")


def main():
    default = parse_cover_footer_config({})
    assert default.cover.eyebrow == "SLIDE PATTERN LIBRARY"
    assert default.footer.text == "{footer}"
    assert default.footer.show_total is True

    custom = parse_cover_footer_config({
        "cover": {
            "eyebrow": "{date} BUSINESS REVIEW",
            "show_rail": False,
            "background_color": "102030",
        },
        "footer": {"text": "{author} | {title}", "show_total": False},
    })
    assert custom.cover.show_rail is False
    assert custom.cover.background_color == RGBColor.from_string("102030")
    assert custom.cover.title_color == default.cover.title_color
    assert custom.footer.show_total is False

    _must_fail({"cover": {"unknown": True}}, "未対応の項目")
    _must_fail({"cover": {"background_color": "blue"}}, "6桁のHEX色")
    _must_fail({"footer": {"text": "{company}"}}, "{company} は使用できません")
    _must_fail({"cover": {"rail": [{"label": "A", "value": "B"}] * 4}},
               "0〜3件")

    too_long = parse_cover_footer_config({
        "footer": {"text": "W" * 100},
    })
    try:
        render_footer(
            None, 2,
            {"title": "T", "footer": "F", "date": "D", "author": "A"},
            10, too_long,
            add_text=lambda *args, **kwargs: None,
            add_rect=lambda *args, **kwargs: None,
        )
    except ValueError as e:
        assert "footer.text の展開後の文字列が長すぎます" in str(e), str(e)
    else:
        raise AssertionError("長すぎるフッターを拒否しませんでした")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cover_footer.json"
        path.write_text(json.dumps({"footer": {"show_text": False}}),
                        encoding="utf-8")
        loaded = load_cover_footer_config(path)
        assert loaded.footer.show_text is False
        assert loaded.cover.eyebrow == default.cover.eyebrow

    print("cover/footer tests passed")


if __name__ == "__main__":
    main()
