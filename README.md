
# Дипломный проект "Резервное копирование"

## Пока реализовано:

1. Получать фотографии с профиля. Для этого нужно использовать метод [photos.get](https://vk.com/dev/photos.get).
2. Сохранять фотографии максимального размера(ширина/высота в пикселях) на Я.Диске.
3. Для имени фотографий использовать количество лайков. 
4. Сохранять информацию по фотографиям в json-файл с результатами. 

### Входные данные:
Пользователь вводит:
1. id пользователя vk;
2. токен с [Полигона Яндекс.Диска](https://yandex.ru/dev/disk/poligon/).
*Важно:* Токен публиковать в github не нужно!

### Выходные данные:
1. json-файл с информацией по файлу:
```javascript
    [{
    "file_name": "34.jpg",
    "size": "z"
    }]
```
2. Измененный Я.диск, куда добавились фотографии.

## Дополнительно реализовано:
1. Просмотр списка альбомов и выбор нужного по айди
2. Выбор количества фотографий для выгрузки
3. Поддержка Ok API, загрузка фото и просмотр списка альбомов
