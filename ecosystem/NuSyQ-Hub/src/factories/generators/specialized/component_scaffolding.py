"""Component Scaffolding - Generate React/Vue components with Storybook stories.

Supports:
- React functional components (TypeScript and JavaScript)
- Vue single-file components
- Component props/properties definition
- Storybook stories for components
- CSS modules and styled-components
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ComponentFramework(str, Enum):
    """Supported component frameworks."""

    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"


class StyleStrategy(str, Enum):
    """CSS/styling strategies."""

    CSS_MODULES = "css_modules"
    STYLED_COMPONENTS = "styled_components"
    TAILWIND = "tailwind"
    SCSS = "scss"
    VUE_SCOPED = "vue_scoped"


@dataclass
class ComponentProp:
    """Represents a component prop/property."""

    name: str
    prop_type: str  # string, number, boolean, ReactNode, etc.
    is_required: bool = False
    default_value: Any | None = None
    description: str | None = None


@dataclass
class ComponentDefinition:
    """Represents a component definition."""

    name: str
    description: str | None = None
    props: list[ComponentProp] = field(default_factory=list)
    is_form_component: bool = False  # Has form handling
    is_layout_component: bool = False  # Layout wrapper
    has_children: bool = False  # Accepts children
    style_strategy: StyleStrategy = StyleStrategy.CSS_MODULES


class ReactComponentGenerator:
    """Generate React components."""

    @staticmethod
    def generate_component(
        component_def: ComponentDefinition,
        use_typescript: bool = True,
        style_strategy: StyleStrategy = StyleStrategy.CSS_MODULES,
    ) -> str:
        """Generate React functional component."""
        if use_typescript:
            return ReactComponentGenerator._generate_typescript_component(
                component_def,
                style_strategy,
            )
        else:
            return ReactComponentGenerator._generate_javascript_component(
                component_def,
                style_strategy,
            )

    @staticmethod
    def _generate_typescript_component(
        component_def: ComponentDefinition,
        style_strategy: StyleStrategy,
    ) -> str:
        """Generate TypeScript React component."""
        # Props interface
        props_lines = []
        for prop in component_def.props:
            required = "" if prop.is_required else "?"
            props_lines.append(f"  {prop.name}{required}: {prop.prop_type};")

        if component_def.has_children:
            props_lines.append("  children?: React.ReactNode;")

        props_interface = "\n".join(props_lines) if props_lines else "  // No props"

        # Imports
        imports = ["import React from 'react';"]

        if style_strategy == StyleStrategy.CSS_MODULES:
            imports.append(f"import styles from './{component_def.name}.module.css';")
        elif style_strategy == StyleStrategy.STYLED_COMPONENTS:
            imports.append("import styled from 'styled-components';")
        elif style_strategy == StyleStrategy.TAILWIND:
            pass  # No style import needed
        elif style_strategy == StyleStrategy.SCSS:
            imports.append(f"import './{component_def.name}.scss';")

        imports_str = "\n".join(imports)

        # Component code
        code = f"""{imports_str}

interface {component_def.name}Props {{
{props_interface}
}}

/**
 * {component_def.description or component_def.name}
 */
export const {component_def.name}: React.FC<{component_def.name}Props> = ({{
  {", ".join(prop.name for prop in component_def.props)}{", children" if component_def.has_children else ""}
}}) => {{
  return (
    <div className={{styles.container}}>
      <h2>{component_def.name}</h2>
      {{/* Component implementation belongs in the application layer. */}}
      {{children}}
    </div>
  );
}};

export default {component_def.name};
"""

        return code

    @staticmethod
    def _generate_javascript_component(
        component_def: ComponentDefinition,
        style_strategy: StyleStrategy,
    ) -> str:
        """Generate JavaScript React component."""
        # Imports
        imports = ["import React from 'react';"]

        if style_strategy == StyleStrategy.CSS_MODULES:
            imports.append(f"import styles from './{component_def.name}.module.css';")

        imports_str = "\n".join(imports)

        # Props destructuring
        props_destructure = ", ".join(prop.name for prop in component_def.props)
        if component_def.has_children:
            props_destructure += ", children" if props_destructure else "children"

        code = f"""{imports_str}

/**
 * {component_def.description or component_def.name}
 */
const {component_def.name} = ({{{props_destructure}}}) => {{
  return (
    <div className="container">
      <h2>{component_def.name}</h2>
      {{/* Component implementation belongs in the application layer. */}}
      {{children}}
    </div>
  );
}};

{component_def.name}.propTypes = {{
  {", ".join(f"{prop.name}: PropTypes.{props_proptype(prop.prop_type)}{'isRequired' if prop.is_required else ''}" for prop in component_def.props)},
}};

export default {component_def.name};
"""

        return code

    @staticmethod
    def generate_story(component_def: ComponentDefinition) -> str:
        """Generate Storybook story for component."""
        # Build story export
        stories = []

        # Default story
        default_props = {}
        for prop in component_def.props:
            if prop.default_value:
                default_props[prop.name] = prop.default_value
            else:
                # Use type-appropriate default
                if prop.prop_type == "string":
                    default_props[prop.name] = "Sample text"
                elif prop.prop_type == "number":
                    default_props[prop.name] = 0
                elif prop.prop_type == "boolean":
                    default_props[prop.name] = False

        default_story = f"""
