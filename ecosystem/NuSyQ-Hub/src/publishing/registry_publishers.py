"""Registry-Specific Publishers.

Handles publishing to PyPI, NPM, and VS Code Marketplace with
metadata generation, build automation, and authentication.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# PyPI PUBLISHER
# ============================================================================


@dataclass
class PyPIMetadata:
    """PyPI package metadata."""

    name: str
    version: str
    description: str
    author: str
    author_email: str
    url: str | None = None
    license: str = "MIT"
    classifiers: list[str] = None
    keywords: list[str] = None
    requires_python: str = ">=3.8"

    def __post_init__(self):
        """Implement __post_init__."""
        if self.classifiers is None:
            self.classifiers = [
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Programming Language :: Python :: 3.12",
            ]
        if self.keywords is None:
            self.keywords = []


class PyPIPublisher:
    """Publish Python packages to PyPI."""

    def __init__(self, project_path: Path, pypi_token: str):
        """Initialize PyPI publisher.

        Args:
            project_path: Path to Python project
            pypi_token: PyPI authentication token
        """
        self.project_path = Path(project_path)
        self.pypi_token = pypi_token

    def generate_setup_py(self, metadata: PyPIMetadata) -> str:
        """Generate setup.py file content."""
        classifiers_str = ",\n        ".join(f'"{c}"' for c in metadata.classifiers)
        keywords_str = ", ".join(f'"{k}"' for k in metadata.keywords)

        setup_py = f'''"""
{metadata.description}
"""
from setuptools import setup, find_packages

setup(
    name="{metadata.name}",
    version="{metadata.version}",
    description="{metadata.description}",
    author="{metadata.author}",
    author_email="{metadata.author_email}",
    url="{metadata.url or "https://github.com/example/repo"}",
    license="{metadata.license}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires="{metadata.requires_python}",
    classifiers=[
        {classifiers_str}
    ],
    keywords=[{keywords_str}],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)
'''
        return setup_py

    def generate_pyproject_toml(self, metadata: PyPIMetadata) -> str:
        """Generate pyproject.toml file content."""
        pyproject = f"""[build-system]
