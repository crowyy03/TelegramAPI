import json
import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError
from random import choice, randint
from datetime import datetime

async def main():
    api_id = 2040
    api_hash = 'b18441a1ff607e10a989891a5462e627'
    app_versions = ['6.1.3 x64']
    devices_sdk = [
        "P8610:Windows", "Latitude 5400:Windows", "G55VW:Windows", "Shark 2.0:Windows", "OptiPlex 745:Windows",
        "81EF:Windows", "SX2801:Windows", "H87-D3H:Windows", "SABERTOOTH P67:Windows", "B360M D3H-CF:Windows",
        "Z170 PRO GAMING:Windows", "4313CTO:Windows", "Alienware:Windows", "VPCF22J1E:Windows", "30B9:Windows",
        "Inspiron 7720:Windows", "eMachines E725:Windows", "HP Pavilion P6000 Series:Windows", "A78XA-A2T:Windows",
        "VGN-NW265F:Windows", "Boston:Windows", "Z370P D3-CF:Windows", "NP740U5L-Y03US:Windows", "M3A770DE:Windows",
        "MS-7599:Windows", "Inspiron 1750:Windows", "Satellite L635:Windows", "MS-7327:Windows", "MS-7678:Windows",
        "Z170X-Gaming 5:Windows", "HP EliteBook 8540w:Windows", "Z87N-WIFI:Windows", "XPS M1530:Windows",
        "GT5654:Windows", "HP Laptop 15-da0xxx:Windows", "GA-MA770T-UD3:Windows", "LH700:Windows", "EP45-UD3LR:Windows",
        "LH700:Windows", "MS-7502:Windows", "90NC00JBUS:Windows", "GL552VW:Windows", "Z87M Extreme4:Windows",
        "MS-7325:Windows", "GE60 2OC\\2OE:Windows", "GL552VW:Windows", "304Bh:Windows", "Aspire 5738:Windows",
        "HP HDX18:Windows", "Aspire A515-51G:Windows", "131-GT-E767:Windows", "DX4831:Windows", "Alienware X51:Windows",
        "MS-7B00:Windows", "Aspire M5802:Windows", "MS-7850:Windows", "0T105W:Windows", "UX32VD:Windows", "844C:Windows",
        "04VWF2:Windows", "MS-7673:Windows", "GA-880GM-D2H:Windows", "PRIME B450M-A:Windows", "RS690M2MA:Windows",
        "F5SL:Windows", "HP Pavilion dv6:Windows", "M4A785TD-M EVO:Windows", "80000:Windows", "M4A79 Deluxe:Windows",
        "P5Q SE2:Windows", "PRIME B450M-A:Windows", "Veriton E430:Windows", "2A9A:Windows", "VPCEB27FD:Windows",
        "F5SL:Windows", "Vostro 1520:Windows", "h8-1070t:Windows", "Alienware 17:Windows", "HP EliteDesk 800 G1 SFF:Windows",
        "Z68AP-D3:Windows", "Aurora R5:Windows", "D900T:Windows", "GL553VD:Windows", "P35-DS3L:Windows", "HP ENVY 14:Windows",
        "M4A78LT-M:Windows", "Shark 2.0:Windows", "GA-880GM-UD2H:Windows", "IMEDIA MC 2569:Windows", "Inspiron 1526:Windows",
        "LX6810-01:Windows", "K50AB:Windows"
    ]

    # Запрос номера телефона
    phone = input("Введите номер телефона (в международном формате): ").strip()
    session_file = f'accounts/{phone}.session'
    json_file = f'accounts/{phone}.json'
    
    # Выбор случайных параметров
    app_version = choice(app_versions)
    device_sdk = choice(devices_sdk)
    device, sdk_base = device_sdk.split(':')
    sdk = f"{sdk_base} {randint(10, 11)}"
    
    client = TelegramClient(session_file, api_id, api_hash, 
                            device_model=device, system_version=sdk, 
                            app_version=app_version, lang_code='ru', system_lang_code='ru-ru')
    
    await client.connect()
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            code = input("Введите код, который вы получили: ").strip()
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Введите двухфакторный пароль: ").strip()
                await client.sign_in(password=password)
        except (PhoneNumberInvalidError, PhoneCodeInvalidError) as e:
            print(f"Ошибка авторизации: {e}")
            return
    
    # Получение информации о пользователе
    me = await client.get_me()
    first_name = me.first_name if me.first_name else ''
    last_name = me.last_name if me.last_name else ''
    username = me.username if me.username else ''
    user_id = me.id
    
    # Сохранение данных в JSON файл
    config_data = {
        "app_id": api_id,
        "app_hash": api_hash,
        "sdk": sdk,
        "device": device,
        "app_version": app_version,
        "lang_pack": "ru",
        "system_lang_pack": "ru",
        "twoFA": "",  # Если есть двухфакторный пароль, можно его сюда добавить
        "role": None,
        "id": user_id,
        "phone": phone,
        "username": username,
        "date_of_birth": None,  # Если есть дата рождения, можно добавить
        "date_of_birth_integrity": None,  # Если есть дата рождения, можно добавить
        "is_premium": False,
        "first_name": first_name,
        "last_name": last_name,
        "has_profile_pic": False,
        "spamblock": None,
        "session_file": phone,
        "stats_spam_count": 0,
        "stats_invites_count": 0,
        "last_connect_date": str(datetime.now()),
        "proxy": None,
        "last_check_time": 0,
        "register_time": None,  # Если есть время регистрации, можно добавить
        "success_registred": True,
        "ipv6": False,
        "avatar": "img/default.png",
        "module": "Subscribes",
        "time": str(datetime.now().time())
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)
    
    print(f"Аккаунт {phone} успешно авторизован и сохранен.")

if __name__ == '__main__':
    asyncio.run(main())