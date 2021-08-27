import setuptools
from distutils.core import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="collectington",
    packages=setuptools.find_packages(),
    install_requires=["prometheus-client", "termcolor", "pyfiglet", "requests"],
    scripts=["cton"],
    license="MIT",
    version="0.1.2",
    description="Collectington is a framework that allows any 3rd party API data to be sent to Prometheus",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="YoungJun Park, Nathan Boswell, Eric Jalbert",
    author_email="collectington@homex.com",
    url="https://github.com/HomeXLabs/collectington",
    download_url="https://github.com/HomeXLabs/collectington",
    package_dir={"collectington": "collectington"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
)
