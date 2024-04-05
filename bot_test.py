from imports import *

# Пути к файлам JSON
TOKEN_FILE = "token.json"
BANNED_PHRASES_FILE = "banned_phrases.json"
BANNED_PHRASES_FILE_NEW = "banned_phrases_new.json"
WARNING_PHRASES_FILE = "warning_phrases.json"
BANSTAT_FILE = "ban_stat.json"
BOT_STAT_FILE = "bot_stat.json"
ADMINLIST_FILE = "adminlist.json"

# Переменная для времени задержки при удалении сообщения бота (в секундах)
DELETE_MESSAGE_DELAY = 5

# Количество повторяющихся сообщений
message_count = 3

# Определяем словарь для кэширования сообщений
message_occurrences_cache = {}

#Если используем мут в секундах
MUTE_DURATION = 1209600

#Логирование
logging.basicConfig(filename='Telebot.json', encoding='utf-8', level=logging.INFO,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s')

# Создаем словарь для замены латинских букв на кириллические
replacement_dict = {'e': 'е', 'y': 'у', 'u': 'и', 'o': 'о', 'p': 'р', 'a': 'а', 'k': 'к', 'x': 'х', 'c': 'с',
                    'n': 'п', 'm': 'т', 't': 'т', 'b': 'б', 'ё': 'е', '0':'о', '6':'б'}
translation_table = str.maketrans(replacement_dict)

# Функция для чтения токена и id чата из файла
def read_token_and_chat_id():
    try:
        with open(TOKEN_FILE, "r") as file:
            data = json.load(file)
            token = data.get("token")
            chat_id = data.get("chat_id")
        if token is not None and chat_id is not None:  # Проверяем, что данные были успешно считаны из файла
            return token, chat_id
        else:
            print(f"Ошибка: Не удалось получить токен и/или ID чата из файла '{TOKEN_FILE}'.")
            logging.error(f"Ошибка: Не удалось получить токен и/или ID чата из файла '{TOKEN_FILE}'.")
            return None, None
    except FileNotFoundError:
        print(f"Файл '{TOKEN_FILE}' не найден.")
        logging.error(f"Файл '{TOKEN_FILE}' не найден.")
        return None, None
    except json.JSONDecodeError:
        print(f"Ошибка при чтении файла '{TOKEN_FILE}': неверный формат JSON.")
        logging.error(f"Ошибка при чтении файла '{TOKEN_FILE}': неверный формат JSON.")
        return None, None

# Функция для записи данных в файл с указанием кодировки
def write_data_to_file(filename, data):
    with open(filename, "a", encoding="utf-8") as file:
        try:
            file.write(str(data) + "\n")
        except Exception as e:
            print(f"Ошибка при записи данных в файл: {e}")
            logging.error(f"Ошибка при записи данных в файл: {e}")

# Функция для чтения данных из файла
def read_data_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = [line.strip().lower() for line in file]
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден.")
        data = []
    return data

# Функция для записи события бана в файл
def record_ban_event(user_id, user_name, message_text, phrase, event_type):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": current_time,
        "user_id": user_id,
        "user_name": user_name,
        "ban_phrase": phrase,
        "message_text": message_text,
        "event_type": event_type}
    with open(BANSTAT_FILE, "a", encoding="utf-8") as file:
        try:
            json.dump(entry, file, ensure_ascii=False)
            file.write("\n")
        except Exception as e:
            print(f"Ошибка при записи данных в файл: {e}")
    return BANSTAT_FILE

# Функция для записи попытки добавления бота
def record_bot_add_event(user_id, user_name, bot_id, bot_name):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": current_time,
        "user_id": user_id,
        "user_name": user_name,
        "bot_id": bot_id,
        "bot_name": bot_name}
    with open(BOT_STAT_FILE, "a", encoding="utf-8") as file:
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

# Устанавливаем параметр skip_bot для обработки сообщений от других ботов
bot.skip_pending = False

