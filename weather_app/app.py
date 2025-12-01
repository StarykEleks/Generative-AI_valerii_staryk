import json
import os
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()


def fetch_weather(location: str) -> Dict[str, Any]:
    """Request a weather summary for the provided location via the OpenAI API."""
    if not location or not location.strip():
        raise ValueError("Please provide a location to look up.")

    completion = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a weather specialist. Estimate current weather conditions "
                    "for the provided location. Respond as JSON with keys: summary (string), "
                    "temperature_c (number), conditions (list of strings), humidity (integer percent), "
                    "wind_kph (number), and advice (string). Keep numbers realistic and avoid fabrication "
                    "of exact times or sources."
                ),
            },
            {
                "role": "user",
                "content": f"Share the current weather for {location} in concise terms.",
            },
        ],
    )

    content = completion.choices[0].message.content
    return json.loads(content)


def render_weather(data: Dict[str, Any]) -> None:
    st.subheader(data.get("summary", "Weather update"))
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature", f"{data.get('temperature_c', '?')} °C")
    col2.metric("Humidity", f"{data.get('humidity', '?')}%")
    col3.metric("Wind", f"{data.get('wind_kph', '?')} kph")

    conditions = data.get("conditions")
    if isinstance(conditions, list):
        st.write("**Conditions:** " + ", ".join(str(c) for c in conditions))

    advice = data.get("advice")
    if advice:
        st.info(advice)


st.set_page_config(page_title="AI Weather", page_icon="⛅")
st.title("AI-Powered Weather")
st.write(
    "Enter your city (and country for clarity). The app uses the OpenAI API to craft a "
    "current weather briefing."
)

with st.form("weather_form"):
    location = st.text_input("Location", placeholder="e.g., Copenhagen, Denmark")
    submit = st.form_submit_button("Get weather")

if submit:
    try:
        with st.spinner("Contacting OpenAI..."):
            weather_data = fetch_weather(location)
        st.success("Here is your weather update:")
        render_weather(weather_data)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Couldn't fetch the weather right now: {exc}")
