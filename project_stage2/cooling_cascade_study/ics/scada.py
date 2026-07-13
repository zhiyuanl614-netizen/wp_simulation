"""
第二级 ICS —— SCADA
===================
职责:
  1. 数据汇集 + 历史归档(写 SQLite)
  2. 故障检测: 仅监测【市政供水压力水头】(源头信号)
  3. 上传监控数据到调度层

简化说明(依据研究者确认):
  - 检测只考虑市政供水压力侧: 补水箱/集水池/凝汽器背压均属电力系统内部子系统,
    彼此存在交互, 不作为独立预警监测点。
  - 不考虑检测延时/丢包/漏报: 一旦市政压头跌破阈值即刻可靠检出。
  - 只区分"有无早期预警"两种情形(warning on/off), 不做多策略对比。
"""


class SCADA:
    # 市政供水压力阈值(可整定): 低于此判为市政断供
    P_MUNI_TRIP = 5.0        # m (正常约 25 m)
    # 告警(集水池水位, 仅作监视记录, 不用于预警触发)
    ALARM_WARN = 2.2
    ALARM_CRIT = 1.5

    def __init__(self, db, warning_enabled=True):
        self.db = db
        self.warning_enabled = warning_enabled   # 是否启用早期预警(有/无)
        self.monitor = {}
        self._detected = False
        self._detect_t = None

    def collect(self, t, readings, actuators):
        """归档传感器与执行器数据。"""
        self.monitor = {"readings": readings, "actuators": actuators}
        for sid, val in readings.items():
            unit = {"p_muni": "m", "H_tank": "m", "H_pool": "m",
                    "m_cw": "m3/s", "p_b": "kPa", "make_flow": "m3/s"}.get(sid, "")
            self.db.write_sensor(t, sid, val, unit)
        for aid, sta in actuators.items():
            self.db.write_actuator(t, aid, sta, "PLC")

    def detect_fault(self, t):
        """基于【市政供水压力】判定是否检出故障。检出后锁存。
        无早期预警(warning_enabled=False)时永不检出。
        返回 (detected_now, detected_latched)。"""
        if not self.warning_enabled:
            return False, False
        if self._detected:
            return False, True
        r = self.monitor.get("readings", {})
        hit = r.get("p_muni", 99) < self.P_MUNI_TRIP
        if hit:
            self._detected = True
            self._detect_t = t
        return hit, self._detected

    def monitor_and_alarm(self, t, fault_active):
        """告警分级(仅监视记录)。"""
        r = self.monitor.get("readings", {})
        hp = r.get("H_pool", 9.0)
        if hp < self.ALARM_CRIT:
            code, msg = 2, "CRITICAL: cooling basin extremely low"
        elif hp < self.ALARM_WARN:
            code, msg = 1, "WARNING: cooling basin low"
        else:
            code, msg = 0, ""
        detail = (f"p_muni:{r.get('p_muni',0):.1f}m H_pool:{hp:.2f}m "
                  f"warning:{int(self.warning_enabled)} fault:{int(fault_active)}")
        self.db.write_monitor(t, code, msg, detail)
        self.monitor["alarm_code"] = code
        return code, msg

    def upload(self):
        return dict(self.monitor)
