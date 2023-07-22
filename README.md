# Sputnik_secrets

Сервис хранения секретов (Restful).

## Swagger по адресу: /docs

## Локальный запуск:

- #### venv c python 3.11
- #### ```>> pip install --upgrade pip```  
- #### ```>> pip install -r requirements.txt --no-dependencies```
- #### mark path ``src`` как source root в вашей IDE (или ``>>cd /src``)
- #### ``.local.env`` - пишем креды для БД (и прочее - соль, секреты)
- #### ``python app.py`` - локальный запуск

## Tесты:
### ` >> pytest -v -tests ` (покрыто на 88%)

## Для запуска в докере используйте докерфайлы dockers/build
#### Образ приложения в docker hub - ``iburhanov/secrets1440:latest``

#### Запуск демона: `docker-compose -f dockers\build\docker-compose.yaml up -d`
