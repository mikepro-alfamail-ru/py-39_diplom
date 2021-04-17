import time

import requests
import json
import tqdm
from tokens import ya_token, vk_token, vk_service_token
ROOTDIR = 'diplomupload'

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
        if owner_id == None:
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
            for size in photo['sizes']:
                if maxsize < size.get('height') + size.get('width'):
                    maxsize = size.get('height') + size.get('width')
                    photo_url = size.get('url')
                    photo_size = size.get('type')
            output += [(photo['id'], photo_url, photo['likes']['count'], photo_size)]
        return output

    def get_user_albums(self, owner_id=None):
        if owner_id == None:
            owner_id = self.owner_id
        album_params = {
            **self.params,
            'owner_id': owner_id,
            'need_system': 1
        }
        if owner_id == self.owner_id:
            album_params['access_token'] = vk_service_token
        print(album_params)
        print(requests.get(self.apiurl + 'photos.getAlbums', album_params).json())
        return requests.get(self.apiurl + 'photos.getAlbums', album_params).json()['response']['items']

    def get_user_id(self, username):
        params = {
            **self.params,
            'user_ids': username
        }
        return requests.get(self.apiurl + 'users.get', params).json()['response'][0]['id']

def main():

    print('Получаем данные из vk...')

    vk = VkAPI()

    owner_id_input = input('Введите id или короткое имя пользователя или нажмите Enter для личного id: ')
    owner_id = vk.get_user_id(owner_id_input) if owner_id_input else vk.owner_id
    print(f'Пользователь id{owner_id}')

    album_id_input = input('Enter для фото со стены или введите что угодно для просмотра списка альбомов: ')
    album_id = 'wall'
    album_title = 'Стена'

    if album_id_input:
        user_albums = vk.get_user_albums(owner_id)
        if len(user_albums) > 0:
            albums_dict = {}
            for album in user_albums:
                if str(album['id']) != '-9000':
                    albums_dict.update({str(album['id']): album['title']})
                    print(f"id: {album['id']}, Название: {album['title']}")
            album_id = input('Введите id альбома: ')
            album_title = albums_dict[album_id] if album_id != '-7' else 'Стена'
        else:
            print('Нет альбомов, возьмем со стены')

    photos_list = vk.get_user_photos_list(owner_id, album_id)
    print(f'Всего фотографий в альбоме: {len(photos_list)}.')

    number_of_photos_input = input('Сколько фотографий грузить? (По умолчанию - 5): ')
    if number_of_photos_input:
        number_of_photos = int(number_of_photos_input)
    else:
        number_of_photos = 5
    photos_list = photos_list[:number_of_photos]

    ya_token_input = input('Введите токен с полигона Яндекса: ')
    if ya_token_input:
        uploader = YaUploader(ya_token_input)
    else:
        uploader = YaUploader()

    path = f'/{ROOTDIR}/{owner_id}/{album_title}'
    temp_path = ''
    print()

    print('Проверка пути на диске, создание папок...')
    for folder in tqdm.tqdm(path.split('/'), bar_format='{l_bar}{bar}|'):
        temp_path += folder + '/'
        uploader.check_path(temp_path)
    print()

    print('Загружаем...')
    time.sleep(0.1)

    log = []
    for photo_id, photo_url, likes_count, photo_size in tqdm.tqdm(photos_list):
        filename = f'{likes_count}_likes_{photo_id}.jpg'

        upload_url = uploader.get_upload_url(path=path, file=filename)
        upload_result = uploader.upload(requests.get(photo_url).content, upload_url)

        if upload_result != 201:
            print(f'Ошибка на стороне яндекса, файл с id {photo_id} не загружен: {upload_result}')
        else:
            log.append(
                {
                    'filename': filename,
                    'size': photo_size
                }
            )

    with open('log.json', 'w', encoding='utf8') as logfile:
        json.dump(log, logfile, indent=4, ensure_ascii=False)

main()