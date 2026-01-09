#!/usr/bin/env python3
"""
Setup HuggingFace authentication for Pyannote.audio.

Pyannote.audio models require a free HuggingFace token to download.
This script helps you set up authentication.

Steps:
1. Create free account at https://huggingface.co
2. Generate token at https://huggingface.co/settings/tokens
3. Accept license for the model:
   https://huggingface.co/pyannote/speaker-diarization-3.1
4. Run this script and paste your token
"""

import os
import sys
from pathlib import Path
from typing import Optional


def setup_hf_token() -> bool:
    """
    Setup HuggingFace token interactively.
    
    Returns:
        True if successful
    """
    print("\n" + "=" * 70)
    print("HuggingFace Authentication Setup for Pyannote.audio")
    print("=" * 70)
    
    # Check if already set
    existing_token = os.getenv("HF_TOKEN")
    if existing_token:
        print("✓ HF_TOKEN environment variable already set")
        return True
    
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    if token_path.exists():
        print(f"✓ HuggingFace token found at: {token_path}")
        return True
    
    print("\nTo use speaker diarization, you need:")
    print("1. Free HuggingFace account (https://huggingface.co)")
    print("2. Authentication token\n")
    
    print("Steps:")
    print("  a) Create account: https://huggingface.co/join")
    print("  b) Generate token: https://huggingface.co/settings/tokens")
    print("     - Use 'read' permission (not 'write')")
    print("  c) Accept license: https://huggingface.co/pyannote/speaker-diarization-3.1")
    print("     - Click 'Agree and access repository'\n")
    
    print("Option 1: Login with CLI (recommended)")
    print("  Run: huggingface-cli login")
    print("  Then paste your token when prompted\n")
    
    print("Option 2: Set environment variable")
    token = input("Paste your HuggingFace token (or press Enter to skip): ").strip()
    
    if not token:
        print("\nSkipped token setup. You can set it later with:")
        print("  set HF_TOKEN=your_token_here  (Windows)")
        print("  export HF_TOKEN=your_token_here  (Linux/Mac)")
        return False
    
    # Set environment variable for this session
    os.environ["HF_TOKEN"] = token
    
    # Try to save to standard location
    try:
        token_dir = token_path.parent
        token_dir.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(token)
        print(f"\n✓ Token saved to: {token_path}")
        print("  (automatically used for future sessions)")
        return True
    except Exception as e:
        print(f"\n⚠ Could not save token to disk: {e}")
        print("  Token is set for this session only")
        print("  You can set HF_TOKEN environment variable permanently")
        return True


def verify_setup() -> bool:
    """
    Verify Pyannote.audio setup.
    
    Returns:
        True if ready to use
    """
    print("\n" + "=" * 70)
    print("Verifying Pyannote.audio Setup")
    print("=" * 70)
    
    checks_passed = 0
    total_checks = 3
    
    # Check 1: Pyannote installed
    print("\n[1/3] Checking Pyannote.audio installation...", end=" ")
    try:
        from pyannote.audio import Pipeline
        print("✓ Installed")
        checks_passed += 1
    except ImportError:
        print("✗ Not installed")
        print("  Install with: pip install pyannote.audio")
    
    # Check 2: PyTorch
    print("[2/3] Checking PyTorch...", end=" ")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ GPU available ({torch.cuda.get_device_name(0)})")
        else:
            print("✓ CPU mode")
        checks_passed += 1
    except ImportError:
        print("✗ Not installed")
        print("  Install with: pip install torch torchaudio")
    
    # Check 3: HuggingFace token
    print("[3/3] Checking HuggingFace authentication...", end=" ")
    token = os.getenv("HF_TOKEN")
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    
    if token or token_path.exists():
        print("✓ Authenticated")
        checks_passed += 1
    else:
        print("✗ Not authenticated")
        print("  Run 'python setup_diarization.py' to authenticate")
    
    print(f"\nSetup Status: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("\n✓ System ready for speaker diarization!")
        return True
    else:
        print("\n⚠ Some setup steps are incomplete")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup Pyannote.audio for speaker diarization"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify setup without prompting for token"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        success = verify_setup()
    else:
        success = setup_hf_token()
        if success:
            verify_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
