import setuptools
from distutils.core import setup


setup(
    name="collectington",
    packages=setuptools.find_packages(),
    install_requires=["prometheus-client", "termcolor", "pyfiglet", "requests"],
    scripts=["cton"],
    license="MIT",
    version="1.0.0",
    description="",  # change later
    author="HomeX",
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
