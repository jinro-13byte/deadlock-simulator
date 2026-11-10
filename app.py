"""
Deadlock Detection and Recovery Simulator
Giao diện người dùng Streamlit đơn giản, học thuật, không icon và không bo góc.
"""

import streamlit as st
import json
import os
import matplotlib.pyplot as plt

from simulator import DeadlockSimulator
from graph import WaitForGraph
from detection import DeadlockDetector
from recovery import DeadlockRecovery
from visualization import (
    draw_wait_for_graph_matplotlib,
    draw_resource_allocation_graph_matplotlib,
)

# Cấu hình trang tối giản
st.set_page_config(
    page_title="Deadlock Simulator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS loại bỏ toàn bộ bo góc (border-radius: 0), bỏ gradient và hiệu ứng bóng đổ
st.markdown("""
<style>
    /* Bỏ bo góc và đổ bóng cho toàn bộ thành phần */
    *, *::before, *::after {
        border-radius: 0px !important;
        box-shadow: none !important;
    }
    
    /* Nút bấm phẳng, vuông góc */
    .stButton>button, .stDownloadButton>button {
        border-radius: 0px !important;
        border: 1px solid #333333 !important;
        box-shadow: none !important;
        font-weight: 500;
    }
    
    /* Ô nhập dữ liệu, selectbox, multiselect phẳng */
    div[data-baseweb="select"] > div, input, textarea {
        border-radius: 0px !important;
    }

    /* Các khối thông báo phẳng */
    div[data-testid="stAlert"] {
        border-radius: 0px !important;
        border-left-width: 4px !important;
    }

    /* Tab phẳng */
    button[data-baseweb="tab"] {
        border-radius: 0px !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "simulator" not in st.session_state:
        sim = DeadlockSimulator()
        default_file = os.path.join(os.path.dirname(__file__), "examples", "deadlock.json")
        if os.path.exists(default_file):
            with open(default_file, "r", encoding="utf-8") as f:
                sim.from_dict(json.load(f))
        else:
            sim.add_process("P1")
            sim.add_process("P2")
            sim.add_resource("R1")
            sim.add_resource("R2")
            sim.assign_resource("P1", "R1")
            sim.assign_resource("P2", "R2")
            sim.request_resource("P1", "R2")
            sim.request_resource("P2", "R1")
        st.session_state.simulator = sim

    if "last_detection" not in st.session_state:
        st.session_state.last_detection = None


init_session_state()
sim: DeadlockSimulator = st.session_state.simulator


# ==========================================
# SIDEBAR: Cấu hình và Kịch bản mẫu
# ==========================================
with st.sidebar:
    st.subheader("Cấu hình & Kịch bản")

    preset_choice = st.selectbox(
        "Kịch bản mẫu:",
        [
            "-- Chọn kịch bản --",
            "1. Chờ vòng tròn (Deadlock 2 tiến trình)",
            "2. Chờ một chiều (Chaining - An toàn)",
            "3. Bình thường (Safe - Không chờ)",
            "4. Chờ vòng tròn 3 tiến trình (P1 -> P2 -> P3 -> P1)"
        ],
        index=0
    )

    if preset_choice != "-- Chọn kịch bản --":
        if st.button("Nạp kịch bản", use_container_width=True):
            examples_dir = os.path.join(os.path.dirname(__file__), "examples")
            preset_files = {
                "1. Chờ vòng tròn (Deadlock 2 tiến trình)": "deadlock.json",
                "2. Chờ một chiều (Chaining - An toàn)": "chaining.json",
                "3. Bình thường (Safe - Không chờ)": "safe.json",
                "4. Chờ vòng tròn 3 tiến trình (P1 -> P2 -> P3 -> P1)": "deadlock_3p.json"
            }
            target_file = os.path.join(examples_dir, preset_files[preset_choice])
            if os.path.exists(target_file):
                with open(target_file, "r", encoding="utf-8") as f:
                    sim.from_dict(json.load(f))
                st.session_state.last_detection = None
                st.success(f"Đã nạp: {preset_choice}")
                st.rerun()

    st.divider()

    st.subheader("Quản lý kịch bản (JSON)")
    current_json = json.dumps(sim.to_dict(), indent=2, ensure_ascii=False)
    st.download_button(
        label="Tải kịch bản hiện tại (.json)",
        data=current_json,
        file_name="deadlock_scenario.json",
        mime="application/json",
        use_container_width=True
    )

    uploaded_file = st.file_uploader("Nạp file JSON từ máy:", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            if st.button("Áp dụng file JSON", use_container_width=True):
                sim.from_dict(data)
                st.session_state.last_detection = None
                st.success("Đã nạp dữ liệu từ file JSON thành công.")
                st.rerun()
        except Exception as e:
            st.error(f"Lỗi đọc file JSON: {e}")

    st.divider()

    if st.button("Đặt lại hệ thống (Reset)", use_container_width=True):
        sim.reset()
        st.session_state.last_detection = None
        st.rerun()

    st.caption("Đề tài: Mô phỏng phát hiện và xử lý Deadlock\nThuật toán: Wait-for Graph + DFS")


# ==========================================
# MAIN CONTENT
# ==========================================
st.title("Mô phỏng phát hiện và xử lý Deadlock")
st.caption("Deadlock Detection and Recovery Simulator | Môn học Hệ điều hành")
st.divider()

# Các tab chính
tab_sim, tab_recovery, tab_theory, tab_logs = st.tabs([
    "1. Mô phỏng & Phát hiện",
    "2. Xử lý Deadlock",
    "3. Lý thuyết",
    "4. Nhật ký hoạt động"
])


# ==========================================
# TAB 1: MÔ PHỎNG & PHÁT HIỆN
# ==========================================
with tab_sim:
    col_input, col_graph = st.columns([1, 1.2], gap="large")

    with col_input:
        st.subheader("1. Cấu hình Tiến trình và Tài nguyên")

        c_p, c_r = st.columns(2)
        with c_p:
            st.markdown("**Tiến trình (Process)**")
            new_p = st.text_input("Tên tiến trình mới:", placeholder="Ví dụ: P3", key="new_p")
            if st.button("Thêm Process", use_container_width=True):
                if new_p:
                    if sim.add_process(new_p):
                        st.success(f"Đã thêm {new_p}")
                        st.rerun()
                    else:
                        st.warning("Tên tiến trình đã tồn tại hoặc không hợp lệ.")

            if sim.processes:
                del_p = st.selectbox("Xóa tiến trình:", ["-- Chọn --"] + sim.processes, key="del_p")
                if del_p != "-- Chọn --" and st.button("Xóa Process đã chọn", use_container_width=True):
                    sim.remove_process(del_p)
                    st.session_state.last_detection = None
                    st.rerun()

        with c_r:
            st.markdown("**Tài nguyên (Resource)**")
            new_r = st.text_input("Tên tài nguyên mới:", placeholder="Ví dụ: R3", key="new_r")
            if st.button("Thêm Resource", use_container_width=True):
                if new_r:
                    if sim.add_resource(new_r):
                        st.success(f"Đã thêm {new_r}")
                        st.rerun()
                    else:
                        st.warning("Tên tài nguyên đã tồn tại hoặc không hợp lệ.")

            if sim.resources:
                del_r = st.selectbox("Xóa tài nguyên:", ["-- Chọn --"] + sim.resources, key="del_r")
                if del_r != "-- Chọn --" and st.button("Xóa Resource đã chọn", use_container_width=True):
                    sim.remove_resource(del_r)
                    st.session_state.last_detection = None
                    st.rerun()

        st.divider()

        st.subheader("2. Bảng phân bổ và yêu cầu tài nguyên")
        st.caption("Quy tắc: Mỗi tài nguyên là single-instance (1 đơn vị), tối đa 1 tiến trình giữ tại một thời điểm.")

        if not sim.processes or not sim.resources:
            st.info("Chưa có đủ Process hoặc Resource. Vui lòng thêm dữ liệu ở phía trên.")
        else:
            with st.form("state_form"):
                for p in sim.processes:
                    st.markdown(f"**Tiến trình {p}:**")
                    c_hold, c_req = st.columns(2)

                    with c_hold:
                        currently_held = sim.get_held_resources(p)
                        available_for_p = [
                            r for r in sim.resources
                            if sim.allocation.get(r) is None or sim.allocation.get(r) == p
                        ]
                        selected_holds = st.multiselect(
                            f"Đang giữ (Holds):",
                            options=available_for_p,
                            default=currently_held,
                            key=f"holds_{p}"
                        )

                    with c_req:
                        currently_req = sim.get_requested_resources(p)
                        requestable = [r for r in sim.resources if r not in selected_holds]
                        selected_reqs = st.multiselect(
                            f"Đang yêu cầu (Requests):",
                            options=requestable,
                            default=[r for r in currently_req if r in requestable],
                            key=f"reqs_{p}"
                        )

                    st.markdown("---")

                submitted = st.form_submit_button("Lưu và cập nhật trạng thái", use_container_width=True)
                if submitted:
                    for r in sim.resources:
                        sim.allocation[r] = None
                    for p in sim.processes:
                        sim.requests[p].clear()

                    for p in sim.processes:
                        p_holds = st.session_state.get(f"holds_{p}", [])
                        p_reqs = st.session_state.get(f"reqs_{p}", [])
                        for r in p_holds:
                            sim.assign_resource(p, r)
                        for r in p_reqs:
                            sim.request_resource(p, r)

                    st.session_state.last_detection = None
                    st.success("Đã cập nhật trạng thái.")
                    st.rerun()

    with col_graph:
        st.subheader("3. Kiểm tra Deadlock và Đồ thị")

        btn_detect = st.button("Kiểm tra Deadlock (DFS)", type="primary", use_container_width=True)

        wfg = WaitForGraph(sim)
        detector = DeadlockDetector(wfg)

        if btn_detect or st.session_state.last_detection is not None:
            detection_res = detector.detect_deadlock()
            st.session_state.last_detection = detection_res
        else:
            detection_res = None

        if detection_res:
            if detection_res["has_deadlock"]:
                cycles_str = " | ".join([" -> ".join(c) for c in detection_res["cycles"]])
                st.error(f"PHÁT HIỆN DEADLOCK: Chu trình: {cycles_str}")
                for reason in detection_res["reasons"]:
                    st.write(reason)
            else:
                st.success("HỆ THỐNG AN TOÀN: Không phát hiện chu trình trên Wait-for Graph.")

        graph_view = st.radio(
            "Đồ thị hiển thị:",
            ["Wait-for Graph (Vector)", "Wait-for Graph (Matplotlib)", "Resource Allocation Graph (RAG)"],
            horizontal=True
        )

        deadlock_cycles = detection_res["cycles"] if detection_res and detection_res["has_deadlock"] else None

        if graph_view == "Wait-for Graph (Vector)":
            dot_data = wfg.to_dot(deadlock_cycles=deadlock_cycles)
            st.graphviz_chart(dot_data, use_container_width=True)
            st.caption("Màu xanh: Tiến trình an toàn | Màu đỏ: Tiến trình trong Deadlock | Mũi tên: Phụ thuộc tài nguyên")

        elif graph_view == "Wait-for Graph (Matplotlib)":
            fig = draw_wait_for_graph_matplotlib(wfg, deadlock_cycles=deadlock_cycles)
            st.pyplot(fig)
            plt.close(fig)

        else:
            fig_rag = draw_resource_allocation_graph_matplotlib(sim)
            st.pyplot(fig_rag)
            plt.close(fig_rag)
            st.caption("Hình tròn: Tiến trình | Hình vuông: Tài nguyên | Mũi tên liền: Đang giữ | Mũi tên đứt: Đang yêu cầu")


# ==========================================
# TAB 2: XỬ LÝ DEADLOCK
# ==========================================
with tab_recovery:
    st.subheader("Xử lý Deadlock: Kết thúc tiến trình (Process Termination)")
    st.write(
        "Khi phát hiện chu trình chờ, phương pháp cơ bản nhất là kết thúc một tiến trình trong chu trình "
        "để thu hồi tài nguyên và phá vỡ bế tắc."
    )

    wfg_current = WaitForGraph(sim)
    detector_current = DeadlockDetector(wfg_current)
    current_check = detector_current.detect_deadlock()

    if not current_check["has_deadlock"]:
        st.info("Hệ thống hiện không có Deadlock cần xử lý.")
    else:
        st.warning(f"Các tiến trình bị kẹt trong Deadlock: {', '.join(current_check['deadlocked_processes'])}")

        st.markdown("#### Đề xuất xử lý:")
        for idx, rec in enumerate(current_check["recommendations"], 1):
            st.markdown(f"- **Phương án {idx}:** {rec['advice']}")

        st.divider()
        st.markdown("#### Thực hiện kết thúc tiến trình:")
        c_rec1, c_rec2 = st.columns([2, 1])

        with c_rec1:
            target_p = st.selectbox(
                "Chọn tiến trình cần kết thúc:",
                options=current_check["deadlocked_processes"]
            )
            auto_grant = st.checkbox(
                "Tự động cấp phát tài nguyên vừa giải phóng cho tiến trình đang chờ",
                value=True
            )

        with c_rec2:
            st.write("")
            st.write("")
            if st.button("Kết thúc tiến trình", type="primary", use_container_width=True):
                recovery = DeadlockRecovery(sim)
                result = recovery.terminate_process(target_p, auto_grant_freed=auto_grant)

                if result["success"]:
                    st.success(f"Đã kết thúc tiến trình {target_p}.")
                    for act in result["actions"]:
                        st.write(act)

                    # Kiểm tra lại trạng thái
                    wfg_new = WaitForGraph(sim)
                    check_new = DeadlockDetector(wfg_new).detect_deadlock()
                    st.session_state.last_detection = check_new
                    st.rerun()


# ==========================================
# TAB 3: LÝ THUYẾT
# ==========================================
with tab_theory:
    st.subheader("Lý thuyết về Deadlock trong Hệ điều hành")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown(r"""
        #### 1. Bốn điều kiện gây Deadlock (Coffman Conditions)
        Deadlock xảy ra khi đồng thời thỏa mãn:
        1. **Mutual Exclusion (Độc quyền):** Mỗi thời điểm, tài nguyên chỉ được một tiến trình sử dụng.
        2. **Hold and Wait (Giữ và chờ):** Tiến trình giữ tài nguyên và đồng thời yêu cầu tài nguyên khác đang bị giữ.
        3. **No Preemption (Không thu hồi cưỡng chế):** Tài nguyên chỉ được giải phóng tự nguyện bởi tiến trình nắm giữ.
        4. **Circular Wait (Chờ vòng tròn):** Tồn tại chuỗi tiến trình $P_1 \rightarrow P_2 \rightarrow \dots \rightarrow P_n \rightarrow P_1$.
        """)

    with col_t2:
        st.markdown(r"""
        #### 2. Wait-for Graph và DFS
        - **Wait-for Graph:**
          - Đồ thị rút gọn từ Resource Allocation Graph cho hệ thống tài nguyên đơn vị (single-instance).
          - Các đỉnh là các Tiến trình.
          - Cạnh $P_i \rightarrow P_j$ biểu diễn: $P_i$ chờ tài nguyên do $P_j$ nắm giữ.
        - **Thuật toán DFS:**
          - Duyệt theo chiều sâu với 3 trạng thái tô màu: Chưa thăm (0), Đang duyệt (1), Đã duyệt xong (2).
          - Khi gặp một đỉnh đang trong trạng thái 1 (cạnh ngược / back-edge), đồ thị có chu trình.
          - Đối với tài nguyên đơn vị: **Có chu trình tương đương với có Deadlock**.
        """)

    st.divider()
    st.markdown("""
    #### 3. So sánh: Phát hiện (Detection) vs Tránh (Avoidance - Banker's Algorithm)
    | Tiêu chí | Phát hiện & Xử lý (Wait-for Graph) | Tránh Deadlock (Banker's Algorithm) |
    | :--- | :--- | :--- |
    | **Cách tiếp cận** | Định kỳ kiểm tra chu trình và phục hồi | Kiểm tra trạng thái an toàn trước mỗi lần cấp phát |
    | **Thông tin yêu cầu** | Trạng thái hiện tại (Đang giữ & Đang chờ) | Yêu cầu tối đa (Max Claim) của từng tiến trình |
    | **Độ phức tạp** | $O(V + E)$ với DFS | $O(m \times n^2)$ với ma trận cấp phát |
    | **Phục hồi** | Cần kết thúc tiến trình hoặc thu hồi tài nguyên | Không cần phục hồi vì không để xảy ra Deadlock |
    """)


# ==========================================
# TAB 4: NHẬT KÝ HOẠT ĐỘNG
# ==========================================
with tab_logs:
    st.subheader("Nhật ký mô phỏng")
    if not sim.history_logs:
        st.write("Chưa có sự kiện nào được ghi nhận.")
    else:
        for idx, entry in enumerate(reversed(sim.history_logs), 1):
            st.text(f"[{len(sim.history_logs) - idx + 1}] {entry}")
