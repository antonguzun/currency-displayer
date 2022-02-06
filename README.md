# currency-displayer

### Запуск тестов в контейнерах:
```
make run_tests
```

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
### Создание контейнера приложения
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
#### Трогаем вебсокет используя websocat или postman:
Получить список пар
```shell
websocat ws://0.0.0.0:8000/
{"action":"assets","message":{}}

{"action": "assets", "message": {"assets": [{"id": 1, "name": "EURUSD"}, {"id": 2, "name": "USDJPY"}, {"id": 3, "name": "GBPUSD"}, {"id": 4, "name": "AUDUSD"}, {"id": 5, "name": "USDCAD"}]}}
```
Подписаться на конкретную пару
```shell
websocat ws://0.0.0.0:8000/
{"action":"subscribe","message":{"assetId":2}}

{"action": "asset_history", "message": {"message": {"points": [{"id": 5, "assetName": "USDJPY", "assetId": 2, "value": 115.2, "time": 1644161201}, {"id": 10, "assetName": "USDJPY", "assetId": 2, "value": 115.2, "time": 1644161206}]}}}
{"action": "point", "message": {"id": 1445, "assetName": "USDJPY", "assetId": 2, "value": 115.2, "time": 1644162325}}
{"action": "point", "message": {"id": 1450, "assetName": "USDJPY", "assetId": 2, "value": 115.2, "time": 1644162327}}
{"action": "point", "message": {"id": 1455, "assetName": "USDJPY", "assetId": 2, "value": 115.2, "time": 1644162328}}

// подписаться на другую
{"action":"subscribe","message":{"assetId":3}}

{"action": "asset_history", "message": {"message": {"points": [{"id": 6, "assetName": "GBPUSD", "assetId": 3, "value": 1.353535, "time": 1644161201}, {"id": 11, "assetName": "GBPUSD", "assetId": 3, "value": 1.353535, "time": 1644161206}]}}}
{"action": "point", "message": {"id": 1496, "assetName": "GBPUSD", "assetId": 3, "value": 1.353535, "time": 1644162338}}
{"action": "point", "message": {"id": 1501, "assetName": "GBPUSD", "assetId": 3, "value": 1.353535, "time": 1644162339}}
{"action": "point", "message": {"id": 1506, "assetName": "GBPUSD", "assetId": 3, "value": 1.353535, "time": 1644162340}}
```
