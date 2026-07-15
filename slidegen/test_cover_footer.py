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


def _must_fail(data, expected, **kwargs):
    try:
        parse_cover_footer_config(data, **kwargs)
    except ValueError as e:
        assert expected in str(e), str(e)
    else:
        raise AssertionError(f"ValueErrorになりませんでした: {data}")


def main():
    default = parse_cover_footer_config({})
    assert default.cover.eyebrow == "SLIDE PATTERN LIBRARY"
    assert default.cover.background_image is None
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
