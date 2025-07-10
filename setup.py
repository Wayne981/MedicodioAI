#!/usr/bin/env python3
"""
Setup script for Clinical Information Extraction System
"""

import subprocess
import sys
import os

def run_command(command, description=""):
    """Run a command and print the result"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        print("✅ Success!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main setup function"""
    print("🏥 Clinical Information Extraction System Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Install requirements
    print("\n📦 Installing Python packages...")
    success = run_command("pip install -r requirements.txt", "Installing dependencies")
    
    if not success:
        print("\n⚠️  Trying alternative installation...")
        # Try installing packages individually
        packages = [
            "spacy>=3.4.0",
            "PyPDF2>=3.0.0", 
            "pandas>=1.5.0",
            "scispacy>=0.5.1"
        ]
        
        for package in packages:
            run_command(f"pip install {package}", f"Installing {package}")
    
    # Download spaCy models
    print("\n🔤 Downloading spaCy language models...")
    
    # Download general English model
    success1 = run_command("python -m spacy download en_core_web_sm", "Downloading general English model")
    
    # Try to download scientific model
    success2 = run_command("pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_sm-0.5.1.tar.gz", 
                          "Downloading scientific model")
    
    print("\n" + "="*50)
    print("📋 SETUP SUMMARY")
    print("="*50)
    
    if success1:
        print("✅ General English model installed")
    else:
        print("❌ General English model failed")
    
    if success2:
        print("✅ Scientific model installed")
    else:
        print("⚠️  Scientific model failed (will use general model)")
    
    print("\n🚀 Setup complete! You can now run:")
    print("   python clinical_extractor.py")
    print("\n📄 Make sure to place 'Input Data for assignment.pdf' in this directory")

if __name__ == "__main__":
    main() 