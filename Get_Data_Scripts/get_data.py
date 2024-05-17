import requests
import json

# convert json into python dict
def load_json(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

url = "https://129.21.255.22:64297/kibana/api/console/proxy?path=_search&method=GET"

headers = {
    "Content-Length": "413",
    "Authorization": "Basic dHNlYzpeWUhOM2VkYzhpaywhUUFa",
    "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Chromium";v="112"',
    "Content-Type": "application/json",
    "Kbn-Version": "8.6.2",
    "X-Kbn-Context": "%7B%22type%22%3A%22application%22%2C%22name%22%3A%22dev_tools%22%2C%22url%22%3A%22%2Fkibana%2Fapp%2Fdev_tools%22%2C%22page%22%3A%22console%22%7D",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.50 Safari/537.36",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Accept": "*/*",
    "Origin": "https://129.21.255.22:64297",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://129.21.255.22:64297/kibana/app/dev_tools",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9"
}


payload = load_json('query.json')

response = requests.post(url, headers=headers, json=payload, verify=False)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    result = response.json()
    # Process the result as needed
    print(result)

    # and write to a file for further analysis later
    with open('data.json', 'w') as f:
        json.dump(result, f)
else:
    print(f"Request failed with status code: {response.status_code}")
    print(response.text)
