import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import String
from mes_interfaces.msg import Etat


class Emetteur(Node):
    def __init__(self):
        super().__init__('emetteur')
        self.declare_parameter('texte', 'Bonjour ROS 2')
        self.declare_parameter('periode', 0.5)
        periode = self.get_parameter('periode').value

        self.pub = self.create_publisher(String, 'bavardage', 10)
        self.pub_etat = self.create_publisher(Etat, 'etat', 10)

        self.compteur = 0
        self.batterie = 100.0
        self.timer = self.create_timer(periode, self.tick)

        # Appelée à chaque "ros2 param set" sur ce node
        self.add_on_set_parameters_callback(self.sur_changement_params)

    def sur_changement_params(self, params):
        for p in params:
            if p.name == 'periode':
                if p.value <= 0.0:
                    return SetParametersResult(
                        successful=False, reason='La période doit être supérieure à 0')
                self.destroy_timer(self.timer)
                self.timer = self.create_timer(p.value, self.tick)
                self.get_logger().info(f'Nouvelle période : {p.value} s')
        return SetParametersResult(successful=True)

    def tick(self):
        texte = self.get_parameter('texte').value
        msg = String()
        msg.data = f'{texte} n°{self.compteur}'
        self.pub.publish(msg)
        self.compteur += 1

        etat = Etat()
        etat.nom = 'robot_orso'
        etat.batterie = self.batterie
        self.pub_etat.publish(etat)
        self.get_logger().info(f'Batterie : {self.batterie:.0f} %')

        self.batterie -= 5.0
        if self.batterie < 0.0:
            self.batterie = 100.0


def main():
    rclpy.init()
    node = Emetteur()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()