# Geoscan_bot
Этот бот предназначен для модерации сообщений в чатах Telegram. Он автоматически удаляет сообщения, содержащие запрещенные фразы, и ведет статистику по забаненным и предупрежденным пользователям.

**Как начать использование:**
1. Убедитесь, что у вас установлен Python версии 3.x.
2. Установите необходимые библиотеки, выполнив команду `pip install -r requirements.txt`.
3. Создайте файл `token.json` и добавьте в него токен вашего бота и id чата, в котором он будет работать, в следующем формате:

"{"token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"}"

Особенности:

1. Модерация сообщений:
Бот автоматически удаляет сообщения, содержащие запрещенные фразы/слова, которые указаны в файлах banned_phrases.json и warning_phrases.json.
При обнаружении нарушения бот отправляет уведомление в чат. На этапе тестирования БАН пользователя не применяется. Списки фраз пополняются и обновляются. Текущие спики используются только для тестирования

3. Удаление сервисных сообщений:
Бот удаляет сообщения о вступлении и выходе из чата, изменении названия чата и другие служебные сообщения, которые не являются релевантными для пользователей.

4. Не позволяет пригласить бота в группу:
При добавление бота в группу, бот удаляется, добавивший и сам бот попадает в статистику нарушителей.

5. Статистика:
Бот ведет статистику по забаненным и предупрежденным пользователям, записывая данные в файл banstat.json.
Статистика включает количество забаненных сообщений и вынесенных предупреждений с указанием даты и времени события. Отдельная статистика ведется по добавившим ботов в группу.

Управление.

- Администрирование бота:
Администраторы чата могут использовать команду /start, чтобы вызвать меню управления ботом и просмотреть статистику.

- Добавление новых фраз:
Администраторы могут добавлять новые запрещенные и предупреждающие фразы через команды бота.

- Вызов статистики:
При вводе даты или интервала дат в установленном формате бот присылает сообщение о количестве событий WARNING и BAN за выбранный промежуток времени или за указанную дату.

- Запрос статуса:
В ответ бот присылает сообщение, когда он был запущен.
