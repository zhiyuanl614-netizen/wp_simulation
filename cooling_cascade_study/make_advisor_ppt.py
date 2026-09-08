# -*- coding: utf-8 -*-
"""生成导师汇报 PPT（为什么做 / 怎么做 / 预期结果 / 计划与请求）。
用法：python3 make_advisor_ppt.py  →  导师汇报_研究介绍.pptx
口径与 导师汇报_方法与结果.md（e8d6552）及论文完整版 v2（6efabc8）一致。
"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = lambda f: os.path.join(HERE, "figures", f)
OUT = os.path.join(HERE, "导师汇报_研究介绍.pptx")

# ---------- 样式常量 ----------
FONT_LATIN, FONT_EA = "Microsoft YaHei", "微软雅黑"
NAVY, TEAL, ORANGE, GRAY = "1F4E79", "0E7490", "D97706", "6B7280"
RED, GREEN, INK = "B03A2E", "1E7B45", "2B2B2B"
COVER_BG, COVER_SUB = "17375E", "A8C4E0"
LIGHT_B, LIGHT_O, LIGHT_G, LIGHT_R = "EAF1F8", "FDF3E7", "EAF3EC", "FBEAEA"
LINE_GRAY = "D5DBE3"
SEC = {"why": ORANGE, "how": NAVY, "what": TEAL, "plan": GRAY}
CHIP_TXT = {"why": "为什么做 WHY", "how": "怎么做 HOW", "what": "预期结果 WHAT", "plan": "计划 PLAN"}

SW, SH = 13.333, 7.5  # 幻灯片尺寸（英寸，16:9）
MX = 0.55             # 左右页边距
CW = SW - 2 * MX      # 内容宽度 12.233


def C(hexstr):
    return RGBColor.from_string(hexstr)


def style_run(r, size=13, bold=False, color=INK):
    f = r.font
    f.name, f.size, f.bold = FONT_LATIN, Pt(size), bold
    f.color.rgb = C(color)
    rPr = r._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
    ea.set("typeface", FONT_EA)


ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
ANCHOR = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}


def add_text(slide, x, y, w, h, paras, anchor="t", wrap=True):
    """paras: [ (runs, opts) ]，runs=[(text,size,bold,color)]，opts=dict(align,sb,sa)"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = ANCHOR[anchor]
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (runs, opts) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ALIGN[opts.get("align", "l")]
        p.space_before = Pt(opts.get("sb", 0))
        p.space_after = Pt(opts.get("sa", 0))
        if opts.get("lh"):
            p.line_spacing = opts["lh"]
        for (t, s, b, c) in runs:
            r = p.add_run()
            r.text = t
            style_run(r, s, b, c)
    return tb


