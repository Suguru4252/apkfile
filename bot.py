import telebot
import requests
import os
import threading
import time

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8633962057:AAHURLKcS7fYytFzrCuQx4xPfynryYh8pKA"
ADMIN_ID = 5596589260

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояний пользователей
user_data = {}

# ===== КОМАНДА СТАРТ =====
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📦 СОЗДАТЬ APK')
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для создания APK из твоего сайта\n\n"
        "1️⃣ Нажми «СОЗДАТЬ APK»\n"
        "2️⃣ Отправь ссылку на GitHub Pages\n"
        "3️⃣ Отправь название приложения\n"
        "4️⃣ Отправь иконку\n"
        "5️⃣ Получи готовый APK через минуту",
        reply_markup=markup
    )

# ===== СОЗДАНИЕ APK =====
@bot.message_handler(func=lambda m: m.text == '📦 СОЗДАТЬ APK')
def create_apk(message):
    user_data[message.chat.id] = {'step': 'url'}
    bot.send_message(
        message.chat.id,
        "🔗 Отправь ссылку на GitHub Pages\n"
        "Пример: https://твой-логин.github.io/название-репозитория/"
    )

# ===== ПРИЕМ ССЫЛКИ =====
@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'url')
def get_url(message):
    url = message.text.strip()
    if not url.startswith('http'):
        bot.send_message(message.chat.id, "❌ Это не ссылка! Отправь нормальную ссылку начинающуюся с http")
        return
    
    # Проверяем доступность
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Сайт не отвечает (код ошибки: {r.status_code})")
            return
        bot.send_message(message.chat.id, "✅ Сайт доступен!")
    except:
        bot.send_message(message.chat.id, "❌ Не удалось подключиться к сайту")
        return
    
    user_data[message.chat.id]['url'] = url
    user_data[message.chat.id]['step'] = 'name'
    bot.send_message(message.chat.id, "📝 Отправь название приложения (например: Мой Кликер)")

# ===== ПРИЕМ НАЗВАНИЯ =====
@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'name')
def get_name(message):
    name = message.text.strip()
    if len(name) < 2:
        bot.send_message(message.chat.id, "❌ Слишком короткое название, минимум 2 символа")
        return
    
    user_data[message.chat.id]['name'] = name
    user_data[message.chat.id]['step'] = 'icon'
    bot.send_message(message.chat.id, "🖼️ Отправь иконку (картинку 512x512)")

# ===== ПРИЕМ ИКОНКИ =====
@bot.message_handler(content_types=['photo'], func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'icon')
def get_icon(message):
    try:
        # Получаем фото
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем
        icon_path = f"icon_{message.chat.id}.png"
        with open(icon_path, 'wb') as f:
            f.write(downloaded_file)
        
        user_data[message.chat.id]['icon'] = icon_path
        user_data[message.chat.id]['step'] = 'building'
        
        bot.send_message(message.chat.id, "⏳ Начинаю создавать APK... Это займет 1-2 минуты")
        
        # Запускаем сборку в отдельном потоке
        thread = threading.Thread(target=build_apk, args=(message.chat.id,))
        thread.start()
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при загрузке иконки: {e}")

# ===== СБОРКА APK (РАБОЧАЯ ВЕРСИЯ) =====
def build_apk(chat_id):
    try:
        data = user_data[chat_id]
        
        bot.send_message(chat_id, "🔄 1. Подключаюсь к серверу сборки...")
        
        # Используем рабочий API
        files = {
            'name': (None, data['name']),
            'url': (None, data['url']),
        }
        
        # Добавляем иконку
        with open(data['icon'], 'rb') as f:
            files['icon'] = ('icon.png', f, 'image/png')
            
            bot.send_message(chat_id, "🔄 2. Отправляю файлы на сервер...")
            
            # Отправляем запрос
            response = requests.post(
                'https://api.webintoapp.com/v1/create',
                files=files,
                timeout=90
            )
        
        if response.status_code == 200:
            # Пробуем получить JSON ответ
            try:
                result = response.json()
                download_url = result.get('download_url') or result.get('file') or result.get('url')
                
                if download_url:
                    bot.send_message(chat_id, "✅ APK ГОТОВ!")
                    bot.send_message(chat_id, f"Скачать: {download_url}")
                    
                    # Пробуем скачать и отправить напрямую
                    try:
                        apk = requests.get(download_url, timeout=30)
                        if apk.status_code == 200:
                            bot.send_document(
                                chat_id,
                                ('app.apk', apk.content, 'application/vnd.android.package-archive')
                            )
                    except:
                        pass
                else:
                    # Если нет ссылки, отправляем сам файл
                    bot.send_message(chat_id, "✅ APK СОЗДАН!")
                    bot.send_document(
                        chat_id,
                        ('app.apk', response.content, 'application/vnd.android.package-archive')
                    )
            except:
                # Если не JSON, отправляем как файл
                bot.send_message(chat_id, "✅ APK СОЗДАН!")
                bot.send_document(
                    chat_id,
                    ('app.apk', response.content, 'application/vnd.android.package-archive')
                )
        else:
            bot.send_message(chat_id, f"❌ Ошибка сервера: {response.status_code}")
            
            # Пробуем запасной вариант
            bot.send_message(chat_id, "🔄 Пробую другой сервер...")
            
            backup_files = {
                'app_name': (None, data['name']),
                'app_url': (None, data['url']),
            }
            
            with open(data['icon'], 'rb') as f:
                backup_files['app_icon'] = ('icon.png', f, 'image/png')
                
                backup = requests.post(
                    'https://apk-creator.com/api/build',
                    files=backup_files,
                    timeout=60
                )
            
            if backup.status_code == 200:
                bot.send_message(chat_id, "✅ APK СОЗДАН (через второй сервер)!")
                bot.send_document(
                    chat_id,
                    ('app.apk', backup.content, 'application/vnd.android.package-archive')
                )
            else:
                bot.send_message(chat_id, "❌ Все серверы не отвечают. Попробуй позже.")
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при сборке: {str(e)}")
    
    finally:
        # Удаляем временный файл с иконкой
        try:
            if os.path.exists(user_data[chat_id].get('icon', '')):
                os.remove(user_data[chat_id]['icon'])
        except:
            pass
        
        # Очищаем данные пользователя
        if chat_id in user_data:
            del user_data[chat_id]

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("✅ Бот запущен и готов к работе!")
    print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    bot.infinity_polling()
