import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill, SetPen, TeleportAbsolute

# nom : (x_min, y_min, x_max, y_max, couleur RVB)
ZONES = {
    'recharge': (1.0, 1.0, 3.0, 3.0, (0, 200, 0)),
    'danger':   (7.5, 7.5, 10.0, 10.0, (220, 0, 0)),
}
TORTUES = ['turtle1', 'tortue2']


class Zones(Node):
    def __init__(self):
        super().__init__('zones')
        self.pub = self.create_publisher(String, 'evenements', 10)
        self.dedans = {}   # (tortue, zone) -> True/False
        for t in TORTUES:
            # t=t : chaque abonnement garde le nom de SA tortue
            self.create_subscription(
                Pose, f'/{t}/pose', lambda msg, t=t: self.sur_pose(t, msg), 10)

    def appeler(self, type_srv, nom, **champs):
        """Appelle un service et attend la réponse (utilisé au démarrage seulement)."""
        cli = self.create_client(type_srv, nom)
        cli.wait_for_service()
        req = type_srv.Request()
        for cle, val in champs.items():
            setattr(req, cle, val)
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        return fut.result()

    def dessiner_zones(self):
        self.appeler(Spawn, '/spawn', x=1.0, y=1.0, theta=0.0, name='peintre')
        for nom, (x0, y0, x1, y1, (r, g, b)) in ZONES.items():
            # stylo levé pour aller au premier coin
            self.appeler(SetPen, '/peintre/set_pen', r=0, g=0, b=0, width=1, off=1)
            self.appeler(TeleportAbsolute, '/peintre/teleport_absolute', x=x0, y=y0, theta=0.0)
            # stylo baissé : chaque téléportation trace un trait
            self.appeler(SetPen, '/peintre/set_pen', r=r, g=g, b=b, width=4, off=0)
            for x, y in [(x1, y0), (x1, y1), (x0, y1), (x0, y0)]:
                self.appeler(TeleportAbsolute, '/peintre/teleport_absolute', x=x, y=y, theta=0.0)
        self.appeler(Kill, '/kill', name='peintre')
        self.get_logger().info('Zones dessinées')

    def sur_pose(self, tortue, pose):
        for nom, (x0, y0, x1, y1, _) in ZONES.items():
            dedans = x0 <= pose.x <= x1 and y0 <= pose.y <= y1
            avant = self.dedans.get((tortue, nom), False)
            if dedans != avant:   # on ne réagit qu'au CHANGEMENT
                self.dedans[(tortue, nom)] = dedans
                msg = String()
                msg.data = f"{tortue} {'entre dans' if dedans else 'sort de'} {nom}"
                self.pub.publish(msg)
                self.get_logger().info(msg.data)


def main():
    rclpy.init()
    node = Zones()
    node.dessiner_zones()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()