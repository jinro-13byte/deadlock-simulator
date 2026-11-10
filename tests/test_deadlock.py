"""
Unit Tests for Deadlock Detection and Recovery Simulator
Bao gồm 3 trường hợp thử nghiệm bắt buộc từ đặc tả PDF:
1. Trường hợp bình thường (Không có yêu cầu chờ -> An toàn)
2. Trường hợp chờ một chiều (Không chu trình -> An toàn)
3. Trường hợp chờ vòng tròn (Có chu trình -> Deadlock -> Recovery thành công)
4. Trường hợp mở rộng (3 tiến trình vòng tròn)
"""

import sys
import os
import unittest

# Đảm bảo đường dẫn import thư mục gốc
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import DeadlockSimulator
from graph import WaitForGraph
from detection import DeadlockDetector
from recovery import DeadlockRecovery


class TestDeadlockSimulator(unittest.TestCase):

    def test_case_1_normal(self):
        """Trường hợp 1: P1 giữ R1, P2 giữ R2, không có yêu cầu chờ -> Không có Deadlock"""
        sim = DeadlockSimulator()
        sim.add_process("P1")
        sim.add_process("P2")
        sim.add_resource("R1")
        sim.add_resource("R2")

        sim.assign_resource("P1", "R1")
        sim.assign_resource("P2", "R2")

        wfg = WaitForGraph(sim)
        detector = DeadlockDetector(wfg)
        result = detector.detect_deadlock()

        self.assertFalse(result["has_deadlock"], "Trường hợp bình thường không được có Deadlock!")
        self.assertEqual(len(result["cycles"]), 0)

    def test_case_2_chaining(self):
        """Trường hợp 2: P1 chờ R2 do P2 giữ, P2 không chờ -> Không có Deadlock"""
        sim = DeadlockSimulator()
        sim.add_process("P1")
        sim.add_process("P2")
        sim.add_resource("R1")
        sim.add_resource("R2")

        sim.assign_resource("P1", "R1")
        sim.assign_resource("P2", "R2")
        sim.request_resource("P1", "R2")  # P1 chờ R2

        wfg = WaitForGraph(sim)
        self.assertIn("P2", wfg.adj["P1"])
        self.assertEqual(wfg.adj["P2"], [])

        detector = DeadlockDetector(wfg)
        result = detector.detect_deadlock()

        self.assertFalse(result["has_deadlock"], "Chờ một chiều không tạo chu trình, không được báo Deadlock!")
        self.assertEqual(len(result["cycles"]), 0)

    def test_case_3_circular_wait_and_recovery(self):
        """Trường hợp 3: P1 chờ P2 và P2 chờ P1 -> Phát hiện Deadlock, xử lý thành công"""
        sim = DeadlockSimulator()
        sim.add_process("P1")
        sim.add_process("P2")
        sim.add_resource("R1")
        sim.add_resource("R2")

        # P1 giữ R1, P2 giữ R2
        sim.assign_resource("P1", "R1")
        sim.assign_resource("P2", "R2")

        # P1 yêu cầu R2, P2 yêu cầu R1
        sim.request_resource("P1", "R2")
        sim.request_resource("P2", "R1")

        # Kiểm tra Wait-for graph
        wfg = WaitForGraph(sim)
        self.assertIn("P2", wfg.adj["P1"])
        self.assertIn("P1", wfg.adj["P2"])

        # Phát hiện Deadlock
        detector = DeadlockDetector(wfg)
        result = detector.detect_deadlock()

        self.assertTrue(result["has_deadlock"], "Chờ vòng tròn bắt buộc phải phát hiện Deadlock!")
        self.assertEqual(len(result["cycles"]), 1)
        self.assertIn("P1", result["deadlocked_processes"])
        self.assertIn("P2", result["deadlocked_processes"])

        # Phục hồi (Recovery): Kết thúc P2
        recovery = DeadlockRecovery(sim)
        rec_res = recovery.terminate_process("P2", auto_grant_freed=True)
        self.assertTrue(rec_res["success"])
        self.assertIn("R2", rec_res["freed_resources"])
        # R2 được tự động cấp cho P1
        self.assertEqual(rec_res["reallocated"].get("R2"), "P1")

        # Kiểm tra lại đồ thị sau khi phục hồi
        wfg_after = WaitForGraph(sim)
        detector_after = DeadlockDetector(wfg_after)
        result_after = detector_after.detect_deadlock()

        self.assertFalse(result_after["has_deadlock"], "Sau khi kết thúc P2, hệ thống phải hết Deadlock!")

    def test_case_4_three_processes_cycle(self):
        """Trường hợp 4: Chu trình 3 tiến trình P1 -> P2 -> P3 -> P1"""
        sim = DeadlockSimulator()
        for p in ["P1", "P2", "P3"]:
            sim.add_process(p)
        for r in ["R1", "R2", "R3"]:
            sim.add_resource(r)

        sim.assign_resource("P1", "R1")
        sim.assign_resource("P2", "R2")
        sim.assign_resource("P3", "R3")

        sim.request_resource("P1", "R2")
        sim.request_resource("P2", "R3")
        sim.request_resource("P3", "R1")

        wfg = WaitForGraph(sim)
        detector = DeadlockDetector(wfg)
        result = detector.detect_deadlock()

        self.assertTrue(result["has_deadlock"])
        self.assertEqual(len(result["deadlocked_processes"]), 3)

        # Kết thúc P3
        recovery = DeadlockRecovery(sim)
        recovery.terminate_process("P3", auto_grant_freed=True)

        # Sau khi P3 kết thúc, chu trình bị phá vỡ
        wfg_after = WaitForGraph(sim)
        detector_after = DeadlockDetector(wfg_after)
        result_after = detector_after.detect_deadlock()
        self.assertFalse(result_after["has_deadlock"])


if __name__ == "__main__":
    unittest.main()
