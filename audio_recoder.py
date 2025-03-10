import pyaudio
import wave
import time
import struct
import streamlit as st
from stt import stt

class AudioRecorder:
    def __init__(self, filename="output.wav", format=pyaudio.paInt16, channels=1, rate=44100, chunk=1024,
                 silence_threshold=10, silence_timeout=2):
        self.filename = filename
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.silence_threshold = silence_threshold
        self.silence_timeout = silence_timeout
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.silence_time = 0
        self.silence_start_time = None

    def start_recording(self):
        st.markdown("""
                   <style>
                       .st-emotion-cache-ocsh0s {
                           background-color: #FF4B4B;
                       }
                        .st-emotion-cache-ocsh0s:hover {
                            border: 1px solid #FF4B4B;
                       }
                   </style>
               """, unsafe_allow_html=True)
        print("녹음 시작...")
        self.frames = []
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)
        self.recording = True
        self.silence_time = 0
        self.silence_start_time = None
        return self.record_audio()

    def stop_recording(self):
        st.markdown("""
                   <style>
                       .st-emotion-cache-ocsh0s {
                           background-color: #F0F2F6;
                       }
                        .st-emotion-cache-ocsh0s:hover {
                            border: 1px solid #FF4B4B;
                        }
                   </style>
               """, unsafe_allow_html=True)
        if self.recording:
            print("녹음 종료.")
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            if len(self.frames) == 0 or all(self.is_silent(frame) for frame in self.frames):
                print("무음으로만 채워져 파일 저장을 건너뜁니다.")
                return None

            with wave.open(self.filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            print(f"'{self.filename}' 파일로 저장되었습니다.")

            user_input = stt(self.filename)
            print(f"음성 텍스트 변환 결과: {user_input}")
            return user_input

    def is_silent(self, frame):
        audio_data = struct.unpack("<" + "h" * (len(frame) // 2), frame)
        audio_level = max(abs(sample) for sample in audio_data)
        return audio_level < self.silence_threshold

    def record_audio(self):
        while self.recording:
            data = self.stream.read(self.chunk)
            audio_data = struct.unpack("<" + "h" * (len(data) // 2), data)
            audio_level = max(abs(sample) for sample in audio_data)
            print("오디오 레벨:", audio_level)

            if audio_level < self.silence_threshold:
                if self.silence_start_time is None:
                    self.silence_start_time = time.time()

                self.silence_time = time.time() - self.silence_start_time

                if self.silence_time >= self.silence_timeout:
                    print("녹음을 종료합니다.")
                    return self.stop_recording()

            else:
                self.silence_start_time = None
                self.silence_time = 0
            self.frames.append(data)

    def run(self):
        if st.button("🎙️"):
            if not self.recording:
                return self.start_recording()
            else :
                return self.stop_recording()
