#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合稿脚本：将 docs/paper_chapters/ 八件正稿合并为单一完整版《论文完整版.md》。

变换规则（全部经断言校验，正文逐字保真）：
  1. 前后件拆分：摘要（含关键词）置文首；数据与代码可用性、致谢置文末；
     合稿待办清单与各文件头部编辑说明 blockquote 不并入。
  2. 去除各章文末"本章参考文献"小节，按全文首次出现顺序重建总表（21 条）。
  3. 图片相对路径 ../../figures/ → figures/（图 1–14 随图注嵌入正文）。
  4. 参考文献编号按全文首次出现顺序统一重排，旧→新映射写 docs/renumber_map.json。
     引注 token 判定：[n] / [n,m] / [n–m]，展开后全部数字 ∈ 1..21 方可重写；
     τ＝[0,0,0]、[600, 24 000]、[3.75, 9.75, 17.0]、[i,t]、[2pt]、数学 \bigr] 、
     图片 alt 方括号等一律识别为非引注、原样保留。

用法：python3 docs/merge_manuscript.py
输出：论文完整版.md（研究根目录）、docs/renumber_map.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # cooling_cascade_study/
CH = ROOT / "docs" / "paper_chapters"
OUT_MD = ROOT / "论文完整版.md"
OUT_MAP = ROOT / "docs" / "renumber_map.json"
TODAY = "2026-09-07"

# (文件名, 期望图片嵌入数, 是否含"本章参考文献")
CHAPTERS = [
    ("ch1_introduction.md", 0, True),
    ("ch2_methodology.md", 3, True),
    ("ch3_case_study_and_parameters.md", 1, True),
    ("ch4_results.md", 7, True),
    ("ch5_sensitivity.md", 3, True),
    ("ch6_discussion.md", 0, True),
    ("ch7_conclusion.md", 0, False),
]

# 手工推导的全文首次出现顺序（旧编号）——脚本独立计算后与此比对，防推导/实现双重出错
EXPECTED_ORDER = [18, 19, 20, 2, 3, 21, 11, 12, 13, 1, 4, 5, 7, 8, 15, 9, 10, 16, 6, 14, 17]

# ---------------- 引注 token 识别 ----------------
CAND = re.compile(r"\[[0-9][0-9,，、:：\s–—-]*\]")


def parse_nums(inner):
    """把方括号内容解析为引注号列表；非引注（含 0/越界/非整数记法）返回 None。"""
    inner = inner.strip()
    if not inner:
        return None
    nums = []
    for p in re.split(r"[,，、]", inner):
        p = p.strip()
        if not p:
            return None
        m = re.fullmatch(r"(\d+)\s*[–—-]\s*(\d+)", p)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if not (1 <= a <= b <= 21):
                return None
            nums.extend(range(a, b + 1))
        elif p.isdigit():
            nums.append(int(p))
        else:
            return None
    if not nums:
        return None
    return nums if all(1 <= n <= 21 for n in nums) else None


def scan_tokens(text):
    """返回 [(token, nums)]，并按出现顺序登记首次出现（写入全局 order/seen）。"""
    toks = []
    for m in CAND.finditer(text):
        nums = parse_nums(m.group(0)[1:-1])
        if nums is not None:
            toks.append((m.group(0), nums))
            for n in nums:
                if n not in SEEN:
                    SEEN.add(n)
                    ORDER.append(n)
    return toks


def fmt(nums):
    """新编号升序分组：连续 ≥3 用区间 a–b，其余逗号连接。"""
    nums = sorted(set(nums))
    groups, start, prev = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        groups.append((start, prev))
        start = prev = n
    groups.append((start, prev))
    parts = []
    for a, b in groups:
        if b - a >= 2:
            parts.append(f"{a}–{b}")
        elif b - a == 1:
            parts.append(f"{a},{b}")
        else:
            parts.append(str(a))
    return "[" + ",".join(parts) + "]"


