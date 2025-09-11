import gradio as gr
import whisper
from transformers import pipeline
from pydub import AudioSegment
import os
import tempfile

# Load models
whisper_model = whisper.load_model("tiny")  # tiny for speed
# summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
# ner = pipeline("ner", aggregation_strategy="simple", grouped_entities=True)

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
        result = whisper_model.transcribe(audio_path, fp16=False, language='en')
        return result.get("text", "")
    except:
        return ""

def summarize_text(text, chunk_size=500):
    if not text.strip():
        return "Error: No transcribable audio detected."
    
    words = text.split()
    if len(words) <= chunk_size:
        return summarizer(text, max_length=150, min_length=40, do_sample=False)[0]["summary_text"]
    
    summaries = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        try:
            summaries.append(summarizer(chunk, max_length=150, min_length=40, do_sample=False)[0]["summary_text"])
        except:
            summaries.append(" ".join(chunk.split()[:50]) + "...")
    
    combined = " ".join(summaries)
    try:
        final_summary = summarizer(combined, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
    except:
        final_summary = combined[:500] + "..."
    return final_summary

def summarize_meeting(file):
    if os.path.getsize(file) > 100 * 1024 * 1024:
        return "Error: File too large. Upload <100 MB.", {}
    
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
    
    try:
        entities = ner(transcript[:1000]) if transcript.strip() else []
    except:
        entities = []

    return summary, entities

iface = gr.Interface(
    fn=summarize_meeting,
    inputs=gr.File(label="Upload Audio/Video", type="filepath"),
    outputs=[gr.Textbox(label="Summary"), gr.JSON(label="Entities")],
    title="Meeting Summarizer",
    description="Upload audio/video (<100 MB) to get a summary and extracted entities."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 8080)), share=False)
