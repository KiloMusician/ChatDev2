"""
Tests for Database Helpers - Phase 3.2

Tests:
- SQL schema generation (PostgreSQL, MySQL, SQLite)
- Prisma schema generation
- Migration file creation
- Table and column definitions
"""

import pytest
from src.generators.database_helpers import (
    ColumnType,
    DatabaseColumn,
    DatabaseIndex,
    DatabaseTable,
    DatabaseType,
    ForeignKey,
    MigrationGenerator,
    PrismaField,
    PrismaModel,
    PrismaSchemaGenerator,
    SQLSchemaGenerator,
)


class TestDatabaseColumn:
    """Test database column definitions."""

    def test_simple_column_creation(self):
        """Test creating a simple column."""
        col = DatabaseColumn(
            name="id",
            column_type=ColumnType.INT,
            is_primary_key=True,
        )

        assert col.name == "id"
        assert col.column_type == ColumnType.INT
        assert col.is_primary_key

    def test_column_with_varchar(self):
        """Test column with VARCHAR type."""
        col = DatabaseColumn(
            name="email",
            column_type=ColumnType.VARCHAR,
            length=255,
            is_unique=True,
            is_nullable=False,
        )

        assert col.length == 255
        assert col.is_unique
        assert not col.is_nullable


class TestDatabaseTable:
    """Test database table definitions."""

    def test_simple_table_creation(self):
        """Test creating a simple table."""
        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("name", ColumnType.VARCHAR, length=255),
            DatabaseColumn("created_at", ColumnType.TIMESTAMP),
        ]

        table = DatabaseTable(
            name="users",
            columns=columns,
        )

        assert table.name == "users"
        assert len(table.columns) == 3

    def test_table_with_foreign_key(self):
        """Test table with foreign key relationship."""
        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("user_id", ColumnType.INT),
        ]

        fk = ForeignKey(
            column="user_id",
            referenced_table="users",
            referenced_column="id",
        )

        table = DatabaseTable(
            name="posts",
            columns=columns,
            foreign_keys=[fk],
        )

        assert len(table.foreign_keys) == 1
        assert table.foreign_keys[0].column == "user_id"

    def test_table_with_index(self):
        """Test table with indexes."""
        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("email", ColumnType.VARCHAR, length=255),
        ]

        idx = DatabaseIndex(
            name="email_idx",
            columns=["email"],
            is_unique=True,
        )

        table = DatabaseTable(
            name="users",
            columns=columns,
            indexes=[idx],
        )

        assert len(table.indexes) == 1


class TestSQLSchemaGenerator:
    """Test SQL schema generation."""

    def test_postgresql_schema_generation(self):
        """Test PostgreSQL schema generation."""
        generator = SQLSchemaGenerator(DatabaseType.POSTGRESQL)

        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("name", ColumnType.VARCHAR, length=255, is_nullable=False),
            DatabaseColumn("email", ColumnType.VARCHAR, length=255, is_unique=True),
        ]

        table = DatabaseTable(name="users", columns=columns)
        generator.add_table(table)

        schema = generator.generate_schema()

        assert "CREATE TABLE users" in schema
        assert "id INT PRIMARY KEY" in schema
        assert "name VARCHAR(255) NOT NULL" in schema
        assert "email VARCHAR(255) UNIQUE" in schema

    def test_mysql_schema_generation(self):
        """Test MySQL schema generation."""
        generator = SQLSchemaGenerator(DatabaseType.MYSQL)

        columns = [
            DatabaseColumn("id", ColumnType.SERIAL, is_primary_key=True),
            DatabaseColumn("title", ColumnType.TEXT, is_nullable=False),
        ]

        table = DatabaseTable(name="posts", columns=columns)
        generator.add_table(table)

        schema = generator.generate_schema()

        assert "CREATE TABLE posts" in schema
        assert "ENGINE=InnoDB" in schema
        assert "utf8mb4" in schema.lower()

    def test_sqlite_schema_generation(self):
        """Test SQLite schema generation."""
        generator = SQLSchemaGenerator(DatabaseType.SQLITE)

        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("data", ColumnType.JSON),
        ]

        table = DatabaseTable(name="items", columns=columns)
        generator.add_table(table)

        schema = generator.generate_schema()

        assert "CREATE TABLE items" in schema

    def test_schema_with_foreign_keys(self):
        """Test schema generation with foreign keys."""
        generator = SQLSchemaGenerator(DatabaseType.POSTGRESQL)

        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("user_id", ColumnType.INT),
        ]

        fk = ForeignKey(
            column="user_id",
            referenced_table="users",
            referenced_column="id",
            on_delete="CASCADE",
        )

        table = DatabaseTable(
            name="posts",
            columns=columns,
            foreign_keys=[fk],
        )

        generator.add_table(table)
        schema = generator.generate_schema()

        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in schema
        assert "CASCADE" in schema

    def test_schema_with_indexes(self):
        """Test schema generation with indexes."""
        generator = SQLSchemaGenerator(DatabaseType.POSTGRESQL)

        columns = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("email", ColumnType.VARCHAR, length=255),
        ]

        idx = DatabaseIndex(
            name="email_idx",
            columns=["email"],
            is_unique=True,
        )

        table = DatabaseTable(
            name="users",
            columns=columns,
            indexes=[idx],
        )

        generator.add_table(table)
        schema = generator.generate_schema()

        assert "CREATE UNIQUE INDEX" in schema
        assert "email_idx" in schema


