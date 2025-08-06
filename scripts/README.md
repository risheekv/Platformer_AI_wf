# LLM API Integration

This project integrates with a secure LLM API using Apigee authentication. To use the Ask AI feature, set the following environment variables (e.g., in a `.env` file):

- APIGEE_CONSUMER_KEY
- APIGEE_CONSUMER_SECRET
- GENAI_API_KEY
- GENAI_CLIENT_ID
- (Optional) APIGEE_OAUTH_URL, LLM_API_URL, GENAI_USECASE_ID, GENAI_MODEL

You can use [python-dotenv](https://pypi.org/project/python-dotenv/) to load these automatically from a `.env` file during local development. Example `.env`:

```
APIGEE_CONSUMER_KEY=your_key
APIGEE_CONSUMER_SECRET=your_secret
GENAI_API_KEY=your_genai_key
GENAI_CLIENT_ID=your_client_id
```

Install dependencies:
```
pip install -r requirements.txt
```

See `scripts/llm_client.py` for implementation details.

# Platformer AI Game - AI API Integration

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set required environment variables:**

You can store your secret keys and API credentials in `scripts/secrets.env`:

```
APIGEE_CONSUMER_KEY=your_apigee_consumer_key
APIGEE_CONSUMER_SECRET=your_apigee_consumer_secret
GENAI_API_KEY=your_genai_api_key
GENAI_CLIENT_ID=your_genai_client_id
```

This file is already listed in `.gitignore` and will not be committed to version control.

**Recommended:** Install `python-dotenv` and add this to the top of your main script to load secrets automatically:

```python
from dotenv import load_dotenv
load_dotenv('scripts/secrets.env')
```

Or, you can export the variables manually in your shell as before.

3. **Run the game:**

```bash
python scripts/main.py
```

## How it works

- When you click the "Ask AI" button during a question, the game will send the question to the LLM API and display the answer as a hint/explanation.
- If the API call fails, an error message will be shown.

## Notes
- Make sure you have a working internet connection for the API calls.
- The API endpoints and model can be customized in `scripts/ai_api.py` if needed.
- Keep your `scripts/secrets.env` file safe and never commit it to version control. 