#!/usr/bin/env python3
"""Setup configuration for NuSyQ-Hub package
Includes py.typed marker for PEP 561 type checking support
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read long description from README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

if __name__ == "__main__":
    setup(
        name="nusyq-hub",
        version="0.1.0",
        description="NuSyQ Hub - Multi-AI Orchestration Platform",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="KiloMusician & NuSyQ Development Team",
        python_requires=">=3.11",
        packages=find_packages(include=["src", "src.*"]),
        package_data={
            "src": ["py.typed"],  # Include PEP 561 type marker
        },
        install_requires=[
            # Core dependencies - minimal for runtime
        ],
        extras_require={
            "dev": [
                "pytest>=7.4.0",
                "pytest-asyncio>=0.21.0",
                "pytest-cov>=4.1.0",
                "pytest-timeout>=2.1.0",
                "black>=23.0.0",
                "ruff>=0.1.0",
                "mypy>=1.5.0",
            ],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Typing :: Typed",
        ],
    )
