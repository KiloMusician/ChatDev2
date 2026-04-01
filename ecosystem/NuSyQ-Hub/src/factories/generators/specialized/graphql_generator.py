"""GraphQL Generator - Generate GraphQL schemas and resolvers from project models.

Supports:
- Schema generation from Python/TypeScript types
- Resolver scaffolding
- Query/Mutation/Subscription templates
- Relationship mapping
- Input type generation
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """GraphQL field types."""

    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    ID = "ID"
    DATETIME = "DateTime"
    JSON = "JSON"
    ENUM = "Enum"
    OBJECT = "Object"


@dataclass
class GraphQLField:
    """Represents a GraphQL field in a type."""

    name: str
    field_type: FieldType
    is_list: bool = False
    is_required: bool = False
    description: str | None = None
    enum_values: list[str] | None = None  # For ENUM types
    default_value: Any | None = None


@dataclass
class GraphQLType:
    """Represents a GraphQL object type."""

    name: str
    fields: list[GraphQLField]
    description: str | None = None
    directives: list[str] | None = None


@dataclass
class GraphQLInputType:
    """Represents a GraphQL input type (for mutations)."""

    name: str
    fields: list[GraphQLField]
    description: str | None = None


@dataclass
class GraphQLQuery:
    """Represents a GraphQL query operation."""

    name: str
    return_type: str
    parameters: list[GraphQLField]
    description: str | None = None


@dataclass
class GraphQLMutation:
    """Represents a GraphQL mutation operation."""

    name: str
    input_type: str
    return_type: str
    description: str | None = None


class GraphQLSchemaGenerator:
    """Generate GraphQL schemas from model definitions."""

    def __init__(self):
        """Initialize schema generator."""
        self.types: dict[str, GraphQLType] = {}
        self.input_types: dict[str, GraphQLInputType] = {}
        self.queries: list[GraphQLQuery] = []
        self.mutations: list[GraphQLMutation] = []
        self.enums: dict[str, list[str]] = {}

    def add_type(self, type_def: GraphQLType) -> None:
        """Add a type definition."""
        self.types[type_def.name] = type_def
        logger.info(f"Added type: {type_def.name}")

    def add_input_type(self, input_type: GraphQLInputType) -> None:
        """Add an input type definition."""
        self.input_types[input_type.name] = input_type
        logger.info(f"Added input type: {input_type.name}")

    def add_query(self, query: GraphQLQuery) -> None:
        """Add a query operation."""
        self.queries.append(query)
        logger.info(f"Added query: {query.name}")

    def add_mutation(self, mutation: GraphQLMutation) -> None:
        """Add a mutation operation."""
        self.mutations.append(mutation)
        logger.info(f"Added mutation: {mutation.name}")

    def add_enum(self, enum_name: str, values: list[str]) -> None:
        """Add an enum type."""
        self.enums[enum_name] = values
        logger.info(f"Added enum: {enum_name}")

    def generate_schema(self) -> str:
        """Generate complete GraphQL schema (SDL)."""
        schema_parts = []

        # Add enums
        for enum_name, values in self.enums.items():
            schema_parts.append(self._generate_enum(enum_name, values))

        # Add input types
        for _input_name, input_type in self.input_types.items():
            schema_parts.append(self._generate_input_type(input_type))

        # Add object types
        for _type_name, type_def in self.types.items():
            schema_parts.append(self._generate_type(type_def))

        # Add root Query type
        if self.queries:
            schema_parts.append(self._generate_query_type())

        # Add root Mutation type
        if self.mutations:
            schema_parts.append(self._generate_mutation_type())

        return "\n\n".join(schema_parts)

    def _generate_enum(self, name: str, values: list[str]) -> str:
        """Generate GraphQL enum definition."""
        values_str = "\n  ".join(values)
        return f"""enum {name} {{
  {values_str}
}}"""

    def _generate_input_type(self, input_type: GraphQLInputType) -> str:
        """Generate GraphQL input type definition."""
        description = f'"""\\n{input_type.description}\\n"""\\n' if input_type.description else ""

        fields = []
        for field in input_type.fields:
            field_str = self._field_to_string(field)
            fields.append(f"  {field_str}")

        fields_str = "\n".join(fields)

        return f"""{description}input {input_type.name} {{
{fields_str}
}}"""

    def _generate_type(self, type_def: GraphQLType) -> str:
        """Generate GraphQL object type definition."""
        description = f'"""\\n{type_def.description}\\n"""\\n' if type_def.description else ""

        fields = []
        for field in type_def.fields:
            field_str = self._field_to_string(field)
            fields.append(f"  {field_str}")

        fields_str = "\n".join(fields)

        return f"""{description}type {type_def.name} {{
{fields_str}
}}"""

    def _field_to_string(self, field: GraphQLField) -> str:
        """Convert field to GraphQL string representation."""
        # Handle both FieldType enum and string types
        field_type = (
            field.field_type.value if hasattr(field.field_type, "value") else str(field.field_type)
        )

        if field.is_list:
            field_type = f"[{field_type}]"

        if field.is_required:
            field_type = f"{field_type}!"

        description = f' """{field.description}"""' if field.description else ""

        return f"{field.name}: {field_type}{description}"

    def _generate_query_type(self) -> str:
        """Generate GraphQL Query root type."""
        queries = []
        for query in self.queries:
            params = []
            for param in query.parameters:
                params.append(self._field_to_string(param))

            params_str = ", ".join(params) if params else ""
            query_str = f"  {query.name}({params_str}): {query.return_type}"

            if query.description:
                query_str = f'"""{query.description}"""\n  {query_str}'

            queries.append(query_str)

        queries_str = "\n".join(queries)

        return f"""type Query {{
{queries_str}
}}"""

    def _generate_mutation_type(self) -> str:
        """Generate GraphQL Mutation root type."""
        mutations = []
        for mutation in self.mutations:
            mutation_str = (
                f"  {mutation.name}(input: {mutation.input_type}!): {mutation.return_type}"
            )

            if mutation.description:
                mutation_str = f'"""{mutation.description}"""\n  {mutation_str}'

            mutations.append(mutation_str)

        mutations_str = "\n".join(mutations)

        return f"""type Mutation {{
{mutations_str}
}}"""


class GraphQLResolverGenerator:
    """Generate GraphQL resolver scaffolding."""

    @staticmethod
    def generate_resolver_skeleton(schema: GraphQLSchemaGenerator, language: str = "python") -> str:
        """Generate resolver skeleton in target language.

        Args:
            schema: GraphQLSchemaGenerator instance
            language: Target language (python, javascript, typescript)

        Returns:
            Resolver code as string
        """
        if language.lower() in ["python", "py"]:
            return GraphQLResolverGenerator._generate_python_resolvers(schema)
        elif language.lower() in ["javascript", "js"]:
            return GraphQLResolverGenerator._generate_javascript_resolvers(schema)
        elif language.lower() in ["typescript", "ts"]:
            return GraphQLResolverGenerator._generate_typescript_resolvers(schema)
        else:
            raise ValueError(f"Unsupported language: {language}")

    @staticmethod
    def _generate_python_resolvers(schema: GraphQLSchemaGenerator) -> str:
        """Generate Python resolver skeleton (with Strawberry/Ariadne)."""
        code = '''"""GraphQL Resolvers - Generated Scaffold"""

import logging
from typing import Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryResolver:
    """Root Query resolvers."""

'''

        for query in schema.queries:
            code += f"""    @staticmethod
    async def {query.name}(self"""

            for param in query.parameters:
                # Handle both FieldType enum and string types
                param_type = (
                    param.field_type.value
                    if hasattr(param.field_type, "value")
                    else str(param.field_type)
                )
                code += f", {param.name}: {param_type} = None"

            code += f""") ->"{query.return_type}":
        \"\"\"
        {query.description or query.name}
        \"\"\"
        # Resolver implementation belongs in the application layer.
        logger.info(f\"Resolving {{query.name}}\")
        return None

"""

        if schema.mutations:
            code += '''

class MutationResolver:
    """Root Mutation resolvers."""

'''

            for mutation in schema.mutations:
                code += f'''    @staticmethod
    async def {mutation.name}(self, input: "{mutation.input_type}") -> "{mutation.return_type}":
        """
        {mutation.description or mutation.name}
        """
        # Resolver implementation belongs in the application layer.
        logger.info(f"Executing {mutation.name}")
        return None

'''

        return code

    @staticmethod
    def _generate_javascript_resolvers(schema: GraphQLSchemaGenerator) -> str:
        """Generate JavaScript resolver skeleton (with Apollo/Graphql-js)."""
        code = """// GraphQL Resolvers - Generated Scaffold

const resolvers = {
  Query: {
"""

        for query in schema.queries:
            params = ", ".join([f"{p.name}" for p in query.parameters])
            params = f"(_, {{ {params} }}, context)" if params else "(_, _, context)"

            code += f"""    {query.name}: {params} => {{
      // Resolver implementation belongs in the application layer.
      console.log("Resolving {query.name}");
      return null;
    }},
"""

        code += "  },"

        if schema.mutations:
            code += """
  Mutation: {
"""

            for mutation in schema.mutations:
                code += f"""    {mutation.name}: (_, {{ input }}, context) => {{
      // Resolver implementation belongs in the application layer.
      console.log("Executing {mutation.name}");
      return null;
    }},
"""

            code += "  },"

        code += "\n};\n\nmodule.exports = resolvers;"

        return code

    @staticmethod
    def _generate_typescript_resolvers(schema: GraphQLSchemaGenerator) -> str:
        """Generate TypeScript resolver skeleton."""
        code = """// GraphQL Resolvers - Generated Scaffold
import { GraphQLResolveInfo } from "graphql";

interface Context {
  // Define the application-specific context interface before production use.
}

export const resolvers = {
  Query: {
"""

        for query in schema.queries:
            params = ", ".join([f"{p.name}: string" for p in query.parameters])
            params = f"{{ {params} }}, _context: Context" if params else "{}, _context: Context"

            code += f"""    {query.name}: async ({params}): Promise<{query.return_type} | null> => {{
      // Resolver implementation belongs in the application layer.
      console.log("Resolving {query.name}");
      return null;
    }},
"""

        code += "  },"

        if schema.mutations:
            code += """
  Mutation: {
"""

            for mutation in schema.mutations:
                code += f"""    {mutation.name}: async (
      _,
      {{ input }}: {{ input: {mutation.input_type} }},
      _context: Context
    ): Promise<{mutation.return_type} | null> => {{
      // Resolver implementation belongs in the application layer.
      console.log("Executing {mutation.name}");
      return null;
    }},
"""

            code += "  },"

        code += "\n};"

        return code


class GraphQLTypeMapper:
    """Map Python/TypeScript types to GraphQL types."""

    PYTHON_TO_GRAPHQL: ClassVar[dict] = {
        "str": FieldType.STRING,
        "int": FieldType.INT,
        "float": FieldType.FLOAT,
        "bool": FieldType.BOOLEAN,
        "datetime": FieldType.DATETIME,
        "dict": FieldType.JSON,
    }

    TYPESCRIPT_TO_GRAPHQL: ClassVar[dict] = {
        "string": FieldType.STRING,
        "number": FieldType.INT,
        "float": FieldType.FLOAT,
        "boolean": FieldType.BOOLEAN,
        "Date": FieldType.DATETIME,
        "any": FieldType.JSON,
    }

    @staticmethod
    def map_python_type(python_type: str) -> FieldType:
        """Map Python type to GraphQL type."""
        return GraphQLTypeMapper.PYTHON_TO_GRAPHQL.get(python_type.lower(), FieldType.OBJECT)

    @staticmethod
    def map_typescript_type(ts_type: str) -> FieldType:
        """Map TypeScript type to GraphQL type."""
        return GraphQLTypeMapper.TYPESCRIPT_TO_GRAPHQL.get(ts_type, FieldType.OBJECT)
