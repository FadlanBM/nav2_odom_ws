#!/usr/bin/env python3
"""
save_waypoints.py
=================
Script untuk menyimpan posisi robot saat ini ke dalam file waypoints.yaml.

Cara Penggunaan:
  1. Gerakkan robot ke posisi yang diinginkan (gunakan teleop).
  2. Jalankan script ini di terminal baru.
  3. Tekan Ctrl+C untuk menyimpan posisi saat ini.

Jalankan:
  python3 src/nav2_odom_ws/scripts/save_waypoints.py
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import yaml
import os
import sys

# File default untuk menyimpan waypoints
WAYPOINTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'config', 'waypoints.yaml'
)

# Topik odom robot - sesuaikan jika berbeda
ODOM_TOPIC = '/diff_cont/odom'


class WaypointSaver(Node):
    def __init__(self):
        super().__init__('waypoint_saver')
        self.subscription = self.create_subscription(
            Odometry, ODOM_TOPIC, self.odom_callback, 10
        )
        self.last_pose = None
        self.waypoints = self._load_existing_waypoints()
        self.get_logger().info('=== Waypoint Saver Siap ===')
        self.get_logger().info(f'Mendengarkan topik: {ODOM_TOPIC}')
        self.get_logger().info(f'Sudah ada {len(self.waypoints)} waypoint tersimpan.')
        self.get_logger().info('Gerakkan robot ke posisi yang diinginkan...')
        self.get_logger().info('Tekan Ctrl+C untuk menyimpan posisi saat ini.')

    def odom_callback(self, msg):
        self.last_pose = msg.pose.pose

    def _load_existing_waypoints(self):
        if os.path.exists(WAYPOINTS_FILE):
            with open(WAYPOINTS_FILE, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('waypoints', []) if data else []
        return []

    def save_waypoint(self):
        if self.last_pose is None:
            print('\n[ERROR] Data odom belum diterima!')
            print(f'       Pastikan simulasi berjalan dan topik {ODOM_TOPIC} aktif.')
            print('       Cek dengan: ros2 topic echo /odom')
            return False

        print(f'\nPosisi robot saat ini:')
        print(f'  x  = {self.last_pose.position.x:.4f}')
        print(f'  y  = {self.last_pose.position.y:.4f}')
        print(f'  qz = {self.last_pose.orientation.z:.4f}')
        print(f'  qw = {self.last_pose.orientation.w:.4f}')

        try:
            name = input(f'\nNama waypoint (Enter = "waypoint_{len(self.waypoints) + 1}"): ').strip()
        except EOFError:
            name = ''
        if not name:
            name = f'waypoint_{len(self.waypoints) + 1}'

        waypoint = {
            'name': name,
            'x':   round(float(self.last_pose.position.x), 4),
            'y':   round(float(self.last_pose.position.y), 4),
            'qz':  round(float(self.last_pose.orientation.z), 4),
            'qw':  round(float(self.last_pose.orientation.w), 4),
        }
        self.waypoints.append(waypoint)

        data = {'waypoints': self.waypoints}
        os.makedirs(os.path.dirname(os.path.abspath(WAYPOINTS_FILE)), exist_ok=True)
        with open(WAYPOINTS_FILE, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        print(f'\n[OK] Waypoint "{name}" berhasil disimpan!')
        print(f'     File: {os.path.abspath(WAYPOINTS_FILE)}')
        print(f'     Total waypoints: {len(self.waypoints)}')
        return True


def main():
    rclpy.init()
    node = WaypointSaver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\n\n[INFO] Menyimpan posisi saat ini...')
        saved = node.save_waypoint()

        if saved:
            try:
                again = input('\nSimpan waypoint lain? (y/n): ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                again = 'n'

            if again == 'y':
                print('\nGerakkan robot ke posisi berikutnya, lalu tekan Ctrl+C lagi.')
                try:
                    rclpy.spin(node)
                except KeyboardInterrupt:
                    print('\n\n[INFO] Menyimpan posisi berikutnya...')
                    node.save_waypoint()

        print('\n[SELESAI] Semua waypoints disimpan.')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
