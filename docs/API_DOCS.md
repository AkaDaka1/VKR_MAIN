# Документация по API

## Аутентификация

### POST /token
Получение JWT-токена для аутентификации.

**Тело запроса:**
- username: строка
- password: строка

**Ответ:**
```json
{
  "access_token": "токен_пользователя",
  "token_type": "bearer"
}
```

## Сотрудники (Employees)

### GET /employees/
Получение списка всех сотрудников.

**Ответ:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "last_online": "2023-01-01T00:00:00"
  }
]
```

### GET /employees/{employee_id}
Получение информации о конкретном сотруднике.

### POST /employees/
Создание нового сотрудника.

**Тело запроса:**
```json
{
  "username": "новое_имя_пользователя",
  "password": "пароль",
  "role": "роль"
}
```

### DELETE /employees/{employee_id}
Удаление сотрудника по ID.

## Франчайзинг (Franchises)

### GET /franchises/
Получение списка всех франчайзингов.

### GET /franchises/{franchise_id}
Получение информации о конкретном франчайзинге.

### POST /franchises/
Создание нового франчайзинга.

**Тело запроса:**
```json
{
  "contact_person": "Контактное лицо",
  "organization": "Организация",
  "phone": "+1234567890",
  "email": "email@example.com",
  "address": "Адрес",
  "start_date": "2023-01-01T00:00:00",
  "end_date": "2024-01-01T00:00:00",
  "status": "статус",
  "royalty_percentage": 10.5,
  "initial_fee": 1000.0,
  "monthly_fee": 500.0
}
```

### PUT /franchises/{franchise_id}
Обновление информации о франчайзинге.

### DELETE /franchises/{franchise_id}
Удаление франчайзинга по ID.

## Театры (Theaters)

### GET /theaters/
Получение списка всех театров.

### POST /theaters/
Создание нового театра.

**Тело запроса:**
```json
{
  "contract_id": 1,
  "name": "Название театра",
  "location": "Местоположение"
}
```

### DELETE /theaters/{theater_id}
Удаление театра по ID.

## Залы (Halls)

### GET /halls/
Получение списка всех залов.

### POST /halls/
Создание нового зала.

**Тело запроса:**
```json
{
  "theater_id": 1,
  "capacity": 100
}
```

### DELETE /halls/{hall_id}
Удаление зала по ID.

## Сценарии (Scenarios)

### GET /scenarios/
Получение списка всех сценариев.

### POST /scenarios/
Создание нового сценария.

**Тело запроса:**
```json
{
  "title": "Название сценария",
  "status": "статус",
  "description": "Описание"
}
```

### DELETE /scenarios/{scenario_id}
Удаление сценария по ID.

### Файл ТЗ сценария (загрузка, скачивание, обработка через n8n)

Файлы хранятся на диске сервера API (см. `SCENARIO_TZ_UPLOAD_ROOT` в `api/config.py`, по умолчанию `data/scenario_tz/` в корне проекта). В БД сохраняются относительный путь и оригинальное имя файла.

**Права:** загрузка и запуск обработки — как у создания сценария (`PERMISSION_CONTENT_WRITE`, роли сценариста/админа и т.п.); скачивание — любой авторизованный пользователь.

### POST /scenarios/{scenario_id}/tz-spec/upload
`multipart/form-data`, поле **`file`**. Допустимые расширения: `.txt`, `.md`, `.pdf`, `.doc`, `.docx`, `.rtf`, `.odt`; максимум 25 МБ.

**Ответ:** объект сценария (в т.ч. `tz_source_filename`, `tz_pipeline_status`).

### GET /scenarios/{scenario_id}/tz-spec/download?kind=source|result
Возвращает бинарный файл (`application/octet-stream`). `kind=source` — исходник, `kind=result` — результат после обработки (если есть).

### POST /scenarios/{scenario_id}/tz-spec/process
Отправляет **исходный** файл на вебхук n8n (`N8N_TZ_WEBHOOK_URL`) и сохраняет **тело ответа** как результат. Если URL не задан, ответ **400** с пояснением.

Переменные окружения API: `N8N_TZ_WEBHOOK_URL`, опционально `N8N_TZ_TIMEOUT_SEC` (секунды).

## Акты (Acts)

### GET /acts/
Получение списка всех актов.

### POST /acts/
Создание нового акта.

**Тело запроса:**
```json
{
  "scenario_id": 1,
  "title": "Название акта",
  "position": 1
}
```

### DELETE /acts/{act_id}
Удаление акта по ID.

## Части (Parts)

### GET /parts/
Получение списка всех частей.

### POST /parts/
Создание новой части.

**Тело запроса:**
```json
{
  "act_id": 1,
  "title": "Название части",
  "file_path": "путь_к_файлу",
  "position": 1
}
```

### DELETE /parts/{part_id}
Удаление части по ID.

## Представления (Shows)

### GET /shows/
Получение списка всех представлений.

### POST /shows/
Создание нового представления.

**Тело запроса:**
```json
{
  "hall_id": 1,
  "title": "Название представления",
  "vote_type": "common",
  "duration": "02:00:00",
  "show_date": "2023-01-01T19:00:00"
}
```

### DELETE /shows/{show_id}
Удаление представления по ID.

## Клиенты (Customers)

### GET /customers/
Получение списка всех клиентов.

### POST /customers/
Создание нового клиента.

**Тело запроса:**
```json
{
  "email": "email@example.com",
  "phone": "+1234567890"
}
```

### DELETE /customers/{email}
Удаление клиента по email.

## Билеты (Tickets)

### GET /tickets/
Получение списка всех билетов.

### POST /tickets/
Создание нового билета.

**Тело запроса:**
```json
{
  "owner_id": 1,
  "show_id": 1,
  "seat_number": "A1",
  "price": 100.0,
  "status": "available",
  "vip_status": false,
  "email": "email@example.com"
}
```

### DELETE /tickets/{ticket_id}
Удаление билета по ID.

## Общие голоса (Votes Common)

### GET /votes_common/
Получение списка всех общих голосов.

### POST /votes_common/
Создание нового общего голоса.

**Тело запроса:**
```json
{
  "ticket_id": 1,
  "value": "значение_голоса"
}
```

### DELETE /votes_common/{ticket_id}/{vote_id}
Удаление общего голоса по ID билета и ID голоса.

## VIP-голоса (Votes VIP)

### GET /votes_vip/
Получение списка всех VIP-голосов.

### POST /votes_vip/
Создание нового VIP-голоса.

**Тело запроса:**
```json
{
  "ticket_id": 1,
  "show_id": 1,
  "act_id": 1,
  "value": "значение_голоса"
}
```

### DELETE /votes_vip/{vote_id}
Удаление VIP-голоса по ID.

## Оборудование (Equipment)

### GET /equipments/
Получение списка всего оборудования.

### POST /equipments/
Создание нового оборудования.

**Тело запроса:**
```json
{
  "name": "Название оборудования",
  "price": 1000.0,
  "amount": 5
}
```

### DELETE /equipments/{equipment_id}
Удаление оборудования по ID.

## Аренда оборудования (Rent Equipment)

### POST /rents_equipment/
Создание новой аренды оборудования.

**Тело запроса:**
```json
{
  "equipment_id": 1,
  "show_id": 1,
  "rent_start": "2023-01-01T00:00:00",
  "rent_end": "2023-01-02T00:00:00"
}
```

### DELETE /rents_equipment/{equipment_id}/{show_id}
Удаление аренды оборудования.

## Услуги (Services)

### GET /services/
Получение списка всех услуг.

### POST /services/
Создание новой услуги.

**Тело запроса:**
```json
{
  "name": "Название услуги",
  "price": 500.0,
  "amount": 3
}
```

### DELETE /services/{service_id}
Удаление услуги по ID.

## Аренда услуг (Rent Services)

### POST /rents_service/
Создание новой аренды услуги.

**Тело запроса:**
```json
{
  "service_id": 1,
  "show_id": 1,
  "rent_start": "2023-01-01T00:00:00",
  "rent_end": "2023-01-02T00:00:00"
}
```

### DELETE /rents_service/{service_id}/{show_id}
Удаление аренды услуги.

## Защищенные маршруты

Для доступа к защищенным маршрутам необходимо включить заголовок Authorization:
```
Authorization: Bearer {access_token}
```

## Текущий пользователь

### GET /users/me
Получение информации о текущем аутентифицированном пользователе.

## Public API для Android клиента

Публичные маршруты вынесены под префикс `/public/v1`. Они не зависят от ролей сотрудников.

### POST /public/v1/auth/register
Регистрация клиента.

**Тело запроса:**
```json
{
  "email": "client@example.com",
  "phone": "+79990000000",
  "password": "secure-password"
}
```

### POST /public/v1/auth/login
Логин клиента и получение JWT.

### GET /public/v1/me
Информация о текущем клиенте.

### GET /public/v1/theaters
Список театров для клиентского приложения.

### GET /public/v1/theaters/{theater_id}/shows?show_date=YYYY-MM-DD
Список представлений выбранного театра. Фильтр по дате опционален.

### GET /public/v1/shows/{show_id}/seats
Список мест (билетов) для конкретного представления.

### POST /public/v1/reservations
Резерв выбранного места.

**Тело запроса:**
```json
{
  "show_id": 1,
  "seat_number": "A1"
}
```

### GET /public/v1/reservations/my
Список моих броней (билеты со статусом `booked`).