"""
Deadlock Simulator - Quản lý trạng thái Process và Resource
Theo yêu cầu đề tài: Mỗi tài nguyên là single-instance (1 đơn vị),
tại một thời điểm chỉ có tối đa 1 tiến trình được giữ tài nguyên đó.
"""

from typing import Dict, List, Optional, Set
import copy


class DeadlockSimulator:
    def __init__(self):
        # Danh sách tiến trình (Processes)
        self.processes: List[str] = []
        # Danh sách tài nguyên (Resources)
        self.resources: List[str] = []
        # Tài nguyên nào đang được tiến trình nào giữ: resource_id -> process_id (None nếu rảnh)
        self.allocation: Dict[str, Optional[str]] = {}
        # Tiến trình đang yêu cầu những tài nguyên nào: process_id -> Set[resource_id]
        self.requests: Dict[str, Set[str]] = {}
        # Lịch sử các bước xử lý (để hiển thị log mô phỏng)
        self.history_logs: List[str] = []

    def add_process(self, process_id: str) -> bool:
        pid = process_id.strip()
        if not pid or pid in self.processes:
            return False
        self.processes.append(pid)
        self.requests[pid] = set()
        self.log(f"Đã thêm tiến trình {pid}.")
        return True

    def remove_process(self, process_id: str) -> bool:
        if process_id not in self.processes:
            return False
        # Giải phóng mọi tài nguyên đang giữ
        for res, holder in list(self.allocation.items()):
            if holder == process_id:
                self.allocation[res] = None
                self.log(f"Tài nguyên {res} được tự động giải phóng do xoá {process_id}.")
        # Xóa yêu cầu
        self.requests.pop(process_id, None)
        self.processes.remove(process_id)
        self.log(f"Đã xoá tiến trình {process_id}.")
        return True

    def add_resource(self, resource_id: str) -> bool:
        rid = resource_id.strip()
        if not rid or rid in self.resources:
            return False
        self.resources.append(rid)
        self.allocation[rid] = None
        self.log(f"Đã thêm tài nguyên {rid}.")
        return True

    def remove_resource(self, resource_id: str) -> bool:
        if resource_id not in self.resources:
            return False
        self.allocation.pop(resource_id, None)
        # Xóa tài nguyên khỏi các danh sách yêu cầu
        for pid in self.processes:
            self.requests[pid].discard(resource_id)
        self.resources.remove(resource_id)
        self.log(f"Đã xoá tài nguyên {resource_id}.")
        return True

    def assign_resource(self, process_id: str, resource_id: str) -> tuple[bool, str]:
        """Cấp phát tài nguyên cho tiến trình (holds)."""
        if process_id not in self.processes:
            return False, f"Tiến trình {process_id} không tồn tại!"
        if resource_id not in self.resources:
            return False, f"Tài nguyên {resource_id} không tồn tại!"

        current_holder = self.allocation.get(resource_id)
        if current_holder and current_holder != process_id:
            return False, f"Tài nguyên {resource_id} đã bị {current_holder} giữ! Mỗi tài nguyên chỉ có 1 instance."

        # Nếu trước đó đang yêu cầu tài nguyên này, thì xóa khỏi request
        self.requests[process_id].discard(resource_id)
        self.allocation[resource_id] = process_id
        self.log(f"Tiến trình {process_id} đang giữ tài nguyên {resource_id}.")
        return True, "Thành công."

    def release_resource(self, process_id: str, resource_id: str) -> tuple[bool, str]:
        """Tiến trình trả lại tài nguyên."""
        if self.allocation.get(resource_id) != process_id:
            return False, f"Tiến trình {process_id} hiện không giữ tài nguyên {resource_id}."
        self.allocation[resource_id] = None
        self.log(f"Tiến trình {process_id} đã giải phóng tài nguyên {resource_id}.")
        return True, "Thành công."

    def request_resource(self, process_id: str, resource_id: str) -> tuple[bool, str]:
        """Tiến trình yêu cầu thêm tài nguyên (requests)."""
        if process_id not in self.processes:
            return False, f"Tiến trình {process_id} không tồn tại!"
        if resource_id not in self.resources:
            return False, f"Tài nguyên {resource_id} không tồn tại!"
        if self.allocation.get(resource_id) == process_id:
            return False, f"Tiến trình {process_id} đang giữ sẵn tài nguyên {resource_id} rồi!"

        self.requests[process_id].add(resource_id)
        self.log(f"Tiến trình {process_id} yêu cầu tài nguyên {resource_id}.")
        return True, "Thành công."

    def cancel_request(self, process_id: str, resource_id: str) -> bool:
        if process_id in self.requests and resource_id in self.requests[process_id]:
            self.requests[process_id].discard(resource_id)
            self.log(f"Tiến trình {process_id} đã hủy yêu cầu tài nguyên {resource_id}.")
            return True
        return False

    def get_held_resources(self, process_id: str) -> List[str]:
        return [res for res, holder in self.allocation.items() if holder == process_id]

    def get_requested_resources(self, process_id: str) -> List[str]:
        return sorted(list(self.requests.get(process_id, set())))

    def log(self, message: str):
        self.history_logs.append(message)

    def reset(self):
        self.processes.clear()
        self.resources.clear()
        self.allocation.clear()
        self.requests.clear()
        self.history_logs.clear()

    def clone(self) -> 'DeadlockSimulator':
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {
            "processes": list(self.processes),
            "resources": list(self.resources),
            "allocation": dict(self.allocation),
            "requests": {p: list(res_set) for p, res_set in self.requests.items()},
        }

    def from_dict(self, data: dict):
        self.reset()
        for p in data.get("processes", []):
            self.add_process(p)
        for r in data.get("resources", []):
            self.add_resource(r)
        for r, holder in data.get("allocation", {}).items():
            if holder in self.processes and r in self.resources:
                self.allocation[r] = holder
        for p, req_list in data.get("requests", {}).items():
            if p in self.processes:
                for r in req_list:
                    if r in self.resources:
                        self.requests[p].add(r)
