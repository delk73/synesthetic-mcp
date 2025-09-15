from setuptools import find_packages, setup

setup(
    name="synesthetic-mcp",
    version="0.1.0",
    packages=find_packages(include=["mcp", "mcp.*"]),
)
