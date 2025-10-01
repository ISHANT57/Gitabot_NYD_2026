#!/usr/bin/env python3
"""
Setup script for running the Hindu Texts Q&A chatbot locally.
This script helps configure the environment and check dependencies.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required. You have:", sys.version)
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'requests', 'pandas', 'faiss-cpu', 'numpy'
    ]
    
    missing_packages = []
    
    print("\n📦 Checking dependencies...")
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 Installing missing packages...")
        print(f"Run: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_data_files():
    """Check if data files exist"""
    print("\n📁 Checking data files...")
    
    data_dir = "attached_assets"
    if not os.path.exists(data_dir):
        print(f"❌ Data directory '{data_dir}' not found")
        return False
    
    # Check for key data files
    key_files = [
        "Bhagwad_Gita_Verses_English_Questions_1757068789961.csv",
        "processed_bhagwat_gita_1757068789966.csv",
        "valmiki-ramayana-verses_1757069097291.json"
    ]
    
    found_files = 0
    for filename in key_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            print(f"✅ {filename}")
            found_files += 1
        else:
            print(f"⚠️  {filename} (not found)")
    
    if found_files == 0:
        print("❌ No data files found. Please ensure your data files are in the attached_assets directory.")
        return False
    
    print(f"✅ Found {found_files} data files")
    return True

def check_api_setup():
    """Check API key configuration"""
    print("\n🔑 Checking API configuration...")
    
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not openrouter_key:
        print("⚠️  OPENROUTER_API_KEY not set")
        print("\n📖 To set up API key:")
        print("1. Get your API key from: https://openrouter.ai/")
        print("2. Set the environment variable:")
        
        if os.name == 'nt':  # Windows
            print("   Windows: set OPENROUTER_API_KEY=your_key_here")
        else:  # Unix/Linux/macOS
            print("   Unix/Linux: export OPENROUTER_API_KEY=your_key_here")
        
        print("\n💡 The chatbot will work without the API key but won't generate answers.")
        return False
    else:
        print("✅ OPENROUTER_API_KEY is set")
        return True

def create_sample_env_file():
    """Create a sample .env file"""
    env_content = """# Hindu Texts Q&A Chatbot Environment Variables
# Copy this file to .env and fill in your API keys

# OpenRouter API Key (required for answer generation)
# Get from: https://openrouter.ai/
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Mistral API Key (optional, fallback)
# Get from: https://console.mistral.ai/
MISTRAL_API_KEY=your_mistral_api_key_here

# Vector Database (optional, uses FAISS if not available)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key_here
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    print("📄 Created .env.example file with sample configuration")

def main():
    """Main setup function"""
    print("🚀 Hindu Texts Q&A Chatbot - Local Setup")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python version
    if not check_python_version():
        all_checks_passed = False
    
    # Check dependencies
    if not check_dependencies():
        all_checks_passed = False
    
    # Check data files
    if not check_data_files():
        all_checks_passed = False
    
    # Check API setup
    api_configured = check_api_setup()
    
    # Create sample env file
    print("\n📝 Creating sample configuration...")
    create_sample_env_file()
    
    print("\n" + "=" * 50)
    
    if all_checks_passed:
        print("🎉 Setup complete! You can now run the chatbot:")
        print("   python backend_chatbot.py --help")
        print("   python backend_chatbot.py -q 'What is dharma?'")
        print("   python backend_chatbot.py -i  # Interactive mode")
        
        if not api_configured:
            print("\n⚠️  Note: Set up OPENROUTER_API_KEY for full functionality")
    else:
        print("❌ Setup incomplete. Please fix the issues above and run again.")
        sys.exit(1)

if __name__ == "__main__":
    main()