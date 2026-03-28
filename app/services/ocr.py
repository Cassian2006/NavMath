from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None


def extract_text_from_image(image_bytes: bytes) -> dict[str, Any]:
    if pytesseract is None:
        return {
            "text": "",
            "engine": "unavailable",
            "message": "未检测到 pytesseract 依赖，当前返回空识别结果。安装 Tesseract OCR 后可启用真实 OCR。",
        }

    image = Image.open(BytesIO(image_bytes))
    text = pytesseract.image_to_string(image, lang="eng+chi_sim")
    return {
        "text": text.strip(),
        "engine": "pytesseract",
        "message": "OCR 识别完成。",
    }
