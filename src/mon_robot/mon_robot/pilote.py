import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

MARGE = 1.5     # distance au mur avant de tourner
TAILLE = 11.0   # taille du monde turtlesim
CENTRE = 5.5


class Pilote(Node):
    def __init__(self):
        super().__init__('pilote')
        self.declare_parameter('vitesse', 1.5)
        self.declare_parameter('rayon', 0.5)   # distance de répulsion
        self.declare_parameter('tortues', ['turtle1', 'tortue2', 'tortue3'])
        self.declare_parameter('perception', 3.0)        # rayon où l'on « voit » les voisines
        self.declare_parameter('gain_alignement', 1.0)
        self.declare_parameter('gain_cohesion', 1.0)
        self.pose = None
        self.voisins = {}   # nom -> dernière Pose reçue

        # S'abonner à toutes les tortues sauf soi-même
        moi = self.get_namespace().strip('/')
        for nom in self.get_parameter('tortues').value:
            if nom != moi:
                self.create_subscription(
                    Pose, f'/{nom}/pose',
                    lambda msg, nom=nom: self.sur_voisin(nom, msg), 10)

        self.sub = self.create_subscription(Pose, 'pose', self.sur_pose, 10)
        self.cmd = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.boucle)

    def sur_pose(self, msg):
        self.pose = msg

    def sur_voisin(self, nom, msg):
        self.voisins[nom] = msg

    def orienter_vers(self, cible, p):
        """Tourne vers l'angle cible, avance une fois à peu près orientée."""
        ecart = math.atan2(math.sin(cible - p.theta), math.cos(cible - p.theta))
        twist = Twist()
        twist.angular.z = 4.0 * ecart
        twist.linear.x = 0.5 if abs(ecart) < 0.5 else 0.0
        return twist

    def voisin_le_plus_proche(self, p):
        plus_proche, d_min = None, float('inf')
        for nom, v in self.voisins.items():
            d = math.hypot(v.x - p.x, v.y - p.y)
            if d < d_min:
                plus_proche, d_min = nom, d
        return plus_proche, d_min

    def boucle(self):
        if self.pose is None:
            return
        p = self.pose

        pres_du_mur = (p.x < MARGE or p.x > TAILLE - MARGE or
                       p.y < MARGE or p.y > TAILLE - MARGE)
        nom, d = self.voisin_le_plus_proche(p)

        if pres_du_mur:                                        # priorité 1
            twist = self.orienter_vers(math.atan2(CENTRE - p.y, CENTRE - p.x), p)
        elif nom is not None and d < self.get_parameter('rayon').value:   # priorité 2
            v = self.voisins[nom]
            fuite = math.atan2(p.y - v.y, p.x - v.x)
            twist = self.orienter_vers(fuite, p)
            self.get_logger().info(f'Évite {nom} (distance {d:.1f})',
                                   throttle_duration_sec=1.0)
        else:                                                  # priorités 3 et 4
            twist = Twist()
            twist.linear.x = self.get_parameter('vitesse').value
            visibles = self.voisines_visibles(p)
            if visibles:
                # Alignement : direction moyenne (moyenne circulaire)
                cap = math.atan2(sum(math.sin(v.theta) for v in visibles),
                                 sum(math.cos(v.theta) for v in visibles))
                ecart_align = self.ecart(cap, p.theta)

                # Cohésion : direction vers le centre des voisines
                cx = sum(v.x for v in visibles) / len(visibles)
                cy = sum(v.y for v in visibles) / len(visibles)
                ecart_coh = self.ecart(math.atan2(cy - p.y, cx - p.x), p.theta)

                twist.angular.z = (self.get_parameter('gain_alignement').value * ecart_align +
                                   self.get_parameter('gain_cohesion').value * ecart_coh)

        self.cmd.publish(twist)

    @staticmethod
    def ecart(cible, actuel):
        """Différence d'angle ramenée entre -π et +π."""
        return math.atan2(math.sin(cible - actuel), math.cos(cible - actuel))

    def voisines_visibles(self, p):
        portee = self.get_parameter('perception').value
        return [v for v in self.voisins.values()
                if math.hypot(v.x - p.x, v.y - p.y) < portee]

def main():
    rclpy.init()
    node = Pilote()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()