import logging, os
from PIL import Image
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

IMAGE_MODEL = "gpt-image-1"
LLM_MODEL = "gpt-4o-mini"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("voice-to-image-app")

USE_OPENAI = False
client = None

try:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)  # or just OpenAI() if you prefer env
        USE_OPENAI = True
        logger.info("OpenAI client ready")
    else:
        logger.warning("OPENAI_API_KEY is not set. Running in mock mode.")
except Exception as e:
    logger.warning(f"OpenAI not available: {e}")
    client = None
    USE_OPENAI = False

def _pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _placeholder_image() -> bytes:
    img = Image.new("RGB", (512, 512), color=(240, 240, 240))
    return _pil_to_png_bytes(img)


def generate_image(image_prompt: str) -> bytes:
    logger.info("Generating image from prompt")

    # If OpenAI is not configured, immediately return placeholder
    if not USE_OPENAI or client is None:
        logger.warning("OpenAI not configured. Returning placeholder image.")
        return _placeholder_image()

    try:
        img_response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=image_prompt,
            size="1024x1024",
        )

        # Defensive checks so we never end up with None
        if not img_response.data:
            logger.error("Image API returned no data. Using placeholder image.")
            return _placeholder_image()

        image_base64 = getattr(img_response.data[0], "b64_json", None)
        if not image_base64:
            logger.error("Image API returned empty b64_json. Using placeholder image.")
            return _placeholder_image()

        image_bytes = base64.b64decode(image_base64)
        logger.info("Image generated successfully")
        return image_bytes

    except Exception as e:
        logger.exception("Error during image generation: %s", e)
        return _placeholder_image()

def generate_image_prompt(user_text: str) -> str:
    logger.info("Generating image prompt from transcript")

    if not USE_OPENAI or client is None:
        logger.warning("OpenAI not configured. Returning mock image prompt.")
        return (
            "Detailed digital illustration of the described scene, with clear focus on "
            "the main objects, atmosphere and colors."
        )

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You convert short spoken user requests into clear, visual "
                        "image generation prompts. "
                        "Describe the scene, mood, style and key objects in one paragraph."
                    ),
                },
                {
                    "role": "user",
                    "content": f"User voice transcript: {user_text}",
                },
            ],
            temperature=0.7,
        )
        prompt = response.choices[0].message.content.strip()
        logger.info("Image prompt generated successfully")
        return prompt
    except Exception as e:
        logger.exception("Error during image prompt generation: %s", e)
        # Fallback text so the rest of the app still works
        return (
            "A visually rich scene matching the user's description, with clear main "
            "subjects, background details and coherent lighting."
        )
