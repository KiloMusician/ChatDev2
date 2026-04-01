"""Database Helpers - Generate database schemas and migrations.

Supports:
- SQL schema generation (PostgreSQL, MySQL, SQLite)
- Prisma schema generation
- Migration file creation
- Relationship handling (foreign keys, joins)
- Index definitions
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class ColumnType(str, Enum):
    """Database column types."""

    TEXT = "TEXT"
    VARCHAR = "VARCHAR"
    INT = "INT"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    TIME = "TIME"
    JSON = "JSON"
    UUID = "UUID"
    SERIAL = "SERIAL"


@dataclass
class DatabaseColumn:
    """Represents a database column."""

    name: str
    column_type: ColumnType
    is_primary_key: bool = False
    is_nullable: bool = True
    is_unique: bool = False
    default_value: Any | None = None
    description: str | None = None
    length: int | None = None  # For VARCHAR


@dataclass
class DatabaseIndex:
    """Represents a database index."""

    name: str
    columns: list[str]
    is_unique: bool = False


@dataclass
class ForeignKey:
    """Represents a foreign key relationship."""

    column: str
    referenced_table: str
    referenced_column: str
    on_delete: str = "CASCADE"  # CASCADE, RESTRICT, SET NULL
    on_update: str = "CASCADE"


@dataclass
class DatabaseTable:
    """Represents a database table."""

    name: str
    columns: list[DatabaseColumn]
    description: str | None = None
    indexes: list[DatabaseIndex] | None = None
    foreign_keys: list[ForeignKey] | None = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.indexes is None:
            self.indexes = []
        if self.foreign_keys is None:
            self.foreign_keys = []


class SQLSchemaGenerator:
    """Generate SQL schemas for different databases."""

    def __init__(self, db_type: DatabaseType = DatabaseType.POSTGRESQL):
        """Initialize SQL schema generator."""
        self.db_type = db_type
        self.tables: dict[str, DatabaseTable] = {}

    def add_table(self, table: DatabaseTable) -> None:
        """Add a table definition."""
        self.tables[table.name] = table
        logger.info(f"Added table: {table.name}")

    def generate_schema(self) -> str:
        """Generate complete SQL schema."""
        if self.db_type == DatabaseType.POSTGRESQL:
            return self._generate_postgresql_schema()
        elif self.db_type == DatabaseType.MYSQL:
            return self._generate_mysql_schema()
        elif self.db_type == DatabaseType.SQLITE:
            return self._generate_sqlite_schema()
        else:
            raise ValueError(f"Unsupported database: {self.db_type}")

    def _generate_postgresql_schema(self) -> str:
        """Generate PostgreSQL schema."""
        statements = []

        for table in self.tables.values():
            statements.append(self._generate_postgresql_table(table))

        return "\n\n".join(statements)

    def _generate_postgresql_table(self, table: DatabaseTable) -> str:
        """Generate PostgreSQL CREATE TABLE statement."""
        columns = []

        for col in table.columns:
            col_def = self._generate_postgresql_column(col)
            columns.append(col_def)

        # Add foreign keys
        for fk in table.foreign_keys:
            fk_def = f"""CONSTRAINT fk_{table.name}_{fk.column}
    FOREIGN KEY ({fk.column}) REFERENCES {fk.referenced_table}({fk.referenced_column})
    ON DELETE {fk.on_delete} ON UPDATE {fk.on_update}"""
            columns.append(fk_def)

        columns_str = ",\n  ".join(columns)

        sql = f"""CREATE TABLE {table.name} (
  {columns_str}
);"""

        # Add indexes
        for idx in table.indexes:
            unique_str = "UNIQUE " if idx.is_unique else ""
            cols = ", ".join(idx.columns)
            sql += (
                f"\n\nCREATE {unique_str}INDEX idx_{table.name}_{idx.name} ON {table.name}({cols});"
            )

        return sql

    def _generate_postgresql_column(self, col: DatabaseColumn) -> str:
        """Generate PostgreSQL column definition."""
        col_type = col.column_type.value

        if col.length and col.column_type == ColumnType.VARCHAR:
            col_type = f"VARCHAR({col.length})"

        nullable = "" if col.is_nullable else " NOT NULL"
        unique = " UNIQUE" if col.is_unique else ""
        primary = " PRIMARY KEY" if col.is_primary_key else ""
        default = f" DEFAULT {col.default_value}" if col.default_value else ""

        return f"{col.name} {col_type}{nullable}{unique}{primary}{default}"

    def _generate_mysql_schema(self) -> str:
        """Generate MySQL schema."""
        statements = []

        for table in self.tables.values():
            statements.append(self._generate_mysql_table(table))

        return "\n\n".join(statements)

    def _generate_mysql_table(self, table: DatabaseTable) -> str:
        """Generate MySQL CREATE TABLE statement."""
        columns = []

        for col in table.columns:
            col_def = self._generate_mysql_column(col)
            columns.append(col_def)

        # Add primary keys and foreign keys
        for fk in table.foreign_keys:
            fk_def = f"""CONSTRAINT fk_{table.name}_{fk.column}
    FOREIGN KEY ({fk.column}) REFERENCES {fk.referenced_table}({fk.referenced_column})
    ON DELETE {fk.on_delete} ON UPDATE {fk.on_update}"""
            columns.append(fk_def)

        columns_str = ",\n  ".join(columns)

        sql = f"""CREATE TABLE {table.name} (
  {columns_str}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""

        return sql

    def _generate_mysql_column(self, col: DatabaseColumn) -> str:
        """Generate MySQL column definition."""
        col_type = col.column_type.value

        if col.length and col.column_type == ColumnType.VARCHAR:
            col_type = f"VARCHAR({col.length})"

        nullable = "" if col.is_nullable else " NOT NULL"
        unique = " UNIQUE" if col.is_unique else ""
        primary = " PRIMARY KEY AUTO_INCREMENT" if col.is_primary_key else ""
        default = f" DEFAULT {col.default_value}" if col.default_value else ""

        return f"{col.name} {col_type}{nullable}{unique}{primary}{default}"

    def _generate_sqlite_schema(self) -> str:
        """Generate SQLite schema."""
        statements = []

        for table in self.tables.values():
            statements.append(self._generate_sqlite_table(table))

        return "\n\n".join(statements)

    def _generate_sqlite_table(self, table: DatabaseTable) -> str:
        """Generate SQLite CREATE TABLE statement."""
        columns = []

        for col in table.columns:
            col_def = self._generate_sqlite_column(col)
            columns.append(col_def)

        columns_str = ",\n  ".join(columns)

        return f"""CREATE TABLE {table.name} (
  {columns_str}
);"""

    def _generate_sqlite_column(self, col: DatabaseColumn) -> str:
        """Generate SQLite column definition."""
        col_type = col.column_type.value

        if col.length and col.column_type == ColumnType.VARCHAR:
            col_type = f"VARCHAR({col.length})"

        nullable = "" if col.is_nullable else " NOT NULL"
        unique = " UNIQUE" if col.is_unique else ""
        primary = " PRIMARY KEY" if col.is_primary_key else ""
        default = f" DEFAULT {col.default_value}" if col.default_value else ""

        return f"{col.name} {col_type}{nullable}{unique}{primary}{default}"


class PrismaSchemaGenerator:
    """Generate Prisma schema (schema.prisma)."""

    def __init__(self, db_type: DatabaseType = DatabaseType.POSTGRESQL):
        """Initialize Prisma schema generator."""
        self.db_type = db_type
        self.models: dict[str, PrismaModel] = {}

    def add_model(self, model: "PrismaModel") -> None:
        """Add a Prisma model."""
        self.models[model.name] = model

    def generate_schema(self) -> str:
        """Generate complete Prisma schema."""
        parts = []

        # Datasource
        parts.append(self._generate_datasource())

        # Generator
        parts.append(self._generate_generator())

        # Models
        for model in self.models.values():
            parts.append(self._generate_model(model))

        return "\n\n".join(parts)

    def _generate_datasource(self) -> str:
        """Generate datasource block."""
        db_url_var = {
            DatabaseType.POSTGRESQL: "DATABASE_URL",
            DatabaseType.MYSQL: "DATABASE_URL",
            DatabaseType.SQLITE: "DATABASE_URL",
        }.get(self.db_type, "DATABASE_URL")

        db_provider = {
            DatabaseType.POSTGRESQL: "postgresql",
            DatabaseType.MYSQL: "mysql",
            DatabaseType.SQLITE: "sqlite",
        }.get(self.db_type, "postgresql")

        return f"""datasource db {{
  provider = "{db_provider}"
  url      = env("{db_url_var}")
}}"""

    def _generate_generator(self) -> str:
        """Generate generator block."""
        return """generator client {
  provider = "prisma-client-js"
}"""

    def _generate_model(self, model: "PrismaModel") -> str:
        """Generate a single Prisma model."""
        fields = []

        for field in model.fields:
            field_str = self._generate_field(field)
            fields.append(field_str)

        fields_str = "\n  ".join(fields)

        return f"""model {model.name} {{
  {fields_str}
}}"""

    def _generate_field(self, field: "PrismaField") -> str:
        """Generate a single field definition."""
        field_type = field.field_type
        modifiers = []

        if field.is_id:
            modifiers.append("@id")

        if field.is_unique:
            modifiers.append("@unique")

        if field.default_value:
            modifiers.append(f"@default({field.default_value})")

        if field.relation_name:
            modifiers.append(f'@relation("{field.relation_name}")')

        modifiers_str = " ".join(modifiers)
        if modifiers_str:
            modifiers_str = f" {modifiers_str}"

        optional_suffix = "?" if field.is_optional else ""

        return f"{field.name} {field_type}{optional_suffix}{modifiers_str}"


@dataclass
class PrismaField:
    """Represents a Prisma model field."""

    name: str
    field_type: str  # String, Int, Boolean, DateTime, etc.
    is_id: bool = False
    is_unique: bool = False
    is_optional: bool = False
    default_value: str | None = None
    relation_name: str | None = None


@dataclass
class PrismaModel:
    """Represents a Prisma model."""

    name: str
    fields: list[PrismaField]


class MigrationGenerator:
    """Generate database migration files."""

    @staticmethod
    def generate_migration(
        migration_name: str,
        up_sql: str,
        down_sql: str,
        timestamp: str | None = None,
    ) -> tuple[str, str]:
        """Generate migration files.

        Returns: (filename, content)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        filename = f"{timestamp}_{migration_name}.sql"

        content = f"""-- Migration: {migration_name}
-- Created: {datetime.now().isoformat()}

-- Up Migration
{up_sql}

-- Down Migration (Rollback)
{down_sql}
"""

        return filename, content

    @staticmethod
    def generate_prisma_migration(
        migration_name: str,
        sql: str,
        timestamp: str | None = None,
    ) -> tuple[str, str]:
        """Generate Prisma migration files."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        filename = f"{timestamp}_{migration_name}.sql"

        return filename, sql
