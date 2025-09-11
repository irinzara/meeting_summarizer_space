import gradio as gr
import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile

# Initialize recognizer
recognizer = sr.Recognizer()

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
            audio = AudioSegment.from_file(file_path)  # fallback for video files
        
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(audio_path, format="wav")
        return audio_path
    except Exception as e:
        raise Exception(f"Audio extraction failed: {e}")

def chunk_audio(audio_path, chunk_length_ms=30000):
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        fd, chunk_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        audio[i:i+chunk_length_ms].export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def transcribe_audio(audio_path):
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_sphinx(audio_data)
    except:
        return ""

def summarize_text(text, chunk_size=500):
    # return plain transcript since summarizer is commented
    return text

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
    
    summary = summarize_text(transcript)
    
    # Safe empty JSON output for Gradio
    entities = {"entities": []}

    return summary, entities

iface = gr.Interface(
    fn=summarize_meeting,
    inputs=gr.File(label="Upload Audio/Video", type="filepath"),
    outputs=[gr.Textbox(label="Summary"), gr.JSON(label="Entities", type="auto")],
    title="Meeting Summarizer",
    description="Upload audio/video (<100 MB) to get a summary and extracted entities."
)

if __name__ == "__main__":
    # Use PORT from Render automatically, no share needed
    iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 8080)))
