import math
import random

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32
from turtlesim.msg import Pose
from mes_interfaces.msg import CaseVisitee

TAILLE = 11              # grille 11 x 11 cases de 1 m
CENTRE = 5.5
LARGEUR = 11.09          # largeur de l'arène turtlesim
Y_BAS, Y_HAUT = 0.6, 10.5


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
        self.declare_parameter('strategie', 'levy')   # 'levy' ou 'bandes'
        self.declare_parameter('nb_allees', 10)

        self.moi = self.get_namespace().strip('/')
        self.pose = None
        self.cap = random.uniform(-math.pi, math.pi)
        self.reste = 1.0
        self.ma_case = -1
        self.visites = [0] * (TAILLE * TAILLE)
        self.voisins = {}
        # stratégie bandes
        self.allees_finies = set()
        self.proprietaire = self.partage_initial()   # allée -> robot
        self.morts = set()
        self.plan_pret = False
        self.points = []          # (x, y, allée terminée en arrivant ici, ou None)
        self.i_point = 0

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.pub_case = self.create_publisher(CaseVisitee, '/cases_visitees', 50)
        self.pub_allee = self.create_publisher(Int32, '/allees_finies', 10)
        self.create_subscription(Pose, 'pose', self.cb_pose, 10)
        self.create_subscription(CaseVisitee, '/cases_visitees', self.cb_case, 50)
        self.create_subscription(Int32, '/allees_finies', self.cb_allee, 10)
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

    def cb_allee(self, msg):
        self.allees_finies.add(msg.data)

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

    # ---------- stratégie bandes ----------
    def partage_initial(self):
        """Même table chez tous les robots : des blocs d'allées voisines."""
        robots = self.get_parameter('robots').value
        nb = self.get_parameter('nb_allees').value
        n = len(robots)
        return {k: robots[k * n // nb] for k in range(nb)}

    def mes_allees(self):
        return sorted(k for k, r in self.proprietaire.items()
                      if r == self.moi and k not in self.allees_finies)

    def verifier_pannes(self):
        """Un voisin silencieux depuis plus d'1 s est en panne (traité une seule fois)."""
        maintenant = self.get_clock().now()
        for nom, (x, y, instant) in list(self.voisins.items()):
            if nom not in self.morts and (maintenant - instant).nanoseconds / 1e9 > 1.0:
                self.morts.add(nom)
                self.reprendre(nom)

    def reprendre(self, mort):
        """Réparation locale : les voisins vivants se partagent les allées orphelines."""
        robots = self.get_parameter('robots').value
        orphelines = sorted(k for k, r in self.proprietaire.items()
                            if r == mort and k not in self.allees_finies)
        i = robots.index(mort)
        gauche = next((r for r in reversed(robots[:i]) if r not in self.morts), None)
        droite = next((r for r in robots[i + 1:] if r not in self.morts), None)
        if gauche and droite:
            moitie = len(orphelines) // 2
        elif gauche:
            moitie = len(orphelines)          # tout pour la gauche
        else:
            moitie = 0                        # tout pour la droite
        for k in orphelines[:moitie]:
            self.proprietaire[k] = gauche
        for k in orphelines[moitie:]:
            self.proprietaire[k] = droite
        mes_nouvelles = [k for k in orphelines if self.proprietaire[k] == self.moi]
        msg = f'{mort} en panne, allées orphelines : {orphelines}'
        if mes_nouvelles:
            msg += f' -> je reprends {mes_nouvelles}'
            self.ajouter_au_plan(mes_nouvelles)
        self.get_logger().warn(msg)

    def ajouter_au_plan(self, allees):
        """On finit ce qu'on fait, puis on enchaîne sur les nouvelles allées."""
        reste = self.points[self.i_point:]
        if reste:
            x, y = reste[-1][0], reste[-1][1]
        else:
            x, y = self.pose.x, self.pose.y
        self.points = reste + self.chemin(allees, x, y)
        self.i_point = 0

    def chemin(self, allees, x0, y0):
        """Points des allées, en partant de (x0, y0) : allée et bout les plus proches d'abord."""
        if not allees:
            return []
        ecart = LARGEUR / self.get_parameter('nb_allees').value
        x_premiere = (allees[0] + 0.5) * ecart
        x_derniere = (allees[-1] + 0.5) * ecart
        if abs(x_derniere - x0) < abs(x_premiere - x0):
            allees = allees[::-1]
        monter = y0 < CENTRE
        points = []
        for k in allees:
            x = (k + 0.5) * ecart
            debut, fin = (Y_BAS, Y_HAUT) if monter else (Y_HAUT, Y_BAS)
            points += [(x, debut, None), (x, fin, k)]  # l'allée k est finie en arrivant au bout
            monter = not monter
        return points

    def suivre_bandes(self, p):
        tx, ty, allee = self.points[self.i_point]
        dist = math.hypot(tx - p.x, ty - p.y)
        cmd = Twist()
        if dist < 0.2:
            self.i_point += 1
            if allee is not None:
                self.pub_allee.publish(Int32(data=allee))
            if self.i_point == len(self.points):
                self.get_logger().info('Mes allées sont finies : je passe en Lévy')
        else:
            err = ecart_angle(math.atan2(ty - p.y, tx - p.x), p.theta)
            cmd.angular.z = 4.0 * err
            if abs(err) < 0.3:
                cmd.linear.x = min(self.get_parameter('vitesse').value, 2.0 * dist)
        self.pub.publish(cmd)

    # ---------- Lévy ----------
    def longueur_levy(self):
        mu = self.get_parameter('mu').value
        u = max(random.random(), 1e-6)
        return min(0.5 * u ** (-1.0 / (mu - 1.0)), 8.0)

    def nouveau_pas(self):
        """8 candidats qui restent dans l'arène, on garde la case la moins fouillée."""
        meilleur = None
        for _ in range(8):
            cap = random.uniform(-math.pi, math.pi)
            longueur = self.longueur_levy()
            tx = self.pose.x + longueur * math.cos(cap)
            ty = self.pose.y + longueur * math.sin(cap)
            if not (0.5 < tx < 10.5 and 0.5 < ty < 10.5):
                continue                           # sortirait de l'arène
            score = self.visites[case(tx, ty)] + random.random() * 0.5
            if meilleur is None or score < meilleur[0]:
                meilleur = (score, cap, longueur)
        if meilleur is None:                       # aucun candidat valable (rare)
            meilleur = (0, random.uniform(-math.pi, math.pi), 1.0)
        _, self.cap, self.reste = meilleur

    # ---------- boucle principale ----------
    def boucle(self):
        if self.pose is None:
            return
        p = self.pose
        if self.get_parameter('strategie').value == 'bandes':
            if not self.plan_pret:                 # premier tick : on a enfin notre position
                self.points = self.chemin(self.mes_allees(), p.x, p.y)
                self.plan_pret = True
                self.get_logger().info(f'Mes allées : {self.mes_allees()}')
            self.verifier_pannes()
            if self.i_point < len(self.points):
                self.suivre_bandes(p)
                return
            # plus d'allée à faire : on continue en Lévy (la suite)
        # 1. répulsion : s'éloigner des voisins trop proches
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
        # 2. Lévy + carte : pas terminé -> choisir le prochain
        if self.reste <= 0.0:
            self.nouveau_pas()
        # 3. murs en dernier (ils ont le dernier mot) : rebond de billard
        marge = 0.5
        if (p.x < marge and math.cos(self.cap) < 0) or \
           (p.x > 11.0 - marge and math.cos(self.cap) > 0):
            self.cap = math.pi - self.cap          # mur gauche ou droit
        if (p.y < marge and math.sin(self.cap) < 0) or \
           (p.y > 11.0 - marge and math.sin(self.cap) > 0):
            self.cap = -self.cap                   # mur bas ou haut
        # 4. tourner vers le cap, avancer si on est bien orienté
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