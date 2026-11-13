from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'mon_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orso',
    maintainer_email='orso@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'emetteur = mon_robot.emetteur:main',
            'ecouteur = mon_robot.ecouteur:main',
            'calculatrice = mon_robot.calculatrice:main',
            'client = mon_robot.client:main',
            'calculatrice2 = mon_robot.calculatrice2:main',
            'zones = mon_robot.zones:main',
            'pilote = mon_robot.pilote:main',
        ],
    },
)
