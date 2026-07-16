"""同梱画像資産の配置と互換パス解決。"""
from pathlib import Path


ASSET_DIR = Path(__file__).parent / "assets"
ICON_DIR = ASSET_DIR / "icons"
AWS_ICON_DIR = ICON_DIR / "aws"
FLUENT_ICON_DIR = ICON_DIR / "fluent"


def resolve_icon_path(icon: str) -> Path:
    """アイコン指定をassets配下の実ファイルパスへ変換する。

    正規表記は ``icons/aws/...`` / ``icons/fluent/...``。既存content.jsonとの
    互換性のため、AWSの裸ファイル名と旧 ``fluent/...`` も受け付ける。
    """
    raw = Path(icon)
    if raw.is_absolute() or not raw.parts:
        raise ValueError("アイコンはslidegen/assets内の相対パスで指定してください")

    if raw.parts[0] == "fluent":
        candidate = FLUENT_ICON_DIR.joinpath(*raw.parts[1:])
    elif raw.parts[0] == "aws":
        candidate = AWS_ICON_DIR.joinpath(*raw.parts[1:])
    elif len(raw.parts) == 1:
        candidate = AWS_ICON_DIR / raw
    else:
        candidate = ASSET_DIR / raw

    resolved = candidate.resolve()
    try:
        resolved.relative_to(ASSET_DIR.resolve())
    except ValueError as exc:
        raise ValueError(
            "アイコンはslidegen/assets内の相対パスで指定してください"
        ) from exc
    return resolved
