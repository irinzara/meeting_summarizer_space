import gradio as gr
import os
import tempfile
from pydub import AudioSegment
import whisper
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK punkt tokenizer if not already
import nltk
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


# Load Whisper model once
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        import whisper
        whisper_model = whisper.load_model("tiny")
    return whisper_model

def extract_audio(file_path):
    """Extract audio from audio/video files and convert to mono WAV 16kHz"""
    ext = os.path.splitext(file_path)[1].lower()
    fd, audio_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        if ext == ".mp3":
            audio = AudioSegment.from_file(file_path, format="mp3")
        elif ext == ".wav":
            audio = AudioSegment.from_file(file_path, format="wav")
        else:
            audio = AudioSegment.from_file(file_path)  # fallback for video
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(audio_path, format="wav")
        return audio_path
    except Exception as e:
        raise Exception(f"Audio extraction failed: {e}")

def chunk_audio(audio_path, chunk_length_ms=30000):
    """Split audio into chunks (30s default)"""
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        fd, chunk_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        audio[i:i+chunk_length_ms].export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def transcribe_audio(audio_path):
    """Whisper transcription"""
    try:
        model = get_whisper_model()
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        return f"[Transcription error: {e}]"


def summarize_text_simple(text, max_sentences=5):
    """Simple summarizer: pick first and most important sentences"""
    sentences = sent_tokenize(text)
    if len(sentences) <= max_sentences:
        return text
    # Simple scoring: pick sentences with most words (heuristic for importance)
    scored = sorted(sentences, key=lambda s: len(s.split()), reverse=True)
    top_sentences = sorted(scored[:max_sentences], key=lambda s: text.index(s))  # maintain order
    return " ".join(top_sentences)

def summarize_meeting(file):
    if os.path.getsize(file) > 100 * 1024 * 1024:
        return "Error: File too large. Upload <100 MB.", {"entities": []}
    
    audio_path = extract_audio(file)
    chunks = chunk_audio(audio_path)
    
    transcript = ""
    for c in chunks:
        transcript += transcribe_audio(c) + " "
        if os.path.exists(c):
            os.remove(c)
    
    if audio_path != file and os.path.exists(audio_path):
        os.remove(audio_path)
    
    summary = summarize_text_simple(transcript, max_sentences=5)
    entities = {"entities": []}  # placeholder
    
    return summary, entities

iface = gr.Interface(
    fn=summarize_meeting,
    inputs=gr.File(label="Upload Audio/Video", type="filepath"),
    outputs=[gr.Textbox(label="Summary"), gr.JSON(label="Entities")],
    title="Meeting Summarizer",
    description="Upload audio/video (<100 MB) to get a short summary."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0")


