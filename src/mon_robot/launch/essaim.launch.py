from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

# Tortues à ajouter : nom -> (x, y, orientation)
TORTUES = {
    
    'tortue2': (8.0, 3.0, 1.57),
    'tortue3': (3.0, 8.0, 3.14),
    'tortue4': (7.0, 7.0, 0.8),
    'tortue5': (4.0, 4.0, -0.8),
}


def generate_launch_description():
    noms = ['turtle1'] + list(TORTUES)
    actions = [
        Node(package='turtlesim', executable='turtlesim_node',
             additional_env={'QT_SCALE_FACTOR': '2'}),
        Node(package='mon_robot', executable='zones', output='screen'),
        # turtle1 existe déjà au démarrage de turtlesim
        Node(package='mon_robot', executable='pilote',
             namespace='turtle1', output='screen',
             parameters=[{'tortues': noms}],),
    ]

    for nom, (x, y, theta) in TORTUES.items():
        # 1. faire apparaître la tortue
        actions.append(ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                 f"{{x: {x}, y: {y}, theta: {theta}, name: '{nom}'}}"],
        ))
        # 2. lancer son pilote dans son namespace
        actions.append(Node(package='mon_robot', executable='pilote',
                            namespace=nom, output='screen',
                            parameters=[{'tortues': noms}],))

    return LaunchDescription(actions)