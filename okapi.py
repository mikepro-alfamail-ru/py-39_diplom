import requests
from datetime import datetime
from hashlib import md5

import ok_tokens


class OkAPI:
    apiurl = 'https://api.ok.ru/fb.do'

    def __init__(self):
        self.params = {
            'application_key': ok_tokens.pub_key,
            'format': 'json',
            'access_token': ok_tokens.access_token,
        }
        sig = md5(f'application_key={ok_tokens.pub_key}format=jsonmethod=users.getCurrentUser'
                  '{ok_tokens.session_secret_key}'.encode()).hexdigest()
        user_params = {
            **self.params,
            'method': 'users.getCurrentUser',
            'sig': sig
        }
        response = requests.get(self.apiurl, user_params)
        self.uid = response.json()['uid']

    def get_photos_list(self, album_id=None):
        fields = 'user_photo.PIC_MAX,user_photo.LIKE_COUNT,user_photo.CREATED_MS'
        self.params.update({
            'fields': fields,
            'method': 'photos.getPhotos',
        })
        if album_id is not None:
            sig = md5(f'aid={album_id}application_key={ok_tokens.pub_key}fields={fields}'
                      'format=jsonmethod=photos.getPhotos'
                      '{ok_tokens.session_secret_key}'.encode()).hexdigest()
            self.params.update({
                'aid': album_id,
                'sig': sig
            })
        else:
            sig = md5(f'application_key={ok_tokens.pub_key}fields={fields}format=jsonmethod=photos.getPhotos'
                      '{ok_tokens.session_secret_key}'.encode()).hexdigest()
            self.params.update({
                'sig': sig,
            })
        response = requests.get(self.apiurl, self.params)
        response_dict = response.json()
        if response_dict.get('error_code'):
            return 'Error', response_dict.get('error_code')
        else:
            output = []

            for photo in response_dict.get('photos'):
                photo_date = datetime.utcfromtimestamp(photo['created_ms'] // 1000).strftime('%Y-%m-%d_%H.%M.%S')
                output += [(photo_date, photo['pic_max'], photo['like_count'], 'max')]
            return output

    def get_albums(self):
        sig = md5(f'application_key={ok_tokens.pub_key}format=jsonmethod=photos.getAlbums'
                  '{ok_tokens.session_secret_key}'.encode()).hexdigest()
        self.params.update({
            'method': 'photos.getAlbums',
            'sig': sig
        })
        response = requests.get(self.apiurl, self.params)
        response_dict = response.json()

        if response_dict.get('error_code'):
            return 'Error', response_dict.get('error_code')
        else:
            output = []
            for album in response_dict.get('albums'):
                output += [
                    (album['aid'], album['title'])
                ]
            return output
