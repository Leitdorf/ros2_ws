import math
import random

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from mes_interfaces.msg import CaseVisitee

TAILLE = 11          # grille 11 x 11 cases de 1 m
CENTRE = 5.5


def ecart_angle(a, b):
    """Différence a - b ramenée entre -pi et pi."""
    return math.atan2(math.sin(a - b), math.cos(a - b))


def case(x, y):
    """Numéro de la case qui contient le point (x, y)."""
    cx = min(max(int(x), 0), TAILLE - 1)
    cy = min(max(int(y), 0), TAILLE - 1)
    return cy * TAILLE + cx


class Explorateur(Node):
    def __init__(self):
        super().__init__('explorateur')
        self.declare_parameter('vitesse', 1.5)
        self.declare_parameter('mu', 2.0)
        self.declare_parameter('rayon_repulsion', 1.5)
        self.declare_parameter('partage', True)
        self.declare_parameter('robots', ['turtle1'])
        self.declare_parameter('portee', 0.0)

        self.moi = self.get_namespace().strip('/')
        self.pose = None
        self.cap = random.uniform(-math.pi, math.pi)
        self.reste = 1.0
        self.ma_case = -1
        self.visites = [0] * (TAILLE * TAILLE)
        self.voisins = {}

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.pub_case = self.create_publisher(CaseVisitee, '/cases_visitees', 50)
        self.create_subscription(Pose, 'pose', self.cb_pose, 10)
        self.create_subscription(CaseVisitee, '/cases_visitees', self.cb_case, 50)
        for nom in self.get_parameter('robots').value:
            if nom != self.moi:
                self.create_subscription(
                    Pose, f'/{nom}/pose',
                    lambda msg, nom=nom: self.cb_voisin(nom, msg), 10)
        self.create_timer(0.1, self.boucle)

    # ---------- callbacks ----------
    def cb_pose(self, msg):
        self.pose = msg
        c = case(msg.x, msg.y)
        if c != self.ma_case:
            self.ma_case = c
            self.pub_case.publish(CaseVisitee(robot=self.moi, x=msg.x, y=msg.y, index=c))
            if not self.get_parameter('partage').value:
                self.visites[c] += 1                  # mémoire perso seulement

    def cb_case(self, msg):
        if not self.get_parameter('partage').value:
            return
        if msg.robot != self.moi and self.pose is not None:
            portee = self.get_parameter('portee').value
            d = math.hypot(self.pose.x - msg.x, self.pose.y - msg.y)
            if portee > 0 and d > portee:
                return                                # trop loin : message perdu
        self.visites[msg.index] += 1

    def cb_voisin(self, nom, msg):
        self.voisins[nom] = (msg.x, msg.y, self.get_clock().now())

    def voisins_valides(self):
        """Voisins récents (moins d'1 s) et à portée radio."""
        maintenant = self.get_clock().now()
        portee = self.get_parameter('portee').value
        for (x, y, instant) in self.voisins.values():
            if (maintenant - instant).nanoseconds / 1e9 > 1.0:
                continue                    # fantôme : on l'oublie
            if portee > 0 and math.hypot(self.pose.x - x, self.pose.y - y) > portee:
                continue                    # trop loin pour la radio
            yield x, y

    # ---------- décisions ----------
    def longueur_levy(self):
        mu = self.get_parameter('mu').value
        u = max(random.random(), 1e-6)
        return min(0.5 * u ** (-1.0 / (mu - 1.0)), 8.0)

    def nouveau_pas(self):
        """8 candidats, on garde celui qui va vers la case la moins fouillée."""
        meilleur = None
        for _ in range(8):
            cap = random.uniform(-math.pi, math.pi)
            longueur = self.longueur_levy()
            tx = self.pose.x + longueur * math.cos(cap)
            ty = self.pose.y + longueur * math.sin(cap)
            score = self.visites[case(tx, ty)] + random.random() * 0.5
            if meilleur is None or score < meilleur[0]:
                meilleur = (score, cap, longueur)
        _, self.cap, self.reste = meilleur

    def boucle(self):
        if self.pose is None:
            return
        p = self.pose
        # 1. murs : trop près d'un bord -> viser le centre
        marge = 1.0
        if not (marge < p.x < 11.0 - marge and marge < p.y < 11.0 - marge):
            self.cap = math.atan2(CENTRE - p.y, CENTRE - p.x)
            self.reste = max(self.reste, 1.0)
        else:
            # 2. répulsion : s'éloigner des voisins trop proches
            r = self.get_parameter('rayon_repulsion').value
            rx = ry = 0.0
            for (x, y) in self.voisins_valides():
                d = math.hypot(p.x - x, p.y - y)
                if 1e-3 < d < r:
                    rx += (p.x - x) / d ** 2
                    ry += (p.y - y) / d ** 2
            if rx or ry:
                self.cap = math.atan2(ry, rx)
                self.reste = max(self.reste, 0.8)
        # 3. Lévy + carte : pas terminé -> choisir le prochain
        if self.reste <= 0.0:
            self.nouveau_pas()
        err = ecart_angle(self.cap, p.theta)
        cmd = Twist()
        cmd.angular.z = 4.0 * err
        if abs(err) < 0.3:
            v = self.get_parameter('vitesse').value
            cmd.linear.x = v
            self.reste -= v * 0.1
        self.pub.publish(cmd)


def main():
    rclpy.init()
    rclpy.spin(Explorateur())
    rclpy.shutdown()