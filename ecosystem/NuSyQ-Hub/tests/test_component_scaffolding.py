"""
Tests for Component Scaffolding - Phase 3.3

Tests:
- React component generation (TypeScript, JavaScript)
- Vue component generation
- Storybook story generation
- Style generation (CSS Modules, styled-components, Tailwind)
"""

import pytest
from src.generators.component_scaffolding import (
    ComponentDefinition,
    ComponentProp,
    ComponentStylesGenerator,
    ReactComponentGenerator,
    StyleStrategy,
    VueComponentGenerator,
)


class TestComponentProp:
    """Test component property definitions."""

    def test_simple_prop_creation(self):
        """Test creating a simple prop."""
        prop = ComponentProp(
            name="label",
            prop_type="string",
            is_required=True,
            description="Button label text",
        )

        assert prop.name == "label"
        assert prop.prop_type == "string"
        assert prop.is_required

    def test_prop_with_default_value(self):
        """Test prop with default value."""
        prop = ComponentProp(
            name="disabled",
            prop_type="boolean",
            default_value=False,
        )

        assert prop.default_value is False
        assert not prop.is_required


class TestComponentDefinition:
    """Test component definitions."""

    def test_simple_component_creation(self):
        """Test creating a simple component definition."""
        component = ComponentDefinition(
            name="Button",
            description="Reusable button component",
            props=[
                ComponentProp("label", "string", is_required=True),
                ComponentProp("onClick", "function"),
            ],
        )

        assert component.name == "Button"
        assert len(component.props) == 2

    def test_component_with_children(self):
        """Test component that accepts children."""
        component = ComponentDefinition(
            name="Card",
            description="Card wrapper component",
            has_children=True,
        )

        assert component.has_children

    def test_layout_component(self):
        """Test layout component definition."""
        component = ComponentDefinition(
            name="Header",
            is_layout_component=True,
            has_children=True,
        )

        assert component.is_layout_component


class TestReactComponentGenerator:
    """Test React component generation."""

    def test_typescript_component_generation(self):
        """Test generating TypeScript React component."""
        component = ComponentDefinition(
            name="Button",
            props=[
                ComponentProp("label", "string", is_required=True),
                ComponentProp("disabled", "boolean", default_value=False),
            ],
        )

        code = ReactComponentGenerator.generate_component(
            component,
            use_typescript=True,
        )

        assert "interface ButtonProps" in code
        assert "label: string;" in code
        assert "disabled?: boolean;" in code
        assert "export const Button: React.FC<ButtonProps>" in code

    def test_javascript_component_generation(self):
        """Test generating JavaScript React component."""
        component = ComponentDefinition(
            name="Input",
            props=[
                ComponentProp("value", "string"),
                ComponentProp("onChange", "function"),
            ],
        )

        code = ReactComponentGenerator.generate_component(
            component,
            use_typescript=False,
        )

        assert "const Input =" in code
        assert "propTypes" in code

    def test_component_with_children(self):
        """Test component that accepts children."""
        component = ComponentDefinition(
            name="Container",
            has_children=True,
            props=[],
        )

        code = ReactComponentGenerator.generate_component(component)

        assert "children?: React.ReactNode;" in code
        assert "{children}" in code

    def test_storybook_story_generation(self):
        """Test Storybook story generation."""
        component = ComponentDefinition(
            name="Badge",
            props=[
                ComponentProp("label", "string", default_value="Badge"),
                ComponentProp("variant", "string", default_value="default"),
            ],
        )

        story = ReactComponentGenerator.generate_story(component)

        assert "export const Default: Story" in story
        assert "Badge" in story
        assert "@storybook/react" in story

    def test_css_modules_import(self):
        """Test CSS Modules import in component."""
        component = ComponentDefinition(
            name="Button",
            props=[],
            style_strategy=StyleStrategy.CSS_MODULES,
        )

        code = ReactComponentGenerator.generate_component(
            component,
            style_strategy=StyleStrategy.CSS_MODULES,
        )

        assert "import styles from './Button.module.css';" in code
        assert "className={styles.container}" in code

    def test_styled_components_support(self):
        """Test styled-components support."""
        component = ComponentDefinition(
            name="Card",
            props=[],
            style_strategy=StyleStrategy.STYLED_COMPONENTS,
        )

        code = ReactComponentGenerator.generate_component(
            component,
            style_strategy=StyleStrategy.STYLED_COMPONENTS,
        )

        assert "import styled from 'styled-components';" in code


