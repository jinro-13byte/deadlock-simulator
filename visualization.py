"""
Visualization Module
Sử dụng NetworkX và Matplotlib để vẽ trực quan Wait-for Graph và Resource Allocation Graph (RAG).
Hỗ trợ đổi màu chu trình Deadlock để người dùng dễ quan sát.
"""

from typing import List
import matplotlib.pyplot as plt
import networkx as nx
from graph import WaitForGraph
from simulator import DeadlockSimulator


def draw_wait_for_graph_matplotlib(wfg: WaitForGraph, deadlock_cycles: List[List[str]] = None):
    """
    Vẽ Wait-for Graph bằng Matplotlib và NetworkX.
    - Node an toàn: Màu xanh ngọc / lá cây
    - Node bị Deadlock: Màu đỏ cam
    - Cạnh trong chu trình Deadlock: Đỏ đậm, nét dày
    - Cạnh hai chiều u <-> v được uốn cong tránh đè nhau
    """
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    G = wfg.nx_graph

    if len(G.nodes) == 0:
        ax.text(0.5, 0.5, "Chưa có tiến trình nào trong đồ thị",
                ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        return fig

    # Xác định các node và edge nằm trong deadlock cycle
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

    # Bố cục vị trí (circular layout hoặc spring layout)
    if len(G.nodes) <= 4:
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42, k=1.2)

    # Màu sắc các đỉnh
    node_colors = []
    for node in G.nodes:
        if node in deadlock_nodes:
            node_colors.append('#FF6B6B')  # Đỏ nhạt
        else:
            node_colors.append('#51CF66')  # Xanh lá

    # Vẽ Nodes
    nx.draw_networkx_nodes(
        G, pos,
        ax=ax,
        node_color=node_colors,
        node_size=2200,
        edgecolors='#2B2D42',
        linewidths=2
    )

    # Nhãn đỉnh (tên tiến trình)
    node_labels = {p: p for p in G.nodes}
    nx.draw_networkx_labels(
        G, pos,
        labels=node_labels,
        ax=ax,
        font_size=13,
        font_weight='bold',
        font_family='sans-serif'
    )

    # Phân loại cạnh: thường và cạnh deadlock
    normal_edges = [e for e in G.edges if e not in deadlock_edges]
    dl_edges = [e for e in G.edges if e in deadlock_edges]

    # Vẽ cạnh bình thường (xanh dương, nét cong nhẹ)
    if normal_edges:
        nx.draw_networkx_edges(
            G, pos,
            edgelist=normal_edges,
            ax=ax,
            edge_color='#339AF0',
            width=2,
            arrowsize=22,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.15'
        )

    # Vẽ cạnh Deadlock (đỏ tươi, nét dày)
    if dl_edges:
        nx.draw_networkx_edges(
            G, pos,
            edgelist=dl_edges,
            ax=ax,
            edge_color='#E03131',
            width=3.5,
            arrowsize=26,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.15'
        )

    # Nhãn trên cạnh (hiển thị tài nguyên đang chờ)
    edge_labels = {}
    for (u, v), res_list in wfg.edge_reasons.items():
        edge_labels[(u, v)] = f"chờ {','.join(res_list)}"

    # Vẽ nhãn cạnh
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        ax=ax,
        font_size=9,
        font_color='#1C7ED6',
        label_pos=0.4,
        rotate=False
    )

    # Chú thích góc đồ thị
    title = "Wait-for Graph (Đồ thị chờ)"
    if deadlock_cycles:
        title += " - [PHÁT HIỆN DEADLOCK]"
        ax.set_title(title, fontsize=14, fontweight='bold', color='#C92A2A', pad=15)
    else:
        title += " - [TRẠNG THÁI AN TOÀN]"
        ax.set_title(title, fontsize=14, fontweight='bold', color='#2B8A3E', pad=15)

    ax.axis('off')
    plt.tight_layout()
    return fig


def draw_resource_allocation_graph_matplotlib(simulator: DeadlockSimulator):
    """
    Vẽ Đồ thị Cấp phát Tài nguyên (Resource Allocation Graph - RAG).
    - Tiến trình: Hình tròn (Nodes)
    - Tài nguyên: Hình vuông (Nodes)
    - Cạnh Resource -> Process: Tài nguyên đã được cấp phát (Assignment edge)
    - Cạnh Process -> Resource: Tiến trình đang yêu cầu tài nguyên (Request edge)
    """
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    RAG = nx.DiGraph()

    for p in simulator.processes:
        RAG.add_node(p, bipartite=0, type='process')

    for r in simulator.resources:
        RAG.add_node(r, bipartite=1, type='resource')

    # Cạnh cấp phát: Resource -> Process
    assignment_edges = []
    for r, holder in simulator.allocation.items():
        if holder:
            RAG.add_edge(r, holder)
            assignment_edges.append((r, holder))

    # Cạnh yêu cầu: Process -> Resource
    request_edges = []
    for p, req_set in simulator.requests.items():
        for r in req_set:
            RAG.add_edge(p, r)
            request_edges.append((p, r))

    if len(RAG.nodes) == 0:
        ax.text(0.5, 0.5, "Chưa có tiến trình hoặc tài nguyên nào",
                ha='center', va='center', fontsize=14, color='gray')
        ax.axis('off')
        return fig

    pos = nx.spring_layout(RAG, seed=123, k=1.0)

    # Vẽ Process nodes (Tròn, Xanh dương)
    p_nodes = [n for n in RAG.nodes if RAG.nodes[n].get('type') == 'process']
    nx.draw_networkx_nodes(
        RAG, pos,
        nodelist=p_nodes,
        ax=ax,
        node_shape='o',
        node_color='#D0EBFF',
        node_size=1800,
        edgecolors='#1864AB',
        linewidths=2
    )

    # Vẽ Resource nodes (Vuông, Cam)
    r_nodes = [n for n in RAG.nodes if RAG.nodes[n].get('type') == 'resource']
    nx.draw_networkx_nodes(
        RAG, pos,
        nodelist=r_nodes,
        ax=ax,
        node_shape='s',
        node_color='#FFE8CC',
        node_size=1800,
        edgecolors='#D9480F',
        linewidths=2
    )

    # Nhãn nodes
    nx.draw_networkx_labels(RAG, pos, ax=ax, font_size=11, font_weight='bold')

    # Cạnh cấp phát (R -> P): Màu xanh lá, nét liền
    if assignment_edges:
        nx.draw_networkx_edges(
            RAG, pos,
            edgelist=assignment_edges,
            ax=ax,
            edge_color='#2F9E44',
            width=2.5,
            arrowsize=20,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )

    # Cạnh yêu cầu (P -> R): Màu cam/đỏ, nét đứt
    if request_edges:
        nx.draw_networkx_edges(
            RAG, pos,
            edgelist=request_edges,
            ax=ax,
            edge_color='#E8590C',
            width=2,
            style='dashed',
            arrowsize=20,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )

    ax.set_title("Resource Allocation Graph (RAG)", fontsize=14, fontweight='bold', color='#1864AB', pad=15)
    ax.axis('off')
    plt.tight_layout()
    return fig
