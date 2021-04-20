import time
import requests
import json
import tqdm

from pprint import pprint
from datetime import datetime
from hashlib import md5

from tokens import ya_token, vk_token, vk_service_token
import ok_tokens

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
            photo_date = datetime.utcfromtimestamp(photo['date']).strftime('%Y-%m-%d_%H.%M.%S')
            output += [(photo_date, photo_url, photo['likes']['count'], photo_size)]
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
        return requests.get(self.apiurl + 'photos.getAlbums', album_params).json()['response']['items']

    def get_user_id(self, username):
        params = {
            **self.params,
            'user_ids': username
        }
        return requests.get(self.apiurl + 'users.get', params).json()['response'][0]['id']

class OkAPI:
    apiurl = 'https://api.ok.ru/fb.do'

    def __init__(self):
        self.params = {
            'application_key': ok_tokens.pub_key,
            'format': 'json',
            'access_token': ok_tokens.access_token,
        }
        sig = md5(f'application_key={ok_tokens.pub_key}format=jsonmethod=users.getCurrentUser{ok_tokens.session_secret_key}'.encode()).hexdigest()
        user_params = {
            **self.params,
            'method': 'users.getCurrentUser',
            'sig': sig
        }
        response = requests.get(self.apiurl, user_params)
        self.uid = response.json()['uid']


    def get_photos_list(self, album_id = None):
        fields = 'user_photo.PIC_MAX,user_photo.LIKE_COUNT,user_photo.CREATED_MS'
        self.params.update({
            'fields': fields,
            'method': 'photos.getPhotos',
        })
        if album_id != None:
            sig = md5(
                f'aid={album_id}application_key={ok_tokens.pub_key}fields={fields}format=jsonmethod=photos.getPhotos{ok_tokens.session_secret_key}'.encode()).hexdigest()
            self.params.update({
                'aid': album_id,
                'sig': sig
            })
        else:
            sig = md5(f'application_key={ok_tokens.pub_key}fields={fields}format=jsonmethod=photos.getPhotos{ok_tokens.session_secret_key}'.encode()).hexdigest()
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
        sig = md5(
            f'application_key={ok_tokens.pub_key}format=jsonmethod=photos.getAlbums{ok_tokens.session_secret_key}'.encode()).hexdigest()
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

def get_photos_vk():

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
    return photos_list, owner_id, album_title

def get_photos_ok():

    print('Получаем данные из ok...')

    ok = OkAPI()


    album_id_input = input('Enter для Личных фото или введите что угодно для просмотра списка альбомов: ')
    album_id = None
    album_title = 'Личные фото'

    if album_id_input:
        user_albums = ok.get_albums()
        if len(user_albums) > 0:
            albums_dict = {}
            for album_id, album_title in user_albums:
                albums_dict.update({album_id: album_title})
                print(f"id: {album_id}, Название: {album_title}")
            album_id = input('Введите id альбома: ')
            album_title = albums_dict[album_id]
        else:
            print('Нет альбомов, возьмем личные')

    photos_list = ok.get_photos_list(album_id)
    print(f'Всего фотографий в альбоме: {len(photos_list)}.')

    number_of_photos_input = input('Сколько фотографий грузить? (По умолчанию - 5): ')
    if number_of_photos_input:
        number_of_photos = int(number_of_photos_input)
    else:
        number_of_photos = 5
    photos_list = photos_list[:number_of_photos]
    return photos_list, 'ok photos', album_title

def upload_to_ya(photos_list, owner_id, album_title):
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

commands = {
    'ok': get_photos_ok,
    'vk': get_photos_vk
}

#upload_to_ya(*get_photos_vk())

command = input('ok or vk? ')
if command in commands:
    pprint(commands[command]())
