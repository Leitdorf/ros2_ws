import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'essaim_sar'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orso',
    maintainer_email='onegroni@free.fr',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'victimes = essaim_sar.victimes:main',
            'explorateur = essaim_sar.explorateur:main',
            'base = essaim_sar.base:main',
        ],
    },
)
