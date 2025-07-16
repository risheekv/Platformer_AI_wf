"""
llm_client.py
--------------
Provides LLMClient for secure LLM API access via Apigee authentication.
Requires environment variables for all credentials. See README for details.
"""
import os
import requests
from typing import Optional
import uuid
from datetime import datetime, timezone

class LLMClient:
    """
    Client for authenticating with Apigee and querying the LLM API.
    Handles token management and error handling.
    """
    def __init__(self):
        self.apigee_consumer_key = os.getenv('APIGEE_CONSUMER_KEY')
        self.apigee_consumer_secret = os.getenv('APIGEE_CONSUMER_SECRET')
        self.oauth_url = os.getenv('APIGEE_OAUTH_URL', '')
        self.llm_url = os.getenv('LLM_API_URL', '')
        self.genai_api_key = os.getenv('GENAI_API_KEY')
        self.genai_client_id = os.getenv('GENAI_CLIENT_ID')
        self.usecase_id = os.getenv('GENAI_USECASE_ID', 'GENAI84_PRPLT')
        self.model = os.getenv('GENAI_MODEL', 'gemini-1.5-flash-002')
        self._access_token = None

    def authenticate(self) -> Optional[str]:
        """
        Authenticates with Apigee and retrieves an access token.
        Returns the access token or None if authentication fails.
        """
        try:
            resp = requests.post(
                self.oauth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.apigee_consumer_key,
                    'client_secret': self.apigee_consumer_secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            resp.raise_for_status()
            self._access_token = resp.json().get('access_token')
            return self._access_token
        except Exception as e:
            print(f"[LLMClient] Authentication failed: {e}")
            return None

    def ask(self, question: str) -> Optional[str]:
        """
        Sends a question to the LLM API and returns the answer.
        Returns None if there is an error.
        """
        if not self._access_token:
            if not self.authenticate():
                return None
        now = datetime.now(timezone.utc).isoformat()
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
            'x-wf-client-id': os.getenv('WF_CLIENT_ID', 'PRPLT'),
            'x-wf-usecase-id': os.getenv('WF_USECASE_ID', 'GENAI184_PRPLT'),
            'x-request-id': str(uuid.uuid4()),
            'x-wf-request-date': now,
            'x-wf-api-key': os.getenv('WF_API_KEY', self.genai_api_key),
            'x-correlation-id': str(uuid.uuid4()),
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": question}
            ],
            "top_p": 0,
            "top_k": 1,
            "temperature": 0,
            "max_tokens": 8192
        }
        try:
            resp = requests.post(self.llm_url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 401:
                # Token expired, re-authenticate
                self._access_token = None
                if not self.authenticate():
                    return None
                headers['Authorization'] = f'Bearer {self._access_token}'
                resp = requests.post(self.llm_url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # Adjust this extraction based on actual API response structure
            return data.get('choices', [{}])[0].get('message', {}).get('content')
        except Exception as e:
            print(f"[LLMClient] LLM API call failed: {e}")
            return None

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    client = LLMClient()
    print('APIGEE_OAUTH_URL:', client.oauth_url)
    print('APIGEE_CONSUMER_KEY:', client.apigee_consumer_key)
    print('APIGEE_CONSUMER_SECRET:', client.apigee_consumer_secret)
    data = {
        'grant_type': 'client_credentials',
        'client_id': client.apigee_consumer_key,
        'client_secret': client.apigee_consumer_secret
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    print('Auth Request Data:', data)
    print('Auth Request Headers:', headers)
    try:
        token = client.authenticate()
        print('Access Token:', token)
        if token:
            print('Authentication succeeded.')
        else:
            print('Authentication failed.')
    except Exception as e:
        print('Exception during authentication:', e)
    test_question = "What is the capital of France?"
    print(f"Testing LLM API with question: {test_question}")
    answer = client.ask(test_question)
    if answer:
        print(f"LLM Answer: {answer}")
    else:
        print("Failed to get answer from LLM API.") 