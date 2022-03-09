from setuptools import setup, find_packages

setup(
    name='learnvcs',
    version='0.3.5',
    license='GPL-3.0',
    author='LQR471814',
    author_email='bramblefern1013@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/LQR471814/learn.vcs-scraper',
    keywords='vcs scraper',
    install_requires=['requests', 'lxml'],
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
)
