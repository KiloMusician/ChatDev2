"""Virtual Filesystem for CyberTerminal.

Provides a simulated Linux-like filesystem with directories, files, permissions,
and user/group management for the educational game.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class FilePermission(Enum):
    """File permission levels (simplified Unix permissions)."""

    READ = 0o4
    WRITE = 0o2
    EXECUTE = 0o1
    NONE = 0o0


class UserRole(Enum):
    """User roles in the filesystem."""

    OWNER = "owner"
    GROUP = "group"
    OTHER = "other"


@dataclass
class VirtualFile:
    """Represents a file in the virtual filesystem."""

    name: str
    content: str = ""
    owner: str = "root"
    group: str = "root"
    permissions: dict[UserRole, int] = field(
        default_factory=lambda: {
            UserRole.OWNER: 0o6,  # rw-
            UserRole.GROUP: 0o4,  # r--
            UserRole.OTHER: 0o4,  # r--
        }
    )
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_hidden: bool = False
    file_type: str = "text"  # text, binary, script, config
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_read(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can read this file."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.READ.value)

    def can_write(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can write to this file."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.WRITE.value)

    def can_execute(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can execute this file."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.EXECUTE.value)

    def get_size(self) -> int:
        """Get file size in bytes."""
        return len(self.content.encode("utf-8"))


@dataclass
class VirtualDirectory:
    """Represents a directory in the virtual filesystem."""

    name: str
    owner: str = "root"
    group: str = "root"
    permissions: dict[UserRole, int] = field(
        default_factory=lambda: {
            UserRole.OWNER: 0o7,  # rwx
            UserRole.GROUP: 0o5,  # r-x
            UserRole.OTHER: 0o5,  # r-x
        }
    )
    created_at: datetime = field(default_factory=datetime.now)
    parent: Optional["VirtualDirectory"] = None
    is_hidden: bool = False
    tags: list[str] = field(default_factory=list)

    # Contents
    files: dict[str, VirtualFile] = field(default_factory=dict)
    subdirs: dict[str, "VirtualDirectory"] = field(default_factory=dict)

    def can_read(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can list directory contents."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.READ.value)

    def can_write(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can create files in this directory."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.WRITE.value)

    def can_enter(self, _user: str, user_role: UserRole) -> bool:
        """Check if user can enter (cd into) this directory."""
        perms = self.permissions.get(user_role, 0)
        return bool(perms & FilePermission.EXECUTE.value)

    def add_file(self, file: VirtualFile) -> None:
        """Add a file to this directory."""
        self.files[file.name] = file

    def add_directory(self, directory: "VirtualDirectory") -> None:
        """Add a subdirectory."""
        directory.parent = self
        self.subdirs[directory.name] = directory

    def get_full_path(self) -> str:
        """Get full path from root."""
        if self.parent is None:
            return "/" + self.name if self.name != "/" else "/"
        parent_path = self.parent.get_full_path()
        if parent_path == "/":
            return "/" + self.name
        return f"{parent_path}/{self.name}"


class VirtualFilesystem:
    """Main virtual filesystem implementation."""

    def __init__(self):
        """Initialize filesystem with standard directory structure."""
        self.root = VirtualDirectory(name="/")
        self.current_directory = self.root
        self.current_user = "player"
        self.current_user_role = UserRole.OTHER
        self.command_history: list[str] = []

        # Initialize standard directories
        self._initialize_standard_structure()

    def _initialize_standard_structure(self) -> None:
        """Create standard Linux directory structure."""
        standard_dirs = [
            ("home", "root", "root"),
            ("etc", "root", "root"),
            ("bin", "root", "root"),
            ("usr", "root", "root"),
            ("var", "root", "root"),
            ("tmp", "root", "root"),
            ("opt", "root", "root"),
            ("var/log", "root", "root"),
            ("usr/bin", "root", "root"),
            ("usr/local", "root", "root"),
        ]

        for path_parts, owner, group, directory in [
            (d.split("/")[:-1], owner, group, d) for d, owner, group in standard_dirs
        ]:
            self._create_directory_path(path_parts or [directory.split("/")[0]], owner, group)

    def _create_directory_path(
        self, path_parts: list[str], owner: str, group: str
    ) -> VirtualDirectory | None:
        """Create a directory and its parents if needed."""
        current = self.root
        for part in path_parts:
            if part not in current.subdirs:
                new_dir = VirtualDirectory(name=part, owner=owner, group=group)
                current.add_directory(new_dir)
            current = current.subdirs[part]
        return current

    def navigate_to(self, path: str) -> bool:
        """Navigate to a directory by path."""
        if path == "/":
            self.current_directory = self.root
            return True

        if path.startswith("/"):
            current = self.root
            path = path[1:]
        else:
            current = self.current_directory

        for part in path.split("/"):
            if part == "..":
                if current.parent:
                    current = current.parent
            elif part == "." or part == "":
                continue
            elif part in current.subdirs:
                current = current.subdirs[part]
            else:
                return False

        self.current_directory = current
        return True

    def list_directory(self, path: str | None = None, show_hidden: bool = False) -> list[str]:
        """List contents of a directory."""
        if path and not self.navigate_to(path):
            return []

        contents = []

        # Add parent directory reference unless at root
        if self.current_directory.parent:
            contents.append("..")

        # Add subdirectories
        for name, subdir in sorted(self.current_directory.subdirs.items()):
            if show_hidden or not subdir.is_hidden:
                contents.append(f"{name}/")

        # Add files
        for name, file in sorted(self.current_directory.files.items()):
            if show_hidden or not file.is_hidden:
                contents.append(name)

        return contents

    def create_file(self, filename: str, content: str = "", owner: str | None = None) -> bool:
        """Create a file in the current directory."""
        if filename in self.current_directory.files:
            return False

        owner = owner or self.current_user
        file = VirtualFile(name=filename, content=content, owner=owner)
        self.current_directory.add_file(file)
        return True

    def get_file(self, filename: str) -> VirtualFile | None:
        """Get a file from the current directory."""
        return self.current_directory.files.get(filename)

    def get_current_path(self) -> str:
        """Get the current working directory path."""
        return self.current_directory.get_full_path()

    def change_permissions(self, filename: str, permissions: dict[UserRole, int]) -> bool:
        """Change file permissions."""
        file = self.get_file(filename)
        if file:
            file.permissions = permissions
            file.modified_at = datetime.now()
            return True
        return False
