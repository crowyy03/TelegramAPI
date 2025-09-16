#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI для работы с невидимыми сессиями Telegram
"""

import asyncio
import argparse
import os
from invisible_session_manager import InvisibleSessionManager


async def create_session(session_file: str, json_file: str):
    """Создает невидимую сессию."""
    if not os.path.exists(session_file):
        print(f"Файл сессии не найден: {session_file}")
        return
    
    if not os.path.exists(json_file):
        print(f"JSON файл не найден: {json_file}")
        return
    
    manager = InvisibleSessionManager(session_file, json_file)
    
    try:
        if await manager.connect_and_verify():
            token_data = await manager.create_invisible_session()
            if token_data:
                print("Невидимая сессия создана успешно!")
                print(f"Токен сохранен в: {session_file}_invisible_token.json")
            else:
                print("Ошибка создания невидимой сессии")
        else:
            print("Не удалось подключиться к аккаунту")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await manager.cleanup()


async def reauthorize(session_file: str, json_file: str, token_file: str):
    """Выполняет повторную авторизацию через токен."""
    if not os.path.exists(token_file):
        print(f"Файл токена не найден: {token_file}")
        return
    
    manager = InvisibleSessionManager(session_file, json_file)
    
    try:
        success = await manager.reauthorize_with_token(token_file)
        if success:
            print("Повторная авторизация успешна!")
            
            # Показываем статус
            status = await manager.check_session_status()
            if status['status'] == 'active':
                print(f"Пользователь: {status['user']['first_name']} {status['user']['last_name']}")
                print(f"Телефон: {status['user']['phone']}")
        else:
            print("Ошибка повторной авторизации")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await manager.cleanup()


async def status(session_file: str, json_file: str):
    """Проверяет статус сессии."""
    manager = InvisibleSessionManager(session_file, json_file)
    
    try:
        if await manager.connect_and_verify():
            status = await manager.check_session_status()
            print(f"Статус: {status['status']}")
            if status['status'] == 'active':
                print(f"Пользователь: {status['user']['first_name']} {status['user']['last_name']}")
                print(f"Телефон: {status['user']['phone']}")
                print(f"Активных сессий: {status['active_sessions']}")
        else:
            print("Сессия не авторизована")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await manager.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Менеджер невидимых сессий Telegram')
    parser.add_argument('command', choices=['create', 'reauth', 'status'], help='Команда для выполнения')
    parser.add_argument('--session', required=True, help='Путь к файлу сессии')
    parser.add_argument('--json', required=True, help='Путь к JSON файлу')
    parser.add_argument('--token', help='Путь к файлу токена (для команды reauth)')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        asyncio.run(create_session(args.session, args.json))
    elif args.command == 'reauth':
        if not args.token:
            print("Для команды reauth необходимо указать --token")
            return
        asyncio.run(reauthorize(args.session, args.json, args.token))
    elif args.command == 'status':
        asyncio.run(status(args.session, args.json))


if __name__ == "__main__":
    main()
