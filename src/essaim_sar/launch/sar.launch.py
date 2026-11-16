import math

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess,
                            OpaqueFunction, Shutdown, TimerAction)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

COULEURS = [
    (255, 80, 0),     # orange
    (0, 160, 255),    # bleu
    (60, 200, 90),    # vert
    (230, 40, 160),   # rose
    (255, 200, 0),    # jaune
    (140, 90, 255),   # violet
    (0, 200, 200),    # turquoise
    (255, 255, 255),  # blanc
]


def lancer(context):
    n = int(LaunchConfiguration('n').perform(context))
    graine = int(LaunchConfiguration('graine').perform(context))
    partage = LaunchConfiguration('partage').perform(context) == 'true'
    panne = LaunchConfiguration('panne').perform(context)
    t_panne = float(LaunchConfiguration('t_panne').perform(context))
    portee = float(LaunchConfiguration('portee').perform(context))
    robots = [f'turtle{i}' for i in range(1, n + 1)]

    actions = []
    for i, nom in enumerate(robots):
        if i > 0:
            theta = 2 * math.pi * i / n
            actions.append(ExecuteProcess(cmd=[
                'ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                f"{{x: 5.5, y: 5.5, theta: {theta:.2f}, name: '{nom}'}}"]))
        r, g, b = COULEURS[i % len(COULEURS)]
        actions.append(TimerAction(period=2.0, actions=[ExecuteProcess(cmd=[
            'ros2', 'service', 'call', f'/{nom}/set_pen', 'turtlesim/srv/SetPen',
            f"{{r: {r}, g: {g}, b: {b}, width: 3, 'off': 0}}"])]))

    noeuds = [
        Node(package='essaim_sar', executable='explorateur', namespace=nom,
             parameters=[{'robots': robots, 'partage': partage, 'portee': portee}])
        for nom in robots
    ]
    noeuds.append(Node(package='essaim_sar', executable='victimes',
                       parameters=[{'robots': robots, 'graine': graine}]))
    noeuds.append(Node(package='essaim_sar', executable='base', output='screen',
                        parameters=[{'nb_robots': n, 'graine': graine, 'partage': partage,
                                'panne': panne, 'portee': portee}],
                        on_exit=Shutdown()))
    actions.append(TimerAction(period=4.0, actions=noeuds))

    # panne : la tortue disparaît t_panne secondes après le départ
    if panne != 'aucune':
        actions.append(TimerAction(period=4.0 + t_panne, actions=[ExecuteProcess(cmd=[
            'ros2', 'service', 'call', '/kill', 'turtlesim/srv/Kill',
            f"{{name: '{panne}'}}"])]))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('n', default_value='4'),
        DeclareLaunchArgument('graine', default_value='42'),
        DeclareLaunchArgument('partage', default_value='true'),
        DeclareLaunchArgument('panne', default_value='aucune'),
        DeclareLaunchArgument('t_panne', default_value='20'),
        DeclareLaunchArgument('portee', default_value='0'),
        Node(package='turtlesim', executable='turtlesim_node'),
        OpaqueFunction(function=lancer),
    ])