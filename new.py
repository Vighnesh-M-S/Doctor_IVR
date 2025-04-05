import requests
import os
from dotenv import load_dotenv


load_dotenv()

def download_twilio_audio(url, account_sid, auth_token, output_filename="audio2.wav"):
    """Downloads an audio file from a Twilio URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Audio downloaded successfully to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading audio: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
twilio_url = "https://api.twilio.com/2010-04-01/Accounts/ACd732e6a1635e6225b8d0b6dd69cdc4e5/Recordings/REec48a4f7c64367701f9319833eab1dc3"
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

download_twilio_audio(twilio_url, account_sid, auth_token)