import requests
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'}
resp = requests.get('https://baidu.com',headers = headers)
resp.encoding = 'utf-8'
if resp.status_code == 200:
    print(resp.text)




