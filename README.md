# Менеджер невидимых сессий Telegram

Создает долговременные токены для авторизации в Telegram без SMS-кода.

## Особенности

- Создает долговременные токены (действуют до года)
- Авторизация без SMS-кода
- Работает с существующими сессиями
- Поддерживает эмуляцию устройств
- Простой CLI интерфейс

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

### Создание невидимой сессии

```bash
python cli.py create --session path/to/session.session --json path/to/config.json
```

### Повторная авторизация через токен

```bash
python cli.py reauth --session path/to/session.session --json path/to/config.json --token path/to/session_invisible_token.json
```

### Проверка статуса сессии

```bash
python cli.py status --session path/to/session.session --json path/to/config.json
```

## Структура проекта

- `invisible_session_manager.py` - основной модуль
- `cli.py` - командная строка
- `authorization.py` - базовый скрипт авторизации
- `requirements.txt` - зависимости

## Важные замечания

1. **НЕ выполняет логаут** - исходная сессия остается активной
2. Требует активную сессию для создания токена
3. Токены сохраняются в файлы `*_invisible_token.json`
4. Поддерживает 2FA (пароль сохраняется в токене)

## Формат JSON конфигурации

```json
{
  "app_id": 12345,
  "app_hash": "your_api_hash",
  "phone": "+1234567890",
  "id": 123456789,
  "device": "Device Model",
  "sdk": "SDK Version",
  "app_version": "App Version",
  "lang_pack": "ru",
  "system_lang_pack": "ru-RU",
  "twoFA": "your_2fa_password"
}
```