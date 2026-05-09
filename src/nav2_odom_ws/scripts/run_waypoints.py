#!/usr/bin/env python3
"""
run_waypoints.py
================
Script untuk memuat waypoints dari file waypoints.yaml dan mengirimkan
robot untuk bergerak secara otomatis ke setiap waypoint menggunakan Nav2.

Robot akan berhenti di setiap waypoint dan menunggu konfirmasi sebelum
melanjutkan ke waypoint berikutnya (mode interaktif), atau berjalan
terus secara otomatis (mode auto).

Cara Penggunaan:
  # Mode interaktif (berhenti di setiap waypoint):
  python3 src/nav2_odom_ws/scripts/run_waypoints.py

  # Mode otomatis (tidak berhenti):
  python3 src/nav2_odom_ws/scripts/run_waypoints.py --auto

  # Mode loop (kembali ke awal setelah selesai):
  python3 src/nav2_odom_ws/scripts/run_waypoints.py --auto --loop
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from action_msgs.msg import GoalStatus
import yaml
import os
import sys
import time

# File waypoints — harus sama dengan save_waypoints.py
WAYPOINTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'config', 'waypoints.yaml'
)


class WaypointRunner(Node):
    def __init__(self, auto_mode=False, loop_mode=False):
        super().__init__('waypoint_runner')
        self.auto_mode = auto_mode
        self.loop_mode = loop_mode
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.current_goal_handle = None
        self.goal_reached = False

    def load_waypoints(self):
        if not os.path.exists(WAYPOINTS_FILE):
            self.get_logger().error(
                f'File waypoints tidak ditemukan: {WAYPOINTS_FILE}\n'
                f'Jalankan save_waypoints.py terlebih dahulu!'
            )
            return []

        with open(WAYPOINTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        waypoints = data.get('waypoints', []) if data else []
        self.get_logger().info(
            f'Berhasil memuat {len(waypoints)} waypoints dari {WAYPOINTS_FILE}'
        )
        return waypoints

    def send_goal(self, waypoint):
        self.get_logger().info(
            f'Mengirim robot ke waypoint: "{waypoint["name"]}" '
            f'(x={waypoint["x"]:.2f}, y={waypoint["y"]:.2f})'
        )

        # Tunggu action server siap
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server navigate_to_pose tidak tersedia!')
            return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'odom'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = waypoint['x']
        goal_msg.pose.pose.position.y = waypoint['y']
        goal_msg.pose.pose.orientation.z = waypoint['qz']
        goal_msg.pose.pose.orientation.w = waypoint['qw']

        self.goal_reached = False
        future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        future.add_done_callback(self.goal_response_callback)

        # Tunggu sampai robot mencapai goal
        while not self.goal_reached:
            rclpy.spin_once(self, timeout_sec=0.1)

        return True

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal ditolak oleh Nav2!')
            self.goal_reached = True
            return

        self.get_logger().info('Goal diterima, robot sedang bergerak...')
        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result()
        status = result.status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('[SUKSES] Robot telah tiba di waypoint!')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('[BATAL] Goal dibatalkan.')
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error('[GAGAL] Robot gagal mencapai waypoint!')
        
        self.goal_reached = True

    def feedback_callback(self, feedback_msg):
        distance = feedback_msg.feedback.distance_remaining
        # Tampilkan feedback setiap 1 meter
        if distance and int(distance * 10) % 10 == 0:
            self.get_logger().info(
                f'  Jarak tersisa: {distance:.2f} meter',
                throttle_duration_sec=1.0
            )

    def run(self):
        waypoints = self.load_waypoints()
        if not waypoints:
            return

        print('\n' + '='*50)
        print('=== WAYPOINT RUNNER ===')
        print('='*50)
        print(f'Mode: {"Auto" if self.auto_mode else "Interaktif"}')
        print(f'Loop: {"Ya" if self.loop_mode else "Tidak"}')
        print(f'Jumlah waypoints: {len(waypoints)}')
        for i, wp in enumerate(waypoints):
            print(f'  {i+1}. {wp["name"]} (x={wp["x"]:.2f}, y={wp["y"]:.2f})')
        print('='*50)

        run = True
        while run:
            for i, waypoint in enumerate(waypoints):
                print(f'\n[{i+1}/{len(waypoints)}] Menuju: {waypoint["name"]}')

                if not self.auto_mode:
                    confirm = input('Tekan Enter untuk melanjutkan, atau "q" untuk berhenti: ').strip()
                    if confirm.lower() == 'q':
                        print('Dihentikan oleh pengguna.')
                        return

                success = self.send_goal(waypoint)
                if not success:
                    print(f'Gagal mengirim goal untuk waypoint: {waypoint["name"]}')
                    break

                if not self.auto_mode:
                    print(f'[OK] Tiba di {waypoint["name"]}!')

            if self.loop_mode:
                print('\n[LOOP] Semua waypoints selesai, kembali ke awal...')
                time.sleep(1.0)
            else:
                run = False

        print('\n[SELESAI] Semua waypoints telah dikunjungi!')


def main():
    auto_mode = '--auto' in sys.argv
    loop_mode = '--loop' in sys.argv

    rclpy.init()
    node = WaypointRunner(auto_mode=auto_mode, loop_mode=loop_mode)

    try:
        node.run()
    except KeyboardInterrupt:
        print('\n[INFO] Dihentikan oleh pengguna.')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
