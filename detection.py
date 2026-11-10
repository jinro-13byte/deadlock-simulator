"""
Deadlock Detection Module using Depth-First Search (DFS)
Phát hiện chu trình trong Wait-for Graph.
Đối với tài nguyên đơn vị (Single-instance resources),
sự tồn tại của chu trình trên Wait-for Graph đồng nghĩa với DEADLOCK.
"""

from typing import Dict, List, Set, Tuple
from graph import WaitForGraph


class DeadlockDetector:
    def __init__(self, wait_for_graph: WaitForGraph):
        self.wfg = wait_for_graph
        self.simulator = wait_for_graph.simulator
        self.adj = wait_for_graph.adj

    def detect_deadlock(self) -> dict:
        """
        Thực hiện thuật toán DFS tìm chu trình trên đồ thị có hướng.
        Sử dụng trạng thái 3 màu:
        0: UNVISITED (Chưa thăm)
        1: VISITING (Đang trong ngăn xếp đệ quy hiện tại)
        2: VISITED (Đã duyệt xong hoàn toàn)
        """
        color: Dict[str, int] = {p: 0 for p in self.simulator.processes}
        parent_path: List[str] = []
        cycles: List[List[str]] = []
        visited_cycles_signatures: Set[Tuple[str, ...]] = set()

        def dfs(u: str):
            color[u] = 1
            parent_path.append(u)

            for v in self.adj.get(u, []):
                if color[v] == 1:
                    # Tìm thấy back-edge -> Phát hiện chu trình!
                    cycle_start_idx = parent_path.index(v)
                    cycle = parent_path[cycle_start_idx:] + [v]

                    # Chuẩn hóa chu trình để tránh trùng lặp
                    # (ví dụ: P1->P2->P1 và P2->P1->P2)
                    cycle_nodes = cycle[:-1]
                    min_idx = cycle_nodes.index(min(cycle_nodes))
                    canonical = tuple(cycle_nodes[min_idx:] + cycle_nodes[:min_idx])

                    if canonical not in visited_cycles_signatures:
                        visited_cycles_signatures.add(canonical)
                        cycles.append(cycle)

                elif color[v] == 0:
                    dfs(v)

            parent_path.pop()
            color[u] = 2

        # Duyệt DFS qua tất cả các tiến trình
        for p in self.simulator.processes:
            if color[p] == 0:
                dfs(p)

        has_deadlock = len(cycles) > 0
        deadlocked_processes = set()
        for c in cycles:
            deadlocked_processes.update(c[:-1])

        reasons = self._generate_explanations(cycles)
        recommendations = self._generate_recommendations(cycles)

        return {
            "has_deadlock": has_deadlock,
            "cycles": cycles,
            "deadlocked_processes": sorted(list(deadlocked_processes)),
            "reasons": reasons,
            "recommendations": recommendations,
        }

    def _generate_explanations(self, cycles: List[List[str]]) -> List[str]:
        """Tạo giải thích chi tiết nguyên nhân dẫn đến Deadlock."""
        explanations = []
        for idx, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle)
            details = []
            for i in range(len(cycle) - 1):
                u = cycle[i]
                v = cycle[i + 1]
                res_list = self.wfg.edge_reasons.get((u, v), [])
                res_str = ", ".join(res_list) if res_list else "tài nguyên"
                details.append(f"{u} đang chờ {res_str} do {v} nắm giữ")

            explanation = (
                f"Chu trình {idx}: {cycle_str}\n"
                f"Nguyên nhân: {'; '.join(details)}."
            )
            explanations.append(explanation)
        return explanations

    def _generate_recommendations(self, cycles: List[List[str]]) -> List[dict]:
        """Đề xuất phương án kết thúc tiến trình để phá vỡ chu trình Deadlock."""
        recommendations = []
        for cycle in cycles:
            cycle_procs = cycle[:-1]
            # Đánh giá tiến trình nào nên kết thúc
            # Tiêu chí: tiến trình giữ nhiều tài nguyên nhất hoặc có yêu cầu trong chu trình
            for p in cycle_procs:
                held = self.simulator.get_held_resources(p)
                recommendations.append({
                    "process": p,
                    "held_resources": held,
                    "advice": (
                        f"Kết thúc tiến trình {p} để giải phóng các tài nguyên ({', '.join(held) if held else 'không có'}). "
                        f"Sau đó các tài nguyên này có thể cấp phát cho các tiến trình đang chờ."
                    )
                })
        return recommendations
