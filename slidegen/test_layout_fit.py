"""段階的収容ポリシーの単体検証。"""
from layout_fit import FitError, fit_text_or_raise, select_fit, stepped


def main():
    assert list(stepped(1.0, 0.8, 0.1)) == [1.0, 0.9, 0.8]

    result = select_fit(
        "sample", 4.0,
        [
            ("standard", {"gap": 0.5}, 4.3),
            ("gap", {"gap": 0.3}, 3.9),
            ("scale", {"gap": 0.3, "size": 0.5}, 3.6),
        ],
        guidance="項目を減らしてください。",
    )
    assert result.stage == "gap"
    assert result.values["gap"] == 0.3

    result = select_fit(
        "sample", 3.7,
        [
            ("standard", {"gap": 0.5}, 4.3),
            ("gap", {"gap": 0.3}, 3.9),
            ("scale", {"gap": 0.3, "size": 0.5}, 3.6),
        ],
        guidance="項目を減らしてください。",
    )
    assert result.stage == "scale"
    assert result.values["size"] == 0.5

    size, lines = fit_text_or_raise(
        "sample", "body", "短い本文", 2.0, 0.5, 14, min_pt=11,
    )
    assert size == 14
    assert len(lines) == 1

    try:
        fit_text_or_raise(
            "sample", "body", "長い本文" * 100, 1.0, 0.2, 14,
            min_pt=11,
        )
    except FitError as e:
        assert "不足" in str(e)
        assert "文言を短く" in str(e)
    else:
        raise AssertionError("過密テキストを拒否しませんでした")

    print("layout fit tests passed")


if __name__ == "__main__":
    main()
