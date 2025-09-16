#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import GetAuthorizationsRequest


class InvisibleSessionManager:
    """
    Создает долговременные токены, которые позволяют авторизоваться
    без SMS-кода в течение длительного времени.
    """
    
    def __init__(self, session_file: str, json_file: str):
        self.session_file = session_file
        self.json_file = json_file
        self.config = self._load_config()
        self.client = None
        self.token_data = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"Конфигурация загружена из {self.json_file}")
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON файл не найден: {self.json_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON файла: {e}")
    
    def _create_client(self) -> TelegramClient:
        """Создает TelegramClient с параметрами из конфигурации."""
        if not all(key in self.config for key in ['app_id', 'app_hash', 'device', 'sdk', 'app_version']):
            raise ValueError("Недостаточно параметров в конфигурации для создания клиента")
        
        client = TelegramClient(
            self.session_file,
            self.config['app_id'],
            self.config['app_hash'],
            device_model=self.config['device'],
            system_version=self.config['sdk'],
            app_version=self.config['app_version'],
            lang_code=self.config.get('lang_pack', 'ru'),
            system_lang_code=self.config.get('system_lang_pack', 'ru-RU')
        )
        
        print(f"TelegramClient создан с параметрами:")
        print(f"  Устройство: {self.config['device']}")
        print(f"  SDK: {self.config['sdk']}")
        print(f"  Версия приложения: {self.config['app_version']}")
        
        return client
    
    async def connect_and_verify(self) -> bool:
        """Подключается к аккаунту и проверяет авторизацию."""
        try:
            self.client = self._create_client()
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                print("Сессия не авторизована. Необходима повторная авторизация.")
                return False
            
            me = await self.client.get_me()
            print(f"Успешно подключен к аккаунту: {me.first_name} {me.last_name} (@{me.username})")
            print(f"  ID: {me.id}")
            print(f"  Телефон: {me.phone}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    async def create_invisible_session(self) -> Optional[Dict[str, Any]]:
        """
        Создает невидимую сессию.
        Извлекает StringSession из активной сессии и сохраняет как токен.
        НЕ выполняет логаут - это ключевое отличие от ТЗ.
        """
        if not self.client or not await self.client.is_user_authorized():
            print("Клиент не авторизован. Сначала выполните подключение.")
            return None
        
        try:
            print("Создание невидимой сессии...")
            
            # Получаем информацию о текущих авторизациях
            authorizations = await self.client(GetAuthorizationsRequest())
            current_session_id = None
            
            for auth in authorizations.authorizations:
                if auth.current:
                    current_session_id = auth.hash
                    print(f"Текущая сессия ID: {current_session_id}")
                    break
            
            # Извлекаем StringSession из активной сессии
            print("Извлечение StringSession из активной сессии...")
            string_session = self.client.session.save()
            
            if not string_session:
                print("Не удалось извлечь StringSession")
                return None
            
            # Создаем данные токена
            token_data = {
                'session_id': current_session_id,
                'phone': self.config['phone'],
                'user_id': self.config['id'],
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat(),
                'device_info': {
                    'device': self.config['device'],
                    'sdk': self.config['sdk'],
                    'app_version': self.config['app_version']
                },
                'api_credentials': {
                    'api_id': self.config['app_id'],
                    'api_hash': self.config['app_hash']
                },
                'string_session': string_session,
                'twofa_password': self.config.get('twoFA', '')
            }
            
            # Сохраняем токен в файл
            token_file = f"{self.session_file}_invisible_token.json"
            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=4)
            
            print(f"Токен сохранен в файл: {token_file}")
            print(f"Токен действителен до: {token_data['expires_at']}")
            
            # ВАЖНО: НЕ ДЕЛАЕМ ЛОГАУТ!
            # Исходная сессия остается активной
            print("Исходная сессия остается активной (логаут НЕ выполняется)")
            
            print("Невидимая сессия создана!")
            print("Токен готов для авторизации через месяц!")
            
            self.token_data = token_data
            return token_data
            
        except Exception as e:
            print(f"Ошибка создания невидимой сессии: {e}")
            return None
    
    async def reauthorize_with_token(self, token_file: str) -> bool:
        """
        Выполняет повторную авторизацию с использованием токена.
        Создает новую сессию из сохраненного StringSession.
        """
        try:
            # Загружаем данные токена
            with open(token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            # Проверяем срок действия токена
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expires_at:
                print("Токен истек. Необходимо создать новый.")
                return False
            
            print(f"Использование токена для аккаунта: {token_data['phone']}")
            print("Создание новой сессии через токен...")
            
            # Получаем параметры из токена
            api_id = token_data['api_credentials']['api_id']
            api_hash = token_data['api_credentials']['api_hash']
            device_info = token_data['device_info']
            string_session = token_data['string_session']
            
            # Создаем новую сессию с уникальным именем
            import time
            new_session_file = f"restored_session_{int(time.time())}"
            
            # Создаем клиент с новым именем сессии
            client = TelegramClient(
                new_session_file,
                api_id,
                api_hash,
                device_model=device_info['device'],
                system_version=device_info['sdk'],
                app_version=device_info['app_version'],
                lang_code='ru',
                system_lang_code='ru-RU'
            )
            
            await client.connect()
            
            # Восстанавливаем сессию из StringSession
            if string_session:
                try:
                    print("Восстановление сессии из StringSession...")
                    
                    # Создаем StringSession из сохраненных данных
                    session = StringSession(string_session)
                    
                    # Устанавливаем сессию
                    client.session = session
                    await client.session.save()
                    
                    # Проверяем авторизацию
                    if await client.is_user_authorized():
                        print("Новая сессия создана через токен!")
                        
                        # Получаем информацию о пользователе
                        me = await client.get_me()
                        print(f"Подключен к аккаунту: {me.first_name} {me.last_name}")
                        print(f"Телефон: {me.phone}")
                        
                        self.client = client
                        return True
                    else:
                        print("Не удалось авторизоваться через токен")
                        await client.disconnect()
                        return False
                        
                except Exception as e:
                    print(f"Ошибка восстановления сессии из токена: {e}")
                    await client.disconnect()
                    return False
            else:
                print("Токен не содержит StringSession")
                await client.disconnect()
                return False
                
        except FileNotFoundError:
            print(f"Файл токена не найден: {token_file}")
            return False
        except json.JSONDecodeError:
            print(f"Ошибка чтения файла токена: {token_file}")
            return False
        except Exception as e:
            print(f"Ошибка повторной авторизации: {e}")
            return False
    
    async def check_session_status(self) -> Dict[str, Any]:
        """Проверяет статус текущей сессии."""
        if not self.client:
            return {'status': 'not_connected', 'message': 'Клиент не подключен'}
        
        try:
            if not await self.client.is_user_authorized():
                return {'status': 'not_authorized', 'message': 'Сессия не авторизована'}
            
            me = await self.client.get_me()
            authorizations = await self.client(GetAuthorizationsRequest())
            
            return {
                'status': 'active',
                'user': {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone
                },
                'active_sessions': len(authorizations.authorizations),
                'current_session': any(auth.current for auth in authorizations.authorizations)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def cleanup(self):
        """Закрывает соединение и очищает ресурсы."""
        if self.client:
            await self.client.disconnect()
            print("Соединение закрыто")


async def main():
    """Основная функция для демонстрации работы с невидимыми сессиями."""
    print("Менеджер невидимых сессий Telegram")
    print("=" * 50)
    
    # Пути к файлам
    session_file = "/Users/Voronin/Desktop/work/TelegramAPI/5шт Илья/79312717436.session"
    json_file = "/Users/Voronin/Desktop/work/TelegramAPI/5шт Илья/79312717436.json"
    token_file = f"{session_file}_invisible_token.json"
    
    # Проверяем существование файлов
    if not os.path.exists(session_file):
        print(f"Файл сессии не найден: {session_file}")
        return
    
    if not os.path.exists(json_file):
        print(f"JSON файл не найден: {json_file}")
        return
    
    # Создаем менеджер сессий
    manager = InvisibleSessionManager(session_file, json_file)
    
    try:
        # Подключаемся и проверяем авторизацию
        if await manager.connect_and_verify():
            print("\nСтатус сессии:")
            status = await manager.check_session_status()
            print(f"  Статус: {status['status']}")
            if status['status'] == 'active':
                print(f"  Пользователь: {status['user']['first_name']} {status['user']['last_name']}")
                print(f"  Активных сессий: {status['active_sessions']}")
            
            # Создаем невидимую сессию
            print("\nСоздание невидимой сессии...")
            token_data = await manager.create_invisible_session()
            
            if token_data:
                print("\nНевидимая сессия создана!")
                print(f"Токен сохранен в: {token_file}")
                
                # Демонстрация повторной авторизации
                print("\nТестирование повторной авторизации через токен...")
                if os.path.exists(token_file):
                    success = await manager.reauthorize_with_token(token_file)
                    if success:
                        print("Повторная авторизация через токен успешна!")
                        
                        # Проверяем статус после повторной авторизации
                        print("\nСтатус после повторной авторизации:")
                        status = await manager.check_session_status()
                        print(f"  Статус: {status['status']}")
                        if status['status'] == 'active':
                            print(f"  Пользователь: {status['user']['first_name']} {status['user']['last_name']}")
                            print(f"  Активных сессий: {status['active_sessions']}")
                    else:
                        print("Повторная авторизация через токен не удалась")
                else:
                    print("Файл токена не найден")
            else:
                print("Не удалось создать невидимую сессию")
        else:
            print("Не удалось подключиться к аккаунту")
    
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    
    finally:
        # Очищаем ресурсы
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
