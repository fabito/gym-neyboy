from setuptools import setup, find_packages
import sys

if sys.version_info.major != 3:
    print('This Python is only compatible with Python 3, but you are running '
          'Python {}. The installation will likely fail.'.format(sys.version_info.major))

setup(name='gym_neyboy',
      version='0.0.1',
      package_data={'gym_neyboy': ['env/*.js']},
           packages=[package for package in find_packages()],
      extras_require={
            "terminal": ["asciimatics"],
      },
      install_requires=['gym', 'pyppeteer', 'syncer', 'Pillow']
)
