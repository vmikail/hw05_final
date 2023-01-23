# Yatube - социальная сеть для публикации личных дневников.

### Описание
Социальная сеть для публикации личных дневников. Реализована пагинация постов и кэширование данных, так же реализована регистрация пользователей с верификацией данных, сменой и восстановлением пароля через почту.
### Технологии
Python 3.8
Django 2.2.19
SQLite
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- В папке с файлом manage.py выполните команду:
- Выполнить migrate
```
python manage.py migrate
```
- Создайте пользователя
```
python manage.py createsuperuser
```
- (или) Сменить пароль для пользователя admin
```
python manage.py changepassword admin
```
- Запуск сервиса
```
python manage.py runserver
```
