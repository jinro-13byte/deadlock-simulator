"""
Wait-for Graph Builder
Xây dựng Đồ thị chờ (Wait-for Graph) từ trạng thái của Simulator.
Quy tắc:
- Các đỉnh (Nodes) là các tiến trình (Processes).
- Có cạnh có hướng P_i -> P_j nếu P_i đang yêu cầu một tài nguyên mà P_j đang nắm giữ.
"""

from typing import Dict, List, Tuple
import networkx as nx
from simulator import DeadlockSimulator


class WaitForGraph:
    def __init__(self, simulator: DeadlockSimulator):
        self.simulator = simulator
        # Danh sách kề: process -> list các process mà nó đang chờ
        self.adj: Dict[str, List[str]] = {p: [] for p in simulator.processes}
        # Chi tiết cạnh: (Pi, Pj) -> danh sách tài nguyên Pj đang giữ mà Pi chờ
        self.edge_reasons: Dict[Tuple[str, str], List[str]] = {}
        # NetworkX DiGraph
        self.nx_graph = nx.DiGraph()

        self._build_graph()

    def _build_graph(self):
        # Thêm tất cả processes vào đồ thị
        for p in self.simulator.processes:
            self.nx_graph.add_node(p)

        # Kiểm tra từng tiến trình và tài nguyên nó yêu cầu
        for pi in self.simulator.processes:
            requested_res = self.simulator.get_requested_resources(pi)
            for res in requested_res:
                holder = self.simulator.allocation.get(res)
                # Nếu tài nguyên đang bị một tiến trình khác (pj != pi) nắm giữ
                if holder and holder != pi and holder in self.simulator.processes:
                    pj = holder
                    if pj not in self.adj[pi]:
                        self.adj[pi].append(pj)

                    edge_key = (pi, pj)
                    if edge_key not in self.edge_reasons:
                        self.edge_reasons[edge_key] = []
                    self.edge_reasons[edge_key].append(res)

                    self.nx_graph.add_edge(
                        pi, pj,
                        resource=res,
                        resources=self.edge_reasons[edge_key]
                    )

    def get_edges(self) -> List[Tuple[str, str, List[str]]]:
        """Trả về danh sách các cạnh (Pi, Pj, [R...])"""
        return [(u, v, self.edge_reasons[(u, v)]) for u, v in self.nx_graph.edges()]

    def to_dot(self, deadlock_cycles: List[List[str]] = None) -> str:
        """Xuất định dạng DOT (Graphviz) để render cực nét trên Streamlit."""
        deadlock_nodes = set()
        deadlock_edges = set()

        if deadlock_cycles:
            for cycle in deadlock_cycles:
                for i in range(len(cycle) - 1):
                    u = cycle[i]
                    v = cycle[i + 1]
                    deadlock_nodes.add(u)
                    deadlock_nodes.add(v)
                    deadlock_edges.add((u, v))

        dot_lines = [
            'digraph WaitForGraph {',
            '  rankdir=LR;',
            '  bgcolor="transparent";',
            '  node [shape=circle, fontname="Helvetica-Bold", fontsize=14, style=filled, penwidth=2];',
            '  edge [fontname="Helvetica", fontsize=11, penwidth=2];'
        ]

        # Định nghĩa các node
        for p in self.simulator.processes:
            held = self.simulator.get_held_resources(p)
            req = self.simulator.get_requested_resources(p)
            label = f"{p}\\nHolds: {','.join(held) if held else 'None'}\\nReq: {','.join(req) if req else 'None'}"

            if p in deadlock_nodes:
                dot_lines.append(
                    f'  "{p}" [label="{label}", fillcolor="#FFE5E5", color="#E53935", fontcolor="#B71C1C"];'
                )
            else:
                dot_lines.append(
                    f'  "{p}" [label="{label}", fillcolor="#E8F5E9", color="#43A047", fontcolor="#1B5E20"];'
                )

        # Định nghĩa các edge
        for (u, v), res_list in self.edge_reasons.items():
            res_label = f"chờ {','.join(res_list)}"
            if (u, v) in deadlock_edges:
                dot_lines.append(
                    f'  "{u}" -> "{v}" [label="{res_label}", color="#E53935", fontcolor="#C62828", penwidth=3];'
                )
            else:
                dot_lines.append(
                    f'  "{u}" -> "{v}" [label="{res_label}", color="#1E88E5", fontcolor="#0D47A1"];'
                )

        dot_lines.append('}')
        return '\n'.join(dot_lines)