#ID бота
BOT_ID = bot.get_me().id

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

# Функция для очистки текста
def preprocess_text(text):
    # Удаляем все знаки препинания, спец символы и смайлики
    text = re.sub(r'[^\w\s]', '', text)
    # Заменяем множественные пробелы на одиночные
    text = re.sub(r'\s+', ' ', text)

    # Проходим по каждому слову в тексте
    words = text.split()
    result = []
    for word in words:
        # Проверяем, являются ли все символы в слове латинскими буквами
        if all(char.isalpha() and re.match('[a-z]', char.lower()) for char in word):
            # Если да, то оставляем слово без изменений
            result.append(word)
        else:
            # Иначе, производим замену символов
            result.append(word.translate(translation_table))
    return ' '.join(result)

# Функция подсчета сообщений в бане
def count_message_occurrences(text):
    count = 0
    # Проверяем, есть ли значение в кэше для данного сообщения
    if text in message_occurrences_cache:
        return message_occurrences_cache

    with open(BANSTAT_FILE, "r", encoding="utf-8") as file:
        for line in file:
            entry = json.loads(line)
            if entry.get("message_text") == text:
                count += 1
            if count >= message_count:
                # Сохраняем результат в кэше
                message_occurrences_cache[text] = count
                return message_occurrences_cache

# Функция логирования и отправки сообщения админам
def log_and_admin_message(notification_message):
    logging.info(notification_message)
    for admin_id in admin_ids:
        if str(admin_id) == str(BOT_ID):
            continue
        try:
            bot.send_message(admin_id, notification_message)
            logging.info(f'Отправлено {admin_id}')
        except telebot.apihelper.ApiException as e:
            logging.error(f"Не удалось отправить {admin_id}: {e}")

# Логирование ошибок
def log_error(e):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Ошибка: {e}")
    logging.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Ошибка: {e}")
    time.sleep(10)  # Пауза перед повторной попыткой

#Распознаём текст с картинки
def recognize_text(image_stream):
    # Открываем изображение с помощью PIL
    image = Image.open(image_stream)
    # Используем pytesseract для распознавания текста
    extracted_text = pytesseract.image_to_string(image)

    return extracted_text

#тестим новый способ проверки
def check_suspicious_text(text, banned_phrases_new):
    found_words = [word.lower() for word in banned_phrases_new if word.lower() in text.lower()]
    found_count = len(found_words)
    total_words = len(text.split())  # Общее количество слов в тексте
    suspicious_percentage = round((found_count / total_words) * 100, 2) if total_words > 0 else 0
    suspicious = suspicious_percentage > 30
    return suspicious, found_count, found_words, suspicious_percentage

# Получение списка администраторов чата
admin_ids = get_chat_admins(CHAT_ID)

# Чтение списка запрещенных фраз
banned_phrases = read_data_from_file(BANNED_PHRASES_FILE)
banned_phrases_new = read_data_from_file(BANNED_PHRASES_FILE_NEW)

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
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_text = message.text.strip()

    # Проверка, что команда отправлена в личном сообщении и отправитель является администратором
    if str(user_id) in admin_ids:
        if str(message_text == "/start"):
            # Создаем клавиатуру
            keyboard = types.ReplyKeyboardMarkup(row_width=2)
            button_texts = ["Добавить данные в BAN", "Добавить данные в WARNING", "Статистика", "Статус"]
            for text in button_texts:
                button = types.KeyboardButton(text=text)
                keyboard.add(button)
            # Отправляем сообщение с клавиатурой в личное сообщение администратору
            try:
                bot.send_message(user_id, "Выберите действие:", reply_markup=keyboard)
            except ApiTelegramException as e:
                if e.error_code == 403:
                    bot.send_message(chat_id, "Для работы с ботом, пожалуйста, разрешите получение сообщений от ботов в настройках конфиденциальности Telegram.")
                else:
                    bot.send_message(chat_id, f"Произошла ошибка: {e}")
    if str(message_text) == "/start":
        bot.delete_message(chat_id, message.message_id)

