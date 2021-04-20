import requests
import json
from tokens import ya_token


class YaUploader:
    apiurl = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, token=ya_token):
        self.token = token
        self.auth = {
            'Authorization': f'OAuth {self.token}'
        }

    def get_upload_url(self, path, file):
        params = {
            'path': f'{path}/{file}',
            'overwrite': 'true'
        }
        response = requests.get(self.apiurl, params=params, headers=self.auth)
        result = json.loads(response.text)
        return result.get('href')

    def check_path(self, path):
        params = {
            'path': path
        }
        url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        requests.put(url, params=params, headers=self.auth)

    def upload(self, file, upload_url):
        if upload_url:
            response = requests.put(upload_url, data=file)
            return response.status_code
        else:
            return False