class TestVueComponentGenerator:
    """Test Vue component generation."""

    def test_vue_component_generation(self):
        """Test generating Vue component."""
        component = ComponentDefinition(
            name="Alert",
            props=[
                ComponentProp("message", "string", is_required=True),
                ComponentProp("type", "string", default_value="info"),
            ],
        )

        code = VueComponentGenerator.generate_component(component)

        assert "<template>" in code
        assert '<script lang="ts">' in code
        assert "defineComponent" in code
        assert "message:" in code
        assert "type:" in code

    def test_vue_component_with_slots(self):
        """Test Vue component with slots."""
        component = ComponentDefinition(
            name="Modal",
            has_children=True,
        )

        code = VueComponentGenerator.generate_component(component)

        assert "<slot></slot>" in code

    def test_vue_storybook_story(self):
        """Test Vue Storybook story generation."""
        component = ComponentDefinition(
            name="Dropdown",
            props=[
                ComponentProp("options", "array"),
                ComponentProp("selected", "string"),
            ],
        )

        story = VueComponentGenerator.generate_story(component)

        assert "@storybook/vue3" in story
        assert "export const Default: Story" in story
        assert "WithSlot" in story


class TestComponentStylesGenerator:
    """Test style generation utilities."""

    def test_css_modules_generation(self):
        """Test CSS Modules stylesheet generation."""
        css = ComponentStylesGenerator.generate_css_modules("Button")

        assert ".container" in css
        assert ".title" in css
        assert "padding" in css
        assert "border-radius" in css

    def test_styled_components_generation(self):
        """Test styled-components definition generation."""
        code = ComponentStylesGenerator.generate_styled_components("Card")

        assert "StyledContainer" in code
        assert "styled.div" in code
        assert "padding: 1rem" in code

    def test_tailwind_generation(self):
        """Test Tailwind CSS classes generation."""
        component = ComponentDefinition(name="Button")

        tailwind = ComponentStylesGenerator.generate_tailwind_component(component)

        assert "container" in tailwind
        assert "p-4" in tailwind
        assert "border" in tailwind


class TestComponentIntegration:
    """Integration tests for component generation."""

    def test_full_button_component_react(self):
        """Test generating a complete Button component in React."""
        button = ComponentDefinition(
            name="Button",
            description="Reusable button component",
            props=[
                ComponentProp("label", "string", is_required=True),
                ComponentProp("variant", "string", default_value="primary"),
                ComponentProp("disabled", "boolean", default_value=False),
                ComponentProp("onClick", "function"),
            ],
        )

        # Generate component
        component_code = ReactComponentGenerator.generate_component(button)
        assert "interface ButtonProps" in component_code
        assert "export const Button" in component_code

        # Generate story
        story_code = ReactComponentGenerator.generate_story(button)
        assert "export const Default: Story" in story_code

        # Generate styles
        css = ComponentStylesGenerator.generate_css_modules("Button")
        assert ".container" in css

    def test_full_card_component_vue(self):
        """Test generating a complete Card component in Vue."""
        card = ComponentDefinition(
            name="Card",
            description="Card component with header, body, and footer",
            props=[
                ComponentProp("title", "string"),
                ComponentProp("elevated", "boolean", default_value=False),
            ],
            has_children=True,
            is_layout_component=True,
        )

        # Generate component
        component_code = VueComponentGenerator.generate_component(card)
        assert "defineComponent" in component_code
        assert "<slot></slot>" in component_code

        # Generate story
        story_code = VueComponentGenerator.generate_story(card)
        assert "WithSlot: Story" in story_code

    def test_form_component_generation(self):
        """Test generating a form input component."""
        form_input = ComponentDefinition(
            name="FormInput",
            description="Controlled form input component",
            props=[
                ComponentProp("label", "string"),
                ComponentProp("value", "string", is_required=True),
                ComponentProp("onChange", "function", is_required=True),
                ComponentProp("error", "string"),
                ComponentProp("required", "boolean", default_value=False),
            ],
            is_form_component=True,
        )

        code = ReactComponentGenerator.generate_component(form_input)

        assert "interface FormInputProps" in code
        assert "label?" in code
        assert "value: string" in code
        assert "onChange: function" in code
        assert "error?" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
