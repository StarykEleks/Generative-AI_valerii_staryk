# 🎙️ Voice to Image App

Voice to Image App is a simple demo agent that:

1. Takes a **short voice message** as input.
2. Uses an **LLM speech model** to **transcribe** the audio.
3. Uses an **LLM (chat model)** to convert the transcript into a **detailed image description**.
4. Sends that description to an **image generation model**.
5. Shows the **generated image** and **all intermediate data** (transcript, image prompt, model names) in the UI.
6. Prints **logs to the console** for debugging and homework demonstration.

The app is built in **Python** with a **Streamlit UI**.

---

## ✅ Requirements from the task

- Agent should take a short voice message as an input ✅
- LLM should convert user request to image description ✅
- Image model generates the picture and gives it back to the user ✅
- UI shows:
  - recorded message (audio player) ✅
  - transcript ✅
  - prompt for image generator ✅
  - models used ✅
- Agent prints logs to the console ✅
- Code in Python ✅
- UI built with Streamlit ✅
- Instructions in README with screenshots ✅ (see below)

---

## 🧱 Tech Stack

- **Python 3.10+**
- **Streamlit** – UI
- **OpenAI Python SDK** – speech-to-text, LLM, image generation (optional; can run in mock mode)
- **Pillow** – working with images

---

## 📦 Installation

1. **Clone the repository** and make sure you’re on the `main` (or `master`) branch:

   ```bash
   git clone <your-repo-url>.git
   cd <your-repo-folder>
   git checkout main   # or master
