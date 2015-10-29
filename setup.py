from setuptools import setup

MAJOR_VERSION = '0'
MINOR_VERSION = '4'
MICRO_VERSION = '114'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

setup(name='yagmail',
      version=VERSION,
      description='Yet Another GMAIL client',
      url='https://github.com/kootenpv/yagmail',
      author='Pascal van Kooten',
      author_email='kootenpv@gmail.com',
      license='MIT',
      packages=['yagmail'],
      install_requires=[
          'keyring',
      ],
      extras_require={
          'lxml': 'lxml >= 3.4.0'
      },
      entry_points={
          'console_scripts': ['yagmail = yagmail.yagmail:main']
      },
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Customer Service',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: Microsoft',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Communications :: Email',
          'Topic :: Communications :: Email :: Email Clients (MUA)',
          'Topic :: Software Development',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Debuggers',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities'
      ],
      zip_safe=False,
      platforms='any')
