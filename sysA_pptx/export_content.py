"""content.pyのDECKをJSONに書き出す(システムB以降と共有)。"""
import json
from pathlib import Path

from content import DECK

out = Path(__file__).parent.parent / "content.json"
out.write_text(json.dumps(DECK, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes)")
