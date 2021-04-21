import time
import requests
import json
import tqdm
from pprint import pprint

from vkapi import VkAPI
from okapi import OkAPI
from yadiskapi import YaUploader

ROOTDIR = 'diplomupload'


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
    friend_id = input('Введите id друга, или просто Enter: ')

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


def upload_to_yadisk(photos_list, owner_id, album_title):
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


def main():
    commands = {
        'ok': get_photos_ok,
        'vk': get_photos_vk
    }

    command = ''
    while command != 'q':
        command = input('ok or vk? ')
        if command in commands:
            pprint(commands[command]())
            # upload_to_yadisk(*commands[command]())


if __name__ == "__main__":
    main()
