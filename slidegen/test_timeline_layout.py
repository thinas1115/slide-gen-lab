"""roadmap系の期間解決・自動レーン・段階的収容を検証する。"""
from copy import deepcopy

from layout_fit import FitError
from timeline_layout import (fit_program_roadmap, fit_roadmap, pack_activities,
                             resolve_marker, resolve_span)
from validate_content import validate


def _must_fail(fn, expected):
    try:
        fn()
    except (FitError, ValueError) as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError("過密または不正な入力を拒否しませんでした")


def main():
    periods = ["4月", "5月", "6月", "7月"]
    assert resolve_span({"start": 0, "end": 2}, periods) == (0.0, 2.0)
    assert resolve_span({"start": "5月", "end": "6月"}, periods) == (1.0, 3.0)
    assert resolve_marker("6月", periods) == 2.5
    _must_fail(
        lambda: resolve_span({"start": "4月", "end": "不明"}, periods),
        "期間一覧にありません",
    )

    placements, lane_count = pack_activities([
        {"label": "A", "start": "4月", "end": "6月"},
        {"label": "B", "start": "5月", "end": "7月"},
        {"label": "C", "start": "7月", "end": "7月"},
    ], periods)
    assert lane_count == 2
    assert [placement.lane for placement in placements] == [0, 1, 0]

    assert fit_roadmap(5.27, 3).stage == "standard"
    assert fit_roadmap(5.27, 6).stage == "gap"
    assert fit_roadmap(4.57, 6).stage == "element"
    _must_fail(lambda: fit_roadmap(3.70, 6), "最小設定")

    assert fit_program_roadmap(5.27, [1, 2, 1]).stage == "standard"
    assert fit_program_roadmap(4.40, [2, 2, 4, 1, 1]).stage == "gap"
    assert fit_program_roadmap(4.80, [3, 3, 3, 3, 3]).stage == "element"
    _must_fail(
        lambda: fit_program_roadmap(5.27, [4, 4, 4, 4, 4, 4]),
        "最小設定",
    )

    deck = {
        "meta": {"title": "検証", "footer": "検証", "date": "2026年7月",
                 "author": "検証担当"},
        "slides": [{
            "type": "program_roadmap", "kicker": "検証", "title": "工程表",
            "periods": periods,
            "tracks": [{"name": "テーマ", "activities": [
                {"label": "作業", "start": "4月", "end": "6月"},
            ]}],
        }],
    }
    assert not validate(deck)
    invalid = deepcopy(deck)
    invalid["slides"][0]["tracks"][0]["activities"][0]["end"] = "不明"
    assert any("期間一覧にありません" in error for error in validate(invalid))

    print("timeline layout tests passed")


if __name__ == "__main__":
    main()
