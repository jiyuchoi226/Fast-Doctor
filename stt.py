import openai
openai.api_key="Your API key"

def stt(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcriptions = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ko"
        )
        return transcriptions.text

