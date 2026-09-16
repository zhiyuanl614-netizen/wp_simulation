"""
统一图件样式（出版级） —— 所有 matplotlib 结果图共用
=====================================================
- 字体：统一无衬线 Arial 族；环境无 Arial 时回退 Liberation Sans（与 Arial 度量
  完全等价的开源替身）/ DejaVu Sans；全英文标注，故无需中文字体
- 字号（校准规范 v2, 2026-09-02）：全图统一 12 号——轴标签/刻度/图例/面板序号
  均为 12 pt；面板序号 (a)(b)(c) 加粗置左上，不设描述性图标题（与前文一致）
- 线宽、刻度朝向、留白、网格、保存 dpi=300、去多余边框 —— 统一规范
- 配色：与项目一致的语义色板（见 COLORS）

用法：
    import figstyle                      # 直接 import 即生效 (设置 rcParams)
    figstyle.apply()                     # 或显式调用
    fig.savefig(path, **figstyle.SAVE)   # 统一 300dpi / tight / 白底
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ---- 字体：Arial 族优先，回退开源等价 ----
_SANS = ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"]

# 语义色板（全项目统一）
COLORS = {
    "muni":  "#2980b9",   # 市政水
    "cool":  "#17a2b8",   # 冷却水
    "power": "#c0392b",   # 电力
    "warn":  "#e74c3c",   # 信息/预警
    "ok":    "#27ae60",   # 正常/成功
    "amber": "#e08a1e",   # 冷却塔/次要
    "mut":   "#5b6b7a",   # 中性
    "PA":    "#c0392b", "SP": "#e08a1e", "DP": "#27ae60",
}

# 统一保存参数
SAVE = dict(dpi=300, bbox_inches="tight", facecolor="white")


def apply():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": _SANS,
        "font.size": 12,            # 校准规范 v2: 全图统一 12 号 (Arial)
        "axes.titlesize": 12,       # 面板序号 (a)(b)(c) 用, 加粗左上
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "figure.titlesize": 13,
        "figure.titleweight": "bold",
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#33414d",
        "axes.grid": True,
        "grid.color": "#d6dde3",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,
        "lines.linewidth": 2.0,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": True,
        "legend.framealpha": 0.92,
        "legend.edgecolor": "#c9d3dc",
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,   # TrueType 内嵌 (期刊要求可编辑字体)
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


# import 即生效
apply()
