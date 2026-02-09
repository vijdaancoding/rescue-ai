import os 
from dotenv import load_dotenv
from flask import Flask
from livekit import api

load_dotenv(".env")

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

app = Flask(__name__)

@app.route('/getToken')
def getToken():
  token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
    .with_identity("identity") \
    .with_name("hackweek") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room="rescue_ai",
    ))
  return token.to_jwt()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