class TestPrismaSchemaGenerator:
    """Test Prisma schema generation."""

    def test_prisma_model_creation(self):
        """Test creating a Prisma model."""
        fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("email", "String", is_unique=True),
            PrismaField("name", "String"),
        ]

        model = PrismaModel(
            name="User",
            fields=fields,
        )

        assert model.name == "User"
        assert len(model.fields) == 3

    def test_prisma_schema_generation(self):
        """Test Prisma schema generation."""
        generator = PrismaSchemaGenerator(DatabaseType.POSTGRESQL)

        fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("email", "String", is_unique=True),
            PrismaField("createdAt", "DateTime", default_value="now()"),
        ]

        model = PrismaModel(name="User", fields=fields)
        generator.add_model(model)

        schema = generator.generate_schema()

        assert "datasource db" in schema
        assert 'provider = "postgresql"' in schema
        assert "model User" in schema
        assert "id Int @id" in schema
        assert "email String @unique" in schema
        assert "@default(now())" in schema

    def test_prisma_with_relations(self):
        """Test Prisma schema with relationships."""
        generator = PrismaSchemaGenerator(DatabaseType.MYSQL)

        user_fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("name", "String"),
        ]

        post_fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("title", "String"),
            PrismaField("userId", "Int"),
            PrismaField("user", "User", relation_name="posts"),
        ]

        generator.add_model(PrismaModel("User", user_fields))
        generator.add_model(PrismaModel("Post", post_fields))

        schema = generator.generate_schema()

        assert "model User" in schema
        assert "model Post" in schema
        assert '@relation("posts")' in schema


class TestMigrationGenerator:
    """Test migration file generation."""

    def test_migration_generation(self):
        """Test generating a migration file."""
        up_sql = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255));"
        down_sql = "DROP TABLE users;"

        filename, content = MigrationGenerator.generate_migration(
            migration_name="create_users_table",
            up_sql=up_sql,
            down_sql=down_sql,
            timestamp="20240101120000",
        )

        assert "20240101120000" in filename
        assert "create_users_table" in filename
        assert "CREATE TABLE users" in content
        assert "DROP TABLE users" in content

    def test_prisma_migration_generation(self):
        """Test Prisma migration generation."""
        sql = """-- CreateTable
CREATE TABLE "User" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    PRIMARY KEY ("id")
);"""

        filename, content = MigrationGenerator.generate_prisma_migration(
            migration_name="create_user_model",
            sql=sql,
            timestamp="20240101120000",
        )

        assert "20240101120000" in filename
        assert "CREATE TABLE" in content
        assert "User" in content


class TestDatabaseIntegration:
    """Integration tests for database schema generation."""

    def test_complete_blog_schema_sql(self):
        """Test creating a complete blog database schema."""
        generator = SQLSchemaGenerator(DatabaseType.POSTGRESQL)

        # Users table
        user_cols = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("email", ColumnType.VARCHAR, length=255, is_unique=True),
            DatabaseColumn("name", ColumnType.VARCHAR, length=255),
            DatabaseColumn("created_at", ColumnType.TIMESTAMP),
        ]
        generator.add_table(DatabaseTable("users", user_cols))

        # Posts table
        post_cols = [
            DatabaseColumn("id", ColumnType.INT, is_primary_key=True),
            DatabaseColumn("user_id", ColumnType.INT),
            DatabaseColumn("title", ColumnType.VARCHAR, length=255),
            DatabaseColumn("content", ColumnType.TEXT),
            DatabaseColumn("created_at", ColumnType.TIMESTAMP),
        ]
        post_fk = ForeignKey("user_id", "users", "id")
        generator.add_table(DatabaseTable("posts", post_cols, foreign_keys=[post_fk]))

        schema = generator.generate_schema()

        assert "CREATE TABLE users" in schema
        assert "CREATE TABLE posts" in schema
        assert "FOREIGN KEY" in schema

    def test_complete_blog_schema_prisma(self):
        """Test creating a blog schema with Prisma."""
        generator = PrismaSchemaGenerator(DatabaseType.POSTGRESQL)

        user_fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("email", "String", is_unique=True),
            PrismaField("name", "String"),
            PrismaField("createdAt", "DateTime", default_value="now()"),
        ]
        generator.add_model(PrismaModel("User", user_fields))

        post_fields = [
            PrismaField("id", "Int", is_id=True),
            PrismaField("title", "String"),
            PrismaField("content", "String"),
            PrismaField("userId", "Int"),
            PrismaField("createdAt", "DateTime", default_value="now()"),
        ]
        generator.add_model(PrismaModel("Post", post_fields))

        schema = generator.generate_schema()

        assert "model User" in schema
        assert "model Post" in schema
        assert "datasource db" in schema


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
