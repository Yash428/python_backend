"""
Installation validation script.

Run this after setup to verify all components are correctly installed.

Usage:
    python test_installation.py
"""

import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_python_version():
    """Check Python version."""
    print("✓ Python Version Check")
    version_info = sys.version_info
    version_string = f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major >= 3 and version_info.minor >= 10:
        print(f"  ✓ {version_string} (OK)")
        return True
    else:
        print(f"  ✗ {version_string} (requires 3.10+)")
        return False


def check_ffmpeg():
    """Check FFmpeg installation."""
    print("\n✓ FFmpeg Check")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
            check=True
        )
        version_line = result.stdout.decode().split('\n')[0]
        print(f"  ✓ {version_line}")
        return True
    except Exception as e:
        print(f"  ✗ FFmpeg not found: {e}")
        print("    Install from: https://ffmpeg.org/download.html")
        return False


def check_ffprobe():
    """Check FFprobe installation."""
    print("\n✓ FFprobe Check")
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            timeout=5,
            check=True
        )
        version_line = result.stdout.decode().split('\n')[0]
        print(f"  ✓ {version_line}")
        return True
    except Exception as e:
        print(f"  ✗ FFprobe not found: {e}")
        return False


def check_imports():
    """Check required Python packages."""
    print("\n✓ Python Packages Check")
    
    packages = {
        "whisper": "openai-whisper",
        "torch": "torch",
        "numpy": "numpy",
        "scipy": "scipy",
    }
    
    all_ok = True
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} not installed")
            print(f"    Run: pip install {package_name}")
            all_ok = False
    
    return all_ok


def check_project_structure():
    """Check project directory structure."""
    print("\n✓ Project Structure Check")
    
    required_files = [
        "src/__init__.py",
        "src/utils.py",
        "src/extract_audio.py",
        "src/transcribe.py",
        "src/segment.py",
        "run_pipeline.py",
        "requirements.txt",
        "README.md",
    ]
    
    required_dirs = [
        "src",
        "recordings",
        "transcripts",
    ]
    
    all_ok = True
    
    # Check files
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} not found")
            all_ok = False
    
    # Check directories
    for dir_path in required_dirs:
        full_path = Path(__file__).parent / dir_path
        if full_path.is_dir():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ not found")
            all_ok = False
    
    return all_ok


def check_src_modules():
    """Check that src modules can be imported."""
    print("\n✓ Source Modules Check")
    
    modules = [
        ("utils", "Utilities"),
        ("extract_audio", "Audio Extractor"),
        ("transcribe", "Whisper Transcriber"),
        ("segment", "Segment Processor"),
    ]
    
    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(f"src.{module_name}")
            print(f"  ✓ {display_name} ({module_name}.py)")
        except Exception as e:
            print(f"  ✗ {display_name}: {e}")
            all_ok = False
    
    return all_ok


def test_core_functions():
    """Test core functionality."""
    print("\n✓ Core Functions Test")
    
    try:
        from utils import (
            seconds_to_timestamp,
            timestamp_to_seconds,
            format_duration,
            setup_logger
        )
        
        # Test time conversion
        test_seconds = 125.456
        timestamp = seconds_to_timestamp(test_seconds)
        back_to_seconds = timestamp_to_seconds(timestamp)
        
        if abs(back_to_seconds - test_seconds) < 0.01:
            print(f"  ✓ Time conversion: {test_seconds}s → {timestamp} → {back_to_seconds}s")
        else:
            print(f"  ✗ Time conversion error")
            return False
        
        # Test duration formatting
        duration_str = format_duration(3665)
        if "1h" in duration_str:
            print(f"  ✓ Duration formatting: 3665s → {duration_str}")
        else:
            print(f"  ✗ Duration formatting error")
            return False
        
        # Test logger
        logger = setup_logger(__name__)
        print(f"  ✓ Logger initialization")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Core functions error: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("JITSI TRANSCRIPTION PIPELINE - INSTALLATION CHECK")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("FFmpeg", check_ffmpeg),
        ("FFprobe", check_ffprobe),
        ("Python Packages", check_imports),
        ("Project Structure", check_project_structure),
        ("Source Modules", check_src_modules),
        ("Core Functions", test_core_functions),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✓ ALL CHECKS PASSED!")
        print("\nYou're ready to transcribe. Try:")
        print("  python run_pipeline.py recordings/meeting.mp4")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("\nPlease fix the issues above and try again.")
        print("\nFor help, see: QUICKSTART.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
