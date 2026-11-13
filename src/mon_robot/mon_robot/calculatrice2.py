import rclpy
from rclpy.node import Node
from mes_interfaces.srv import Calcul
import math

class Calculatrice2(Node):
    def __init__(self):
        super().__init__('calculatrice2')
        self.srv = self.create_service(Calcul, 'calculer', self.calculer)

    def calculer(self, req, rep):
        op = req.operation
        rep.succes = True
        rep.message = 'OK'
        if op == 'add':
            rep.resultat = req.a + req.b
        elif op == 'sub':
            rep.resultat = req.a - req.b
        elif op == 'mul':
            rep.resultat = req.a * req.b
        elif op == 'div':
            if req.b == 0.0:
                rep.succes = False
                rep.message = 'Division par zéro impossible'
            else:
                rep.resultat = req.a / req.b
        elif op == 'pow':
            rep.resultat = math.pow(req.a, req.b)
        else:
            rep.succes = False
            rep.message = f"Opération inconnue : '{op}' (add, sub, mul, div)"
        self.get_logger().info(f'{req.a} {op} {req.b} -> {rep.resultat} ({rep.message})')
        return rep


def main():
    rclpy.init()
    node = Calculatrice2()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()