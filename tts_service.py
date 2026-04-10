import os
import re
import wave
import io
import threading

PIPER_MODEL_PATH = '/workspaces/codespaces-blank/en_US-lessac-medium.onnx'

piper_available = False
piper_voice = None
_lock = threading.Lock()

def init_piper():
    global piper_available, piper_voice
    try:
        if os.path.exists(PIPER_MODEL_PATH):
            from piper.voice import PiperVoice
            with _lock:
                piper_voice = PiperVoice.load(PIPER_MODEL_PATH)
            piper_available = True
            print(f"Piper TTS loaded: {PIPER_MODEL_PATH}")
    except Exception as e:
        print(f"Piper TTS init failed: {e}")

init_piper()

def synthesize_streaming(text):
    if not piper_available or not piper_voice:
        return None
    
    try:
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = cleaned_text[:2000]
        
        if not cleaned_text:
            return None
        
        audio_chunks = piper_voice.synthesize(cleaned_text)
        
        sample_rate = 22050
        is_first_chunk = True
        
        for chunk in audio_chunks:
            sample_rate = chunk.sample_rate
            audio_array = chunk.audio_float_array
            int16_array = (audio_array * 32767).astype('int16')
            wav_bytes = int16_array.tobytes()
            
            if is_first_chunk:
                header = create_wav_header(len(wav_bytes), sample_rate)
                yield header
                is_first_chunk = False
            
            yield wav_bytes
        
    except Exception as e:
        print(f"TTS stream error: {e}")
        return None

def create_wav_header(data_size, sample_rate):
    with io.BytesIO() as buf:
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.setnframes(data_size)
            header = buf.getvalue()
    return header

def generate_tts_audio(text):
    if not piper_available or not piper_voice:
        return None
    
    try:
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        cleaned_text = cleaned_text[:2000]
        
        if not cleaned_text:
            return None
        
        with _lock:
            audio_chunks = list(piper_voice.synthesize(cleaned_text))
        
        if not audio_chunks:
            return None
        
        sample_rate = audio_chunks[0].sample_rate
        
        wav_data = b''
        for chunk in audio_chunks:
            audio_array = chunk.audio_float_array
            int16_array = (audio_array * 32767).astype('int16')
            wav_data += int16_array.tobytes()
        
        return wav_data, sample_rate
    except Exception as e:
        print(f"TTS error: {e}")
        return None