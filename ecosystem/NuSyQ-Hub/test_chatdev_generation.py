#!/usr/bin/env python3
"""
ChatDev Multi-Agent Generation Test
Demonstrates the multi-agent workflow for code generation using ChatDev + Ollama
"""

from datetime import datetime
from pathlib import Path


def test_chatdev_generation():
    """Test ChatDev generation with Ollama local LLM."""
    print("=" * 80)
    print("🤖 CHATDEV MULTI-AGENT GENERATION TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Test generation task
    task = "Create a simple Python calculator with basic arithmetic operations (add, subtract, multiply, divide)"
    project_name = "SimpleCalculator"
    model = "qwen2.5-coder:7b"

    print(
        f"""
📋 Generation Task:
   Task: {task}
   Project: {project_name}
   Model: {model}
   AI Team: CEO → CTO → Programmer → Tester → Reviewer
   
⏳ Starting multi-agent generation workflow..."""
    )

    # Build command
    chatdev_path = Path("C:\\Users\\keath\\NuSyQ\\ChatDev\\run_ollama.py")

    # Show what will happen
    print(
        f"""
🔄 Workflow Steps:
   1. CEO Agent: Analyze requirements and create specification
   2. CTO Agent: Design system architecture and file structure  
   3. Programmer Agent: Write implementation code
   4. Tester Agent: Create test cases and validation
   5. Reviewer Agent: Review code quality and formatting
   
⚠️  Note: This is a REAL multi-agent generation process:
   - Runs locally on your machine (no cloud calls)
   - Uses {model} model via Ollama
   - Generates complete, runnable code
   - Creates project in WareHouse directory
   
To RUN this generation (takes 2-5 minutes):
   
   python "{chatdev_path}" \\
     --task "{task}" \\
     --name "{project_name}" \\
     --model "{model}" \\
     --org "NuSyQ"
   
Expected Output:
   ✅ Project created in: C:\\Users\\keath\\NuSyQ\\ChatDev\\WareHouse\\{project_name}_<timestamp>
   ✅ Complete source code (Python files)
   ✅ Test cases
   ✅ Requirements.txt
   ✅ README with usage instructions
   
📊 Multi-Agent Team Roles:
   
   🎯 CEO (Chief Executive Officer)
      - Analyzes requirements
      - Creates specification document
      - Defines project scope
      
   🏗️  CTO (Chief Technology Officer)  
      - Designs architecture
      - Plans file structure
      - Defines APIs and data flow
      
   💻 PROGRAMMER (Lead Developer)
      - Implements all code
      - Follows architecture plan
      - Uses best practices
      
   🧪 TESTER (Quality Assurance)
      - Creates comprehensive tests
      - Validates functionality
      - Tests edge cases
      
   👁️  REVIEWER (Code Reviewer)
      - Reviews code quality
      - Checks standards compliance
      - Suggests improvements

═══════════════════════════════════════════════════════════════════════════════
"""
    )


def show_warehouse_projects():
    """Show existing projects in WareHouse."""
    warehouse = Path("C:\\Users\\keath\\NuSyQ\\ChatDev\\WareHouse")

    print("📁 Existing ChatDev WareHouse Projects:")
    print("─" * 80)

    if warehouse.exists():
        projects = list(warehouse.iterdir())
        if projects:
            for proj in sorted(projects)[-10:]:  # Show last 10
                print(f"   📦 {proj.name}")
        else:
            print("   (No projects yet - run generation to create one)")
    else:
        print("   (WareHouse directory not found)")
    print()


if __name__ == "__main__":
    test_chatdev_generation()
    print()
    show_warehouse_projects()

    print(
        """
🚀 READY TO USE CHATDEV!

Next Steps:
1. Run a generation (copy-paste the command above)
2. Check ChatDev output for project details
3. Review generated code in WareHouse directory
4. Test the generated project
5. Integrate generated code into NuSyQ-Hub

📚 Documentation:
   - ChatDev README: C:\\Users\\keath\\NuSyQ\\ChatDev\\README.md
   - Ollama Integration: C:\\Users\\keath\\NuSyQ\\ChatDev\\INTEGRATION_GUIDE.md
   - ChatDev Prompt: C:\\Users\\keath\\NuSyQ\\ChatDev\\MODULAR_MODELS_README.md
"""
    )
