import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Функция для извлечения ID видео из ссылки TikTok
def extract_tiktok_id(url):
    patterns = [
        r'tiktok\.com/@[\w.-]+/video/(\d+)',
        r'tiktok\.com/v/(\d+)',
        r'vm\.tiktok\.com/([\w\d]+)',
        r'vt\.tiktok\.com/([\w\d]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Функция для скачивания видео через API
async def download_tiktok_video(url):
    try:
        # Используем API tikwm.com
        api_url = "https://www.tikwm.com/api/"
        
        response = requests.post(api_url, data={
            'url': url,
            'hd': 1
        }, timeout=30)
        
        data = response.json()
        
        if data.get('code') == 0:
            video_data = data.get('data', {})
            # Формируем полный URL для видео
            video_url = video_data.get('hdplay') or video_data.get('play')
            
            return {
                'video_url': video_url,
                'title': video_data.get('title', 'Без названия'),
                'description': video_data.get('title', 'Нет описания'),
                'author': video_data.get('author', {}).get('nickname', 'Неизвестен')
            }
        return None
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для скачивания TikTok видео.\n\n"
        "Просто отправь мне ссылку на TikTok видео, и я скачаю его без водяного знака!\n\n"
        "📎 Поддерживаемые форматы ссылок:\n"
        "• tiktok.com/@username/video/...\n"
        "• vm.tiktok.com/...\n"
        "• vt.tiktok.com/..."
    )

# Обработка ссылок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    # Проверяем, содержит ли сообщение ссылку на TikTok
    if 'tiktok.com' in message_text or 'vm.tiktok' in message_text or 'vt.tiktok' in message_text:
        # Отправляем сообщение о начале обработки
        status_msg = await update.message.reply_text("⏳ Скачиваю видео, подожди немного...")
        
        try:
            # Скачиваем видео
            video_data = await download_tiktok_video(message_text)
            
            if video_data and video_data['video_url']:
                # Формируем текст с информацией
                caption = f"📹 *Название:* {video_data['title']}\n\n"
                caption += f"📝 *Описание:* {video_data['description']}\n\n"
                caption += f"👤 *Автор:* {video_data['author']}"
                
                # Скачиваем видео файл
                video_response = requests.get(video_data['video_url'], timeout=60)
                
                if video_response.status_code == 200:
                    # Отправляем видео
                    await update.message.reply_video(
                        video=video_response.content,
                        caption=caption,
                        parse_mode='Markdown',
                        supports_streaming=True
                    )
                    await status_msg.delete()
                else:
                    await status_msg.edit_text("❌ Не удалось скачать видео файл.")
            else:
                await status_msg.edit_text(
                    "❌ Не удалось скачать видео. Возможные причины:\n"
                    "• Видео недоступно или удалено\n"
                    "• Неправильная ссылка\n"
                    "• Приватный аккаунт"
                )
        
        except Exception as e:
            print(f"Ошибка: {e}")
            await status_msg.edit_text(f"❌ Произошла ошибка при обработке видео: {str(e)}")
    else:
        await update.message.reply_text(
            "❌ Это не похоже на ссылку TikTok.\n"
            "Отправь ссылку в формате: https://www.tiktok.com/@username/video/..."
        )

# Основная функция
def main():
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()