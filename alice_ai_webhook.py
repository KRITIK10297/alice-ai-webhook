from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# API ключ от API Airforce
client = OpenAI(
    api_key="sk-air-d61Go3ES8LktdvnP1QG3jjUajqoiu7YDhbpjHYbiSJpw8Ug",
    base_url="https://api.airforce/v1"
)

# Хранилище истории диалогов (для контекста)
conversations = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик запросов от Яндекс.Диалогов"""

    data = request.json

    # Получаем информации о запросе
    user_id = data['session']['user_id']
    user_text = data['request']['command']
    is_new_session = data['session']['new']

    # Если новая сессия - очищаем историю
    if is_new_session:
        conversations[user_id] = []

    # Инициализируем историю для нового пользователя
    if user_id not in conversations:
        conversations[user_id] = []

    # Добавляем сообщение пользователя в историю
    conversations[user_id].append({"role": "user", "content": user_text})

    # Ограничиваем историю последними 10 сообщениями (чтобы не превышать лимиты)
    if len(conversations[user_id]) > 10:
        conversations[user_id] = conversations[user_id][-10:]

    try:
        # Отправляем запрос к AI
        response = client.chat.completions.create(
            model="deepseek-v3",  # Используем DeepSeek V3 - быстрая и умная модель
            messages=conversations[user_id],
            temperature=0.7,
            max_tokens=500  # Ограничиваем ответ для голосового вывода
        )

        ai_text = response.choices[0].message.content

        # Добавляем ответ AI в историю
        conversations[user_id].append({"role": "assistant", "content": ai_text})

        # Формируем ответ для Алисы
        return jsonify({
            "response": {
                "text": ai_text,
                "tts": ai_text,  # Text-to-speech версия
                "end_session": False
            },
            "version": "1.0"
        })

    except Exception as e:
        # В случае ошибки возвращаем понятное сообщение
        error_message = f"Извините, произошла ошибка при обращении к AI: {str(e)}"

        return jsonify({
            "response": {
                "text": error_message,
                "tts": "Извините, произошла ошибка. Попробуйте еще раз.",
                "end_session": False
            },
            "version": "1.0"
        })

@app.route('/health', methods=['GET'])
def health():
    """Проверка работоспособности сервера"""
    return jsonify({"status": "ok", "message": "Alice AI Webhook is running"})

if __name__ == '__main__':
    # Запускаем сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
