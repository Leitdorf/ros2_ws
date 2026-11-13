import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from mes_interfaces.msg import Etat

class Ecouteur(Node):
    def __init__(self):
        super().__init__('ecouteur')
        self.sub = self.create_subscription(String, 'bavardage', self.reception, 10)
        self.sub_etat = self.create_subscription(Etat, 'etat', self.sur_etat, 10)

    def reception(self, msg):
        self.get_logger().info(f'Reçu : {msg.data}')
    def sur_etat(self, msg):
        if msg.batterie < 20.0:
            self.get_logger().warn(f'{msg.nom} : batterie faible ({msg.batterie:.0f} %) !')

def main():
    rclpy.init()
    node = Ecouteur()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()