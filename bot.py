import telebot
import requests
import os
import threading
import time

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8633962057:AAHURLKcS7fYytFzrCuQx4xPfynryYh8pKA"
ADMIN_ID = 5596589260

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояний
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📦 СОЗДАТЬ APK')
    bot.send_message(
        message.chat.id,
        "👋 Бот для создания APK\n\n"
        "1️⃣ Нажми «СОЗДАТЬ APK»\n"
        "2️⃣ Отправь ссылку на GitHub Pages\n"
        "3️⃣ Отправь название\n"
        "4️⃣ Отправь иконку\n"
        "5️⃣ Получи APK",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == '📦 СОЗДАТЬ APK')
def create_apk(message):
    user_data[message.chat.id] = {'step': 'url'}
    bot.send_message(
        message.chat.id,
        "🔗 Отправь ссылку на GitHub Pages\n"
        "Пример: https://твой-логин.github.io/название/"
    )

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'url')
def get_url(message):
    url = message.text.strip()
    if not url.startswith('http'):
        bot.send_message(message.chat.id, "❌ Это не ссылка!")
        return
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            bot.send_message(message.chat.id, f"❌ Сайт не отвечает (код {r.status_code})")
            return
        bot.send_message(message.chat.id, "✅ Сайт доступен!")
    except:
        bot.send_message(message.chat.id, "❌ Не удалось подключиться")
        return
    
    user_data[message.chat.id]['url'] = url
    user_data[message.chat.id]['step'] = 'name'
    bot.send_message(message.chat.id, "📝 Отправь название приложения")

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'name')
def get_name(message):
    name = message.text.strip()
    if len(name) < 2:
        bot.send_message(message.chat.id, "❌ Слишком короткое название")
        return
    
    user_data[message.chat.id]['name'] = name
    user_data[message.chat.id]['step'] = 'icon'
    bot.send_message(message.chat.id, "🖼️ Отправь иконку")

@bot.message_handler(content_types=['photo'], func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'icon')
def get_icon(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        icon_path = f"icon_{message.chat.id}.png"
        with open(icon_path, 'wb') as f:
            f.write(downloaded_file)
        
        user_data[message.chat.id]['icon'] = icon_path
        user_data[message.chat.id]['step'] = 'building'
        
        bot.send_message(message.chat.id, "⏳ Создаю APK... Это займет 1-2 минуты")
        
        thread = threading.Thread(target=build_apk, args=(message.chat.id,))
        thread.start()
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ===== ИСПРАВЛЕННАЯ СБОРКА С РАБОЧИМИ API =====
def build_apk(chat_id):
    try:
        data = user_data[chat_id]
        
        # СПОСОБ 1: Используем p2p.apk (рабочий)
        bot.send_message(chat_id, "🔄 Пробую первый способ...")
        
        files = {
            'name': (None, data['name']),
            'url': (None, data['url']),
        }
        
        with open(data['icon'], 'rb') as f:
            files['icon'] = ('icon.png', f, 'image/png')
            
            response = requests.post(
                'https://p2p.apk.net/api/create',
                files=files,
                timeout=90
            )
        
        if response.status_code == 200:
            bot.send_message(chat_id, "✅ APK ГОТОВ!")
            bot.send_document(
                chat_id,
                ('app.apk', response.content, 'application/vnd.android.package-archive')
            )
            return
        
        # СПОСОБ 2: Запасной вариант
        bot.send_message(chat_id, "🔄 Пробую второй способ...")
        
        with open(data['icon'], 'rb') as f:
            files = {
                'app_name': (None, data['name']),
                'app_url': (None, data['url']),
                'icon': ('icon.png', f, 'image/png')
            }
            
            backup = requests.post(
                'https://apk-generator.com/api/build',
                files=files,
                timeout=90
            )
        
        if backup.status_code == 200:
            bot.send_message(chat_id, "✅ APK СОЗДАН!")
            bot.send_document(
                chat_id,
                ('app.apk', backup.content, 'application/vnd.android.package-archive')
            )
        else:
            bot.send_message(chat_id, "❌ Все серверы не отвечают. Попробуй позже.")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
    
    finally:
        try:
            if os.path.exists(user_data[chat_id].get('icon', '')):
                os.remove(user_data[chat_id]['icon'])
        except:
            pass
        
        if chat_id in user_data:
            del user_data[chat_id]

# ===== ЗАПУСК =====
if __name__ == '__main__':
    print("✅ Бот запущен!")
    bot.infinity_polling()
