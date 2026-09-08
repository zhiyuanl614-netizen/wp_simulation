"""
第一级 ICS —— 现场 PLC
======================
职责:
  1. 传感器采样 (带采样周期): 市政压头/补水箱水位/集水池水位/循环水流量/背压
  2. 本地自动控制封装: 补水阀/集水池阀(液位闭环, 物理层已实现) + 泵/汽机保护标志

采样与物理层解耦: 物理层连续演化, PLC 每 sample_dt 采一次(零阶保持)。
"""


class FieldPLC:
    def __init__(self, sample_dt=1.0):
        self.sample_dt = sample_dt          # 采样周期 s
        self.last_sample_t = -1e9
        self.readings = {}                  # 最近一次采样值(ZOH)

    def acquire(self, t, phys):
        """从物理层状态 phys(dict) 采样传感器。仅在采样时刻更新, 否则保持。"""
        if t - self.last_sample_t + 1e-9 >= self.sample_dt:
            self.readings = {
                "p_muni": phys["muni_head"],     # 市政等效供水压头 m
                "H_tank": phys["H_tank"],        # 补水箱水位 m
                "H_pool": phys["H_pool"],        # 集水池水位 m
                "m_cw":   phys["m_cw"],          # 循环水流量 m^3/s
                "p_b":    phys["p_b"],           # 凝汽器背压 kPa
                "make_flow": phys.get("make_flow", 0.0),  # 市政补水流量 m^3/s
            }
            self.last_sample_t = t
        return dict(self.readings)

    def local_control_status(self, phys):
        """本地执行器状态(物理层液位阀已自动, 此处仅汇报状态)。"""
        return {
            "makeup_valve": 1 if phys.get("make_flow", 0.0) > 1e-6 else 0,
            "circ_pump":    0 if phys.get("pump_tripped", False) else 1,
        }
