# Практическая работа №4: gRPC (Python + Go), mTLS, nginx

Клиент на Django (Python) бросает «кубик», вызывая метод `RollDie` gRPC-сервера на Go двумя путями:

| Путь | Адрес | Защита |
|---|---|---|
| Клиент → Go-сервер напрямую | `127.0.0.1:8443` | mTLS (сервер проверяет сертификат клиента) |
| Клиент → nginx → Go-сервер | `127.0.0.1:9448` → `127.0.0.1:50051` | mTLS до nginx, дальше h2c |

## Структура

```
certs/            конфиги CFSSL (ca-config.json, *-csr.json)
certs.sh          генерация CA, серверного и клиентского сертификатов
proto/api.proto   описание сервиса DiceService
client/           Django-проект; client/api — сгенерированный код и gRPC-клиент
server/           Go-сервер; server/api — сгенерированный код и реализация RollDie
nginx.conf        nginx как gRPC-прокси с проверкой клиентского сертификата
```

## Запуск (Ubuntu 24.04)

```bash
sudo apt install golang nginx protobuf-compiler golang-cfssl python3-venv
sh certs.sh
python3 -m venv venv && source venv/bin/activate
pip install grpcio grpcio-tools django
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
mkdir -p logs

python manage.py runserver & go run server/server.go & nginx -p $(pwd) -c nginx.conf
```

Открыть http://127.0.0.1:8000/ и нажать «Roll it!». Слева значение, полученное напрямую от Go-сервера, справа через nginx.
Ещё два адреса: `/grpc` и `/nginx`.

Несколько клиентов: `python manage.py runserver 8001`, `python manage.py runserver 8002`.

Остановка: `nginx -p $(pwd) -c nginx.conf -s stop`, затем `kill -15 <PID>` для процессов python и go.

## Отличия от методички

- nginx слушает порт `9448`, как в `client/views.py` (в методичке в nginx.conf указан 9445, и запросы через nginx не доходили).
- Маршруты `/grpc` и `/nginx` ведут на свои функции, а не на `index`; в функции `nginx` исправлен вызов `api.Certs`.
- Шаблон `index.html` лежит в `client/templates/`, а не внутри `venv`, чтобы он был в репозитории.
- В `nginx.conf` добавлен `pid logs/nginx.pid`, чтобы nginx запускался из папки проекта.
