"""
Quick test script to validate WhisperX installation and functionality.
Run this before starting the main application to verify everything is set up correctly.

Usage:
    python test_whisperx.py
"""

import os
import sys
from pathlib import Path


def check_whisperx_installation():
    """Check if WhisperX is installed."""
    print("=" * 60)
    print("STEP 1: Checking WhisperX Installation")
    print("=" * 60)
    
    try:
        import whisperx
        print("✅ WhisperX is installed")
        print(f"   Version: {whisperx.__version__ if hasattr(whisperx, '__version__') else 'unknown'}")
        return True
    except ImportError:
        print("❌ WhisperX is NOT installed")
        print("   Install it with: pip install whisperx")
        return False


def check_huggingface_token():
    """Check if HUGGINGFACE_TOKEN is set."""
    print("\n" + "=" * 60)
    print("STEP 2: Checking Hugging Face Token")
    print("=" * 60)
    
    token = os.getenv("HUGGINGFACE_TOKEN")
    if token:
        print("✅ HUGGINGFACE_TOKEN is set")
        print(f"   Token (first 10 chars): {token[:10]}...")
        return True
    else:
        print("❌ HUGGINGFACE_TOKEN is NOT set")
        print("   Set it with:")
        print("   - Windows PowerShell: $env:HUGGINGFACE_TOKEN='your_token'")
        print("   - Linux/Mac: export HUGGINGFACE_TOKEN='your_token'")
        print("   - Or create backend/.env file with: HUGGINGFACE_TOKEN=your_token")
        return False


def check_pytorch():
    """Check if PyTorch is installed."""
    print("\n" + "=" * 60)
    print("STEP 3: Checking PyTorch")
    print("=" * 60)
    
    try:
        import torch
        print("✅ PyTorch is installed")
        print(f"   Version: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU device: {torch.cuda.get_device_name(0)}")
        return True
    except ImportError:
        print("❌ PyTorch is NOT installed")
        return False


def test_whisperx_model_loading():
    """Test loading a WhisperX model."""
    print("\n" + "=" * 60)
    print("STEP 4: Testing WhisperX Model Loading")
    print("=" * 60)
    
    try:
        import whisperx
        import torch
        
        # Fix for PyTorch 2.6+ weights_only=True default
        try:
            from omegaconf import DictConfig, ListConfig
            torch.serialization.add_safe_globals([DictConfig, ListConfig])
            print("   Added omegaconf to safe globals for PyTorch 2.6+")
        except ImportError:
            print("   Note: omegaconf not found, installing whisperx should add it")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading model 'base' on device '{device}' with compute_type '{compute_type}'...")
        print("(This may take a minute on first run to download the model)")
        
        model = whisperx.load_model("base", device, compute_type=compute_type)
        print("✅ Successfully loaded WhisperX model")
        return True
    except Exception as e:
        print(f"❌ Failed to load WhisperX model: {e}")
        return False


def test_diarization_pipeline():
    """Test diarization pipeline initialization."""
    print("\n" + "=" * 60)
    print("STEP 5: Testing Diarization Pipeline")
    print("=" * 60)
    
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("⚠️  Skipping (HUGGINGFACE_TOKEN not set)")
        return False
    
    try:
        from pyannote.audio import Pipeline
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Initializing diarization pipeline on device '{device}'...")
        print("(This may take a minute on first run to download models)")
        
        diarize_model = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token
        )
        if device == "cuda":
            diarize_model.to(torch.device(device))
        
        print("✅ Successfully initialized diarization pipeline")
        print("   You have access to pyannote models")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize diarization pipeline: {e}")
        print("\nPossible issues:")
        print("1. Token is invalid")
        print("2. You haven't accepted model terms at:")
        print("   - https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("   - https://huggingface.co/pyannote/segmentation-3.0")
        return False


def check_test_files():
    """Check if there are any test audio files available."""
    print("\n" + "=" * 60)
    print("STEP 6: Checking for Test Files")
    print("=" * 60)
    
    storage_path = Path("storage")
    if not storage_path.exists():
        print("⚠️  No storage directory found")
        return False
    
    audio_files = []
    for meeting_dir in storage_path.iterdir():
        if meeting_dir.is_dir():
            audio_dir = meeting_dir / "audio"
            if audio_dir.exists():
                for audio_file in audio_dir.iterdir():
                    if audio_file.suffix.lower() in [".mp3", ".mp4", ".wav", ".m4a", ".mkv", ".mov"]:
                        audio_files.append(audio_file)
    
    if audio_files:
        print(f"✅ Found {len(audio_files)} audio file(s):")
        for af in audio_files[:3]:  # Show first 3
            print(f"   - {af}")
        if len(audio_files) > 3:
            print(f"   ... and {len(audio_files) - 3} more")
        return True
    else:
        print("⚠️  No audio files found in storage/")
        print("   Upload a file through the web interface to test")
        return False


def main():
    """Run all checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "WhisperX Setup Validation" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = {
        "WhisperX Installed": check_whisperx_installation(),
        "HuggingFace Token": check_huggingface_token(),
        "PyTorch": check_pytorch(),
    }
    
    # Only test model loading if basics are working
    if results["WhisperX Installed"] and results["PyTorch"]:
        results["Model Loading"] = test_whisperx_model_loading()
    
    # Only test diarization if token is set
    if results["HuggingFace Token"]:
        results["Diarization Pipeline"] = test_diarization_pipeline()
    
    results["Test Files Available"] = check_test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    all_critical_passed = all([
        results.get("WhisperX Installed", False),
        results.get("PyTorch", False),
        results.get("HuggingFace Token", False),
    ])
    
    print("\n" + "=" * 60)
    if all_critical_passed:
        print("🎉 All critical checks passed!")
        print("You're ready to use WhisperX with speaker diarization.")
        print("\nNext steps:")
        print("1. Start the backend: python -m src.main")
        print("2. Start the frontend: cd ../frontend && npm run dev")
        print("3. Upload a meeting file to test transcription + diarization")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        if not results.get("WhisperX Installed", False):
            print("- Install WhisperX: pip install whisperx")
        if not results.get("HuggingFace Token", False):
            print("- Set HUGGINGFACE_TOKEN environment variable")
            print("- Accept model terms (see WHISPERX_SETUP.md)")
    print("=" * 60)
    
    sys.exit(0 if all_critical_passed else 1)


if __name__ == "__main__":
    main()

