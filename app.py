import gradio as gr                     # For UI / deployment
import whisper                          # For speech-to-text
from transformers import pipeline       # For summarization and NER
from pydub import AudioSegment          # For audio/video processing
import speech_recognition as sr         # Fallback for transcription
import os

# Use smaller Whisper model for faster inference on free GPU
whisper_model = whisper.load_model("small")  

# Summarizer and NER pipelines
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
ner = pipeline("ner")

def extract_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    audio_path = "temp_audio.wav"
    audio.export(audio_path, format="wav")
    return audio_path

def chunk_audio(audio_path, chunk_length_ms=60000):  # 1 minute chunks
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk_path = f"chunk_{i}.wav"
        audio[i:i+chunk_length_ms].export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def transcribe_audio(audio_path):
    try:
        result = whisper_model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data)

def summarize_meeting(file):
    # 1. Extract audio
    audio_path = extract_audio(file.name)
    
    # 2. Chunk audio
    chunks = chunk_audio(audio_path)
    
    # 3. Transcribe each chunk
    transcript = ""
    for c in chunks:
        transcript += transcribe_audio(c) + " "
    
    # 4. Summarize transcript
    summary = summarizer(transcript, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
    
    # 5. Extract entities
    entities = ner(transcript)
    
    return summary, entities

iface = gr.Interface(
    fn=summarize_meeting,
    inputs=gr.File(label="Upload Audio/Video"),
    outputs=[gr.Textbox(label="Summary"), gr.JSON(label="Entities")],
    title="Meeting Summarizer"
)

iface.launch()
