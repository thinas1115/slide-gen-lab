"""日本語テキストの実測折り返し・自動フィットエンジン。

PowerPointに置く前にPillowで游ゴシックの実寸を測り、
「テキストボックスから溢れない」ことを生成時点で保証する。
"""
import os
import re
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

if "WINDIR" not in os.environ:
    raise RuntimeError("游ゴシックの検出にはWindows環境が必要です")
FONT_DIR = Path(os.environ["WINDIR"]) / "Fonts"
FONT_PATHS = {
    "regular": str(FONT_DIR / "YuGothR.ttc"),
    "medium": str(FONT_DIR / "YuGothM.ttc"),
    "bold": str(FONT_DIR / "YuGothB.ttc"),
}

# pt -> px (96dpi)。PowerPoint実測はPillow計測より僅かに広く出ることが
# あるため安全係数を掛ける。
PT_TO_PX = 96 / 72
SAFETY = 1.08


@lru_cache(maxsize=64)
def _font(weight: str, size_pt: float) -> ImageFont.FreeTypeFont:
    px = max(4, round(size_pt * PT_TO_PX))
    return ImageFont.truetype(FONT_PATHS[weight], px, index=0)


def text_width_in(text: str, size_pt: float, weight: str = "regular") -> float:
    """文字列1行の幅をインチで返す(安全係数込み)。"""
    if not text:
        return 0.0
    f = _font(weight, size_pt)
    px = f.getlength(text)
    return px * SAFETY / 96.0


_BREAK_BEFORE = "、。，．）」』】”？！・：；"  # 行頭に来てはいけない文字
_BREAK_AFTER = "（「『【“"  # 行末に来てはいけない文字
_TITLE_TOKEN = re.compile(
    r"[A-Za-z0-9]+(?:[-./+_:][A-Za-z0-9]+)*|.", re.DOTALL)


def wrap_text(text: str, width_in: float, size_pt: float,
              weight: str = "regular") -> list[str]:
    """幅width_inに収まるよう禁則処理つきで折り返し、行のリストを返す。

    改行文字は強制改行として扱う。
    """
    lines: list[str] = []
    for para in text.split("\n"):
        lines.extend(_wrap_one(para, width_in, size_pt, weight))
    return lines or [""]


def balance_last_line(lines: list[str], width_in: float, size_pt: float,
                      weight: str = "regular",
                      min_ratio: float = 0.28) -> list[str]:
    """極端に短い最終行へ直前行の末尾を移し、タイトルの孤立語を防ぐ。"""
    if len(lines) < 2 or not lines[-1].strip():
        return list(lines)
    if text_width_in(lines[-1], size_pt, weight) >= width_in * min_ratio:
        return list(lines)

    result = list(lines)
    joined = result[-2] + result[-1]
    original_split = len(result[-2])
    for split in range(original_split - 1, 0, -1):
        left = joined[:split].rstrip()
        right = joined[split:].lstrip()
        if not left or not right:
            continue
        # 英単語や識別子の途中では分割しない。
        before = joined[split - 1]
        after = joined[split]
        if before.isascii() and after.isascii() \
                and before.isalnum() and after.isalnum():
            continue
        if right[0] in _BREAK_BEFORE or left[-1] in _BREAK_AFTER:
            continue
        right_w = text_width_in(right, size_pt, weight)
        if (right_w >= width_in * min_ratio
                and right_w <= width_in
                and text_width_in(left, size_pt, weight) <= width_in):
            result[-2:] = [left, right]
            return result
    return result


def wrap_title(text: str, width_in: float, size_pt: float,
               weight: str = "regular") -> list[str]:
    """英単語を分断せず、短い最終行も補正してタイトルを折り返す。"""
    lines: list[str] = []
    for para in text.split("\n"):
        lines.extend(_wrap_title_one(para, width_in, size_pt, weight))
    return balance_last_line(
        lines or [""], width_in, size_pt, weight, min_ratio=0.28)


def _wrap_title_one(para: str, width_in: float, size_pt: float,
                    weight: str) -> list[str]:
    if not para:
        return [""]
    lines = []
    cur = ""
    for token in _TITLE_TOKEN.findall(para):
        candidate = cur + token
        if text_width_in(candidate, size_pt, weight) <= width_in or not cur:
            cur = candidate
            if text_width_in(cur, size_pt, weight) <= width_in:
                continue
            split_token = _wrap_one(cur, width_in, size_pt, weight)
            lines.extend(split_token[:-1])
            cur = split_token[-1]
            continue
        if token.isspace():
            lines.append(cur.rstrip())
            cur = ""
            continue
        if len(token) == 1 and token in _BREAK_BEFORE:
            cur += token
            lines.append(cur.rstrip())
            cur = ""
            continue
        if cur and cur[-1] in _BREAK_AFTER:
            opener = cur[-1]
            lines.append(cur[:-1].rstrip())
            cur = opener + token.lstrip()
        else:
            lines.append(cur.rstrip())
            cur = token.lstrip()
        if text_width_in(cur, size_pt, weight) > width_in:
            split_token = _wrap_one(cur, width_in, size_pt, weight)
            lines.extend(split_token[:-1])
            cur = split_token[-1]
    if cur:
        lines.append(cur.rstrip())
    return [line for line in lines if line != ""] or [""]


def _wrap_one(para: str, width_in: float, size_pt: float, weight: str) -> list[str]:
    if not para:
        return [""]
    lines = []
    cur = ""
    for ch in para:
        if text_width_in(cur + ch, size_pt, weight) <= width_in or not cur:
            cur += ch
            continue
        # 禁則: 句読点等は前の行に食い込ませる
        if ch in _BREAK_BEFORE:
            cur += ch
            lines.append(cur)
            cur = ""
        elif cur and cur[-1] in _BREAK_AFTER:
            lines.append(cur[:-1])
            cur = cur[-1] + ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def line_height_in(size_pt: float, spacing: float = 1.3) -> float:
    """1行の高さ(インチ)。PowerPointの行送り(倍率spacing)相当。"""
    return size_pt * spacing / 72.0


def fit_font_size(text: str, box_w_in: float, box_h_in: float,
                  max_pt: float, min_pt: float = 10.0,
                  weight: str = "regular", spacing: float = 1.3,
                  pad_in: float = 0.0, wrapper=None) -> tuple[float, list[str]]:
    """ボックス(幅x高さ)に収まる最大フォントサイズと折り返し結果を返す。

    min_ptまで縮めても入らない場合はmin_ptの結果を返す(呼び出し側で
    行数超過を検知してコンテンツを削る判断をする)。
    """
    w = box_w_in - pad_in * 2
    h = box_h_in - pad_in * 2
    wrapper = wrapper or wrap_text
    size = max_pt
    while size >= min_pt:
        lines = wrapper(text, w, size, weight)
        if len(lines) * line_height_in(size, spacing) <= h:
            return size, lines
        size -= 0.5
    return min_pt, wrapper(text, w, min_pt, weight)


def fits(text: str, box_w_in: float, box_h_in: float, size_pt: float,
         weight: str = "regular", spacing: float = 1.3,
         pad_in: float = 0.0) -> bool:
    """指定サイズで収まるかの判定。"""
    w = box_w_in - pad_in * 2
    lines = wrap_text(text, w, size_pt, weight)
    return len(lines) * line_height_in(size_pt, spacing) <= box_h_in - pad_in * 2