# ---------------- 文件处理 ----------------
def load_chapter(fname, exp_imgs, has_refs):
    raw = (CH / fname).read_text(encoding="utf-8")
    lines = raw.split("\n")
    assert lines[0].startswith("# "), f"{fname}: 首行不是 H1"
    # 拆出文末"本章参考文献"
    ref_lines = []
    if has_refs:
        for i, l in enumerate(lines):
            if l.strip() == "## 本章参考文献":
                ref_lines = lines[i + 1:]
                lines = lines[:i]
                break
        else:
            raise AssertionError(f"{fname}: 未找到'## 本章参考文献'")
    # 去除标题后的头部编辑说明 blockquote（连续 > 行）
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    removed = []
    if i < len(lines) and lines[i].startswith(">"):
        while i < len(lines) and lines[i].startswith(">"):
            removed.append(lines[i])
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        lines = [lines[0], ""] + lines[i:]
    assert removed and any("正稿" in r for r in removed), f"{fname}: 头部编辑说明缺失或格式异常"
    body = "\n".join(lines).rstrip() + "\n"
    # 图片路径改写
    n_img = body.count("](../../figures/")
    body = body.replace("](../../figures/", "](figures/")
    assert n_img == exp_imgs, f"{fname}: 图片嵌入数 {n_img} ≠ 期望 {exp_imgs}"
    refs = {}
    for l in ref_lines:
        m = re.match(r"^\[(\d+)\]\s+(.+)$", l.strip())
        if m:
            refs[int(m.group(1))] = m.group(2).strip()
    return body, refs, n_img


