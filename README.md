# currency-displayer

### Запуск тестов в контейнерах:
```
make run_tests
```

### Если хотим работать локально
#### создаем .env с секретами
#### ставим зависимости:
```
pip install -r requirements.txt
```
#### запускаем базу:
```
make up_local_compose
```
#### проводим мигарции:
```
yoyo apply --database postgres://postgres:dbpass@0.0.0.0:5432/db ./migrations -b
```
#### запуск приложения:
```
uvicorn src.app:create_app --host 0.0.0.0 --port 80
```

### Создание контейнера приложения
#### подготовка окужения:
создаем .env с секретами и поднимаем базу:
```
make up_local_compose
```
#### сборка:
```
docker build -t currency_displayer_image .
```
#### запуск веб-сериса в контейнере:
```
docker run \
    --name currency_displayer \
    --env-file .env \
    -p 8000:8000 \
    --network currency-displayer_custom \
    currency_displayer_image 
```

#### Проверяем работу:
```shell
curl 0.0.0.0:8000/ping
```
#### Трогаем вебсокет:
```shell
```
