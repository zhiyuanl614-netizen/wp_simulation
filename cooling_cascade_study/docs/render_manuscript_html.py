#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渲染脚本：论文完整版.md → 论文完整版.html（单文件自包含版）。

特性：
  - 全部 14 张图片以 data URI 内嵌（SVG/PNG），无外部依赖；
  - MathJax v3（tex-svg，SVG 输出无需字体文件）整包内嵌，行内 $...$ 与显示 $$...$$ 均可渲染；
  - 代码跨与公式先占位保护再恢复，杜绝 markdown 对下标/星号的误解析；
  - 图片与表 1–6 自动包 <figure>/<figcaption>；生成 h1/h2 目录锚点；打印分页。
用法：python3 docs/render_manuscript_html.py
"""
import base64
import html
import re
import sys
import urllib.request
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "论文完整版.md"
OUT = ROOT / "论文完整版.html"
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"
TODAY = "2026-09-07"

EXPECT = {"img": 14, "table": 9, "figure": 20}  # 14 图 + 表 1–6（另 ch2 3 张不占号结构表）


def main():
    md_text = SRC.read_text(encoding="utf-8")

    # ---------- 1) 占位保护：代码跨 → 显示公式 → 行内公式 ----------
    store = []  # ('code'|'block'|'inline', raw_text)

    def stash(kind, raw):
        store.append((kind, raw))
        return f"⟦MJ{len(store) - 1}⟧"

    tmp = re.sub(r"`([^`\n]+)`", lambda m: stash("code", m.group(0)), md_text)
    assert "`" not in tmp, "存在未成对的反引号"
    tmp = re.sub(r"\$\$[\s\S]+?\$\$", lambda m: stash("block", m.group(0)), tmp)
    tmp = re.sub(r"\$[^$\n]+\$", lambda m: stash("inline", m.group(0)), tmp)
    assert "$" not in tmp, "公式提取后仍残留孤立 $（配对异常）"
    n_block = sum(1 for k, _ in store if k == "block")
    n_inline = sum(1 for k, _ in store if k == "inline")
    n_code = sum(1 for k, _ in store if k == "code")

    # ---------- 2) Markdown 渲染 ----------
    md = MarkdownIt("commonmark").enable("table")
    body = md.render(tmp)

    # ---------- 3) 恢复占位 ----------
    def unstash(m):
        kind, raw = store[int(m.group(1))]
        esc = html.escape(raw, quote=False)
        if kind == "code":
            return "<code>" + esc[1:-1] + "</code>"  # 去反引号
        return esc

    body = re.sub(r"⟦MJ(\d+)⟧", unstash, body)
    assert "⟦" not in body, "占位符未全部恢复"

    # ---------- 4) 图片 → data URI ----------
    def to_data_uri(rel):
        p = ROOT / rel
        mime = "image/svg+xml" if rel.endswith(".svg") else "image/png"
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"

    n_img = [0]

    def img_sub(m):
        n_img[0] += 1
        return 'src="' + to_data_uri(m.group(1)) + '"'

    body = re.sub(r'src="(figures/[^"]+)"', img_sub, body)

    # ---------- 5) figure/figcaption 包装 ----------
    n_fig_img = [0]
    n_fig_tab = [0]

    def wrap_img(m):
        n_fig_img[0] += 1
        return (f'<figure><img src="{m.group(1)}" alt="图{m.group(2)}">'
                f"<figcaption>{m.group(3)}</figcaption></figure>")

    body = re.sub(
        r'<p><img src="([^"]+)" alt="图(\d+)"\s*/></p>\s*<p>(<strong>图 \2　[\s\S]*?)</p>',
        wrap_img, body)

    def wrap_tab(m):
        n_fig_tab[0] += 1
        return f'<figure class="tab"><figcaption>{m.group(1)}</figcaption>{m.group(3)}</figure>'

    body = re.sub(
        r"<p>(<strong>表 (\d+)[\s\S]*?</strong>.*?)</p>\s*(<table>[\s\S]*?</table>)",
        wrap_tab, body)

    # ---------- 6) 标题 id 与目录 ----------
    entries = []

    def add_id(m):
        level, text = m.group(1), m.group(2)
        entries.append((level, text))
        return f'<{level} id="sec-{len(entries) - 1}">{text}</{level}>'

    body = re.sub(r"<(h[12])>([^<]*)</\1>", add_id, body)
    toc_lis, open_sub, h1_open = [], False, False
    for level, text in entries[1:]:  # 跳过论文题目
        idx = entries.index((level, text))
        if level == "h1":
            if open_sub:
                toc_lis.append("</ul>")
                open_sub = False
            if h1_open:
                toc_lis.append("</li>")
            toc_lis.append(f'<li class="c"><a href="#sec-{idx}">{text}</a>')
            h1_open = True
        else:
            if not open_sub:
                toc_lis.append("<ul>")
                open_sub = True
            toc_lis.append(f'<li><a href="#sec-{idx}">{text}</a></li>')
    if open_sub:
        toc_lis.append("</ul>")
    if h1_open:
        toc_lis.append("</li>")
    toc_html = ('<nav class="toc"><div class="toc-title">目录 Contents</div><ul>'
                + "".join(toc_lis) + "</ul></nav>")
    # 目录插到"摘要"标题之前
    abs_idx = body.index('<h1 id="sec-1">')
    body = body[:abs_idx] + toc_html + "\n" + body[abs_idx:]

    # 题头包装
    body = re.sub(
        r'^<h1 id="sec-0">([^<]+)</h1>\n<p><em>([^<]+)</em></p>',
        r'<header class="title"><h1 id="sec-0">\1</h1><p class="en">\2</p></header>',
        body, count=1)

    # ---------- 7) 参考文献悬挂缩进 ----------
    m = re.search(r'(<h1 id="sec-\d+">参考文献 References</h1>)([\s\S]*?)(<h1 id=)', body)
    assert m, "未找到参考文献小节"
    body = body[:m.start(2)] + m.group(2).replace("<p>[", '<p class="ref">[') + body[m.end(2):]

    # ---------- 8) MathJax ----------
    try:
        mj = urllib.request.urlopen(MATHJAX_URL, timeout=40).read().decode("utf-8")
        mj = mj.replace("</script>", "<\\/script>")
        mathjax_tags = (
            "<script>window.MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']]},"
            "options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']},"
            "svg:{fontCache:'global'}};</script>\n<script>" + mj + "</script>"
        )
        mj_note = "MathJax v3 (tex-svg) 已内嵌"
    except Exception as e:  # 离线兜底：公式以原文呈现
        mathjax_tags = ""
        mj_note = f"!! MathJax 下载失败（{e}），公式将以原文显示"

    # ---------- 9) 模板 ----------
    css = """
