import math
import random

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from turtlesim.srv import Spawn
from mes_interfaces.msg import Victime


class Victimes(Node):
    def __init__(self):
        super().__init__('victimes')
        self.declare_parameter('nb_victimes', 5)
        self.declare_parameter('rayon', 0.6)
        self.declare_parameter('graine', 42)
        self.declare_parameter('robots', ['turtle1'])

        self.rayon = self.get_parameter('rayon').value
        rng = random.Random(self.get_parameter('graine').value)
        self.cachees = {}
        while len(self.cachees) < self.get_parameter('nb_victimes').value:
            x, y = rng.uniform(1.0, 10.0), rng.uniform(1.0, 10.0)
            if math.hypot(x - 5.5, y - 5.5) > 2.0:      # pas collée à la base
                self.cachees[len(self.cachees)] = (x, y)

        self.pub = self.create_publisher(Victime, '/victimes_trouvees', 10)
        self.spawn = self.create_client(Spawn, '/spawn')
        for nom in self.get_parameter('robots').value:
            self.create_subscription(
                Pose, f'/{nom}/pose',
                lambda msg, nom=nom: self.verifier(nom, msg), 10)

        self.get_logger().info(f'{len(self.cachees)} victimes cachées')
        for i, (x, y) in self.cachees.items():           # triche pour tester
            self.get_logger().info(f'  victime {i} en ({x:.1f}, {y:.1f})')

    def verifier(self, nom, pose):
        for i, (x, y) in list(self.cachees.items()):
            if math.hypot(pose.x - x, pose.y - y) < self.rayon:
                del self.cachees[i]
                self.pub.publish(Victime(id=i, x=x, y=y, trouvee_par=nom))
                self.get_logger().info(f'Victime {i} trouvée par {nom} en ({x:.1f}, {y:.1f})')
                self.spawn.call_async(Spawn.Request(x=x, y=y, theta=0.0, name=f'victime{i}'))


def main():
    rclpy.init()
    rclpy.spin(Victimes())
    rclpy.shutdown()