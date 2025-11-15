import logging, os
from dotenv import load_dotenv
load_dotenv()

SPEECH_MODEL = "gpt-4o-mini-transcribe"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("voice-to-image-app")

def transcribe_audio(audio_file) -> str:
    logger.info("Starting audio transcription")
    from openai import OpenAI
    client = OpenAI()
    try:
        audio_bytes = audio_file.read()
        audio_file.seek(0)

        transcript = client.audio.transcriptions.create(
            model=SPEECH_MODEL,
            file=("audio.wav", audio_bytes),
        )
        text = transcript.text.strip()
        logger.info("Transcription completed successfully")
        return text
    except Exception as e:
        logger.exception("Error during transcription: %s", e)
        raise