:root{--ink:#1c1c1c;--accent:#0f4c5c;--line:#c9d4d6;}
html{font-size:15.5px;}
body{font-family:'Source Han Serif SC','Noto Serif SC','Songti SC','STSong',SimSun,serif;
  line-height:1.78;color:var(--ink);max-width:880px;margin:0 auto;padding:1.5rem 1.4rem 4rem;}
header.title{text-align:center;margin:1.5rem 0 .5rem;}
header.title h1{font-size:1.55em;border:none;margin:.2rem 0;color:#111;}
header.title .en{font-style:italic;color:#555;text-align:center;margin:.2rem 0 1rem;}
blockquote{border-left:3px solid #9db4b8;background:#f4f7f7;color:#445;
  margin:1em 0;padding:.5em 1em;font-size:.9em;}
h1{font-size:1.42em;color:var(--accent);border-bottom:2px solid var(--accent);
  padding-bottom:.22em;margin:2.3em 0 .8em;}
h2{font-size:1.2em;margin:1.9em 0 .7em;}
h3{font-size:1.06em;margin:1.5em 0 .6em;color:#333;}
p{margin:.75em 0;text-align:justify;}
a{color:var(--accent);}
table{border-collapse:collapse;width:100%;font-size:.86em;margin:.6em 0;}
th,td{border:1px solid var(--line);padding:.32em .5em;text-align:left;vertical-align:top;}
th{background:#eaf1f2;}
tbody tr:nth-child(even){background:#f8fbfb;}
figure{margin:1.5em 0;text-align:center;break-inside:avoid;}
figure img{max-width:100%;height:auto;}
figcaption{font-size:.85em;color:#3a3a3a;text-align:justify;margin-top:.55em;
  border-left:3px solid var(--accent);padding-left:.75em;}
figure.tab{break-inside:auto;}
figure.tab figcaption{margin-bottom:.5em;}
code{font-family:ui-monospace,'Cascadia Mono',Consolas,monospace;font-size:.86em;
  background:#f1f3f3;padding:.08em .3em;border-radius:3px;}
p.ref{text-indent:-2.4em;padding-left:2.4em;margin:.4em 0;font-size:.92em;text-align:justify;}
nav.toc{background:#f6f9f9;border:1px solid #dbe4e5;border-radius:6px;
  padding:1em 1.6em;margin:1.6em 0;font-size:.92em;}
nav.toc .toc-title{font-weight:bold;color:var(--accent);margin-bottom:.4em;}
nav.toc ul{list-style:none;padding-left:0;margin:0;}
nav.toc ul ul{padding-left:1.6em;margin:.15em 0;}
nav.toc li{margin:.14em 0;}
nav.toc li.c{font-weight:600;}
nav.toc a{text-decoration:none;color:#20505c;}
nav.toc a:hover{text-decoration:underline;}
footer{margin-top:3em;border-top:1px solid var(--line);padding-top:.6em;
  font-size:.8em;color:#888;text-align:center;}
mjx-container{overflow-x:auto;overflow-y:hidden;max-width:100%;}
@media print{
  body{max-width:100%;padding:0;}
  h1{break-before:page;}
  header.title h1{break-before:auto;}
  nav.toc{display:none;}
  figure{break-inside:avoid;}
}
"""
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>基于早期预警的冷却水耦合水-电信息物理系统韧性提升（论文完整版）</title>
<style>{css}</style>
</head>
<body>
{body}
<footer>论文完整版 · 合稿 v2（语言润色，{TODAY}）· 由 docs/render_manuscript_html.py 自包含渲染（图片与 MathJax 均内嵌，可离线查看/打印）</footer>
{mathjax_tags}
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")

    # ---------- 10) 校验 ----------
    problems = []
    if n_img[0] != EXPECT["img"]:
        problems.append(f"内嵌图片 {n_img[0]} ≠ {EXPECT['img']}")
    if body.count("<table>") != EXPECT["table"]:
        problems.append(f"表格数 {body.count('<table>')} ≠ {EXPECT['table']}")
    if n_fig_img[0] != EXPECT["img"]:
        problems.append(f"图 figure 包装 {n_fig_img[0]} ≠ {EXPECT['img']}")
    if n_fig_tab[0] != 6:
        problems.append(f"表 figure 包装 {n_fig_tab[0]} ≠ 6")
    if body.count("<figure") != EXPECT["figure"]:
        problems.append(f"figure 总数 {body.count('<figure>')} ≠ {EXPECT['figure']}")
    if problems:
        print("!! 渲染校验未通过：")
        for p in problems:
            print("   -", p)
        sys.exit(1)

    print("=== HTML 渲染完成 ===")
    print(f"输出：{OUT.relative_to(ROOT)}（{OUT.stat().st_size / 1e6:.2f} MB）")
    print(f"公式：显示块 {n_block} + 行内 {n_inline}；代码跨 {n_code}；{mj_note}")
    print(f"图片内嵌 {n_img[0]}；表格 {body.count('<table>')}（含 figure 包装：图 {n_fig_img[0]}＋表 {n_fig_tab[0]}）")
    print(f"目录条目：h1×{sum(1 for l, _ in entries if l == 'h1')}＋h2×{sum(1 for l, _ in entries if l == 'h2')}")


if __name__ == "__main__":
    main()
