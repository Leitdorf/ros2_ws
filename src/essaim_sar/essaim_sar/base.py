import csv
import os

import rclpy
from rclpy.node import Node
from mes_interfaces.msg import CaseVisitee, Victime


class Base(Node):
    def __init__(self):
        super().__init__('base')
        self.declare_parameter('nb_victimes', 5)
        self.declare_parameter('nb_robots', 4)
        self.declare_parameter('graine', 42)
        self.declare_parameter('partage', True)
        self.declare_parameter('panne', 'aucune')
        self.declare_parameter('portee', 0.0)
        self.declare_parameter('duree_max', 300.0)
        self.declare_parameter('fichier', os.path.expanduser('~/resultats_sar.csv'))

        self.cases = set()
        self.trouvees = set()
        self.debut = self.get_clock().now()
        self.fini = False
        self.create_subscription(CaseVisitee, '/cases_visitees', self.cb_case, 50)
        self.create_subscription(Victime, '/victimes_trouvees', self.cb_victime, 10)
        self.create_timer(5.0, self.rapport)

    def temps(self):
        return (self.get_clock().now() - self.debut).nanoseconds / 1e9

    def couverture(self):
        return 100.0 * len(self.cases) / 121

    def cb_case(self, msg):
        # la base voit tout : pas de filtre de portée ici
        self.cases.add(msg.index)

    def cb_victime(self, msg):
        self.trouvees.add(msg.id)
        if len(self.trouvees) == self.get_parameter('nb_victimes').value:
            self.enregistrer()

    def rapport(self):
        n = self.get_parameter('nb_victimes').value
        self.get_logger().info(
            f't={self.temps():.0f} s | victimes {len(self.trouvees)}/{n} | '
            f'couverture {self.couverture():.0f} %')
        if self.temps() > self.get_parameter('duree_max').value:
            self.enregistrer()

    def enregistrer(self):
        if self.fini:
            return
        fichier = self.get_parameter('fichier').value
        nouveau = not os.path.exists(fichier)
        with open(fichier, 'a', newline='') as f:
            w = csv.writer(f)
            if nouveau:
                w.writerow(['nb_robots', 'partage', 'panne', 'portee', 'graine',
                            'victimes', 'temps_s', 'couverture_pct'])
            w.writerow([self.get_parameter('nb_robots').value,
                        self.get_parameter('partage').value,
                        self.get_parameter('panne').value,
                        self.get_parameter('portee').value,
                        self.get_parameter('graine').value,
                        len(self.trouvees),
                        round(self.temps(), 1),
                        round(self.couverture(), 1)])
        self.get_logger().info(f'Mission terminée en {self.temps():.1f} s')
        self.fini = True


def main():
    rclpy.init()
    node = Base()
    while rclpy.ok() and not node.fini:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()