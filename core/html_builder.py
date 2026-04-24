# -*- coding: utf-8 -*-


def build_html(content: str, cfg: dict, preview: bool = False) -> str:
    body_class = "preview" if preview else ""
    page_start = '<div class="page">' if preview else ""
    page_end = "</div>" if preview else ""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Ruby Output</title>
<style>
    @page {{
        size: A4;
        margin: {cfg["page_margin"]};
    }}

    body {{
        font-family: "Yu Mincho", "MS Mincho", "Hiragino Mincho ProN", serif;
        font-size: {cfg["body_font_size"]};
        line-height: {cfg["line_height"]};
        margin: {cfg["body_margin"]};
        background: white;
        color: black;
        word-break: break-word;
    }}

    body.preview {{
        background: #f3f3f3;
        padding: 20px 0;
        margin: 0;
    }}

    .page {{
        width: 210mm;
        min-height: 297mm;
        margin: 0 auto;
        background: white;
        box-shadow: 0 0 8px rgba(0,0,0,0.18);
        padding: 12mm;
        box-sizing: border-box;
    }}

    p {{
        margin: 0 0 1.2em 0;
        text-align: justify;
    }}

    ruby {{
        ruby-align: center;
        ruby-position: over;
    }}

    rt {{
        font-size: {cfg["ruby_font_size"]};
        color: #444;
    }}
</style>
</head>
<body class="{body_class}">
{page_start}
{content}
{page_end}
</body>
</html>
"""