# Android Client (MVP)

Клиентское приложение для Android на `Kotlin + Jetpack Compose`, использует публичные endpoint'ы backend:

- `POST /public/v1/auth/register`
- `POST /public/v1/auth/login`
- `GET /public/v1/theaters`
- `GET /public/v1/theaters/{theater_id}/shows`
- `GET /public/v1/shows/{show_id}/seats`
- `POST /public/v1/reservations`
- `GET /public/v1/reservations/my`

## Что уже реализовано

- Compose navigation: Auth -> Theaters -> Shows -> Seats -> MyReservations
- Retrofit + Moshi + OkHttp
- Hilt DI
- Хранение JWT токена в SharedPreferences
- Базовый Repository + ViewModel слой

## Запуск (пошагово)

### 1) Подготовить backend

Из корня проекта `VKR_MAIN`:

1. Установите зависимости Python (если еще не устанавливали):
   - `pip install -r requirements.txt`
2. Примените миграцию для customer auth:
   - выполнить SQL из `migrations/add_customer_auth_columns.sql` в вашей PostgreSQL.
3. Запустите API:
   - `python start_api.py`
4. Проверьте, что API доступен:
   - [http://localhost:8000/docs](http://localhost:8000/docs)

### 2) Запустить Android клиент в эмуляторе

1. Откройте папку `android-client` в Android Studio.
2. Дождитесь `Gradle Sync` и установки SDK/Build Tools, если IDE попросит.
3. Создайте/запустите Android эмулятор (AVD).
4. Для эмулятора собирайте с API URL:
   - `-PapiBaseUrl=http://10.0.2.2:8000/`
5. Нажмите Run (`Shift+F10`).

### 3) Запустить на физическом телефоне

1. Телефон и ПК должны быть в одной Wi-Fi сети.
2. Узнайте локальный IP вашего ПК (например `192.168.1.100`).
3. При сборке передайте параметр:
   - `-PapiBaseUrl=http://<ваш_ip>:8000/`
4. Включите USB debugging на телефоне и запустите приложение через Android Studio.
5. Проверьте, что firewall Windows разрешает входящие подключения к порту `8000`.

## Где задается адрес API

Через Gradle property `apiBaseUrl` (см. `app/build.gradle.kts`):

- Эмулятор: `-PapiBaseUrl=http://10.0.2.2:8000/`
- Телефон: `-PapiBaseUrl=http://<ip_пк>:8000/`

Если параметр не указан, используется дефолт: `http://10.0.2.2:8000/`.