requires = ["setuptools>=65", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{metadata.name}"
version = "{metadata.version}"
description = "{metadata.description}"
readme = "README.md"
requires-python = "{metadata.requires_python}"
license = {{text = "{metadata.license}"}}
authors = [
    {{name = "{metadata.author}", email = "{metadata.author_email}"}}
]
keywords = {json.dumps(metadata.keywords)}
classifiers = [
    {"    " + ",".join(json.dumps(c) for c in metadata.classifiers).replace(", ", f",{chr(10)}    ")}
]

[project.urls]
Homepage = "{metadata.url or "https://github.com/example/repo"}"
Documentation = "https://github.com/example/repo/wiki"
Repository = "{metadata.url or "https://github.com/example/repo"}"
Issues = "{metadata.url or "https://github.com/example/repo"}/issues"
"""
        return pyproject

    def publish(self, metadata: PyPIMetadata, dry_run: bool = False) -> dict[str, Any]:
        """Publish package to PyPI.

        Args:
            metadata: PyPI package metadata
            dry_run: If True, don't actually publish

        Returns:
            Result dict with status and URL
        """
        try:
            logger.info(f"Publishing {metadata.name} to PyPI")

            # 1. Generate setup.py and pyproject.toml
            setup_py_content = self.generate_setup_py(metadata)
            pyproject_content = self.generate_pyproject_toml(metadata)

            (self.project_path / "setup.py").write_text(setup_py_content)
            (self.project_path / "pyproject.toml").write_text(pyproject_content)

            logger.debug("Generated setup.py and pyproject.toml")

            # 2. Build distribution
            logger.info("Building distribution...")
            build_cmd = ["python", "-m", "build", str(self.project_path)]
            result = subprocess.run(build_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": f"Build failed: {result.stderr}",
                }

            # 3. Upload with twine (if not dry run)
            if not dry_run:
                logger.info("Uploading to PyPI...")
                upload_cmd = [
                    "twine",
                    "upload",
                    "--repository-url",
                    "https://upload.pypi.org/legacy/",
                    "-u",
                    "__token__",
                    "-p",
                    self.pypi_token,
                    f"{self.project_path}/dist/*",
                ]
                result = subprocess.run(upload_cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"Upload failed: {result.stderr}")
                    return {
                        "status": "failed",
                        "error": f"Upload failed: {result.stderr}",
                    }

            return {
                "status": "success",
                "registry": "pypi",
                "url": f"https://pypi.org/project/{metadata.name}/{metadata.version}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"PyPI publishing failed: {e!s}")
            return {
                "status": "failed",
                "error": str(e),
            }


# ============================================================================
# NPM PUBLISHER
# ============================================================================


@dataclass
class NPMMetadata:
    """NPM package metadata."""

    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    repository: str | None = None
    homepage: str | None = None
    keywords: list[str] = None
    main: str = "dist/index.js"
    types: str = "dist/index.d.ts"
    scripts: dict[str, str] = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.keywords is None:
            self.keywords = []
        if self.scripts is None:
            self.scripts = {
                "build": "tsc",
                "test": "jest",
                "prepublishOnly": "npm run build && npm test",
            }


class NPMPublisher:
    """Publish Node/JavaScript packages to NPM."""

    def __init__(self, project_path: Path, npm_token: str):
        """Initialize NPM publisher.

        Args:
            project_path: Path to Node project
            npm_token: NPM authentication token
        """
        self.project_path = Path(project_path)
        self.npm_token = npm_token

    def generate_package_json(self, metadata: NPMMetadata) -> str:
        """Generate package.json file content."""
        package_json = {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "license": metadata.license,
            "main": metadata.main,
            "types": metadata.types,
            "repository": metadata.repository,
            "homepage": metadata.homepage,
            "keywords": metadata.keywords,
            "scripts": metadata.scripts,
            "engines": {"node": ">=16.0.0", "npm": ">=8.0.0"},
            "files": ["dist/", "README.md", "LICENSE"],
        }

        return json.dumps(package_json, indent=2)

    def generate_npmrc(self) -> str:
        """Generate .npmrc configuration file."""
        npmrc = f"""//registry.npmjs.org/:_authToken={self.npm_token}
registry=https://registry.npmjs.org/
always-auth=true
"""
        return npmrc

    def publish(self, metadata: NPMMetadata, dry_run: bool = False) -> dict[str, Any]:
        """Publish package to NPM.

        Args:
            metadata: NPM package metadata
            dry_run: If True, don't actually publish

        Returns:
            Result dict with status and URL
        """
        try:
            logger.info(f"Publishing {metadata.name} to NPM")

            # 1. Generate package.json
            package_json_content = self.generate_package_json(metadata)
            (self.project_path / "package.json").write_text(package_json_content)

            # 2. Generate .npmrc
            npmrc_content = self.generate_npmrc()
            npmrc_path = self.project_path / ".npmrc"
            npmrc_path.write_text(npmrc_content)

            logger.debug("Generated package.json and .npmrc")

            # 3. Build
            logger.info("Building distribution...")
            build_cmd = ["npm", "run", "build"]
            result = subprocess.run(
                build_cmd, cwd=self.project_path, capture_output=True, text=True
            )

            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": f"Build failed: {result.stderr}",
                }

            # 4. Publish (if not dry run)
            if not dry_run:
                logger.info("Publishing to NPM...")
                publish_cmd = ["npm", "publish"]
                if dry_run:
                    publish_cmd.append("--dry-run")

                result = subprocess.run(
                    publish_cmd, cwd=self.project_path, capture_output=True, text=True
                )

                if result.returncode != 0:
                    logger.error(f"Publish failed: {result.stderr}")
                    return {
                        "status": "failed",
                        "error": f"Publish failed: {result.stderr}",
                    }

            # 5. Cleanup .npmrc
            if npmrc_path.exists():
                npmrc_path.unlink()

            return {
                "status": "success",
                "registry": "npm",
                "url": f"https://www.npmjs.com/package/{metadata.name}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"NPM publishing failed: {e!s}")
            return {
                "status": "failed",
                "error": str(e),
            }


# ============================================================================
# VS CODE MARKETPLACE PUBLISHER
# ============================================================================


@dataclass
class VSCodeMetadata:
    """VS Code extension metadata."""

    name: str
    version: str
    description: str
    publisher: str  # Publisher ID on marketplace
    author: str
    license: str = "MIT"
    repository: str | None = None
    bugs: str | None = None
    homepage: str | None = None
    keywords: list[str] = None
    categories: list[str] = None
    activationEvents: list[str] = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.keywords is None:
            self.keywords = []
        if self.categories is None:
            self.categories = ["Other"]
        if self.activationEvents is None:
            self.activationEvents = ["onStartupFinished"]


class VSCodePublisher:
    """Publish VS Code extensions to Marketplace."""

    def __init__(self, project_path: Path, vscode_token: str):
        """Initialize VS Code publisher.

        Args:
            project_path: Path to extension project
            vscode_token: VS Code Personal Access Token
        """
        self.project_path = Path(project_path)
        self.vscode_token = vscode_token

    def generate_extension_json(self, metadata: VSCodeMetadata) -> dict[str, Any]:
        """Generate package.json for VS Code extension."""
        ext_json = {
            "name": metadata.name,
            "displayName": metadata.name.replace("-", " ").title(),
            "version": metadata.version,
            "publisher": metadata.publisher,
            "description": metadata.description,
            "author": {"name": metadata.author},
            "license": metadata.license,
            "repository": (
                {"type": "git", "url": metadata.repository} if metadata.repository else None
            ),
            "bugs": {"url": metadata.bugs} if metadata.bugs else None,
            "homepage": metadata.homepage,
            "keywords": metadata.keywords,
            "categories": metadata.categories,
            "engine": "vscode^1.80.0",
            "activationEvents": metadata.activationEvents,
            "main": "./dist/extension.js",
            "contributes": {
                "commands": [
                    {
                        "command": f"{metadata.publisher}.{metadata.name}.hello",
                        "title": "Hello World",
                    }
                ]
            },
            "scripts": {
                "vsce": "vsce",
                "pretest": "npm run compile",
                "test": "node ./out/test/runTest.js",
                "compile": "tsc -p ./",
                "watch": "tsc -watch -p ./",
                "prepackage": "npm run test",
                "package": "vsce package",
                "publish": "vsce publish",
            },
        }

        # Remove None values
        return {k: v for k, v in ext_json.items() if v is not None}

    def publish(self, metadata: VSCodeMetadata, dry_run: bool = False) -> dict[str, Any]:
        """Publish extension to VS Code Marketplace.

        Args:
            metadata: Extension metadata
            dry_run: If True, create package but don't publish

        Returns:
            Result dict with status and URL
        """
        try:
            logger.info(f"Publishing {metadata.publisher}.{metadata.name} to VS Code Marketplace")

            # 1. Generate/update extension package.json
            ext_json = self.generate_extension_json(metadata)
            (self.project_path / "package.json").write_text(json.dumps(ext_json, indent=2))

            logger.debug("Generated extension package.json")

            # 2. Compile TypeScript
            logger.info("Compiling TypeScript...")
            compile_cmd = ["npm", "run", "compile"]
            result = subprocess.run(
                compile_cmd, cwd=self.project_path, capture_output=True, text=True
            )

            if result.returncode != 0:
                logger.error(f"Compilation failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": f"Compilation failed: {result.stderr}",
                }

            # 3. Package extension
            logger.info("Packaging extension...")
            package_cmd = ["vsce", "package"]
            result = subprocess.run(
                package_cmd, cwd=self.project_path, capture_output=True, text=True
            )

            if result.returncode != 0:
                logger.error(f"Packaging failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": f"Packaging failed: {result.stderr}",
                }

            # 4. Publish (if not dry run)
            if not dry_run:
                logger.info("Publishing to VS Code Marketplace...")
                pub_cmd = ["vsce", "publish", "-p", self.vscode_token]
                result = subprocess.run(
                    pub_cmd, cwd=self.project_path, capture_output=True, text=True
                )

                if result.returncode != 0:
                    logger.error(f"Publishing failed: {result.stderr}")
                    return {
                        "status": "failed",
                        "error": f"Publishing failed: {result.stderr}",
                    }

            return {
                "status": "success",
                "registry": "vscode",
                "url": f"https://marketplace.visualstudio.com/items?itemName={metadata.publisher}.{metadata.name}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"VS Code publishing failed: {e!s}")
            return {
                "status": "failed",
                "error": str(e),
            }
