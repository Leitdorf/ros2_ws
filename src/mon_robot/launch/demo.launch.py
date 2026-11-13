from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mon_robot',
            executable='emetteur',
            parameters=[{'texte': 'Depuis le launch', 'periode': 1.0}],
            output='screen',
        ),
        Node(package='mon_robot', executable='ecouteur', output='screen'),
        Node(package='mon_robot', executable='calculatrice2', output='screen'),
    ])