def add_box(slide, x, y, w, h, fill=None, line=None, line_w=1.0,
            shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = C(fill)
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = C(line)
        sp.line.width = Pt(line_w)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE and radius is not None:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    sp.text_frame.word_wrap = True
    return sp


def add_img(slide, path, x, y, max_w, max_h, caption=None):
    iw, ih = Image.open(path).size
    ar = iw / ih
    w = max_w
    h = w / ar
    if h > max_h:
        h, w = max_h, max_h * ar
    slide.shapes.add_picture(path, Inches(x + (max_w - w) / 2),
                             Inches(y + (max_h - h) / 2), Inches(w), Inches(h))
    if caption:
        add_text(slide, x, y + max_h + 0.06, max_w, 0.4,
                 [([(caption, 10.5, False, GRAY)], dict(align="c"))])


def new_slide(prs, title, sec=None, page=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if title is not None:
        add_box(s, MX, 0.38, 0.13, 0.52, fill=SEC.get(sec, NAVY), radius=None,
                shape=MSO_SHAPE.RECTANGLE)
        add_text(s, MX + 0.28, 0.34, 9.6, 0.62,
                 [([(title, 21, True, NAVY)], dict())], anchor="m")
        if sec:
            chip = add_box(s, SW - MX - 2.05, 0.40, 2.05, 0.46, fill=SEC[sec], radius=0.5)
            tf = chip.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.vertical_anchor = ANCHOR["m"]
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = CHIP_TXT[sec]
            style_run(r, 11.5, True, "FFFFFF")
    if page is not None:
        add_text(s, MX, 7.14, 9.0, 0.3,
                 [([("冷却水耦合水-电 CPS 早期预警韧性研究 · 2026-09", 9, False, GRAY)], dict())])
        add_text(s, SW - 1.35, 7.14, 0.8, 0.3,
                 [([(str(page), 10, False, GRAY)], dict(align="r"))])
    return s


def bullets(slide, x, y, w, h, items, size=12.5, gap=5, color=INK, lh=1.12):
    """items: [ (前缀符号, [(text,bold,color)...] 或 str) ]"""
    paras = []
    for mark, content in items:
        runs = [(mark + " ", size, True, NAVY)]
        if isinstance(content, str):
            runs.append((content, size, False, color))
        else:
            for (t, b, c) in content:
                runs.append((t, size, b, c))
        paras.append((runs, dict(sa=gap, lh=lh)))
    return add_text(slide, x, y, w, h, paras)


def header_card(slide, x, y, w, title, sub, accent):
    add_box(slide, x, y, w, 0.52, fill=accent, radius=0.14)
    add_text(slide, x + 0.18, y, w - 0.36, 0.52,
             [([(title, 14.5, True, "FFFFFF")], dict())], anchor="m")
    if sub:
        add_text(slide, x + 0.18, y + 0.60, w - 0.36, 0.4,
                 [([(sub, 11, False, GRAY)], dict())])


# ============================================================
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
prs.core_properties.title = "基于早期预警的冷却水耦合水-电信息物理系统韧性提升"
prs.core_properties.author = "课题组"

# ---------- S1 封面 ----------
s = new_slide(prs, None)
add_box(s, 0, 0, SW, SH, fill=COVER_BG, radius=None, shape=MSO_SHAPE.RECTANGLE)
add_box(s, 0.9, 2.42, 1.7, 0.07, fill=ORANGE, radius=None, shape=MSO_SHAPE.RECTANGLE)
add_text(s, 0.9, 1.45, 11.5, 0.5,
         [([("课题组研究汇报 · 2026 年 9 月", 14, False, COVER_SUB)], dict())])
add_text(s, 0.9, 2.72, 11.8, 1.7,
         [([("基于早期预警的冷却水耦合", 30, True, "FFFFFF")], dict(sa=4)),
          ([("水-电信息物理系统韧性提升", 30, True, "FFFFFF")], dict())])
add_text(s, 0.9, 4.28, 11.8, 0.45,
         [([("Early-warning-based resilience enhancement of cooling-water-coupled "
             "water–power cyber-physical systems", 12.5, False, COVER_SUB)], dict())])
chips = [("01", "为什么做", "why"), ("02", "怎么做", "how"),
         ("03", "预期结果", "what"), ("04", "计划与请求", "plan")]
for i, (num, lab, key) in enumerate(chips):
    cx = 0.9 + i * 2.96
    add_box(s, cx, 5.15, 2.72, 0.95, fill=SEC[key], radius=0.12)
    add_text(s, cx + 0.2, 5.15, 2.32, 0.95,
             [([(num + "  ", 17, True, "FFFFFF")], dict()),
              ([(lab, 14, True, "FFFFFF")], dict())], anchor="m")
add_text(s, 0.9, 6.65, 11.8, 0.4,
         [([("冷却水全过程建模 · 三域三级跨域预警 · LP 主动控制 · 能力边界划界", 12, False, COVER_SUB)], dict())])

# ---------- S2 提纲 ----------
s = new_slide(prs, "汇报提纲", sec=None, page=2)
rows = [
    ("01", "why", "为什么做",
     "现实风险与研究缺口：气候让冷却水稀缺、城市供水事故构成共因失效；既有研究以“一条耦合边”留下三个“不知道”"),
    ("02", "how", "怎么做",
     "五层白箱建模链（市政 B / 冷却 W / 机电 A / 信息 I / 电力 C）＋三域三级跨域预警＋LP 主动控制；IEEE-118 × D-town 全耦合案例与四轴敏感性实验"),
    ("03", "what", "预期结果",
     "三问三答：时间差多大？能否转化为韧性？边界在哪？＋跨域洞见：水-电场景的韧性瓶颈自“信息速度”转移至“备用与网络输送”（结果均已经仿真验证）"),
    ("04", "plan", "完成度与计划",
     "中文全文已成稿（8 章 / 图 14 / 表 6）；投稿计划（首选 RESS）；四项支持请求"),
]
for i, (num, key, head, desc) in enumerate(rows):
    y = 1.42 + i * 1.38
    add_box(s, MX, y, 0.78, 0.78, fill=SEC[key], radius=0.16)
    add_text(s, MX, y, 0.78, 0.78, [([(num, 19, True, "FFFFFF")], dict(align="c"))], anchor="m")
    add_text(s, MX + 1.05, y - 0.06, 11.0, 0.55, [([(head, 17, True, NAVY)], dict())])
    add_text(s, MX + 1.05, y + 0.42, 11.0, 0.75,
             [([(desc, 12, False, INK)], dict(lh=1.12))])

# ---------- S3 WHY-1 现实风险 ----------
s = new_slide(prs, "为什么做① 现实风险：冷却水让水网与电网深度互锁", "why", 3)
header_card(s, MX, 1.32, 5.95, "气候侧：冷却水日益稀缺与脆弱", None, ORANGE)
bullets(s, MX + 0.2, 2.0, 5.55, 3.4, [
    ("▪", [("欧美已多次出现", False, INK), ("火电/核电机组因冷却水温升高、河流流量下降", True, INK), ("而减产或临时停机（van Vliet 等，Nature Climate Change 2012）", False, INK)]),
    ("▪", [("预测：2031–2060 年欧美火电容量因冷却水缺乏平均下降 ", False, INK), ("4%–19%", True, RED), ("，直流冷却（once-through）机组最脆弱", False, INK)]),
    ("▪", [("Macknick 等（ERL 2012）梳理各发电技术取水/耗水系数；Bartos 与 Chester（NCC 2015）量化美国西部电网供水-供电联合脆弱性", False, INK)]),
], size=12.5, gap=9)
header_card(s, MX + 6.28, 1.32, 5.95, "城市侧：供水事故的共因冲击", None, NAVY)
bullets(s, MX + 6.48, 2.0, 5.55, 3.4, [
    ("▪", [("爆管、水厂故障、停电反噬——城市供水自身事故可", False, INK), ("同时切断多台机组的冷却补水", True, INK), ("，形成", False, INK), ("共因失效", True, NAVY)]),
    ("▪", [("电厂循环冷却水取自市政管网：物理上经冷却水连通、信息上经 ICS 监控——天然的水-电信息物理耦合系统（CPS）", False, INK)]),
    ("▪", [("市政侧的缓慢失压，既是电力侧的物理威胁，也是可被信息域读取的“预警信号源”", False, INK)]),
], size=12.5, gap=9)
add_box(s, MX, 5.62, CW, 1.1, fill=LIGHT_O, line=ORANGE, line_w=1.2)
add_text(s, MX + 0.3, 5.62, CW - 0.6, 1.1,
         [([("冷却水是水网与电网之间", 13.5, False, INK), ("最普遍、却最少被显式建模", 13.5, True, ORANGE),
            ("的耦合通道：一旦显式建模，“市政失压 → 机组跳机”之间将暴露出一段", 13.5, False, INK),
            ("可资利用的缓冲时间", 13.5, True, ORANGE), ("。", 13.5, False, INK)], dict(lh=1.2))],
         anchor="m")

# ---------- S4 WHY-2 研究缺口 ----------
s = new_slide(prs, "为什么做② 研究缺口：一条耦合边留下的三个“不知道”", "why", 4)
add_box(s, MX, 1.30, CW, 0.98, fill=LIGHT_B, line=NAVY, line_w=1.2)
add_text(s, MX + 0.3, 1.30, CW - 0.6, 0.98,
         [([("既有相互依赖基础设施研究（含 Li & Zhang《RESS》2025 功能耦合范式）普遍以“停水→停机”", 13, False, INK),
            ("一条直接耦合边", 13, True, NAVY),
            ("代替冷却水中间过程——忽略了“市政失压”与“机组跳机”之间", 13, False, INK),
            ("可资利用的缓冲时间", 13, True, NAVY), ("。", 13, False, INK)], dict(lh=1.2))], anchor="m")
gaps = [
    ("不知道① 还剩多少时间？",
     "补水箱 / 集水池 / 凝汽器 / 低压缸各环节的缓冲贡献从未被逐环节量化——“停水到停机”的窗口长度是本征未知量"),
    ("不知道② 时间差能否被利用？",
     "“市政失压”信息经 ICS 跨域预警转化为电网主动控制（降出力 / 备用预升）的链路，未被显式建模与验证"),
    ("不知道③ 边界在哪？",
     "备用容量、爬坡速率、网络输送约束下的能力上限（相变点）无人刻画，“预警有用”停留在定性判断"),
]
for i, (h, d) in enumerate(gaps):
    x = MX + i * 4.145
    add_box(s, x, 2.52, 3.94, 2.42, fill="FFFFFF", line=LINE_GRAY, line_w=1.2)
    add_box(s, x, 2.52, 3.94, 0.5, fill=ORANGE, radius=0.14)
    add_text(s, x + 0.16, 2.52, 3.62, 0.5, [([(h, 12.5, True, "FFFFFF")], dict())], anchor="m")
    add_text(s, x + 0.18, 3.16, 3.58, 1.7, [([(d, 11.5, False, INK)], dict(lh=1.18))])
add_box(s, MX, 5.20, CW, 1.5, fill=LIGHT_B, line=TEAL, line_w=1.2)
add_text(s, MX + 0.3, 5.36, CW - 0.6, 1.2, [
    ([("对标：", 12.5, True, TEAL), ("Yu 等（孙宏斌团队，Nature Communications 2024）的气-电早期预警范式已证明“时间差可转化为韧性”", 12.5, False, INK),
      ("（ALP / AET / SAET 指标＋三策略 LP 主动控制）。", 12.5, False, INK)], dict(sa=4, lh=1.15)),
    ([("但燃气“管存气”缓冲为分钟级、冷却水“储水缓冲”天然更长——该范式能否迁移到水-电域、迁移后结论是否改变，是开放问题，亦即本文切入点。", 12.5, False, INK)], dict(lh=1.15)),
])

# ---------- S5 WHY-3 科学问题与贡献 ----------
s = new_slide(prs, "为什么做③ 科学问题与本文贡献", "why", 5)
add_box(s, MX, 1.30, CW, 2.15, fill=NAVY)
add_text(s, MX + 0.4, 1.48, CW - 0.8, 1.9, [
    ([("Q1  ", 15, True, "F5B971"), ("市政供水失效经电厂冷却链传导为电力缺额的过程有多慢？", 15.5, True, "FFFFFF")], dict(sa=8)),
    ([("Q2  ", 15, True, "F5B971"), ("这一时间差能否在机组跳机之前被跨域信息与主动控制所利用？", 15.5, True, "FFFFFF")], dict(sa=8)),
    ([("Q3  ", 15, True, "F5B971"), ("该利用的物理边界何在？", 15.5, True, "FFFFFF")], dict()),
])
contribs = [
    ("贡献① 冷却水全过程白箱建模",
     "市政配水节点 → 高位补水箱 → 集水池 → 循环水泵 → 凝汽器 → 低压缸 → 发电机，逐环节机理建模；量化缓冲窗口 SAET 与临界降出力速率 r*"),
    ("贡献② 三域三级 ICS 跨域预警",
     "预警阈值＝失效阈值（同测点、同判据、同源）——零可调参数；单通道零时延直达调度级，把时间差转化为主动控制窗口"),
    ("贡献③ 划界式韧性评估",
     "以 k*、R*、rf* 三个相变点刻画主动控制的能力边界，并给出 DP 差异化控制的适用条件——“划界”而非只“证 yes”"),
]
for i, (h, d) in enumerate(contribs):
    x = MX + i * 4.145
    add_box(s, x, 3.70, 3.94, 2.65, fill="FFFFFF", line=SEC["why"], line_w=1.4)
    add_text(s, x + 0.18, 3.90, 3.58, 0.85, [([(h, 13, True, ORANGE)], dict(lh=1.12))])
    add_text(s, x + 0.18, 4.72, 3.58, 1.5, [([(d, 11.5, False, INK)], dict(lh=1.18))])
add_text(s, MX, 6.55, CW, 0.4,
         [([("对标定位：把 Yu 等（NC 2024）的指标体系与三策略 LP 移植到水-电域，并补上其未建模的冷却水中间物理过程", 11.5, False, GRAY)], dict(align="c"))])

# ---------- S6 HOW-1 总体思路 ----------
s = new_slide(prs, "怎么做① 总体思路：把“水慢电快”的时间差转化为韧性", "how", 6)
nodes = [
    (0.60, 3.30, "市政失压起点", "t＝0，预警同时发出", NAVY),
    (4.75, 3.60, "冷却链缓冲过程", "补水箱→集水池→循环水泵→凝汽器→低压缸", TEAL),
    (9.20, 3.53, "机组高背压跳机", "15 kPa 持续 3 s，不可逆", RED),
]
for (x, w, h1, h2, col) in nodes:
    add_box(s, x, 1.48, w, 1.18, fill="FFFFFF", line=col, line_w=1.6)
    add_text(s, x + 0.12, 1.58, w - 0.24, 0.5, [([(h1, 13.5, True, col)], dict(align="c"))])
    add_text(s, x + 0.12, 2.08, w - 0.24, 0.52, [([(h2, 10.5, False, GRAY)], dict(align="c"))])
for ax, lab in [(3.95, "慢动态 · 小时级"), (8.40, "快动态 · 分钟级")]:
    ar = add_box(s, ax, 1.90, 0.75, 0.34, fill=ORANGE, shape=MSO_SHAPE.RIGHT_ARROW)
    add_text(s, ax - 0.5, 2.30, 1.75, 0.32, [([(lab, 10, True, ORANGE)], dict(align="c"))])
add_box(s, 0.60, 2.98, 12.13, 0.05, fill=ORANGE, radius=None, shape=MSO_SHAPE.RECTANGLE)
add_box(s, 0.60, 2.86, 0.05, 0.29, fill=ORANGE, radius=None, shape=MSO_SHAPE.RECTANGLE)
add_box(s, 12.68, 2.86, 0.05, 0.29, fill=ORANGE, radius=None, shape=MSO_SHAPE.RECTANGLE)
add_box(s, 4.10, 2.83, 5.13, 0.48, fill=ORANGE, radius=0.5)
add_text(s, 4.10, 2.83, 5.13, 0.48,
         [([("冷却缓冲窗口 SAET＝88.6–124.8 min（可主动利用的时间差）", 12.5, True, "FFFFFF")], dict(align="c"))], anchor="m")
add_box(s, 0.60, 3.62, 12.13, 0.82, fill=LIGHT_B, line=NAVY, line_w=1.2)
add_text(s, 0.85, 3.62, 11.63, 0.82,
         [([("三域三级 ICS 跨域预警", 12.5, True, NAVY), ("（市政 SCADA → 电力调度，零时延单通道）＋ ", 12.5, False, INK),
            ("滚动 LP 主动控制", 12.5, True, NAVY), ("：降出力 runback / 备用预升 / 机组组合重调度", 12.5, False, INK)], dict(lh=1.15))], anchor="m")
add_box(s, 0.60, 4.72, 6.00, 1.55, fill=LIGHT_R, line=RED, line_w=1.3)
add_text(s, 0.85, 4.90, 5.5, 1.25, [
    ([("无预警（PA 被动）", 13.5, True, RED)], dict(sa=5)),
    ([("信息不跨域：跳机后才知道 → 被动响应", 11.5, False, INK)], dict(sa=3)),
    ([("485.6 MW 少发（≈11.4% 负荷）/ 49.1 MWh 损失", 12.5, True, RED)], dict()),
])
add_box(s, 6.73, 4.72, 6.00, 1.55, fill=LIGHT_G, line=GREEN, line_w=1.3)
add_text(s, 6.98, 4.90, 5.5, 1.25, [
    ([("有预警（SP/DP 主动）", 13.5, True, GREEN)], dict(sa=5)),
    ([("预警 1.1 min 检出，窗口内 LP 主动控制", 11.5, False, INK)], dict(sa=3)),
    ([("0 MW / 0 MWh——缺额与损失双零、零跳机", 12.5, True, GREEN)], dict()),
])
add_text(s, MX, 6.52, CW, 0.45,
         [([("关键设计：预警阈值＝失效阈值（同测点、同判据、同时刻）——“预警即真失效”，零可调参数、语义保守唯一", 12, True, NAVY)], dict(align="c"))])

# ---------- S7 HOW-2 五层建模链 ----------
s = new_slide(prs, "怎么做② 五层白箱建模链：怎么建、为什么、依据什么", "how", 7)
rows_t = [
    ("B\n市政配水",
     ["D-town 399 节点真实管网", "EPANET 延时水力＋Wagner PDD", "B-ST 阶跃 / B-RT 现实双口径"],
     ["边界由真实水力仿真生成而非假设；作单向边界层——城市缓冲小时级、厂内分钟级，两级位置不对称"],
     ["Marchi 2014（BWN II）", "Ostfeld 2016（D-town）", "Rossman 2000（EPANET）"]),
    ("W\n冷却水", ["补水箱 / 集水池质量守恒 ODE", "泵吸口淹没深度分段降额", "蒸发 / 排污 / 风吹三项循环损失"],
     ["既有研究以一条耦合边跳过全部中间过程；逐环节白箱才能量化 SAET、给出可行的 runback 速率（创新①主体）"],
     ["GB/T 50102（循环水定额）", "DL/T 5339（集水池停留时间）"]),
    ("A\n凝汽器-低压缸", ["ε-NTU 换热＋Antoine 饱和蒸汽压", "背压微增降额 γ＝2%/kPa", "高背压 15 kPa / 3 s 保护跳机"],
     ["传热-机电转换是“失水→跳机”必经物理路径；UA₀ 由额定工况自洽反标定（端差 4.9 K 落在标准典型区间），不另假设"],
     ["HEI；ASME PTC 12.2", "Dittus–Boelter（0.8 指数）"]),
    ("I\n信息层", ["三域 × 三级 ICS 架构", "跨域预警单通道直达调度级", "检测判据与失效判据同源、锁存"],
     ["压头是水司既有量测、零新增传感；阈值同源 → 零可调参数、语义保守唯一；各场景共享同一时间零点（创新②）"],
     ["Wang 2022（HLA 架构）", "Yu 2024（NC 预警范式）"]),
    ("C\n电力＋LP", ["IEEE-118 直流潮流（PTDF）", "滚动 LP：min 缺额＋5·过载", "PA / SP / DP 三策略"],
     ["DC-PF 保 LP 线性（HiGHS 秒级解）；被动因果约束（首台跳机前备用禁预升）保证缺额是真实时序后果而非构造"],
     ["MATPOWER（UW-118）", "Wood 2013（两级备用）"]),
]
tbl_shape = s.shapes.add_table(6, 4, Inches(MX), Inches(1.28), Inches(CW), Inches(5.0))
tbl = tbl_shape.table
tbl.first_row = False
tbl.horz_banding = False
for i, w in enumerate([1.30, 3.42, 4.80, 2.71]):
    tbl.columns[i].width = Inches(w)
tbl.rows[0].height = Inches(0.42)
for r in range(1, 6):
    tbl.rows[r].height = Inches(0.92)


def set_cell(cell, lines, size=10.5, bold=False, color=INK, fill=None, align=PP_ALIGN.LEFT):
    if fill:
        cell.fill.solid()
        cell.fill.fore_color.rgb = C(fill)
    cell.margin_left = cell.margin_right = Inches(0.07)
    cell.margin_top = cell.margin_bottom = Inches(0.03)
    cell.vertical_anchor = ANCHOR["m"]
    tf = cell.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(1)
        if isinstance(ln, str):
            ln = [(ln, size, bold, color)]
        for (t, sz, b, c) in ln:
            r = p.add_run()
            r.text = t
            style_run(r, sz, b, c)


heads = ["层", "关键建模", "为什么这么建", "支撑文献 / 标准"]
for j, h in enumerate(heads):
    set_cell(tbl.cell(0, j), [h], size=11.5, bold=True, color="FFFFFF", fill=NAVY, align=PP_ALIGN.CENTER)
for i, (layer, modeling, why, ref) in enumerate(rows_t):
    r = i + 1
    bg = "FFFFFF" if i % 2 == 0 else "F2F6FA"
    parts = layer.split("\n")
    name_runs = [(parts[0], 12, True, NAVY)]
    if len(parts) > 1:
        name_runs.append(("\n" + parts[1], 11, True, NAVY))
    if parts[0] in ("W", "I"):
        name_runs.append(("\n【创新" + ("①" if parts[0] == "W" else "②") + "】", 10, True, ORANGE))
    set_cell(tbl.cell(r, 0), [name_runs], fill="DDE6F2", align=PP_ALIGN.CENTER)
    set_cell(tbl.cell(r, 1), modeling, fill=bg)
    set_cell(tbl.cell(r, 2), why, fill=bg)
    set_cell(tbl.cell(r, 3), ref, fill=bg, size=9.5, color=GRAY)
add_text(s, MX, 6.42, CW, 0.5,
         [([("方法定位：对标 Yu 等（NC 2024）气-电范式并补上冷却水中间过程；三条原则——白箱机理 / 公式与代码一一对应 / 时间尺度分离（秒级机电·分钟级水力热力·小时级市政）", 11, False, GRAY)], dict(align="c", lh=1.1))])

# ---------- S8 HOW-3 案例与实验设计 ----------
s = new_slide(prs, "怎么做③ 案例与实验设计：IEEE-118 × D-town 全耦合", "how", 8)
add_text(s, MX, 1.30, 6.6, 0.42, [([("案例：IEEE-118 电力 × D-town 市政管网，54 对取水耦合", 14, True, NAVY)], dict())])
bullets(s, MX, 1.82, 6.6, 2.2, [
    ("▪", [("电力：118 母线 / 186 线 / 54 机，总负荷 4242 MW（Pmax 合计 9966 MW）", False, INK)]),
    ("▪", [("水网：399 节点 / 443 管，唯一水源 245.8 L/s；54 节点额定补水合计 299.7 L/s", False, INK)]),
    ("▪", [("耦合：取水节点压头 < 28 m 即为冷却失效源，逐一映射到对应机组", False, INK)]),
], size=12, gap=6)
add_text(s, MX, 4.05, 6.6, 0.42, [([("实验设计", 14, True, NAVY)], dict())])
bullets(s, MX, 4.55, 6.6, 2.4, [
    ("▪", [("市政侧：唯一水源停供，B-ST 合成阶跃（应力上界）与 B-RT 现实轨迹双口径 → 逐节点失压时刻", False, INK)]),
    ("▪", [("电力侧：单机 / 多机 N-k 扫描＋全序级联（11 事件 / 2 簇）", False, INK)]),
    ("▪", [("控制策略：PA 被动 / SP 预警＋备用 / DP 预警＋LP 差异化；备用总量 1.2×P_aff，缺额纯来自时序", False, INK)]),
    ("▪", [("敏感性四轴：失效规模 k · 爬坡速率 R · 备用容量 rf · 取水位置", True, INK)]),
], size=12, gap=6)
add_img(s, FIG("Fig4_coupling_topology.png"), 7.55, 1.35, 5.23, 4.9,
        "耦合拓扑：54 对“市政取水节点—机组”配对（图 4）")

# ---------- S9 HOW-4 方法可信度 ----------
s = new_slide(prs, "怎么做④ 方法可信度：白箱、可复现、按标准标定", "how", 9)
cards = [
    ("① 白箱机理，因果链可审计",
     "每环节用经典物理关系：质量守恒 / ε-NTU / Antoine 饱和蒸汽压 / Wagner 压力驱动需水——无黑箱拟合，每个数字都能沿因果链回溯到参数与代码"),
    ("② 公式与代码一一对应",
     "结果全部由 git 版本管理的代码链生成（21 次提交完整演进）；19 项新旧结果锚点回归校验逐位通过；合稿数字 / 引注多重集机器校验一致"),
    ("③ 参数按标准定额标定",
     "循环水量定额 k_cw＝0.0295 m³/(s·MW)（GB/T 50102）；集水池停留时间 3–5 min（DL/T 5339）；反标定端差 4.9 K 落在 HEI / ASME PTC 12.2 典型区间"),
]
for i, (h, d) in enumerate(cards):
    x = MX + i * 4.145
    add_box(s, x, 1.35, 3.94, 3.35, fill="FFFFFF", line=NAVY, line_w=1.4)
    add_box(s, x, 1.35, 3.94, 0.56, fill=NAVY, radius=0.14)
    add_text(s, x + 0.16, 1.35, 3.62, 0.56, [([(h, 13, True, "FFFFFF")], dict())], anchor="m")
    add_text(s, x + 0.20, 2.10, 3.54, 2.4, [([(d, 12, False, INK)], dict(lh=1.22))])
add_box(s, MX, 5.05, CW, 1.55, fill=LIGHT_B, line=TEAL, line_w=1.2)
add_text(s, MX + 0.3, 5.22, CW - 0.6, 1.25, [
    ([("文献支撑 21 条、逐条核实（卷期页码 / DOI）：", 12.5, True, TEAL)], dict(sa=5)),
    ([("范式与同类 3（Yu NC 2024 · Li & Zhang RESS 2025 · Wang AiC 2022）＋ 市政水网 5（Marchi / Ostfeld / Rossman / Klise / Wagner）＋ 中国规范标准 4（GB/T 50102 · DL/T 5339 · HEI · ASME PTC 12.2）＋ 传热 2（Dittus–Boelter · Incropera）＋ 电力 3（UW PSTCA · MATPOWER · Wood）＋ 背景 4（van Vliet · Macknick · Bartos · Ouyang）", 12, False, INK)], dict(lh=1.25)),
])

# ---------- S10 WHAT-1 头条结果 ----------
s = new_slide(prs, "预期结果① 时间差转化为韧性：485.6 MW → 0/0", "what", 10)
add_text(s, MX, 1.32, 6.1, 0.4, [([("单机失效（bus89）· 无预警 → 有预警", 13, True, GRAY)], dict())])
add_box(s, MX, 1.78, 6.1, 1.28, fill=LIGHT_R, line=RED, line_w=1.4)
add_text(s, MX + 0.25, 1.78, 5.6, 1.28, [
    ([("无预警：485.6 MW", 24, True, RED)], dict(sa=2)),
    ([("≈ 11.4% 系统负荷 · 少供电量 49.1 MWh", 12.5, False, INK)], dict()),
], anchor="m")
add_text(s, MX, 3.22, 6.1, 0.42,
         [([("▼  早期预警（1.1 min 检出）＋ SP 主动控制", 13, True, NAVY)], dict(align="c"))])
add_box(s, MX, 3.74, 6.1, 1.28, fill=LIGHT_G, line=GREEN, line_w=1.4)
add_text(s, MX + 0.25, 3.74, 5.6, 1.28, [
    ([("有预警：0 MW / 0 MWh", 24, True, GREEN)], dict(sa=2)),
    ([("缺额与损失双零 · 零跳机 · 零甩负荷", 12.5, False, INK)], dict()),
], anchor="m")
bullets(s, MX, 5.30, 6.1, 1.7, [
    ("▪", [("三机共因与全序级联（11 事件 / 2 簇）下 SP 亦 0/0；24 个故障场景中 SP 零缺额 18 个", False, INK)]),
    ("▪", [("最不利情形：保守上界 192.3 MW / 16.0 MWh，独立下界 8.6 MW / 0.7 MWh", False, INK)]),
    ("▪", [("只要预警信息跨域到达，“被动大停电”可完全避免（能力边界见后）", True, NAVY)]),
], size=11.5, gap=5)
add_img(s, FIG("Fig9_early_warning_comparison.png"), 6.95, 1.45, 5.85, 3.9,
        "无预警 vs 有预警：功率缺额与损失对比（图 9）")

# ---------- S11 WHAT-2 缓冲窗口与负反馈 ----------
s = new_slide(prs, "预期结果② 缓冲窗口与“降额自保护”负反馈", "what", 11)
bullets(s, MX, 1.42, 6.7, 4.6, [
    ("▪", [("SAET＝88.6–124.8 min", True, TEAL), ("（三厂 88.6 / 116.9 / 124.8；合成阶跃＝保守下界，现实衰减轨迹的闭合水量账口径约 20× 更长）", False, INK)]),
    ("▪", [("临界降出力速率 ", False, INK), ("r*＝0.545 %Pg/min", True, TEAL), ("：降出力更快 → 热负荷更低 → 背压升得更缓 → 缓冲更长——“降额自保护”负反馈", False, INK)]),
    ("▪", [("r* 处最长运行 183.3 min＝SAET 的 2.07×", True, TEAL)]),
    ("▪", [("两级缓冲天然不对称：城市侧 P10/50/90＝3.8 / 9.8 / 17.0 h（强位置依赖），厂内侧 88.6–124.8 min（位置无关）", False, INK)]),
    ("▪", [("含义：预警换来的窗口还能被 runback 主动放大一倍——时间差是可经营的资源，而非被动等待的倒计时", True, NAVY)]),
], size=12.5, gap=10)
add_img(s, FIG("Fig8_critical_ramp_example.png"), 7.55, 1.42, 5.23, 4.35,
        "临界降出力速率下的运行时间延长（图 8 节选）")

# ---------- S12 WHAT-3 能力边界 ----------
s = new_slide(prs, "预期结果③ 能力边界：三个相变点划清“能用多少”", "what", 12)
bcs = [
    ("失效规模：k*＝3", "k≤2：缺额完全消除\nk≥3：残留 95.6–128.2 MWh（备用与爬坡的物理限制）"),
    ("爬坡速率：R*∈(0.0035, 0.005]", "既定 0.01·Pmax/min 减半仍可行\n再低则备用起机赶不上缺额传导"),
    ("备用容量：rf*∈(0.35, 0.5]", "备用折半以内主动控制仍有效\n容量充足（5327>4242 MW）时 k≥3 仍恶化——瓶颈并非容量本身"),
    ("DP 差异化的价值条件", "爬坡受限：相变点按 ≈1/α 下移，残差削减 97.5%\n网络受限：仅推迟、不能消除（57.12 MW 输送地板）"),
]
for i, (h, d) in enumerate(bcs):
    x = MX + (i % 2) * 6.24
    y = 1.35 + (i // 2) * 2.06
    add_box(s, x, y, 5.99, 1.88, fill="FFFFFF", line=TEAL, line_w=1.4)
    add_box(s, x, y, 0.14, 1.88, fill=TEAL, radius=None, shape=MSO_SHAPE.RECTANGLE)
    add_text(s, x + 0.32, y + 0.13, 5.5, 0.5, [([(h, 14, True, TEAL)], dict())])
    lines = [(ln, 11.5, False, INK) for ln in d.split("\n")]
    add_text(s, x + 0.32, y + 0.68, 5.5, 1.1, [(lines[:1], dict(sa=4)), (lines[1:], dict())][:2] if len(lines) > 1 else [(lines, dict())])
add_box(s, MX, 5.55, CW, 1.25, fill=LIGHT_O, line=ORANGE, line_w=1.2)
add_text(s, MX + 0.3, 5.55, CW - 0.6, 1.25,
         [([("k≥3 残留经三轴扫描鉴别为“网络输送 × 备用容量”联合约束", 13, True, ORANGE),
            ("——不是预警不够快，而是送不上去、备不够用；这界定了早期预警范式在水-电场景的价值上限。", 13, False, INK)], dict(lh=1.2))], anchor="m")

# ---------- S13 WHAT-4 市政侧与稳健性 ----------
s = new_slide(prs, "预期结果④ 市政侧图景与稳健性", "what", 13)
add_img(s, FIG("Fig12_depressurization_time_distribution.png"), MX, 1.40, 4.95, 4.65,
        "唯一水源停供下的节点失压时刻分布（图 12）")
bullets(s, 5.85, 1.42, 6.93, 5.3, [
    ("▪", [("B-ST（合成阶跃，应力上界）：72.4% 节点 72 h 内失压，失压时刻 0–67 h", True, INK)]),
    ("▪", [("结构三段：", False, INK), ("快失压", True, TEAL), ("（近水源弱缓冲，P10＝0）— ", False, INK), ("渐失压", True, TEAL), ("（水箱缓冲 10–20 h）— ", False, INK), ("不失压平台", True, TEAL), ("（27.6% 强缓冲高区 72 h 不失压）", False, INK)]),
    ("▪", [("B-RT（现实衰减轨迹）：中位失压 35.25 h（闭合水量账口径）", False, INK)]),
    ("▪", [("分散取水：被动峰值 343→315 MW、少损 52.5 MWh——危机错峰、峰值不叠加；SP/DP 对取水位置稳健（仍 0/0）", True, INK)]),
    ("▪", [("主动控制的稳健性来源：厂内冷却缓冲与取水位置无关（分钟级、位置无关 vs 城市小时级、强位置依赖）", False, INK)]),
], size=12.5, gap=10)

# ---------- S14 WHAT-5 跨域洞见与结论 ----------
s = new_slide(prs, "预期结果⑤ 跨域洞见与结论", "what", 14)
add_box(s, MX, 1.35, 5.99, 2.9, fill="FFFFFF", line=GRAY, line_w=1.3)
add_box(s, MX, 1.35, 5.99, 0.52, fill=GRAY, radius=0.14)
add_text(s, MX + 0.2, 1.35, 5.6, 0.52, [([("气-电（Yu 等 NC 2024）", 13.5, True, "FFFFFF")], dict())], anchor="m")
add_text(s, MX + 0.28, 2.05, 5.45, 2.0, [
    ([("▪ 管存气缓冲：分钟级", 12.5, False, INK)], dict(sa=7)),
    ([("▪ 瓶颈在“信息速度”——预警与控制要抢时间", 12.5, False, INK)], dict(sa=7)),
    ([("▪ 需 LP 差异化控制（DP），且仍有残差", 12.5, False, INK)], dict()),
])
add_box(s, MX + 6.24, 1.35, 5.99, 2.9, fill=LIGHT_B, line=TEAL, line_w=1.6)
add_box(s, MX + 6.24, 1.35, 5.99, 0.52, fill=TEAL, radius=0.14)
add_text(s, MX + 6.44, 1.35, 5.6, 0.52, [([("水-电（本文）", 13.5, True, "FFFFFF")], dict())], anchor="m")
add_text(s, MX + 6.52, 2.05, 5.45, 2.0, [
    ([("▪ 储水缓冲：SAET 88.6–124.8 min、城市水箱小时级", 12.5, False, INK)], dict(sa=7)),
    ([("▪ 瓶颈转移至“多机共因下的备用充足性与网络输送”", 12.5, True, TEAL)], dict(sa=7)),
    ([("▪ SP 即达 0/0——时间不再稀缺，物理约束成为主角", 12.5, False, INK)], dict()),
])
add_box(s, MX, 4.50, CW, 1.35, fill=NAVY)
add_text(s, MX + 0.35, 4.50, CW - 0.7, 1.35,
         [([("跨域发现：", 14, True, "F5B971"), ("冷却水储水缓冲天然长于燃气管存气——水-电场景的韧性瓶颈自“信息速度”转移至“多机共因下的备用充足性与网络输送”，", 13.5, True, "FFFFFF"),
            ("这既解释了本文 SP 即达 0/0（异于气-电文献中 DP 仍残留），也界定了该范式迁移的条件。", 13.5, False, "FFFFFF")], dict(lh=1.25))], anchor="m")
add_text(s, MX, 6.10, CW, 0.6,
         [([("结论：早期预警范式可以迁移，但价值兑现点不同——“买时间”不再稀缺，“用时间”受物理约束；本文用 k*、R*、rf* 三个相变点把“能用多少”划清楚。", 12.5, True, NAVY)], dict(align="c", lh=1.15))])

# ---------- S15 完成度与计划 ----------
s = new_slide(prs, "完成度、投稿计划与支持请求", "plan", 15)
header_card(s, MX, 1.35, 5.99, "完成度", None, NAVY)
bullets(s, MX + 0.22, 2.0, 5.55, 3.2, [
    ("▪", [("中文全文已成稿：8 章 / 图 14 / 表 6，结果全部由版本管理代码链生成（21 次提交），机械核验全绿", False, INK)]),
    ("▪", [("21 条参考文献逐条核实（作者 / 卷期页码 / DOI）；数字与引注多重集机器校验一致", False, INK)]),
    ("▪", [("待办：全文英文化、Nomenclature、Highlights、Cover letter、Zenodo 归档", False, INK)]),
], size=12, gap=8)
header_card(s, MX + 6.24, 1.35, 5.99, "恳请指导与支持", None, ORANGE)
bullets(s, MX + 6.46, 2.0, 5.55, 3.2, [
    ("①", [("方法链（尤其冷却水机理深度与 LP 口径）与期刊选择，请老师确认或指正", False, INK)]),
    ("②", [("英文化与润色阶段的时间 / 资源支持", False, INK)]),
    ("③", [("两项取舍的确认：预警时延 / 漏报实验、中等烈度场景（已声明为局限与未来工作）", False, INK)]),
    ("④", [("方向认可的话，恳请推荐审稿视角或潜在合作者", False, INK)]),
], size=12, gap=8)
add_box(s, MX, 5.45, CW, 1.15, fill=LIGHT_B, line=NAVY, line_w=1.2)
add_text(s, MX + 0.3, 5.45, CW - 0.6, 1.15,
         [([("投稿计划：", 13, True, NAVY), ("首选 Reliability Engineering & System Safety（相互依赖基础设施＋级联失效＋敏感性范式契合）；备选 Applied Energy / IJEPES", 13, False, INK)],
           dict(lh=1.2))], anchor="m")
add_text(s, MX, 6.72, CW, 0.4,
         [([("附件可提供：论文完整版（单文件 HTML，图表公式内嵌）· 全部代码与数据（git 完整演进）· 参数标定溯源表", 11, False, GRAY)], dict(align="c"))])

prs.save(OUT)
print("已生成：", OUT)
print("幻灯片数：", len(prs.slides))
