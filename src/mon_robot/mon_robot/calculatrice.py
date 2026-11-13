import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class Calculatrice(Node):
    def __init__(self):
        super().__init__('calculatrice')
        self.srv = self.create_service(AddTwoInts, 'additionner', self.additionner)

    def additionner(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'{request.a} + {request.b} = {response.sum}')
        return response


def main():
    rclpy.init()
    node = Calculatrice()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()