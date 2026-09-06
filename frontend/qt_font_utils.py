"""Шрифты Qt: после QSS с font-size в px у QFont часто pointSize() == -1 — это даёт предупреждения и глюки."""
from __future__ import annotations

from PySide6.QtGui import QFont


def safe_derived_font(base: QFont, default_point: int = 10) -> QFont:
    """
    Копия шрифта с гарантированно допустимым размером (point или pixel), без «пустого» pointSize.
    """
    out = QFont(base)
    if out.pointSize() > 0:
        return out
    px = out.pixelSize()
    if px > 0:
        out = QFont()
        out.setFamily(base.family() or "Segoe UI")
        out.setWeight(base.weight())
        out.setItalic(base.italic())
        out.setPixelSize(max(1, px))
        return out
    fam = base.family()
    if not fam:
        fam = "Segoe UI"
    clean = QFont(fam)
    clean.setPointSize(max(1, default_point))
    return clean
