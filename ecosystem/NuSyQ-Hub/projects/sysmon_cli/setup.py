from setuptools import find_packages, setup

setup(
    name="sysmon_cli",
    version="0.1.0",
    description="CLI tool for monitoring system resources (CPU, memory, disk, network)",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/sysmon_cli",
    packages=find_packages(),
    install_requires=["click>=7.1.2", "psutil>=5.8.0"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "sysmon=sysmon_cli.cli:main",
        ],
    },
)