def main():
    global ORDER, SEEN
    ORDER, SEEN = [], set()

    # ---- 题目（取自骨架权威源）----
    sk = (ROOT / "论文简要版_骨架.md").read_text(encoding="utf-8").split("\n")
    title_zh = sk[0][2:].strip()
    men = re.match(r"\*(.+)\*$", sk[2].strip())
    assert men, "骨架第 3 行应为英文斜体题目"
    title_en = men.group(1)

    # ---- 前后件 ----
    fbm = (CH / "front_back_matter.md").read_text(encoding="utf-8")
    fbm = fbm.split("### 合稿待办清单")[0]
    secs, cur = {}, None
    for line in fbm.split("\n"):
        if line.startswith("## "):
            cur = line[3:].strip()
            secs[cur] = []
        elif cur is not None:
            secs[cur].append(line)

    def clean_sec(lines):
        while lines and (not lines[-1].strip() or lines[-1].strip() == "---"):
            lines.pop()
        return "\n".join(lines).strip()

    abstract = clean_sec(secs["摘要"])
    avail = clean_sec(secs["数据与代码可用性"])
    ack = clean_sec(secs["致谢（占位）"])
    assert "485.6" in abstract and "CC BY-NC" in avail and "Battle of the Water Network" in ack

    # ---- 章节正文与文内文献条目 ----
    bodies, all_refs = [], {}
    for fname, exp_imgs, has_refs in CHAPTERS:
        body, refs, n_img = load_chapter(fname, exp_imgs, has_refs)
        bodies.append(body)
        for n, entry in refs.items():
            if n in all_refs:
                assert all_refs[n] == entry, f"文献 [{n}] 在各章条目不一致：{fname}"
            all_refs[n] = entry
    assert set(all_refs) == set(range(1, 22)), f"文献条目覆盖不全：{sorted(set(all_refs) ^ set(range(1,22)))}"

    # ---- 扫描首现顺序（摘要无引注亦应通过）----
    parts = [("摘要", abstract)] + [(f"ch{i+1}", b) for i, b in enumerate(bodies)] \
            + [("数据可用性", avail), ("致谢", ack)]
    token_counts = {}
    for name, text in parts:
        token_counts[name] = len(scan_tokens(text))
    assert ORDER == EXPECTED_ORDER, f"首现顺序与手工推导不符：\n实际 {ORDER}\n期望 {EXPECTED_ORDER}"
    old2new = {old: i + 1 for i, old in enumerate(ORDER)}

    # ---- 重写引注 ----
    def rewrite(text):
        cnt = [0]

        def repl(m):
            nums = parse_nums(m.group(0)[1:-1])
            if nums is None:
                return m.group(0)
            cnt[0] += 1
            return fmt([old2new[n] for n in nums])

        return CAND.sub(repl, text), cnt[0]

    new_parts = []
    for name, text in parts:
        new_text, c = rewrite(text)
        assert c == token_counts[name], f"{name}: 重写 token 数 {c} ≠ 扫描数 {token_counts[name]}"
        new_parts.append((name, new_text))
    abstract_n = new_parts[0][1]
    bodies_n = [t for _, t in new_parts[1:8]]
    avail_n, ack_n = new_parts[8][1], new_parts[9][1]

    # 新总表（按新编号 1..21）
    ref_list = "\n\n".join(f"[{i}] {all_refs[ORDER[i - 1]]}" for i in range(1, 22))

    headnote = (
        "> 合稿版 v2（语言润色，" + TODAY + "）：本文档由 `docs/paper_chapters/` 八件正稿经 `docs/merge_manuscript.py` "
        "程序化合并生成，正文逐字保真，仅做三类机械变换——去除各章头部编辑说明、图片路径改写为 "
        "`figures/` 相对路径、参考文献编号按全文首次出现顺序统一重排（旧→新映射见 `docs/renumber_map.json`）；"
        "图 1–14 已随图注嵌入正文。投稿前待办（英文化、Nomenclature、Highlights、Zenodo 归档等）"
        "见 `docs/paper_chapters/front_back_matter.md`。"
    )

    doc = "\n\n".join([
        f"# {title_zh}\n\n*{title_en}*\n\n{headnote}\n\n---",
        "# 摘要 Abstract\n\n" + abstract_n + "\n\n---",
        *bodies_n,
        "---\n\n# 参考文献 References\n\n" + ref_list + "\n\n---",
        "# 数据与代码可用性 Data and Code Availability\n\n" + avail_n,
        "# 致谢 Acknowledgments（占位）\n\n" + ack_n,
    ]) + "\n"

    # ================= 终检 =================
    problems = []

    for s in ["本章参考文献", "正稿章节草稿", "（编号沿用", "合稿待办", "../../figures", "⟦"]:
        if s in doc:
            problems.append(f"残留禁用串：{s}")

    # 图片：13 张、顺序 1–13、文件存在、紧邻各自图注
    imgs = re.findall(r"^!\[图(\d+)\]\((figures/[^)]+)\)$", doc, re.M)
    if [int(n) for n, _ in imgs] != list(range(1, 15)):
        problems.append(f"图片序号异常：{[n for n, _ in imgs]}")
    for n, p in imgs:
        if not (ROOT / p).exists():
            problems.append(f"图片文件缺失：{p}")
    caps = re.findall(r"^\*\*图 (\d+)　", doc, re.M)
    if [int(n) for n in caps] != list(range(1, 15)):
        problems.append(f"图注序号异常：{caps}")
    for n, _ in imgs:
        pat = rf"!\[图{n}\]\(figures/[^\n]+\)\n\n\*\*图 {n}　"
        if not re.search(pat, doc):
            problems.append(f"图 {n} 图片与图注未紧邻")

    # 表：表 1–6 各一次
    tabs = re.findall(r"^\*\*表 (\d+)　", doc, re.M)
    if sorted(map(int, tabs)) != [1, 2, 3, 4, 5, 6]:
        problems.append(f"表注序号异常：{tabs}")

    # H1 序列
    h1s = re.findall(r"^# (.+)$", doc, re.M)
    exp_h1 = [title_zh, "摘要 Abstract", "1 引言 Introduction", "2 方法 Methodology",
              "3 案例与参数 Case Study and Setup", "4 结果 Results", "5 敏感性分析 Sensitivity Analysis",
              "6 讨论 Discussion", "7 结论 Conclusion", "参考文献 References",
              "数据与代码可用性 Data and Code Availability", "致谢 Acknowledgments（占位）"]
    if h1s != exp_h1:
        problems.append(f"H1 序列异常：{h1s}")

    # 引注复扫（重写后）：token 总数守恒 + 新号覆盖 1..21（复扫区域＝除文献总表外的全文）
    idx = doc.index("# 参考文献 References")
    tail_start = doc.index("\n---\n", idx) + len("\n---\n")
    body_region = doc[:idx] + doc[tail_start:]
    union = set()
    total = 0
    for m in CAND.finditer(body_region):
        nums = parse_nums(m.group(0)[1:-1])
        if nums is not None:
            union.update(nums)
            total += 1
    if union != set(range(1, 22)):
        problems.append(f"正文引用未覆盖 1..21：缺 {sorted(set(range(1,22))-union)}，多 {sorted(union-set(range(1,22)))}")
    if total != sum(token_counts.values()):
        problems.append(f"终稿 token 总数 {total} ≠ 源 token 总数 {sum(token_counts.values())}")

    # 图/表正文引述计数（报告用；图 4/表 4 应≥2）
    fig_mentions = {n: len(re.findall(rf"图 {n}(?!\d)", doc)) for n in range(1, 15)}
    tab_mentions = {n: len(re.findall(rf"表 {n}(?!\d)", doc)) for n in range(1, 7)}
    for n in (4,):
        if fig_mentions[n] < 2:
            problems.append(f"图 {n} 缺正文引述")
    for n in (1, 2, 3, 4, 5, 6):
        if tab_mentions[n] < 2:
            problems.append(f"表 {n} 缺正文引述")

    if problems:
        print("!! 终检未通过：")
        for p in problems:
            print("   -", p)
        sys.exit(1)

    OUT_MD.write_text(doc, encoding="utf-8")
    OUT_MAP.write_text(json.dumps({
        "generated": TODAY,
        "note": "旧编号（各章正稿既定体系）→ 新编号（合稿版按全文首次出现顺序）",
        "first_appearance_order_old": ORDER,
        "old_to_new": {str(k): v for k, v in sorted(old2new.items())},
        "new_to_old": {str(v): k for k, v in sorted(old2new.items(), key=lambda kv: kv[1])},
        "citation_token_total": total,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 报告 ----
    print("=== 合稿完成 ===")
    print(f"输出：{OUT_MD.relative_to(ROOT)}  （{len(doc.splitlines())} 行 / {len(doc)} 字符）")
    print(f"映射：{OUT_MAP.relative_to(ROOT)}")
    print(f"引注 token 总数（重写前后守恒）：{total}")
    print("\n旧→新 编号映射：")
    print("  " + "  ".join(f"{k}→{old2new[k]}" for k in sorted(old2new)))
    print("\n新编号文献表：")
    for i in range(1, 22):
        e = all_refs[ORDER[i - 1]]
        print(f"  [{i:>2}] {e[:58]}{'…' if len(e) > 58 else ''}")
    print("\n图正文引述计数：", fig_mentions)
    print("表正文引述计数：", tab_mentions)
    print("术语计数：少发功率 ×%d，损失电量 ×%d" % (
        doc.count("少发功率"), doc.count("损失电量")))
    # 抽样展示三处重写效果
    print("\n重写抽样：")
    for name, text in parts:
        m = re.search(r"[^\n]*\[18\][^\n]*", text)
        if m:
            print(f"  [{name}] 旧：…{m.group(0)[:70]}…")
            break
    for name, text in new_parts:
        m = re.search(r"[^\n]*\[1\][^\n]*", text)
        if m:
            print(f"  [{name}] 新：…{m.group(0)[:70]}…")
            break


if __name__ == "__main__":
    main()
