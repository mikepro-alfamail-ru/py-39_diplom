from tokens import vk_token, vk_service_token
from datetime import datetime
import requests


class VkAPI:
    apiurl = 'https://api.vk.com/method/'

    def __init__(self, token=vk_token, version='5.130'):
        self.token = token
        self.version = version
        self.params = {
            'access_token': self.token,
            'v': self.version
        }
        self.owner_id = requests.get(self.apiurl + 'users.get', self.params).json()['response'][0]['id']

    def get_user_photos_list(self, owner_id=None, album_id='wall'):
        if owner_id is None:
            owner_id = self.owner_id
        photo_params = {
            **self.params,
            'owner_id': owner_id,
            'album_id': album_id,
            'extended': 1,
            'count': 1000
        }
        photos_dict = requests.get(self.apiurl + 'photos.get', photo_params).json()

        output = []
        for photo in photos_dict['response']['items']:
            maxsize = 0
            photo_url = ''
            photo_size = ''
            for size in photo['sizes']:
                if maxsize <= size.get('height') + size.get('width'):
                    maxsize = size.get('height') + size.get('width')
                    photo_url = size.get('url')
                    photo_size = size.get('type')
            photo_date = datetime.utcfromtimestamp(photo['date']).strftime('%Y-%m-%d_%H.%M.%S')
            output += [(photo_date, photo_url, photo['likes']['count'], photo_size)]
        return output

    def get_user_albums(self, owner_id=None):
        if owner_id is None:
            owner_id = self.owner_id
        album_params = {
            **self.params,
            'owner_id': owner_id,
            'need_system': 1
        }
        if owner_id == self.owner_id:
            album_params['access_token'] = vk_service_token
        response = requests.get(self.apiurl + 'photos.getAlbums', album_params)
        result = response.json()['response']['items']
        return result

    def get_user_id(self, username):
        params = {
            **self.params,
            'user_ids': username
        }
        return requests.get(self.apiurl + 'users.get', params).json()['response'][0]['id']
