from imports import *

# Пути к файлам JSON
TOKEN_FILE = "token.json"
BANNED_PHRASES_FILE = "banned_phrases.json"
WARNING_PHRASES_FILE = "warning_phrases.json"
BANSTAT_FILE = "banstat.json"
ADMINLIST_FILE = "adminlist.json"

# Переменная для времени задержки при удалении сообщения бота (в секундах)
DELETE_MESSAGE_DELAY = 5

# Функция для чтения токена и id чата из файла
def read_token_and_chat_id():
    try:
        with open(TOKEN_FILE, "r") as file:
            data = json.load(file)
            token = data.get("token")
            chat_id = data.get("chat_id")
        return token, chat_id
    except FileNotFoundError:
        print(f"Файл '{TOKEN_FILE}' не найден.")
        return None, None
    except json.JSONDecodeError:
        print(f"Ошибка при чтении файла '{TOKEN_FILE}': неверный формат JSON.")
        return None, None

# Функция для записи данных в файл с указанием кодировки
def write_data_to_file(filename, data):
    with open(filename, "a", encoding="utf-8") as file:
        try:
            file.write(str(data) + "\n")
        except Exception as e:
            print(f"Ошибка при записи данных в файл: {e}")

# Функция для чтения данных из файла
def read_data_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = [line.strip().lower() for line in file]
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден.")
        data = []
    return data

# Функция для удаления сообщения пользователя
def delete_user_message(chat_id, message_id):
    bot.delete_message(chat_id, message_id)

# Функция для записи события бана в файл
def record_ban_event(user_id, user_name, message_text, event_type):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": current_time,
        "user_id": user_id,
        "user_name": user_name,
        "message_text": message_text,
        "event_type": event_type}
    with open("banstat.json", "a", encoding="utf-8") as file:
        try:
            json.dump(entry, file, ensure_ascii=False)
            file.write("\n")
        except Exception as e:
            print(f"Ошибка при записи данных в файл: {e}")

# Функция для очистки файла
def clear_file(filename):
    with open(filename, "w"):
        pass

# Функция для чтения токена и id чата
TOKEN, CHAT_ID = read_token_and_chat_id()

# Создание объекта бота
bot = telebot.TeleBot(TOKEN)

# Функция для получения списка идентификаторов администраторов чата
def get_chat_admins(chat_id):
    admins = []
    try:
        chat_admins = bot.get_chat_administrators(chat_id)
        for admin in chat_admins:
            admins.append(str(admin.user.id))
    except Exception as e:
        print("Ошибка при получении администраторов чата:", e)
    return admins

# Функция для удаления сообщения через 5 секунд
def delete_message_after_delay(chat_id, message_id, delay):
    time.sleep(delay)
    bot.delete_message(chat_id, message_id)

# Получение списка администраторов чата
admin_ids = get_chat_admins(CHAT_ID)

# Чтение списка запрещенных фраз
banned_phrases = read_data_from_file(BANNED_PHRASES_FILE)

# Чтение списка фраз предупреждений
warning_phrases = read_data_from_file(WARNING_PHRASES_FILE)

# Создаем список для записи в файл
admin_list = [CHAT_ID] + admin_ids

# Очистка файла перед записью новых данных
clear_file(ADMINLIST_FILE)

# Записываем список в файл
write_data_to_file(ADMINLIST_FILE, "\n".join(admin_list))

# Обработчик команды /start
@bot.message_handler(commands=["start", "help", "settings", "any_other_command"])
def handle_commands(message):
# Проверка, что команда отправлена в личном сообщении и отправитель является администратором
    if str(message.from_user.id) in admin_ids:
# Создаем клавиатуру с четырьмя пустыми кнопками
        keyboard = types.ReplyKeyboardMarkup(row_width=2)
        button_texts = ["Добавить данные в BAN", "Добавить данные в WARNING", "Статистика"]
        for text in button_texts:
            button = types.KeyboardButton(text=text)
            keyboard.add(button)
# Отправляем сообщение с клавиатурой в личное сообщение администратору
        try:
            bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=keyboard)
        except ApiTelegramException as e:
            if e.error_code == 403:
                bot.send_message(message.chat.id, "Для работы с ботом, пожалуйста, разрешите получение сообщений от ботов в настройках конфиденциальности Telegram.")
            else:
                bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
# Удаление сообщения, если оно не отправлено в личном чате администратором
        bot.delete_message(message.chat.id, message.message_id)

# Обработчик для сообщений после выбора кнопки "Добавить данные в BAN"
@bot.message_handler(func=lambda message: message.text == "Добавить данные в BAN")
def add_to_ban_phrases(message):
    # Запросить у пользователя текст для добавления в BAN
    bot.send_message(message.chat.id, "Введите текст для добавления в BAN:")
    # Добавить обработчик для следующего сообщения пользователя
    bot.register_next_step_handler(message, process_ban_phrase)

