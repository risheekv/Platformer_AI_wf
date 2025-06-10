import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key is required. Please set the OPENAI_API_KEY environment variable in .env file.")

# Set OpenAI API key
openai.api_key = api_key

def test_model():
    try:
        print("Testing OpenAI API connection...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that provides clear and concise answers to business and finance questions."},
                {"role": "user", "content": "What is one major benefit of leasing equipment instead of buying it?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        print("\nResponse Content:")
        print(response.choices[0].message['content'])
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    test_model() 