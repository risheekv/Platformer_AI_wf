#!/usr/bin/env python3
"""
Build script for creating executable from the Maze Runner game
"""

import os
import sys
import subprocess
import shutil

def main():
    print("🚀 Building Maze Runner Executable...")
    
    # Get the current directory (scripts folder)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(scripts_dir)
    
    # Change to scripts directory
    os.chdir(scripts_dir)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "--break-system-packages"], check=True)
    
    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    # Build the executable
    print("🔨 Building executable...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "maze_runner.spec",
            "--clean",
            "--noconfirm"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Build completed successfully!")
        
        # Check if executable was created
        exe_name = "MazeRunner"
        if os.name == 'nt':  # Windows
            exe_path = os.path.join("dist", f"{exe_name}.exe")
        else:  # macOS/Linux
            exe_path = os.path.join("dist", exe_name)
        
        if os.path.exists(exe_path):
            print(f"🎉 Executable created: {exe_path}")
            print(f"📁 Size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
            
            # Copy to project root for easy access
            final_path = os.path.join(project_root, os.path.basename(exe_path))
            shutil.copy2(exe_path, final_path)
            print(f"📋 Copied to: {final_path}")
            
        else:
            print("❌ Executable not found in expected location")
            print("Available files in dist/:")
            if os.path.exists("dist"):
                for item in os.listdir("dist"):
                    print(f"   - {item}")
                    
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        print("Error output:")
        print(e.stderr)
        return 1
    
    print("\n🎮 Your Maze Runner game is ready to run!")
    print("💡 Users can now double-click the executable to play without installing Python.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 