export const Default: Story<{component_def.name}Props> = (args) => <{component_def.name} {{...args}} />;
Default.args = {json.dumps(default_props, indent=2)};
"""

        stories.append(default_story)

        # Variant stories (for key props)
        for prop in component_def.props[:2]:  # First 2 props
            if prop.prop_type == "boolean":
                stories.append(
                    f"""
export const {prop.name.capitalize()}True: Story<{component_def.name}Props> = (args) => (
  <{component_def.name} {{...args}} {prop.name}={{true}} />
);

export const {prop.name.capitalize()}False: Story<{component_def.name}Props> = (args) => (
  <{component_def.name} {{...args}} {prop.name}={{false}} />
);
"""
                )

        code = f"""import type {{ Meta, StoryObj }} from '@storybook/react';
import {component_def.name} from './{component_def.name}';
import type {{ {component_def.name}Props }} from './{component_def.name}';

const meta = {{
  title: 'Components/{component_def.name}',
  component: {component_def.name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
}} satisfies Meta<typeof {component_def.name}>;

export default meta;
type Story = StoryObj<typeof meta>;

{"".join(stories)}
"""

        return code


class VueComponentGenerator:
    """Generate Vue components."""

    @staticmethod
    def generate_component(
        component_def: ComponentDefinition,
        _style_strategy: StyleStrategy = StyleStrategy.VUE_SCOPED,
    ) -> str:
        """Generate Vue single-file component."""
        # Props definition
        props_code = []
        for prop in component_def.props:
            required = ", required: true" if prop.is_required else ""
            default = f", default: {json.dumps(prop.default_value)}" if prop.default_value else ""
            props_code.append(
                f"""    {prop.name}: {{
      type: {vue_prop_type(prop.prop_type)}{required}{default}
    }}"""
            )

        props_str = ",\n".join(props_code) if props_code else "    // No props"

        # Template
        template = f"""<template>
  <div class="container">
    <h2>{{{{ {component_def.name} }}}}</h2>
    {{<!-- Component implementation belongs in the application layer. -->}}
    <slot></slot>
  </div>
</template>

<script lang="ts">
import {{ defineComponent, PropType }} from 'vue';

export default defineComponent({{
  name: '{component_def.name}',
  props: {{
{props_str}
  }},
  setup(props, {{ slots }}) {{
    // Component logic belongs in the application layer.
    return {{
      {", ".join(prop.name for prop in component_def.props)},
    }};
  }},
}});
</script>

<style scoped>
.container {{
  padding: 1rem;
}}
</style>
"""

        return template

    @staticmethod
    def generate_story(component_def: ComponentDefinition) -> str:
        """Generate Storybook story for Vue component."""
        # Default args
        args = {}
        for prop in component_def.props:
            if prop.default_value:
                args[prop.name] = prop.default_value
            else:
                if prop.prop_type == "String":
                    args[prop.name] = "Sample text"
                elif prop.prop_type == "Number":
                    args[prop.name] = 0
                elif prop.prop_type == "Boolean":
                    args[prop.name] = False

        story = f"""import type {{ Meta, StoryObj }} from '@storybook/vue3';
import {component_def.name} from './{component_def.name}.vue';
import type {{ {component_def.name}Props }} from './{component_def.name}.vue';

const meta = {{
  title: 'Components/{component_def.name}',
  component: {component_def.name},
  args: {json.dumps(args, indent=2)},
}} satisfies Meta<typeof {component_def.name}>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {{}};

export const WithSlot: Story = {{
  render: (args) => ({{
    components: {{ {component_def.name} }},
    setup() {{
      return {{ args }};
    }},
    template: `<{component_def.name} v-bind="args">Slot content</{component_def.name}>`,
  }}),
}};
"""

        return story


class ComponentStylesGenerator:
    """Generate component styles."""

    @staticmethod
    def generate_css_modules(_component_name: str) -> str:
        """Generate CSS Modules stylesheet."""
        css = """.container {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}
"""

        return css

    @staticmethod
    def generate_styled_components(_component_name: str) -> str:
        """Generate styled-components definitions."""
        code = """import styled from 'styled-components';

export const StyledContainer = styled.div`
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
`;

export const StyledTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
`;
"""

        return code

    @staticmethod
    def generate_tailwind_component(
        _component_def: ComponentDefinition,
    ) -> str:
        """Generate Tailwind CSS classes."""
        classes = {
            "container": "p-4 border border-gray-300 rounded",
            "title": "text-xl font-semibold",
            "button": "px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600",
        }

        return json.dumps(classes, indent=2)


def props_proptype(prop_type: str) -> str:
    """Convert property type to PropTypes validator."""
    type_map = {
        "string": "string",
        "number": "number",
        "boolean": "bool",
        "ReactNode": "node",
        "function": "func",
        "object": "object",
        "array": "array",
    }
    return type_map.get(prop_type.lower(), "any")


def vue_prop_type(prop_type: str) -> str:
    """Convert property type to Vue prop type."""
    type_map = {
        "string": "String",
        "number": "Number",
        "boolean": "Boolean",
        "object": "Object",
        "array": "Array",
    }
    return type_map.get(prop_type.lower(), "String")
