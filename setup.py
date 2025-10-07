from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="meshnetmap",
    version="1.0.0",
    author="Meshtastic Network Mapper",
    description="Map and visualize Meshtastic network topology via Bluetooth",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "meshtastic>=2.3.0",
        "bleak>=0.21.0",
        "networkx>=3.0",
        "matplotlib>=3.7.0",
        "plotly>=5.18.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "meshnetmap=meshnetmap.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)