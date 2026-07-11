"""textfitの動作確認。結果をUTF-8ファイルに出力する。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from textfit import fit_font_size, fits, text_width_in, wrap_text

out = []
w = text_width_in("生成AIスライド調査報告", 24, "bold")
out.append(f"width(11chars,24pt,bold) = {w:.3f} in")
assert 2.5 < w < 5.0, "幅が想定レンジ外"

lines = wrap_text("どのツールでも生成後に15〜30分の手作業調整が必須という実測結果。", 3.0, 14)
out.append("wrap 3.0in/14pt:")
for l in lines:
    lw = text_width_in(l, 14)
    out.append(f"  [{lw:.2f}in] {l}")
    assert lw <= 3.0 + 0.01, f"行が幅超過: {l}"
# 行頭禁則: 「。」「、」で始まる行がないこと
assert not any(l and l[0] in "、。" for l in lines), "行頭禁則違反"

size, flines = fit_font_size("社内テンプレート準拠の現実解を検証する", 2.5, 1.0, 20)
out.append(f"fit -> {size}pt, {len(flines)} lines: {flines}")
assert fits("社内テンプレート準拠の現実解を検証する", 2.5, 1.0, size)

out.append("ALL OK")
print("\n".join(out))
