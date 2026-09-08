"""
Shelby County Benchmark Data Processing and Standardization.

Converts raw Extended Shelby County CSV data into:
1. Standardized CSV tables (nodes, arcs, generators, substations, tanks, pumps, coupling)
2. PYPOWER / MATPOWER case dictionary for DC power flow
3. WNTR water network model definition
4. Interdependent water-power coupling map
"""

import os
import csv
import json
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_extended")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_csv_dict(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def process_water_network():
    nodes_raw = load_csv_dict(os.path.join(RAW_DIR, "WaterNodes.csv"))
    arcs_raw = load_csv_dict(os.path.join(RAW_DIR, "WaterArcs.csv"))
    
    nodes_out = []
    for r in nodes_raw:
        nid = int(r["ID"])
        ntype = r["Node Type"].strip()
        x = float(r["X"])
        y = float(r["Y"])
        demand = float(r["Demand"])
        pop = int(float(r["population"])) if r["population"] and r["population"] != "N/A" else 0
        income = float(r["Median income (dollars)"]) if r["Median income (dollars)"] and r["Median income (dollars)"] != "N/A" else 0.0
        
        # Categorize node
        category = "DISTRIBUTION"
        if "Storage" in ntype or "Tank" in ntype:
            category = "TANK"
        elif "Pump" in ntype:
            category = "PUMP_STATION"
            
        nodes_out.append({
            "node_id": nid,
            "category": category,
            "raw_type": ntype,
            "lon": x,
            "lat": y,
            "demand_rate": demand,  # positive = supply/capacity, negative = consumer demand
            "population": pop,
            "median_income": income
        })
        
    pipes_out = []
    for r in arcs_raw:
        aid = int(r["ID"])
        u = float(r["u"])
        l_km = float(r["Length (km)"])
        src = int(r["Start Node"])
        dst = int(r["End Node"])
        pipes_out.append({
            "pipe_id": aid,
            "from_node": src,
            "to_node": dst,
            "length_km": l_km,
            "capacity_u": u,
            "cost_f": float(r["f"]),
            "cost_c": float(r["c"])
        })
        
    return nodes_out, pipes_out

def process_power_network():
    nodes_raw = load_csv_dict(os.path.join(RAW_DIR, "PowerNodes.csv"))
    arcs_raw = load_csv_dict(os.path.join(RAW_DIR, "PowerArcs.csv"))
    
    buses_out = []
    gens_out = []
    
    for r in nodes_raw:
        nid = int(r["ID"])
        ntype = r["Node Type"].strip()
        x = float(r["X"])
        y = float(r["Y"])
        demand_val = float(r["Demand"])
        
        base_kv = 115.0
        bus_type = 1 # PQ
        
        if "Gate" in ntype:
            bus_type = 2 # PV (or Slack for node 0)
            base_kv = 115.0
            pmax = demand_val if demand_val > 0 else 100.0
            gens_out.append({
                "gen_id": len(gens_out) + 1,
                "bus_id": nid,
                "pmax_mw": pmax,
                "pmin_mw": 0.0,
                "pg_mw": pmax * 0.75, # initial dispatch
                "qmax_mvar": pmax * 0.5,
                "qmin_mvar": -pmax * 0.2
            })
            pd_mw = 0.0
        elif "23kV" in ntype:
            base_kv = 23.0
            pd_mw = abs(demand_val)
        elif "12kV" in ntype:
            base_kv = 12.0
            pd_mw = abs(demand_val)
        else: # Intersection
            base_kv = 115.0
            pd_mw = 0.0
            
        buses_out.append({
            "bus_id": nid,
            "bus_type": 3 if nid == 0 else bus_type, # Node 0 as Slack
            "raw_type": ntype,
            "base_kv": base_kv,
            "lon": x,
            "lat": y,
            "pd_mw": pd_mw,
            "qd_mvar": pd_mw * 0.2
        })
        
    branches_out = []
    for r in arcs_raw:
        aid = int(r["ID"])
        src = int(r["Start Node"])
        dst = int(r["End Node"])
        l_km = float(r["Length (km)"])
        u_cap = float(r["u"])
        
        # Approximate transmission reactance: ~0.0008 pu/km on 100 MVA base, r ~ 0.0001 pu/km
        # Minimum reactance to avoid numerical singularity
        x_pu = max(0.005, l_km * 0.001)
        r_pu = x_pu * 0.1
        
        branches_out.append({
            "branch_id": aid,
            "from_bus": src,
            "to_bus": dst,
            "r_pu": r_pu,
            "x_pu": x_pu,
            "b_pu": 0.0,
            "rateA_mw": u_cap if u_cap > 1.0 else 50.0,
            "length_km": l_km
        })
        
    return buses_out, gens_out, branches_out

