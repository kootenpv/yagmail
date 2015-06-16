from setuptools import setup
# run updater like: python setup.py sdist bdist_wininst upload

MAJOR_VERSION = '0'
MINOR_VERSION = '3'
MICRO_VERSION = '78'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

setup(name = 'yagmail',
      version = VERSION,
      description = 'Yet Another GMAIL client',
      url = 'https://github.com/kootenpv/yagmail',
      author = 'Pascal van Kooten',
      author_email = 'kootenpv@gmail.com',
      license = 'GPL',
      packages = ['yagmail'],
      install_requires = [ 
          'keyring',
      ],
      entry_points = { 
          'console_scripts': ['yagmail = yagmail.yagmail:main'] 
          },
      zip_safe = False)