# Обработчик для сообщений после выбора кнопки "Добавить данные в BAN"
@bot.message_handler(func=lambda message: message.text.strip() == "Добавить данные в BAN")
def add_to_ban_phrases(message):
    user_id = message.from_user.id

    if str(user_id) in admin_ids:
        bot.send_message(user_id, "Введите текст для добавления в BAN:")
        bot.delete_message(message.chat.id, message.message_id)
        bot.register_next_step_handler(message, process_ban_phrase, user_id)

# Функция для обработки текста, который нужно добавить в BAN
def process_ban_phrase(message, user_id):
    global banned_phrases
    notification_massege = []
    user_name = message.from_user.first_name
    lines = message.text.splitlines()

    for line in lines:
        new_phrase = preprocess_text(line)

    # Добавить новую фразу в файл Banned_phrases.json
        write_data_to_file(BANNED_PHRASES_FILE, new_phrase)
        logging.info(f'{user_id} {user_name} добавил фарзу "{new_phrase}" в BAN')
        notification_massege.append(new_phrase)

    # Отправить подтверждение администратору
    bot.send_message(user_id, f"Фраза\n{notification_massege}\nуспешно добавлена в BAN.")
    banned_phrases = read_data_from_file(BANNED_PHRASES_FILE)
    return banned_phrases

# Обработчик для сообщений после выбора кнопки "Добавить данные в WARNING"
@bot.message_handler(func=lambda message: message.text.strip() == "Добавить данные в WARNING")
def add_to_warning_phrases(message):
    user_id = message.from_user.id

    if str(user_id) in admin_ids:
        bot.send_message(user_id, "Введите текст для добавления в WARNING:")
        bot.delete_message(message.chat.id, message.message_id)
        bot.register_next_step_handler(message, process_warning_phrase, user_id)

# Функция для обработки текста, который нужно добавить в WARNING
def process_warning_phrase(message, user_id):
    global warning_phrases
    new_phrase = message.text.strip()
    user_name = message.from_user.first_name

    # Добавить новую фразу в файл warning_phrases.json
    write_data_to_file(WARNING_PHRASES_FILE, new_phrase)

    # Отправить подтверждение администратору
    bot.send_message(user_id, f"Фраза\n'{new_phrase}'\nуспешно добавлена в WARNING.")
    logging.info(f'{user_id} {user_name} добавил фарзу "{new_phrase}" в Warning')
    warning_phrases = read_data_from_file(WARNING_PHRASES_FILE)

    return warning_phrases

# Обработчик для сообщений после выбора кнопки "Статистика"
@bot.message_handler(func=lambda message: message.text.strip() == "Статистика")
def handle_statistics(message):
    user_id = message.from_user.id
    if str(user_id) in admin_ids:
        bot.send_message(user_id,"Введите интервал дат для вывода статистики в формате 'гггг-мм-дд гггг-мм-дд', например, '2024-02-01 2024-02-07':")
        bot.delete_message(message.chat.id, message.message_id)
        bot.register_next_step_handler(message, process_dates)

# Функция для обработки полученных дат
def process_dates(message):
    date_range = message.text.split()
    chat_id = message.chat.id
    if len(date_range) == 1:
        start_date = end_date = date_range[0]
    elif len(date_range) == 2:
        start_date, end_date = date_range
    else:
        bot.send_message(chat_id, "Неправильный формат ввода. Попробуйте снова.")
        return

    file_path = BANSTAT_FILE
    file_bot_path = BOT_STAT_FILE
    count_ban, count_warning, count_bot, count_mut = count_events(file_path, file_bot_path, start_date, end_date)
    bot.send_message(chat_id, f"За период с {start_date} по {end_date}:\n"
                                      f"Рекламных {count_ban} сообщений,\n"
                                      f"Вынесено {count_warning} предупреждений,\n"
                                      f"Заблокировано {count_mut},\n"
                                      f"Удалено {count_bot} ботов")

