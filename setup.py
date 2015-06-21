from setuptools import setup

MAJOR_VERSION = '0'
MINOR_VERSION = '4'
MICRO_VERSION = '84'
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
      extras_require = {
          'lxml' : 'lxml >= 3.4.0' 
      },
      entry_points = { 
          'console_scripts': ['yagmail = yagmail.yagmail:main'] 
      },
      zip_safe = False)
