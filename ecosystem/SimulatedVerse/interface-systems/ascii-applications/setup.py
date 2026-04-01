#!/usr/bin/env python3
"""
🚀 CoreLink Foundation Setup and Demo Launcher
Complete TouchDesigner-style ASCII interface setup script
"""

import sys
import subprocess
import importlib
import os

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} (compatible)")
    return True

def check_dependencies():
    """Check and install required dependencies"""
    deps = {
        'textual': 'textual>=0.62.0',
        'rich': 'rich>=13.7.1', 
        'numpy': 'numpy>=1.26.4'
    }
    
    missing = []
    
    for module, pip_name in deps.items():
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (missing)")
            missing.append(pip_name)
    
    if missing:
        print("\n📦 Installing missing dependencies...")
        for dep in missing:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {dep}")
                return False
    
    return True

def check_terminal_support():
    """Check terminal capabilities"""
    print("\n🖥️  Terminal Compatibility:")
    
    # Check terminal size
    try:
        size = os.get_terminal_size()
        print(f"   Size: {size.columns}x{size.lines}")
        
        if size.columns < 80 or size.lines < 24:
            print("   ⚠️  Small terminal (recommend 80x24 minimum)")
        else:
            print("   ✅ Terminal size OK")
    except:
        print("   ❓ Could not detect terminal size")
    
    # Check color support
    if os.getenv('COLORTERM') in ['truecolor', '24bit']:
        print("   ✅ Truecolor support detected")
    elif os.getenv('TERM') and '256' in os.getenv('TERM'):
        print("   ✅ 256 color support detected")
    else:
        print("   ⚠️  Limited color support (may affect appearance)")
    
    # Check Unicode support
    try:
        test_chars = "⠀⠁⠂⠃⠄⠅⠆⠇"  # Braille characters
        print(f"   Unicode test: {test_chars}")
        print("   ✅ Unicode/Braille support OK")
    except:
        print("   ❌ Unicode support issues")

def run_demo(demo_type="simple"):
    """Run the specified demo"""
    demos = {
        "simple": "simple_app.py",
        "complete": "demo_complete.py", 
        "single": "../touchdesigner_complete.py"
    }
    
    if demo_type not in demos:
        print(f"❌ Unknown demo type: {demo_type}")
        return False
    
    script = demos[demo_type]
    
    print(f"\n🚀 Launching {demo_type} demo...")
    print(f"   Script: {script}")
    print("   Press 'q' to quit when running")
    print("   Press '1-5' for different modes")
    
    try:
        if demo_type == "single":
            subprocess.run([sys.executable, script], cwd="..")
        else:
            subprocess.run([sys.executable, script])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        return False
    
    return True

def main():
    """Main setup and launcher"""
    print("🚀 CoreLink Foundation - TouchDesigner ASCII Interface")
    print("=" * 60)
    
    # System checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    check_terminal_support()
    
    print("\n🎮 Available Demos:")
    print("   1. Simple Demo (simple_app.py)")
    print("   2. Complete Demo (demo_complete.py)")
    print("   3. Single File Demo (touchdesigner_complete.py)")
    print("   4. Setup check only")
    
    while True:
        try:
            choice = input("\nSelect demo (1-4, or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                run_demo("simple")
            elif choice == '2':
                run_demo("complete")
            elif choice == '3':
                run_demo("single")
            elif choice == '4':
                print("✅ Setup check complete!")
                break
            else:
                print("❌ Invalid choice")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()