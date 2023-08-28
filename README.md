# Foodgram

## Описание проекта

Проект был создан в рамках прохождения курса Яндекс Практикума.
Foodgram позволяет пользователям создавать свои рецепты, подписываться на других авторов и многое другое.

## Технологии

* Django REST
* Nginx
* Docker
* Ginicorn
* PostgreSGL

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone git@github.com:YanaYugai/foodgram-project-react.git
cd foodgram
```

Прописать все необходимые переменные в .env:

Переменные, которые вам понадобятся:
1. POSTGRES_USER
2. POSTGRES_PASSWORD
3. POSTGRES_DB
4. DB_HOST
5. DB_PORT
6. SECRET_KEY(авттоматически генерируется, можно найти в настройках)
7. DEBUG
8. ALLOWED_HOSTS

Зайдите в свой удаленный сервер.

Создадите директорию foodgram:

```bash
cd
mkdir foodgram
```
На локальном компьютере с помощью утилиты SCP скопируйте файлы .env и
docker-compose.production.yml

```bash
scp -i path_to_SSH/SSH_name docker-compose.production.yml \
username@server_ip:/home/username/taski/docker-compose.production.yml
scp -i path_to_SSH/SSH_name .env\
username@server_ip:/home/username/foodgram/.env
```

Установите Docker Compose на сервере:

```bash
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
```

Запустите все контейнеры:

```bash
sudo docker compose -f docker-compose.production.yml up -d
```
Выполните миграции и соберите всю статику:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

Устанавливаем и настраиваем Nginx на удаленный серевер:

```bash
# Установка и запуск Nginx
sudo apt install nginx -y
sudo systemctl start nginx
# Настраиваем файрвол ufw
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
# Включаем ufw
sudo ufw enable
```
Настраиваем конфигурационный файл Nginx:

```
server {
  listen 80;
  server_name your_registred_domain_name.com;

  location / {
    proxy_set_header Host $http_host;
    proxy_pass http://127.0.0.1:8001;
  }
```
Проверяем конфигурационный файл и перезапускаем Nginx:

```
sudo nginx -t
sudo systemctl start nginx
```

Устанавливаем пакет certbot для установки SSL-сертификата:

```bash
# Устанавливаем пакетнрый менеджер snap
sudo apt install snapd
# Установка и обновление зависимостей для пакетного менеджера snap.
sudo snap install core; sudo snap refresh core
# Установка пакета certbot.
sudo snap install --classic certbot
# Создание ссылки на certbot в системной директории,
# чтобы у пользователя с правами администратора был доступ к этому пакету.
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```
Запускаем certbot и получbnt SSL-сертификат:

```bash
sudo certbot --nginx
```

Перезагрузите Nginx:

```bash
sudo systemctl reload nginx 
```

## Примеры запросов

Вся документация проекта представлена https://foodgramyana.hopto.org/api/docs/

## Автор

YanaYugai(https://github.com/YanaYugai)