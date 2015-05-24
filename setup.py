import re
from setuptools import setup

# run updater like: python setup.py sdist bdist_wininst upload

VERSION = re.search(r'^__version__\s*=\s*"(.*)"', open('yagmail/yagmail.py').read(), re.M).group(1)

setup(name = 'yagmail',
      version = VERSION,
      description = 'Yet Another GMAIL client',
      url = 'https://github.com/kootenpv/yagmail',
      author = 'Pascal van Kooten',
      author_email = 'kootenpv@gmail.com',
      license = 'GPL',
      packages = ['yagmail'],
      install_requires = [ 
          'keyring'
      ],
      entry_points = {
        "console_scripts": ['yagmail = yagmail.yagmail:main']
        },
      zip_safe = False)
