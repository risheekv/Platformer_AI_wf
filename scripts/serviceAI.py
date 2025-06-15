import json
import requests
import time
import os
from pathlib import Path

class serviceAIService:
    def __init__(self):
        self.config = self._load_config()
        self.oauth_token = None
        self.token_expiry = 0
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            config_path = Path(__file__).parent / 'serviceAI_config.json'
            with open(config_path, 'r') as f:
                return json.load(f)['services']
        except Exception as e:
            raise ValueError(f"Failed to load serviceAI configuration: {str(e)}")

    def _get_oauth_token(self):
        """Get OAuth token from risheek with caching"""
        current_time = time.time()
        
        # Return existing token if it's still valid (with 5-minute buffer)
        if self.oauth_token and current_time < self.token_expiry - 300:
            return self.oauth_token

        try:
            auth = (
                self.config['risheek']['consumer']['key'],
                self.config['risheek']['consumer']['secret']
            )
            
            response = requests.post(
                self.config['risheek']['oauth-url'],
                auth=auth,
                data={'grant_type': 'client_credentials'},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10  # 10 second timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get OAuth token: {response.text}")

            token_data = response.json()
            self.oauth_token = token_data['access_token']
            self.token_expiry = current_time + token_data.get('expires_in', 3600)
            
            return self.oauth_token

        except requests.exceptions.Timeout:
            raise Exception("OAuth token request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get OAuth token: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting OAuth token: {str(e)}")

    def get_completion(self, messages, max_tokens=None):
        """Get completion from serviceAI service"""
        try:
            # Get fresh OAuth token
            token = self._get_oauth_token()
            
            # Prepare headers with OAuth token and required headers
            headers = {
                **self.headers,
                'Authorization': f'Bearer {token}',
                'x-api-key': self.config['serviceAI']['api-key'],
                'x-client-id': self.config['serviceAI']['client-id'],
                'x-usecase-id': self.config['serviceAI']['usecase-id']
            }

            # Prepare request payload
            payload = {
                "model": self.config['serviceAI']['model'],
                "messages": messages,
                "max_tokens": max_tokens or self.config['serviceAI']['max_tokens'],
                "temperature": self.config['serviceAI']['temperature'],
                "top_p": self.config['serviceAI']['top_p'],
                "stubs": self.config['serviceAI']['stubs'].split(',')
            }

            # Make the API call with timeout
            response = requests.post(
                self.config['serviceAI']['chat-svc-endpoint'],
                headers=headers,
                json=payload,
                timeout=30  # 30 second timeout
            )

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting completion: {str(e)}")

    def test_connection(self):
        """Test the connection to serviceAI service"""
        try:
            # Try to get an OAuth token
            self._get_oauth_token()
            
            # Try a simple completion request
            response = self.get_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            return True
        except Exception as e:
            raise Exception(f"Connection test failed: {str(e)}") 