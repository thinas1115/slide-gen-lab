"""表紙・フッター設定の単体検証。"""
import json
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches

from cover_footer import (
    COVER_BACKGROUND_NAME,
    load_cover_footer_config,
    parse_cover_footer_config,
    render_cover,
    render_footer,
)
from validate_content import validate


def _must_fail(data, expected, **kwargs):
    try:
        parse_cover_footer_config(data, **kwargs)
    except ValueError as e:
        assert expected in str(e), str(e)
    else:
        raise AssertionError(f"ValueErrorになりませんでした: {data}")


def main():
    default = parse_cover_footer_config({})
    assert default.cover.eyebrow == ""
    assert default.cover.show_rail is False
    assert default.cover.rail == ()
    assert default.cover.background_image is None
    assert default.footer.text == "{footer}"
    assert default.footer.show_total is True

    repo_root = Path(__file__).resolve().parents[1]
    example = load_cover_footer_config(repo_root / "examples" / "cover_footer.json")
    assert example.cover.background_image == (
        repo_root / "slidegen" / "assets" / "cover" /
        "cover-background.png").resolve()
    with Image.open(example.cover.background_image) as image:
        assert image.format == "PNG"
        assert image.width / image.height > 1.7
    assert example.cover.eyebrow == ""
    assert example.cover.show_date is True
    assert example.cover.show_author is True
    assert example.cover.show_rail is False
    assert example.cover.rail == ()
    assert example.footer.text == "{footer}"

    minimal_deck = {
        "meta": {"title": "最小資料"},
        "slides": [{"type": "title", "title": "表紙", "subtitle": "概要"}],
    }
    assert not validate(minimal_deck)
    placeholder_deck = {
        "meta": {"title": "<資料名>"},
        "slides": [{"type": "title", "title": "表紙", "subtitle": "概要"}],
    }
    assert any("入力欄が残っています" in error
               for error in validate(placeholder_deck))
    optional_text_calls = []
    render_cover(
        None, minimal_deck["slides"][0], minimal_deck["meta"], 1, default,
        add_text=lambda *args, **kwargs: optional_text_calls.append(args),
        add_rect=lambda *args, **kwargs: None,
    )
    rendered = {args[5] for args in optional_text_calls}
    assert rendered == {"表紙", "概要"}

    empty_dynamic_rail = parse_cover_footer_config({"cover": {
        "show_date": False,
        "show_author": False,
        "show_rail": True,
        "rail": [
            {"label": "DATE", "value": "{date}"},
            {"label": "OWNER", "value": "{author}"},
        ],
    }})
    empty_rail_text_calls = []
    render_cover(
        None, minimal_deck["slides"][0], minimal_deck["meta"], 1,
        empty_dynamic_rail,
        add_text=lambda *args, **kwargs: empty_rail_text_calls.append(args),
        add_rect=lambda *args, **kwargs: None,
    )
    assert {args[5] for args in empty_rail_text_calls} == {"表紙", "概要"}

    optional_footer_calls = []
    render_footer(
        None, 1, minimal_deck["meta"], 1, default,
        add_text=lambda *args, **kwargs: optional_footer_calls.append(args),
        add_rect=lambda *args, **kwargs: None,
    )
    assert all(args[5] != "" for args in optional_footer_calls)

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
    _must_fail({"cover": {
        "show_rail": True,
        "rail": [{"label": "DATE", "value": "{date}"}],
    }}, "show_date を false")
    _must_fail({"cover": {
        "show_rail": True,
        "rail": [{"label": "OWNER", "value": "{author}"}],
    }}, "show_author を false")

    multiline = parse_cover_footer_config({"cover": {
        "show_date": False,
        "show_author": False,
        "show_rail": True,
        "rail": [
            {"label": "DATE", "value": "{date}"},
            {"label": "ORGANIZATION",
             "value": "組織A\n部門B\nチームC"},
            {"label": "OWNER", "value": "担当A\n役割B"},
        ],
    }})
    text_calls = []
    rect_calls = []
    render_cover(
        None, {"title": "Title", "subtitle": "Subtitle"},
        {"title": "T", "footer": "F", "date": "2026年7月",
         "author": "A"},
        10, multiline,
        add_text=lambda *args, **kwargs: text_calls.append((args, kwargs)),
        add_rect=lambda *args, **kwargs: rect_calls.append((args, kwargs)),
    )
    rendered_text = {args[5]: args for args, _kwargs in text_calls}
    organization = "組織A\n部門B\nチームC"
    owner = "担当A\n役割B"
    assert organization in rendered_text
    assert owner in rendered_text
    assert rendered_text[organization][4] > rendered_text[owner][4] > 0.30
    rail_rect = next(args for args, _kwargs in rect_calls if args[3] == 0.012)
    assert rail_rect[4] > 3.5

    too_many_owner_lines = parse_cover_footer_config({"cover": {
        "show_author": False,
        "show_rail": True,
        "rail": [{
            "label": "OWNER",
            "value": "1行目\n2行目\n3行目\n4行目",
        }],
    }})
    try:
        render_cover(
            None, {"title": "Title", "subtitle": "Subtitle"},
            {"title": "T", "footer": "F", "date": "D", "author": "A"},
            10, too_many_owner_lines,
            add_text=lambda *args, **kwargs: None,
            add_rect=lambda *args, **kwargs: None,
        )
    except ValueError as e:
        assert "3行以内" in str(e), str(e)
    else:
        raise AssertionError("OWNERの4行入力を拒否しませんでした")

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
        tmp_path = Path(tmp)
        image_path = tmp_path / "assets" / "cover.png"
        image_path.parent.mkdir()
        Image.new("RGB", (2000, 900), "#16324F").save(image_path)
        path = tmp_path / "cover_footer.json"
        path.write_text(json.dumps({
            "cover": {"background_image": "assets/cover.png"},
            "footer": {"show_text": False},
        }),
                        encoding="utf-8")
        loaded = load_cover_footer_config(path)
        assert loaded.footer.show_text is False
        assert loaded.cover.eyebrow == default.cover.eyebrow
        assert loaded.cover.background_image == image_path.resolve()
        _must_fail(
            {"cover": {"background_image": "assets/missing.png"}},
            "画像が見つかりません", base_dir=tmp_path,
        )
        _must_fail(
            {"cover": {"background_image": "cover.svg"}},
            "PNGまたはJPEG", base_dir=tmp_path,
        )

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        render_cover(
            slide, {"title": "Title", "subtitle": "Subtitle"},
            {"title": "T", "footer": "F", "date": "D", "author": "A"},
            10, loaded,
            add_text=lambda *args, **kwargs: None,
            add_rect=lambda *args, **kwargs: None,
        )
        picture = slide.shapes[0]
        assert picture.name == COVER_BACKGROUND_NAME
        assert picture.width == prs.slide_width
        assert picture.height == prs.slide_height
        assert picture.crop_left > 0
        assert picture.crop_left == picture.crop_right

    print("cover/footer tests passed")


if __name__ == "__main__":
    main()
