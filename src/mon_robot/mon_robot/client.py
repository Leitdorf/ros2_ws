import sys
import rclpy
from rclpy.node import Node
from mes_interfaces.srv import Calcul


class Client(Node):
    def __init__(self):
        super().__init__('client_calcul')
        self.cli = self.create_client(Calcul, 'calculer')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Service indisponible, j'attends...")

    def demander(self, a, b, operation):
        req = Calcul.Request()
        req.a = a
        req.b = b
        req.operation = operation
        return self.cli.call_async(req)


def main():
    rclpy.init()
    args = rclpy.utilities.remove_ros_args(sys.argv)   # garde seulement tes arguments

    if len(args) != 4:
        print('Usage : ros2 run mon_robot client <a> <b> <add|sub|mul|div>')
        rclpy.try_shutdown()
        return

    node = Client()
    future = node.demander(float(args[1]), float(args[2]), args[3])
    rclpy.spin_until_future_complete(node, future)

    rep = future.result()
    if rep.succes:
        node.get_logger().info(f'Résultat : {rep.resultat}')
    else:
        node.get_logger().error(f'Erreur : {rep.message}')

    node.destroy_node()
    rclpy.try_shutdown()