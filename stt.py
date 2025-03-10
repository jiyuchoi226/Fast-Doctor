import openai
openai.api_key="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"

def stt(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcriptions = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ko"
        )

        if transcriptions.text == "MBC 뉴스 이덕영입니다.":
            transcriptions.text = ""

        return transcriptions.text

