from setuptools import setup, find_packages

setup(
    name='learnvcs',
    version='0.1.0',
    license='GPL-3.0',
    author='LQR471814',
    author_email='bramblefern1013@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/LQR471814/learn.vcs-scraper',
    keywords='vcs scraper',
    install_requires=['requests', 'lxml'],
)
