#!/usr/bin/env python3
"""
OpenAI API Setup Script for LADI Backend

This script helps you configure the OpenAI API key to get real evaluation scores
instead of mock/fake scores.
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 LADI OpenAI API Setup")
    print("=" * 50)
    print()
    print("To get real AI evaluation scores instead of fake/mock scores,")
    print("you need to configure your OpenAI API key.")
    print()
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ No .env file found!")
        print("Creating .env file...")
        env_file.touch()
    
    # Check current API key
    current_key = os.environ.get('OPENAI_API_KEY')
    if current_key and current_key not in ['placeholder-openai-key', 'your-openai-api-key-here']:
        print("✅ OpenAI API key is already configured!")
        print(f"Current key: {current_key[:10]}...{current_key[-4:]}")
        return
    
    print("❌ OpenAI API key not configured or set to placeholder value.")
    print()
    print("To get real evaluation scores, you need to:")
    print()
    print("1. Get an OpenAI API key:")
    print("   - Go to https://platform.openai.com/api-keys")
    print("   - Sign up or log in to your OpenAI account")
    print("   - Create a new API key")
    print()
    print("2. Set the API key in your environment:")
    print()
    print("   Option A - Set environment variable:")
    print("   export OPENAI_API_KEY='your-actual-api-key-here'")
    print()
    print("   Option B - Add to .env file:")
    print("   echo 'OPENAI_API_KEY=your-actual-api-key-here' >> .env")
    print()
    print("   Option C - Set in Render dashboard:")
    print("   - Go to your Render service dashboard")
    print("   - Add environment variable: OPENAI_API_KEY")
    print("   - Set value to your actual API key")
    print()
    print("3. Restart your application")
    print()
    print("⚠️  IMPORTANT: Keep your API key secure and never commit it to version control!")
    print()
    
    # Check if running in Render
    if os.environ.get('RENDER'):
        print("🔍 Detected Render environment")
        print("   Set OPENAI_API_KEY in your Render service environment variables")
        print("   Go to: Dashboard > Your Service > Environment > Environment Variables")
    else:
        print("🔍 Local development detected")
        print("   You can set the API key in your .env file or as an environment variable")
    
    print()
    print("💰 Cost Information:")
    print("   - GPT-4: ~$0.03 per 1K tokens")
    print("   - Typical evaluation: ~$0.10-0.50 per manuscript")
    print("   - Set usage limits in your OpenAI dashboard")
    print()
    
    # Offer to help create .env file
    if input("Would you like to create/update the .env file now? (y/n): ").lower() == 'y':
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
        if api_key:
            with open('.env', 'a') as f:
                f.write(f'\nOPENAI_API_KEY={api_key}\n')
            print("✅ API key added to .env file!")
            print("   Restart your application for changes to take effect.")
        else:
            print("⏭️  Skipped adding API key to .env file")
    else:
        print("⏭️  Skipped .env file creation")

if __name__ == "__main__":
    main()
