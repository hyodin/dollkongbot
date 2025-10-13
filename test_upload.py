import requests
import os

# 테스트 파일 업로드
url = "http://127.0.0.1:8000/api/upload-sync"
file_path = "test.txt"

try:
    with open(file_path, 'rb') as f:
        files = {'file': ('test.txt', f, 'text/plain')}
        response = requests.post(url, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")

