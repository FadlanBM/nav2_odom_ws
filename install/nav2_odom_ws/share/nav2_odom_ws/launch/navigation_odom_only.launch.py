#!/usr/bin/env python3
# ============================================================
# navigation_odom_only.launch.py
#
# Navigation menggunakan Nav2 HANYA dengan odometry.
#
# Yang dilakukan file ini:
#   1. Publish static transform: map -> odom
#      (Karena tidak pakai AMCL, kita "kunci" map=odom)
#   2. Launch semua node Nav2 inti:
#      - controller_server
#      - planner_server
#      - recoveries_server
#      - bt_navigator
#      - waypoint_follower
#      - lifecycle_manager
#
# Costmap dikonfigurasi TANPA sensor layer (tidak perlu /scan).
# Global frame = odom (bukan map) di dalam params.
# ============================================================

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():

    package_name = 'nav2_odom_ws'
    bringup_dir = get_package_share_directory(package_name)

    # ---- Launch Arguments ----
    namespace          = LaunchConfiguration('namespace')
    use_sim_time       = LaunchConfiguration('use_sim_time')
    autostart          = LaunchConfiguration('autostart')
    params_file        = LaunchConfiguration('params_file')
    default_bt_xml     = LaunchConfiguration('default_bt_xml_filename')
    map_sub_transient  = LaunchConfiguration('map_subscribe_transient_local')

    # Lifecycle nodes yang akan di-manage
    lifecycle_nodes = [
        'controller_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
        'waypoint_follower',
    ]

    remappings = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
        ('/cmd_vel', '/diff_cont/cmd_vel_unstamped'),
    ]

    param_substitutions = {
        'use_sim_time':                use_sim_time,
        'default_bt_xml_filename':     default_bt_xml,
        'autostart':                   autostart,
        'map_subscribe_transient_local': map_sub_transient,
    }

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True,
    )

    return LaunchDescription([

        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        # ---- Deklarasi argument ----
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Top-level namespace'),

        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Gunakan jam simulasi Gazebo jika true'),

        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Auto-start Nav2 lifecycle nodes'),

        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                bringup_dir, 'config', 'nav2_params_odom_only.yaml'),
            description='Path ke file parameter Nav2'),

        DeclareLaunchArgument(
            'default_bt_xml_filename',
            default_value=os.path.join(
                get_package_share_directory('nav2_bt_navigator'),
                'behavior_trees', 'navigate_w_replanning_and_recovery.xml'),
            description='Path ke Behavior Tree XML'),

        DeclareLaunchArgument(
            'map_subscribe_transient_local', default_value='false',
            description='QoS transient local untuk map subscriber'),

        # ============================================================
        # STATIC TRANSFORM: map -> odom
        # Karena tidak menggunakan AMCL, kita "kunci" frame map = odom.
        # Robot akan bernavigasi di frame odom secara penuh.
        # Transform ini "zero" artinya map origin = odom origin.
        # ============================================================
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_static_tf',
            output='screen',
            arguments=['0', '0', '0',   # x y z
                       '0', '0', '0',   # roll pitch yaw
                       'map', 'odom'],  # parent child
        ),

        # ---- Nav2 Core Servers ----
        Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings,
        ),

        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings,
        ),

        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[configured_params],
            remappings=remappings,
        ),

        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params],
            remappings=remappings,
        ),

        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params],
            remappings=remappings,
        ),

        # ---- Lifecycle Manager ----
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'autostart': autostart},
                {'node_names': lifecycle_nodes},
            ],
        ),
    ])
