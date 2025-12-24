# WhisperX Setup Guide

This guide explains how to set up WhisperX for better speaker diarization in the Meeting Insight Generator.

## Why WhisperX?

WhisperX provides several advantages over vanilla Whisper + pyannote.audio:
- **Better Integration**: Diarization is built into the pipeline
- **Accurate Timestamps**: Word-level alignment for precise timing
- **Easier Setup**: Single package instead of managing multiple dependencies
- **Better Speaker Assignment**: More accurate speaker-to-text mapping

## Installation

### Step 1: Install WhisperX

```bash
# Navigate to backend directory
cd backend

# Activate your virtual environment
# On Windows:
.venv310\Scripts\activate
# On Linux/Mac:
source .venv310/bin/activate

# Install WhisperX
pip install whisperx

# Or update all requirements
pip install -r ../requirements.txt
```

### Step 2: Get Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token (or use existing one)
3. Copy the token

### Step 3: Accept Model Terms

Visit these pages and accept the terms:
1. https://huggingface.co/pyannote/speaker-diarization-3.1
2. https://huggingface.co/pyannote/segmentation-3.0

Click "Agree and access repository" on each page.

### Step 4: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:HUGGINGFACE_TOKEN="your_token_here"
```

**Windows (Command Prompt):**
```cmd
set HUGGINGFACE_TOKEN=your_token_here
```

**Linux/Mac:**
```bash
export HUGGINGFACE_TOKEN=your_token_here
```

**Permanent Setup (recommended):**

Create a `.env` file in the backend directory:
```bash
# backend/.env
HUGGINGFACE_TOKEN=your_token_here
```

The application will automatically load this file.

## Running with WhisperX

Once installed, simply run the backend as usual:

```bash
cd backend
python -m src.main
```

You should see logs like:
```
[TranscriptionService] Loading WhisperX model: small
[TranscriptionService] WhisperX model loaded successfully
[TranscriptionService] Transcribing audio with WhisperX
[TranscriptionService] Aligning timestamps
[TranscriptionService] Identifying speakers with WhisperX
[TranscriptionService] WhisperX identified 2 unique speakers: {'SPEAKER_00', 'SPEAKER_01'}
[TranscriptionService] Assigned speaker labels to 48/50 segments
```

## Troubleshooting

### Issue: "whisperx not found"
```bash
pip install whisperx
```

### Issue: "HUGGINGFACE_TOKEN not set"
Make sure you've set the environment variable (see Step 4 above).

### Issue: "Authentication error"
1. Check that your token is valid
2. Make sure you've accepted terms for both models (Step 3)
3. Try regenerating your token on Hugging Face

### Issue: Diarization still not working
Check the backend logs for detailed error messages. Common causes:
- Token not set
- Model terms not accepted
- Network issues downloading models (first run)

### Fallback Mode

If WhisperX installation fails, the system automatically falls back to vanilla Whisper:
```
[TranscriptionService] WhisperX not installed, falling back to vanilla Whisper
```

Transcription will still work, but without speaker diarization.

## Model Sizes

WhisperX supports the same model sizes as Whisper:

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| tiny | 39M | Low | Fast |
| base | 74M | Medium | Fast |
| small | 244M | Good | Medium |
| medium | 769M | Better | Slow |
| large | 1550M | Best | Very Slow |

Default is `small` - good balance of accuracy and speed.

To change the model size, edit `backend/src/api/routes/upload.py`:
```python
transcription_service = TranscriptionService(
    model_name="medium",  # Change this
    device="cpu",
    diarization_enabled=True,
    diarization_token=os.getenv("HUGGINGFACE_TOKEN"),
    transcript_store=transcript_store,
)
```

## GPU Acceleration (Optional)

For faster processing, use GPU:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Update device setting in upload.py
transcription_service = TranscriptionService(
    model_name="small",
    device="cuda",  # Change from "cpu" to "cuda"
    ...
)
```

## Testing

Upload a meeting file and check:
1. Backend logs show WhisperX is being used
2. Transcript shows speaker labels (SPEAKER_00, SPEAKER_01, etc.)
3. Timestamps are accurate
4. Diarized transcript file has proper speaker sections

## Support

If you encounter issues:
1. Check backend logs for detailed error messages
2. Verify HUGGINGFACE_TOKEN is set correctly
3. Make sure you've accepted model terms
4. Try reinstalling: `pip uninstall whisperx && pip install whisperx`

