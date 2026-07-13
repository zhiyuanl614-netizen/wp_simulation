"""
ICS 数据库层 (SQLite)
=====================
参照用户提供的市政供水 ICS 代码, 适配冷却水—电网耦合场景。
全过程归档: 传感器 / 执行器 / 告警 / 调度 / 跨域预警 / 快照。
便于审计回放与统计分析。
"""
import sqlite3
import os


class ICSDatabase:
    """冷却水 ICS 专用数据库"""

    def __init__(self, db_path="../results/ics_sim.db", reset=True):
        here = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(here, db_path) if not os.path.isabs(db_path) else db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if reset and os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        # 传感器: 市政压头/水箱水位/集水池水位/循环水流量/背压
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp REAL, sensor_id TEXT, value REAL, unit TEXT,
            is_fault INTEGER DEFAULT 0)''')
        # 执行器: 补水阀/循环水泵
        c.execute('''CREATE TABLE IF NOT EXISTS actuator_cmd (
            timestamp REAL, actuator_id TEXT, status REAL, source TEXT DEFAULT "PLC")''')
        # 告警
        c.execute('''CREATE TABLE IF NOT EXISTS monitor_status (
            timestamp REAL, status_code INTEGER, alarm_msg TEXT, detail TEXT)''')
        # 调度指令
        c.execute('''CREATE TABLE IF NOT EXISTS dispatch_cmd (
            timestamp REAL, cmd_type TEXT, target TEXT, value REAL, source TEXT)''')
        # 跨域预警信号 (本项目核心新增)
        c.execute('''CREATE TABLE IF NOT EXISTS warning_signal (
            timestamp REAL, issued INTEGER, strategy TEXT,
            lead_est_s REAL, confidence REAL, detail TEXT)''')
        # 全系统快照
        c.execute('''CREATE TABLE IF NOT EXISTS network_snapshot (
            timestamp REAL, muni_head REAL, H_tank REAL, H_pool REAL,
            m_cw REAL, p_b REAL, pump_on INTEGER, gen_tripped INTEGER,
            grid_freq REAL, warned INTEGER, fault_active INTEGER)''')
        self.conn.commit()

    # ---- 写入 ----
    def write_sensor(self, t, sid, value, unit='', is_fault=0):
        self.conn.execute('INSERT INTO sensor_data VALUES (?,?,?,?,?)',
                          (float(t), sid, float(value), unit, int(is_fault)))

    def write_actuator(self, t, aid, status, source='PLC'):
        self.conn.execute('INSERT INTO actuator_cmd VALUES (?,?,?,?)',
                          (float(t), aid, float(status), source))

    def write_monitor(self, t, code, alarm='', detail=''):
        self.conn.execute('INSERT INTO monitor_status VALUES (?,?,?,?)',
                          (float(t), int(code), alarm, detail))

    def write_dispatch(self, t, cmd_type, target, value, source):
        self.conn.execute('INSERT INTO dispatch_cmd VALUES (?,?,?,?,?)',
                          (float(t), cmd_type, target, float(value), source))

    def write_warning(self, t, issued, strategy, lead_est, confidence, detail=''):
        self.conn.execute('INSERT INTO warning_signal VALUES (?,?,?,?,?,?)',
                          (float(t), int(issued), strategy,
                           float(lead_est), float(confidence), detail))

    def write_snapshot(self, t, muni, ht, hp, mcw, pb, pump, gtrip,
                       freq, warned, fault):
        self.conn.execute('INSERT INTO network_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                          (float(t), float(muni), float(ht), float(hp), float(mcw),
                           float(pb), int(pump), int(gtrip), float(freq),
                           int(warned), int(fault)))

    def commit(self):
        self.conn.commit()

    def query_df(self, table):
        import pandas as pd
        return pd.read_sql_query(f"SELECT * FROM {table}", self.conn)

    def close(self):
        self.conn.commit()
        self.conn.close()
