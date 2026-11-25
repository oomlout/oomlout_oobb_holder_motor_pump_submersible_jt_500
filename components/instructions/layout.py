"""Small adapter for the vendored Oomlout wave-drive booklet compositor."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def panel_geometry(**kwargs):
    style = kwargs["style"]
    width, height = style["page_mm"]
    columns, rows = style["columns"], style["rows"]
    margin, gap = style["margin_mm"], style["gutter_mm"]
    return ((width - 2 * margin - (columns - 1) * gap) / columns,
            (height - 2 * margin - (rows - 1) * gap) / rows)
