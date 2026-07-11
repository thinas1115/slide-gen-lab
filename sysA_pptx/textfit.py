"""日本語テキストの実測折り返し・自動フィットエンジン。

PowerPointに置く前にPillowで游ゴシックの実寸を測り、
「テキストボックスから溢れない」ことを生成時点で保証する。
"""
from functools import lru_cache

from PIL import ImageFont

FONT_PATHS = {
    "regular": r"C:\Windows\Fonts\YuGothR.ttc",
    "medium": r"C:\Windows\Fonts\YuGothM.ttc",
    "bold": r"C:\Windows\Fonts\YuGothB.ttc",
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


def wrap_text(text: str, width_in: float, size_pt: float,
              weight: str = "regular") -> list[str]:
    """幅width_inに収まるよう禁則処理つきで折り返し、行のリストを返す。

    改行文字は強制改行として扱う。
    """
    lines: list[str] = []
    for para in text.split("\n"):
        lines.extend(_wrap_one(para, width_in, size_pt, weight))
    return lines or [""]


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
                  pad_in: float = 0.0) -> tuple[float, list[str]]:
    """ボックス(幅x高さ)に収まる最大フォントサイズと折り返し結果を返す。

    min_ptまで縮めても入らない場合はmin_ptの結果を返す(呼び出し側で
    行数超過を検知してコンテンツを削る判断をする)。
    """
    w = box_w_in - pad_in * 2
    h = box_h_in - pad_in * 2
    size = max_pt
    while size >= min_pt:
        lines = wrap_text(text, w, size, weight)
        if len(lines) * line_height_in(size, spacing) <= h:
            return size, lines
        size -= 0.5
    return min_pt, wrap_text(text, w, min_pt, weight)


def fits(text: str, box_w_in: float, box_h_in: float, size_pt: float,
         weight: str = "regular", spacing: float = 1.3,
         pad_in: float = 0.0) -> bool:
    """指定サイズで収まるかの判定。"""
    w = box_w_in - pad_in * 2
    lines = wrap_text(text, w, size_pt, weight)
    return len(lines) * line_height_in(size_pt, spacing) <= box_h_in - pad_in * 2
