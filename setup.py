from setuptools import setup, find_packages


VERSION = '0.2.3'


setup(name='simple_json_logger',
      version=VERSION,
      packages=find_packages(exclude=['*test*']),
      url='https://github.com/diogommartins/simple_json_logger',
      author='Diogo Magalhães Martins',
      author_email='magalhaesmartins@icloud.com',
      keywords='logging json log output')