def process_interdependencies():
    interdep_raw = load_csv_dict(os.path.join(RAW_DIR, "Interdep.csv"))
    
    # Standardize coupling map
    coupling_out = []
    for r in interdep_raw:
        src_node = int(r["Dependee Node"])
        dst_node = int(r["Depender Node"])
        src_net = r["Dependee Network"].strip()
        dst_net = r["Depender Network"].strip()
        coupling_type = r["Type"].strip()
        
        coupling_out.append({
            "dependee_net": src_net,
            "dependee_node": src_node,
            "depender_net": dst_net,
            "depender_node": dst_node,
            "coupling_type": coupling_type
        })
    return coupling_out

def write_csv(filepath, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {filepath} ({len(rows)} records)")

def generate_pypower_case(buses, gens, branches, filepath):
    """Generate executable Python module with PYPOWER case structure."""
    lines = [
        "# PYPOWER case format for Shelby County Power Network",
        "# 75 Buses (9 Gate Stations, 17 23kV substations, 25 12kV substations, 24 Intersections)",
        "# 93 Transmission Lines, 9 Generators",
        "import numpy as np",
        "",
        "def case_shelby():",
        "    ppc = {'version': '2'}",
        "    ppc['baseMVA'] = 100.0",
        "",
        "    # bus data: [bus_i, type, Pd, Qd, Gs, Bs, area, Vm, Va, baseKV, zone, Vmax, Vmin]",
        "    ppc['bus'] = np.array(["
    ]
    
    for b in buses:
        bid = b["bus_id"]
        btype = b["bus_type"]
        pd = b["pd_mw"]
        qd = b["qd_mvar"]
        bkv = b["base_kv"]
        lines.append(f"        [{bid}, {btype}, {pd:.4f}, {qd:.4f}, 0.0, 0.0, 1, 1.0, 0.0, {bkv:.1f}, 1, 1.1, 0.9],")
    lines.append("    ])")
    lines.append("")
    
    lines.append("    # gen data: [bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, ...]")
    lines.append("    ppc['gen'] = np.array([")
    for g in gens:
        bid = g["bus_id"]
        pg = g["pg_mw"]
        pmax = g["pmax_mw"]
        pmin = g["pmin_mw"]
        qmax = g["qmax_mvar"]
        qmin = g["qmin_mvar"]
        lines.append(f"        [{bid}, {pg:.2f}, 0.0, {qmax:.2f}, {qmin:.2f}, 1.0, 100.0, 1, {pmax:.2f}, {pmin:.2f}],")
    lines.append("    ])")
    lines.append("")
    
    lines.append("    # branch data: [fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax]")
    lines.append("    ppc['branch'] = np.array([")
    for br in branches:
        fbus = br["from_bus"]
        tbus = br["to_bus"]
        r = br["r_pu"]
        x = br["x_pu"]
        b = br["b_pu"]
        rateA = br["rateA_mw"]
        lines.append(f"        [{fbus}, {tbus}, {r:.5f}, {x:.5f}, {b:.5f}, {rateA:.2f}, {rateA*1.2:.2f}, {rateA*1.5:.2f}, 0.0, 0.0, 1, -360.0, 360.0],")
    lines.append("    ])")
    lines.append("")
    lines.append("    return ppc")
    lines.append("")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated PYPOWER case: {filepath}")

def generate_wntr_script(nodes, pipes, filepath):
    """Generate WNTR network builder script for Shelby County water distribution system."""
    lines = [
        "# WNTR Water Network Builder for Shelby County Water Supply System",
        "# 49 Nodes (6 Tanks, 9 Pumping Stations, 34 Distribution Nodes), 71 Pipes",
        "import wntr",
        "",
        "def build_shelby_water_network():",
        "    wn = wntr.network.WaterNetworkModel()",
        "    wn.options.time.duration = 24 * 3600",
        "    wn.options.time.hydraulic_timestep = 3600",
        "    wn.options.time.report_timestep = 3600",
        "    wn.options.hydraulic.headloss = 'H-W'",
        "",
        "    # Add junctions, reservoirs/tanks",
    ]
    
    for n in nodes:
        nid = f"J_{n['node_id']}"
        cat = n["category"]
        elev = 70.0 + (n["node_id"] % 10) * 3.0 # Estimated elevation 70-100m
        if cat == "TANK":
            lines.append(f"    wn.add_tank('{nid}', elevation={elev:.1f}, init_level=5.0, min_level=1.0, max_level=12.0, diameter=25.0, coordinates=({n['lon']:.4f}, {n['lat']:.4f}))")
        elif cat == "PUMP_STATION":
            # Model pump station as reservoir source + booster pump
            res_id = f"RES_{n['node_id']}"
            lines.append(f"    wn.add_reservoir('{res_id}', base_head={elev+30.0:.1f}, coordinates=({n['lon']:.4f}, {n['lat']:.4f}))")
            lines.append(f"    wn.add_junction('{nid}', elevation={elev:.1f}, base_demand=0.0, coordinates=({n['lon']:.4f}, {n['lat']:.4f}))")
            lines.append(f"    wn.add_pipe('P_SRC_{n['node_id']}', '{res_id}', '{nid}', length=50.0, diameter=0.6, roughness=130)")
        else:
            base_dem = abs(n["demand_rate"]) * 0.001 # m3/s scaling
            lines.append(f"    wn.add_junction('{nid}', elevation={elev:.1f}, base_demand={base_dem:.4f}, coordinates=({n['lon']:.4f}, {n['lat']:.4f}))")
            
    lines.append("")
    lines.append("    # Add pipes")
    for p in pipes:
        pid = f"PIPE_{p['pipe_id']}"
        src = f"J_{p['from_node']}"
        dst = f"J_{p['to_node']}"
        l_m = max(50.0, p["length_km"] * 1000.0)
        diam = 0.4 # 400mm default
        lines.append(f"    wn.add_pipe('{pid}', '{src}', '{dst}', length={l_m:.1f}, diameter={diam:.2f}, roughness=120)")
        
    lines.append("")
    lines.append("    return wn")
    lines.append("")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated WNTR builder script: {filepath}")

def main():
    print("=== Processing Shelby County Benchmark Data ===")
    
    # 1. Process water
    water_nodes, water_pipes = process_water_network()
    write_csv(os.path.join(PROCESSED_DIR, "shelby_water_nodes.csv"), water_nodes)
    write_csv(os.path.join(PROCESSED_DIR, "shelby_water_pipes.csv"), water_pipes)
    
    # 2. Process power
    power_buses, power_gens, power_branches = process_power_network()
    write_csv(os.path.join(PROCESSED_DIR, "shelby_power_buses.csv"), power_buses)
    write_csv(os.path.join(PROCESSED_DIR, "shelby_power_gens.csv"), power_gens)
    write_csv(os.path.join(PROCESSED_DIR, "shelby_power_branches.csv"), power_branches)
    
    # 3. Process interdependencies
    coupling = process_interdependencies()
    write_csv(os.path.join(PROCESSED_DIR, "shelby_coupling_map.csv"), coupling)
    
    # 4. Generate models
    generate_pypower_case(power_buses, power_gens, power_branches, os.path.join(PROCESSED_DIR, "case_shelby.py"))
    generate_wntr_script(water_nodes, water_pipes, os.path.join(PROCESSED_DIR, "shelby_water_wntr.py"))
    
    # 5. Summary statistics
    stats = {
        "dataset_name": "Shelby County Interdependent Infrastructure Benchmark",
        "location": "Shelby County, Tennessee, USA (Memphis Metropolitan Area)",
        "source_authorities": ["MLGW (Memphis Light, Gas and Water)", "TVA (Tennessee Valley Authority)"],
        "literature_foundations": [
            "Chang et al. (1996) MCEER-96-0011",
            "Shinozuka et al. (1998) MCEER-98-MN02",
            "Adachi & Ellingwood (2008) RESS 93(1):78-88",
            "Gonzalez et al. (2016) CA-CIE 31(5):334-350",
            "Wang, Magoua & Li (2022) Autom. Constr. 133:104008"
        ],
        "power_network": {
            "total_buses": len(power_buses),
            "gate_stations_generators": len(power_gens),
            "substations_23kv": len([b for b in power_buses if "23kV" in b["raw_type"]]),
            "substations_12kv": len([b for b in power_buses if "12kV" in b["raw_type"]]),
            "intersections": len([b for b in power_buses if "Intersection" in b["raw_type"]]),
            "transmission_lines": len(power_branches),
            "total_generation_capacity_mw": sum(g["pmax_mw"] for g in power_gens),
            "total_load_demand_mw": sum(b["pd_mw"] for b in power_buses)
        },
        "water_network": {
            "total_nodes": len(water_nodes),
            "storage_tanks": len([n for n in water_nodes if n["category"] == "TANK"]),
            "pumping_stations": len([n for n in water_nodes if n["category"] == "PUMP_STATION"]),
            "distribution_nodes": len([n for n in water_nodes if n["category"] == "DISTRIBUTION"]),
            "pipes": len(water_pipes),
            "total_supply_capacity": sum(n["demand_rate"] for n in water_nodes if n["demand_rate"] > 0),
            "total_customer_demand": sum(abs(n["demand_rate"]) for n in water_nodes if n["demand_rate"] < 0)
        },
        "interdependency": {
            "total_coupling_links": len(coupling),
            "power_to_water": len([c for c in coupling if c["dependee_net"] == "Power" and c["depender_net"] == "Water"]),
            "water_to_power": len([c for c in coupling if c["dependee_net"] == "Water" and c["depender_net"] == "Power"]),
            "power_to_gas": len([c for c in coupling if c["dependee_net"] == "Power" and c["depender_net"] == "Gas"]),
            "gas_to_power": len([c for c in coupling if c["dependee_net"] == "Gas" and c["depender_net"] == "Power"]),
            "power_to_telecom": len([c for c in coupling if c["dependee_net"] == "Power" and c["depender_net"] == "Telecommunication"]),
            "telecom_to_power": len([c for c in coupling if c["dependee_net"] == "Telecommunication" and c["depender_net"] == "Power"])
        }
    }
    
    with open(os.path.join(PROCESSED_DIR, "shelby_summary_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print("Saved summary statistics JSON.")

if __name__ == "__main__":
    main()
