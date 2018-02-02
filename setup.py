from setuptools import setup
from setuptools import find_packages

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()
MAJOR_VERSION = '0'
MINOR_VERSION = '10'
MICRO_VERSION = '209'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

setup(name='yagmail',
      version=VERSION,
      description='Yet Another GMAIL client',
      long_description=LONG_DESCRIPTION,
      url='https://github.com/kootenpv/yagmail',
      author='Pascal van Kooten',
      author_email='kootenpv@gmail.com',
      license='MIT',
      extras_require={
          "all": ["keyring"]
      },
      keywords='email mime automatic html attachment',
      entry_points={
          'console_scripts': ['yagmail = yagmail.__main__:main']
      },
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Customer Service',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
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
      packages=find_packages(),
      zip_safe=False,
      platforms='any')
