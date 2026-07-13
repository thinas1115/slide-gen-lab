"""content.json を入力にしてPPTXを生成する。

使い方:
  python sysA_pptx/generate_from_json.py content.json out/from_json.pptx
"""
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

import generate
from diagrams import s_aws, s_hub, s_org
from diagrams2 import s_matrix, s_process, s_roadmap
from diagrams3 import s_aws2


RENDER = dict(generate.RENDER,
              aws=s_aws, hub=s_hub, org=s_org,
              process=s_process, roadmap=s_roadmap, matrix=s_matrix,
              aws2=s_aws2)


def main(json_path, out_path):
    deck = json.loads(Path(json_path).read_text(encoding="utf-8"))
    generate.DECK = deck

    prs = Presentation()
    prs.slide_width = Inches(generate.SLIDE_W)
    prs.slide_height = Inches(generate.SLIDE_H)
    blank = prs.slide_layouts[6]
    for idx, spec in enumerate(deck["slides"], 1):
        slide = prs.slides.add_slide(blank)
        try:
            renderer = RENDER[spec["type"]]
        except KeyError as e:
            known = ", ".join(sorted(RENDER))
            raise SystemExit(f"unknown slide type: {spec['type']!r}. known: {known}") from e
        renderer(slide, spec, idx)
        if spec["type"] != "title":
            generate.footer(slide, idx)
    prs.save(out_path)
    print(f"saved: {out_path} ({len(deck['slides'])} slides)")


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "content.json",
        sys.argv[2] if len(sys.argv) > 2 else "out/from_json.pptx",
    )
