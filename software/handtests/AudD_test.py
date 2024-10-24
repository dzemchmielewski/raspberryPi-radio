import requests
import json

url = "https://api.audd.io/?api_token=test"
file_path = "clip.mp3"
file_path = "../clips/clip-2024-04-13 01:00:49.083418.mp3"

try:

    with open(file_path, "rb") as f:
        r = requests.post(url, files={'file': f})

    print("ROW: " + r.text)
    response = json.loads(r.text)

    print("Status: " + response["status"])
    print("Artist: " + response["result"]["artist"])
    print("Title: " + response["result"]["title"])
    print("Album: " + response["result"]["album"])
    print("Release: " + response["result"]["release_date"])


except FileNotFoundError:
    print("The file was not found.")
except requests.exceptions.RequestException as e:
    print("There was an exception that occurred while handling your request.", e)
