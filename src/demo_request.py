from dotenv import load_dotenv
import os
import requests

load_dotenv()

TOKEN = os.getenv("TMDB_API_KEY")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.themoviedb.org/3/movie/popular",
    headers=headers,
    params={"language": "en-US", "page": 1}
)

print(f"Status: {response.status_code}")
print(f"Movie แรก: {response.json()['results'][0]['title']}")