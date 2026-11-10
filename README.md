# Hệ Thống Mô Phỏng Phát Hiện Và Xử Lý Deadlock

_(Deadlock Detection and Recovery Simulator)_

Dự án mô phỏng quá trình tranh chấp tài nguyên đơn vị (_Single-instance resources_) giữa các tiến trình, tự động xây dựng đồ thị chờ **Wait-for Graph**, phát hiện Deadlock bằng thuật toán duyệt đồ thị theo chiều sâu **DFS (Depth-First Search)** và cung cấp cơ chế xử lý bằng **Process Termination**.

---

## Mục lục

1. [Tính năng chính](#-tính-năng-chính)
2. [Cấu trúc mã nguồn](#-cấu-trúc-mã-nguồn)
3. [Cài đặt & Khởi chạy](#-cài-đặt--khởi-chạy)
4. [3 Kịch bản thử nghiệm bắt buộc](#-3-kịch-bản-thử-nghiệm-bắt-buộc)
5. [Thuật toán & Cơ chế hoạt động](#-thuật-toán--cơ-chế-hoạt-động)

---

## Tính năng chính

- **Mô phỏng trực quan:** Tạo, chỉnh sửa tiến trình ($P_1, P_2, \dots$) và tài nguyên ($R_1, R_2, \dots$).
- **Đồ thị Wait-for Graph:** Biểu diễn quan hệ phụ thuộc giữa các tiến trình. Hỗ trợ hiển thị vector sắc nét (Graphviz) và đồ thị NetworkX + Matplotlib.
- **Phát hiện Deadlock bằng DFS:** Duyệt tìm chu trình trong $O(V + E)$, phát hiện chu trình chờ và giải thích nguyên nhân rõ ràng.
- **Phục hồi (Recovery):** Lựa chọn kết thúc tiến trình gây bế tắc, giải phóng tài nguyên và tự động tái cấp phát cho tiến trình đang chờ đợi.
- **Kịch bản mẫu & Lưu trữ JSON:** Nạp sẵn các tình huống thử nghiệm (Deadlock, Chờ một chiều, An toàn) hoặc xuất/nhập file JSON tùy ý.

---

## Cấu trúc mã nguồn

```text
deadlock-simulator/
├── app.py              # Giao diện chính Streamlit (Dashboard tương tác)
├── simulator.py        # Logic quản lý tiến trình, tài nguyên, phân bổ (Holds & Requests)
├── graph.py            # Xây dựng Wait-for Graph và định dạng DOT
├── detection.py        # Thuật toán DFS phát hiện chu trình Deadlock
├── recovery.py         # Module kết thúc tiến trình và cấp phát lại tài nguyên
├── visualization.py    # Trực quan hóa Wait-for Graph và RAG bằng NetworkX & Matplotlib
├── requirements.txt    # Danh sách thư viện phụ thuộc
├── README.md           # Hướng dẫn chi tiết
├── examples/           # Các file JSON kịch bản mẫu
│   ├── deadlock.json   # Kịch bản Deadlock chuẩn (P1-R1-R2, P2-R2-R1)
│   ├── chaining.json   # Kịch bản Chờ một chiều (An toàn)
│   ├── safe.json       # Kịch bản Bình thường (An toàn)
│   └── deadlock_3p.json# Kịch bản chu trình 3 tiến trình
└── tests/
    └── test_deadlock.py# Bộ kiểm thử tự động 4 test cases
```

---

## Cài đặt & Khởi chạy

### 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng Streamlit

```bash
streamlit run app.py
```

Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: `http://localhost:8501`.

### 3. Chạy kiểm thử tự động (Unit Tests)

```bash
python tests/test_deadlock.py
```

---

## 3 Kịch bản thử nghiệm bắt buộc

| Trường hợp                           | Dữ liệu đầu vào (Input)                                    | Kết quả mong đợi                                                                                                       |
| :----------------------------------- | :--------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **1. Bình thường (Safe)**            | $P_1$ giữ $R_1$, $P_2$ giữ $R_2$, không có yêu cầu chờ     | **Không có Deadlock** (Hệ thống an toàn)                                                                               |
| **2. Chờ một chiều (Chaining)**      | $P_1$ giữ $R_1$ và chờ $R_2$; $P_2$ giữ $R_2$ và không chờ | **Không có Deadlock** (Chờ tuyến tính)                                                                                 |
| **3. Chờ vòng tròn (Circular Wait)** | $P_1$ giữ $R_1$, chờ $R_2$; $P_2$ giữ $R_2$, chờ $R_1$     | **Phát hiện Deadlock ($P_1 \rightarrow P_2 \rightarrow P_1$)** → Kết thúc $P_2$, giải phóng $R_2$ cho $P_1$ thành công |

---

## Thuật toán & Cơ chế hoạt động

1. **Xây dựng Wait-for Graph:**
   - Mỗi đỉnh là một Process.
   - Nếu $P_i$ đang yêu cầu tài nguyên $R_k$ mà $R_k$ đang do $P_j$ nắm giữ $\implies$ tạo cạnh có hướng $P_i \rightarrow P_j$.
2. **Thuật toán DFS:**
   - Sử dụng mô hình 3 trạng thái: `0: UNVISITED`, `1: VISITING (in call stack)`, `2: VISITED`.
   - Nếu duyệt tới một đỉnh láng giềng đang có trạng thái `1` $\implies$ phát hiện cạnh ngược (_Back-edge_) $\implies$ **Tồn tại chu trình**.
   - Với tài nguyên đơn vị (_Single-instance_), đồ thị có chu trình là điều kiện cần và đủ để xảy ra Deadlock.
3. **Phục hồi (Recovery):**
   - Đánh dấu tiến trình bị hủy.
   - Giải phóng tài nguyên tiến trình đó đang giữ.
   - Xóa các yêu cầu chờ của tiến trình đó.
   - Kiểm tra các tiến trình khác đang chờ tài nguyên vừa giải phóng để chuyển giao, đưa hệ thống trở lại trạng thái an toàn.
