from setuptools import setup

setup(name='gym_neyboy',
      version='0.0.1',
      extras_require={
            "terminal": ["asciimatics"],
      },
      install_requires=['gym', 'pyppeteer', 'syncer', 'Pillow']
)
