from setuptools import setup

# run updater like: python setup.py sdist bdist_wininst upload

setup(name = 'yagmail',
      version = "0.3.6",
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
