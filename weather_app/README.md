# Weather via OpenAI + Streamlit

A lightweight Streamlit app that asks the OpenAI API for a concise weather update based on the user's location.

## Setup
1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

## Running the app
Launch the Streamlit server from the project root:
```bash
streamlit run app.py
```

The app will prompt for your location (city and country recommended), send the request to OpenAI, and display a friendly weather summary along with structured details.