# Функция для подсчета событий в указанном диапазоне дат
def count_events(file_path, file_bot_path, start_date, end_date):
    count_ban = 0
    count_warning = 0
    count_bot = 0
    count_mut = 0
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
                elif event_data['event_type'] == 'MUT':
                    count_mut += 1
    with open(file_bot_path, 'r', encoding='utf-8') as file:
        for line in file:
            event_data = json.loads(line)
            timestamp = datetime.strptime(event_data['timestamp'][:10], '%Y-%m-%d')
            if start_datetime <= timestamp <= end_datetime:
                count_bot += 1
    return count_ban, count_warning, count_bot, count_mut

# Обработчик для сообщений после выбора кнопки "Статус"
@bot.message_handler(func=lambda message: message.text.strip() == "Статус")
def status_command(message):
    user_id = message.from_user.id

    if str(user_id) in admin_ids:
        # Отправляем сообщение со статусом и временем запуска бота
        bot.send_message(user_id, f"Статус бота: онлайн\nВремя запуска бота: {bot_start_time}")
        bot.delete_message(message.chat.id, message.message_id)

#Обработка сообщений с фото
@bot.message_handler(content_types=['photo', 'audio', 'documents', 'video', 'voice', 'sticker'])
def handle_photo(message):
    # Обработка подписи к фотографии, если есть
    if message.caption:
        message_text = message.caption
#    if message.photo:
#        file_id = message.photo[-1].file_id
#        file_info = bot.get_file(file_id)
#        image_stream = BytesIO()
#        file_info.download(out=image_stream)
#        image_stream.seek(0)
#        # Распознаем текст на картинке
#        extracted_text = recognize_text(image_stream)
#
#        message_text.append(f"Текст с картинки: '{extracted_text}'")

        handle_text_messages(message, message_text)

#Обработка всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message, message_text=None):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    message_id = message.message_id
    words = ()

    # Проверка, является ли отправитель администратором
    # Не выполняем никаких действий, если отправитель администратор
    if str(user_id) in admin_ids:
        return

    #Если нет текста не выполняем дальше
    if message_text is None:
        message_text = message.text
        if message_text is None:
            return

    #тестим новый способ проверки
    logging.info(message_text)
    suspicious, found_count, found_words, suspicious_percentage = check_suspicious_text(preprocess_text(message_text), banned_phrases_new)
    if suspicious:
        logging.info(f"Текст подозрителен. Количество совпавших слов: {found_count}, {suspicious_percentage}%")
        logging.info(f"Совпавшие слова: {', '.join(found_words)}")
    else:
        logging.info(f"Текст не подозрителен. Количество совпавших слов: {found_count}, {suspicious_percentage}%")
        logging.info(f"Совпавшие слова: {', '.join(found_words)}")


    # Проверка на повторяющиеся сообщения
    if count_message_occurrences(message_text):
        bot.delete_message(chat_id, message_id)
        notification_message = f"Пользователь {user_name} (ID: {user_id}) отправил повторяющееся сообщение:\n'{message_text}'\nя его замутил на 14 дней"
        record_ban_event(user_id, user_name, message_text,'повтор сообщения',"MUT")
        log_and_admin_message(notification_message)
        #bot.kick_chat_member(CHAT_ID, user_id)
        #Заменить 'MUTE_DURATION' на длительность мута в секундах
        bot.restrict_chat_member(chat_id, user_id, until_date = time.time() + MUTE_DURATION, can_send_messages=False)
        logging.info(f"Пользователь {user_name} ID: {user_id}, заблокирован на 14 дней")
        return

    #Приводим текст в единый формат
    text = preprocess_text(message_text)

    # Проверка на наличие рекламных сообщений
    for phrase in banned_phrases:
        words = phrase.split()
        found = all(word.lower() in text.lower() for word in words)
        if found:
            ban_message = f"Я подозреваю, что {user_name} (ID: {user_id}) отправил рекламу, этому сообщению не место в этом чате!"
            bot.delete_message(chat_id, message_id)
            record_ban_event(user_id, user_name, message_text, phrase,"BAN")
            sent_message = bot.send_message(chat_id, ban_message)
            notification_message = f"Сообщение от пользователя {user_name} (ID: {user_id}) удалено за отправку рекламы\nСловосочетание:\n'{phrase}'\nСообщение пользователя:\n'{message_text}'"
            log_and_admin_message(notification_message)
            threading.Thread(target=delete_message_after_delay, args=(sent_message.chat.id, sent_message.message_id, DELETE_MESSAGE_DELAY)).start()
            break

    # Проверка на наличие матерных слов
    if not found:
        for phrase in warning_phrases:
            words = phrase.split()
            found = any(len(word) == len(word.lower()) and word.lower() in text.split() for word in words)
            if found:
                warning_message = f"Пользователь {user_name} (ID: {user_id}) ваше сообщение содержало запрещенное в этом чате слово {phrase}, попробуйте написать иначе."
                bot.delete_message(chat_id, message_id)
                record_ban_event(user_id, user_name, message_text, phrase,"WARNING")
                sent_message = bot.send_message(chat_id, warning_message)
                notification_message = f"Сообщение от пользователя  {user_name} (ID: {user_id}) удалено за отправку сообщения с матом:\nСлово:\n{phrase}\nСообщение пользователя:\n'{message_text}'"
                log_and_admin_message(notification_message)
                threading.Thread(target=delete_message_after_delay, args=(sent_message.chat.id, sent_message.message_id, DELETE_MESSAGE_DELAY)).start()
                break

