from setuptools import setup
from setuptools import find_packages

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()
MAJOR_VERSION = '0'
MINOR_VERSION = '15'
# MICRO_VERSION = '277'
MICRO_VERSION = '281'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

setup(
    # name='yagmail',
    name='yagmail',
    version=VERSION,
    # description='Yet Another GMAIL client',
    description='fork of yagmail 0.15.280',
    # long_description=LONG_DESCRIPTION,
    long_description='fork of yagmail 0.15.280, fixed Fixed the problem in issue: https://github.com/kootenpv/yagmail/issues/242',
    url='https://github.com/leffss/yagmail',
    author='Pascal van Kooten',
    author_email='kootenpv@gmail.com',
    license='MIT',
    extras_require={"all": ["keyring", "dkimpy"], "dkim": ["dkimpy"]},
    install_requires=["premailer"],
    keywords='email mime automatic html attachment',
    entry_points={'console_scripts': ['yagmail = yagmail.__main__:main']},
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Communications :: Email',
        'Topic :: Communications :: Email :: Email Clients (MUA)',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    packages=find_packages(),
    zip_safe=False,
    platforms='any',
)
