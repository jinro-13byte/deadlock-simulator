"""
Deadlock Recovery Module
Phương pháp: Process Termination (Kết thúc tiến trình mô phỏng)
Thao tác:
1. Đánh dấu và kết thúc tiến trình được chọn.
2. Giải phóng toàn bộ tài nguyên tiến trình này đang nắm giữ.
3. Huỷ toàn bộ các yêu cầu chờ của tiến trình này.
4. Tùy chọn: Tự động cấp phát các tài nguyên vừa được giải phóng cho các tiến trình đang chờ đợi chúng.
5. Cập nhật lại đồ thị và kiểm tra lại trạng thái hệ thống.
"""

from typing import Dict, List, Optional
from simulator import DeadlockSimulator


class DeadlockRecovery:
    def __init__(self, simulator: DeadlockSimulator):
        self.simulator = simulator

    def terminate_process(self, process_id: str, auto_grant_freed: bool = True) -> dict:
        """
        Kết thúc tiến trình và giải phóng tài nguyên.
        """
        if process_id not in self.simulator.processes:
            return {
                "success": False,
                "message": f"Tiến trình {process_id} không tồn tại trong hệ thống!"
            }

        actions_taken: List[str] = []
        freed_resources = self.simulator.get_held_resources(process_id)
        cancelled_requests = self.simulator.get_requested_resources(process_id)
        reallocated: Dict[str, str] = {}

        actions_taken.append(f"1. Tiến trình {process_id} đã được chọn để kết thúc.")

        # Hủy các yêu cầu chờ của process_id
        if cancelled_requests:
            actions_taken.append(
                f"2. Hủy các yêu cầu tài nguyên của {process_id}: {', '.join(cancelled_requests)}."
            )
        self.simulator.requests.pop(process_id, None)

        # Giải phóng các tài nguyên process_id đang giữ
        if freed_resources:
            actions_taken.append(
                f"3. Giải phóng các tài nguyên mà {process_id} đang giữ: {', '.join(freed_resources)}."
            )
            for res in freed_resources:
                self.simulator.allocation[res] = None

        # Xóa process_id khỏi danh sách tiến trình hoạt động
        self.simulator.processes.remove(process_id)
        actions_taken.append(f"4. Đã loại bỏ {process_id} khỏi danh sách tiến trình đang chạy.")

        # Cấp phát lại tài nguyên vừa giải phóng cho các tiến trình đang chờ (nếu auto_grant_freed = True)
        if auto_grant_freed and freed_resources:
            for res in freed_resources:
                # Tìm tiến trình đang chờ tài nguyên res
                candidate = None
                for other_p in self.simulator.processes:
                    if res in self.simulator.requests.get(other_p, set()):
                        candidate = other_p
                        break

                if candidate:
                    # Cấp phát tài nguyên cho candidate
                    self.simulator.requests[candidate].discard(res)
                    self.simulator.allocation[res] = candidate
                    reallocated[res] = candidate
                    actions_taken.append(
                        f"5. Tài nguyên {res} đã được chuyển cấp phát cho tiến trình {candidate} (tiến trình đang chờ)."
                    )

        summary_msg = f"Đã kết thúc thành công {process_id}. "
        if freed_resources:
            summary_msg += f"Giải phóng: {', '.join(freed_resources)}. "
        if reallocated:
            summary_msg += f"Đã cấp mới: {reallocated}."

        self.simulator.log(summary_msg)

        return {
            "success": True,
            "terminated_process": process_id,
            "freed_resources": freed_resources,
            "reallocated": reallocated,
            "actions": actions_taken,
            "message": summary_msg
        }