# Удаление сообщений о вступлении и выходе из чата
@bot.message_handler(content_types=['new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo',
                                    'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created',
                                    'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id'])
def delete(message):
    try:
        if message.content_type == 'new_chat_members':
            for new_chat_member in message.new_chat_members:
                if new_chat_member.is_bot:
                    # Попытка выгнать бота из чата
                    bot.kick_chat_member(message.chat.id, new_chat_member.id)
                    # Получение информации о пользователе, попытка записи события
                    user_id = message.from_user.id
                    user_name = message.from_user.first_name + ' ' + message.from_user.last_name
                    bot_id = new_chat_member.id
                    bot_name = new_chat_member.username
                    record_bot_add_event(user_id, user_name, bot_id, bot_name)
                    notification_message = f"Пользователь {user_name} (ID: {user_id}) попытался добавить бота:\n'{bot_name}'"
                    log_and_admin_message(notification_message)
        # Попытка удалить сообщение
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        # Обработка ошибок
        print(f"Произошла ошибка: {e}")
        logging.error(f"Произошла ошибка: {e}")

# Запуск бота
while True:
    try:
        bot_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        chat_title = bot.get_chat(CHAT_ID).title
        print(f"Бот запущен в {bot_start_time} в чате {chat_title}")
        logging.info(f"Бот запущен {bot_start_time} в чате ID{CHAT_ID}, {chat_title}")
        # Список администраторов для печати
        admins_list = []
        for admin_id in admin_ids:
            admin_info = bot.get_chat_member(CHAT_ID, user_id = admin_id)
            admin_name = admin_info.user.first_name
            admin_last_name = admin_info.user.last_name
            if admin_last_name == None:
                admin_last_name = ''
            admins_list.append(admin_name + ' ' + admin_last_name)
        print(f'Администраторы {admins_list}')
        bot.polling(timeout=320, none_stop=True)
        time.sleep(5)  # Задержка перед чтением администраторов

# Обработка ошибок
    except telebot.apihelper.ApiTelegramException as e:
        log_error(e)
    except Exception as e:
        log_error(e)
