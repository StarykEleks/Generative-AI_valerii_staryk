import logging
from io import BytesIO

import streamlit as st
from PIL import Image

from audio import transcribe_audio
from image import generate_image, generate_image_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("voice-to-image-app")

def main():
    st.set_page_config(
        page_title="Voice to Image App",
        layout="wide",
    )

    st.title("🎙️ Voice to Image App")
    st.write(
        "Speak your idea – the agent will transcribe your voice, turn it into "
        "an image description with an LLM, and generate an image for you."
    )

    st.markdown("---")
    st.markdown("### OpenAI status")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("1️⃣ Voice input")

        audio_file = st.audio_input("🎤 Record your voice message")

        if audio_file is not None:
            st.audio(audio_file, format="audio/wav")
            st.info("Audio file uploaded. Click **Generate image** to continue.")

        generate_button = st.button(
            "✨ Generate image",
            type="primary",
            disabled=audio_file is None,
        )

    with col_right:
        st.subheader("2️⃣ Result & intermediate data")
        transcript_placeholder = st.empty()
        prompt_placeholder = st.empty()
        image_placeholder = st.empty()

    if generate_button and audio_file is not None:
        logger.info("=== New request started ===")

        with st.spinner("Transcribing your voice..."):
            try:
                transcript = transcribe_audio(audio_file)
                transcript_placeholder.markdown(
                    f"**Transcript:**\n\n> {transcript}"
                )
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                return

        with st.spinner("Converting transcript to image prompt..."):
            try:
                img_prompt = generate_image_prompt(transcript)
                prompt_placeholder.markdown(
                    "**Image generation prompt:**\n\n"
                    f"```text\n{img_prompt}\n```"
                )
            except Exception as e:
                st.error(f"Image prompt generation failed: {e}")
                return

        with st.spinner("Generating image..."):
            try:
                image_bytes = generate_image(img_prompt)
            except Exception as e:
                st.error(f"Image generation failed: {e}")
                return

        try:
            image = Image.open(BytesIO(image_bytes))
            image_placeholder.image(
                image,
                caption="Generated image",
            )
            st.success("Done! Scroll up to see all intermediate steps.")
        except Exception as e:
            logger.exception("Error displaying image: %s", e)
            st.error(f"Could not display image: {e}")

        logger.info("=== Request finished ===")


if __name__ == "__main__":
    main()