# Функция для обработки текста, который нужно добавить в BAN
def process_ban_phrase(message):
    new_phrase = message.text.strip()
    # Добавить новую фразу в файл Banned_phrases.json
    with open("banned_phrases.json", "a", encoding="utf-8") as file:
        file.write(new_phrase + "\n")
# Отправить подтверждение администратору
    bot.send_message(message.chat.id, f"Фраза '{new_phrase}' успешно добавлена в BAN.")
    banbanned_phrases = read_data_from_file(BANNED_PHRASES_FILE)

# Обработчик для сообщений после выбора кнопки "Добавить данные в WARNING"
@bot.message_handler(func=lambda message: message.text == "Добавить данные в WARNING")
def add_to_warning_phrases(message):
    bot.send_message(message.chat.id, "Введите текст для добавления в WARNING:")
    bot.register_next_step_handler(message, process_warning_phrase)

# Функция для обработки текста, который нужно добавить в WARNING
def process_warning_phrase(message):
    new_phrase = message.text.strip()
# Добавить новую фразу в файл warning_phrases.json
    with open("warning_phrases.json", "a", encoding="utf-8") as file:
        file.write(new_phrase + "\n")
    bot.send_message(message.chat.id, f"Фраза '{new_phrase}' успешно добавлена в WARNING.")
    warning_phrases = read_data_from_file(WARNING_PHRASES_FILE)

# Обработчик для сообщений после выбора кнопки "Статистика"
@bot.message_handler(func=lambda message: message.text == "Статистика")
def handle_statistics(message):
    bot.send_message(message.chat.id,
                     "Введите интервал дат для вывода статистики в формате 'гггг-мм-дд гггг-мм-дд', например, '2024-02-01 2024-02-07':")
    bot.register_next_step_handler(message, process_dates)

# Функция для обработки полученных дат
def process_dates(message):
    date_range = message.text.split()
    if len(date_range) == 1:
        start_date = end_date = date_range[0]
    elif len(date_range) == 2:
        start_date, end_date = date_range
    else:
        bot.send_message(message.chat.id, "Неправильный формат ввода. Попробуйте снова.")
        return

    file_path = 'banstat.json'
    count_ban, count_warning = count_events(file_path, start_date, end_date)
    bot.send_message(message.chat.id, f"За период с {start_date} по {end_date}:\n"
                                      f"Забанено {count_ban} сообщений,\n"
                                      f"Вынесено {count_warning} предупреждений.")

# Функция для подсчета событий в указанном диапазоне дат
def count_events(file_path, start_date, end_date):
    count_ban = 0
    count_warning = 0
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') if end_date else start_datetime
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            event_data = json.loads(line)
            timestamp = datetime.strptime(event_data['timestamp'][:10], '%Y-%m-%d')
            if start_datetime <= timestamp <= end_datetime:
                if event_data['event_type'] == 'BAN':
                    count_ban += 1
                elif event_data['event_type'] == 'WARNING':
                    count_warning += 1
    return count_ban, count_warning

# Обработчик для всех сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    words = ()
    text = message.text.lower() if message.text else ""

# Проверка, является ли отправитель администратором
# Не выполняем никаких действий, если отправитель администратор
    if str(message.from_user.id) in admin_ids:
        return
    for phrase in banned_phrases:
        words = phrase.split()
        found = all(word.lower() in text for word in words)
        if found:
            user_id = message.from_user.id
            user_name = message.from_user.first_name
            ban_message = f"Пользователь {user_name} (ID: {user_id}) отправил запрещенное сообщение"
            delete_user_message(message.chat.id, message.message_id)
            record_ban_event(user_id, user_name, message.text, "BAN")
            sent_message = bot.send_message(message.chat.id, ban_message)

# Удаление сообщения через 5 секунд
            threading.Thread(target=delete_message_after_delay,
                             args=(sent_message.chat.id, sent_message.message_id, DELETE_MESSAGE_DELAY)).start()
            break
# Если не было найдено запрещенных фраз
    if not found:
        for phrase in warning_phrases:
            words = phrase.split()
            found = all(word.lower() in text for word in words)
            if found:
                user_id = message.from_user.id
                user_name = message.from_user.first_name
                warning_message = f"Пользователь {user_name} (ID: {user_id}) ваше сообщение содержит запрещенное в этом чате слово, попробуйте написать иначе."
                delete_user_message(message.chat.id, message.message_id)
                record_ban_event(user_id, user_name,message.text, "WARNING")
                sent_message = bot.send_message(message.chat.id, warning_message)

# Удаление сообщения бота через 5 секунд
                threading.Thread(target=delete_message_after_delay,
                                 args=(sent_message.chat.id, sent_message.message_id, DELETE_MESSAGE_DELAY)).start()
                break

# Удаление сообщений о вступлении и выходе из чата
@bot.message_handler(content_types=['new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo',
                                    'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
                                    'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id'])
def delete(message):
    bot.delete_message(message.chat.id, message.message_id)

# Запуск бота
if __name__ == "__main__":
    bot.polling(timeout=120)
    time.sleep(5)  # Задержка перед чтением администраторов
