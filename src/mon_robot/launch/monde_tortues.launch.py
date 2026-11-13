from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('zoom', default_value='2',
                              description='Facteur de zoom de la fenêtre turtlesim'),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            additional_env={'QT_SCALE_FACTOR': LaunchConfiguration('zoom')},
        ),
        Node(package='mon_robot', executable='zones', output='screen'),
        Node(
            package='mon_robot',
            executable='pilote',
            parameters=[{'vitesse': ParameterValue(LaunchConfiguration('vitesse'),
                                                   value_type=float)}],
            output='screen',
        )
    ])