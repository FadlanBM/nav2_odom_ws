import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='nav2_odom_ws'

    x_pose = LaunchConfiguration('x', default='0.0')
    y_pose = LaunchConfiguration('y', default='0.0')
    z_pose = LaunchConfiguration('z', default='0.1')
    yaw_pose = LaunchConfiguration('yaw', default='0.0')

    declare_x_pose = DeclareLaunchArgument('x', default_value='0.0', description='X position of the robot')
    declare_y_pose = DeclareLaunchArgument('y', default_value='0.0', description='Y position of the robot')
    declare_z_pose = DeclareLaunchArgument('z', default_value='0.1', description='Z position of the robot')
    declare_yaw_pose = DeclareLaunchArgument('yaw', default_value='0.0', description='Yaw orientation of the robot')

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'true', 'is_ignition': 'true'}.items()
    )

    joystick = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','joystick.launch.py'
                )]), launch_arguments={'use_sim_time': 'true'}.items()
    )

    # twist_mux_params = os.path.join(get_package_share_directory(package_name),'config','twist_mux.yaml')
    # twist_mux = Node(
    #         package="twist_mux",
    #         executable="twist_mux",
    #         parameters=[twist_mux_params, {'use_sim_time': True}],
    #         remappings=[('/cmd_vel_out','/diff_cont/cmd_vel_unstamped')]
    #     )

    # Gazebo Sim (Ignition)
    world = os.path.join(get_package_share_directory(package_name), 'worlds', 'empty_ign.sdf')
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')]),
                    launch_arguments={'gz_args': f'-r {world}'}.items()
             )

    # Spawn
    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', 'robot_description',
                                   '-name', 'my_bot',
                                   '-x', x_pose,
                                   '-y', y_pose,
                                   '-z', z_pose,
                                   '-Y', yaw_pose],
                        output='screen')

    # Bridge
    bridge_params = os.path.join(get_package_share_directory(package_name),'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont", "--ros-args", "-r", "/diff_cont/cmd_vel_unstamped:=/cmd_vel"],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )


    # Set the path to the gazebo models
    ign_resource_path = AppendEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[os.path.join(get_package_share_directory(package_name), '..')]
    )


    # Launch them all!
    return LaunchDescription([
        declare_x_pose,
        declare_y_pose,
        declare_z_pose,
        declare_yaw_pose,
        ign_resource_path,
        rsp,
        joystick,
        # twist_mux,
        gazebo,
        spawn_entity,
        ros_gz_bridge,
        diff_drive_spawner,
        joint_broad_spawner
    ])
