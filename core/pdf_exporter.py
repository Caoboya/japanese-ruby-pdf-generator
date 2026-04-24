# -*- coding: utf-8 -*-

from pathlib import Path
import subprocess

from core.ruby_converter import text_file_to_paragraphs
from core.html_builder import build_html


def find_edge_path() -> Path | None:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def generate_pdf(txt_path: str, output_pdf: str, cfg: dict) -> None:
    txt_path = Path(txt_path.strip().strip('"')).resolve()
    output_pdf = Path(output_pdf.strip().strip('"')).resolve()

    if not txt_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{txt_path}")

    edge_path = find_edge_path()
    if not edge_path:
        raise FileNotFoundError("未找到 Microsoft Edge")

    content = text_file_to_paragraphs(txt_path)
    html_content = build_html(content, cfg, preview=False)

    temp_html = (txt_path.parent / "temp_print.html").resolve()
    temp_html.write_text(html_content, encoding="utf-8")

    cmd = [
        str(edge_path),
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={str(output_pdf)}",
        temp_html.as_uri()
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        temp_html.unlink(missing_ok=True)
    except Exception:
        pass

    if result.returncode != 0:
        raise RuntimeError(
            "Edge 生成 PDF 失败。\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"stderr:\n{result.stderr}"
        )

    if not output_pdf.exists():
        raise RuntimeError("PDF 未生成")