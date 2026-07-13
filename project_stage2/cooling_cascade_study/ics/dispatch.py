"""
第三级 ICS —— 调度中心
======================
职责:
  1. 接收 SCADA 检测结果(基于市政供水压力)
  2. 厂级决策: 确认市政断供 -> 生成"跨域预警信号"
  3. 把预警传给电网调度 -> 触发主动处置(见 p3_ieee118/cascade.py 的 proactive)

简化说明(依据研究者确认):
  - 不考虑检测延时/通信丢包: 预警在检出的同一时刻即送达电网(零时延、可靠)。
"""


class DispatchCenter:
    def __init__(self, db):
        self.db = db
        self.warned = False            # 预警是否已送达电网
        self.warn_arrival_t = None     # 预警送达电网时刻(=检出时刻)
        self._detect_t = None

    def step(self, t, scada, fault_active):
        """处理 SCADA 检测结果, 检出即刻发出并送达预警(零时延)。"""
        _, detected = scada.detect_fault(t)
        if detected and self._detect_t is None:
            self._detect_t = scada._detect_t
            self.warn_arrival_t = self._detect_t     # 零时延: 送达=检出
            self.warned = True
            self.db.write_dispatch(t, "WarnIssued", "GridDispatch", 1.0,
                                   "DispatchCenter")
            self.db.write_warning(t, 1, "MuniPressure",
                                  lead_est=0.0, confidence=1.0,
                                  detail="warning issued & delivered (zero-delay)")
        return self.warned

    def total_latency(self):
        """检出到送达的时延(零时延简化 -> 0)。"""
        return 0.0 if self._detect_t is not None else None
