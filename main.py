import telebot
import os
import datetime
from telebot.apihelper import ApiTelegramException

# Configurations
DEBUG = True
ADMIN_IDS = [7563861429]

# with open(r'c:\\Users\\Matvejs Upesleja\\Desktop\\bottoken1.txt', 'r') as f:
    # TOKEN = f.read().strip()

TOKEN = input("Isert token: ")

print("\nBot Started...\n")

bot = telebot.TeleBot(TOKEN)

# Keyboards
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📝 Заметки"))
    keyboard.add(KeyboardButton("📄 Команды"), KeyboardButton("ℹ️ О боте"))
    keyboard.add(KeyboardButton("💬 Поддержка"))
    return keyboard

def notes_list_keyboard(notes, page, notes_per_page):
    keyboard = InlineKeyboardMarkup()
    start = page * notes_per_page
    end = start + notes_per_page
    for i, note in enumerate(notes[start:end], start=start):
        title = note.split("::", 2)[1].strip()
        emoji = note.split("::", 2)[0].strip()
        keyboard.add(InlineKeyboardButton(f"{emoji} {title}", callback_data=f"open_{i}"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page - 1}"))
    if end < len(notes):
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"page_{page + 1}"))
    if nav_buttons:
        keyboard.row(*nav_buttons)
    keyboard.add(InlineKeyboardButton("➕ Новая заметка", callback_data="new_note"))
    return keyboard

def note_manage_keyboard(index, page):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{index}_{page}"))
    keyboard.add(InlineKeyboardButton("Поменять заголовок", callback_data=f"edit_title_{index}"))
    keyboard.add(InlineKeyboardButton("Поменять заметку", callback_data=f"edit_body_{index}"))
    keyboard.add(InlineKeyboardButton("🎨 Изменить эмодзи", callback_data=f"edit_emoji_{index}"))
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page}"))
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("❌ Отмена"))
    return keyboard

def cancel_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

def popular_emoji_keyboard():
    """
    Creates a keyboard with topic-related emojis in rows of 3 and a cancel button.
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    topic_emojis = ["📚", "📝", "💡", "📅", "✅", "❌", "🎯", "📊", "📌", "🔍"]
    for i in range(0, len(topic_emojis), 3):
        row = [InlineKeyboardButton(emoji, callback_data=f"emoji_{emoji}") for emoji in topic_emojis[i:i+3]]
        keyboard.row(*row)
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

# Для создания заметок
user_note_state = {}
user_note_title = {}
user_note_emoji = {}
user_note_body = {}
user_feedback = {}

NOTES_DIR = r"C:\\Users\\Matvejs Upesleja\\Desktop\\Bot\\notes"

if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

def log_command(message):
    if DEBUG:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] {message.from_user.id} - {message.text}")

def is_admin(user_id):
    return user_id in ADMIN_IDS

def escape_markdown(text):
    """
    Escapes special characters in Markdown text to prevent formatting issues.
    """
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

feedback_storage = []  # Хранилище для обратной связи

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    log_command(message)
    bot.send_message(message.chat.id, "👋 Привет! Добро пожаловать в бота!", reply_markup=main_menu())

# Команда /admin
@bot.message_handler(commands=['admin'])
def admin(message):
    log_command(message)
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🛠 Вы админ. Спецкоманды доступны.\n\n/crash — Перезапуск бота")
    else:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")

# Команда /crash
@bot.message_handler(commands=['crash'])
def crash(message):
    log_command(message)
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "💥 Бот остановлен. Запустите скрипт вручную для перезапуска.")
        print("\n=== Бот остановлен командой /crash ===\n")
        os._exit(0)
    else:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")

# Команда /feedback
@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    if is_admin(message.from_user.id):
        # Если админ, показать все обратные связи
        if feedback_storage:
            feedback_list = "\n\n".join([f"📩 От @{fb['username']}:\n{fb['text']}" for fb in feedback_storage])
            bot.send_message(message.chat.id, f"Все сообщения обратной связи:\n\n{feedback_list}")
        else:
            bot.send_message(message.chat.id, "Обратная связь: Пусто.")
    else:
        # Если пользователь, запросить сообщение
        msg = bot.send_message(message.chat.id, "Напишите ваше сообщение, и я передам его админам:")
        bot.register_next_step_handler(msg, save_feedback)

def save_feedback(message):
    feedback_storage.append({
        "username": message.from_user.username or "Без имени",
        "text": message.text
    })
    bot.send_message(message.chat.id, "Спасибо! Ваше сообщение отправлено.")
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, f"📩 Новое сообщение от @{message.from_user.username}:\n{message.text}")
        except ApiTelegramException:
            print(f"Ошибка отправки сообщения админу с ID {admin_id}")

# 📄 Команды
@bot.message_handler(func=lambda m: m.text == '📄 Команды')
def commands(message):
    log_command(message)
    bot.send_message(message.chat.id, "/start — Запуск бота\n/admin — Панель администратора\n/crash — Остановить бота\n/feedback — Отправить сообщение администратору (abuse = BANana)")

# ℹ️ О боте
def about(message):
    log_command(message)
    bot.send_message(message.chat.id, "Этот бот создан для управления личными заметками.\nРазработчик: @KusokMedi52")

# ℹ️ О боте
@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def bot_about(message):
    about(message)

# 💬 Поддержка
@bot.message_handler(func=lambda m: m.text == '💬 Поддержка')
def support(message):
    log_command(message)
    bot.send_message(message.chat.id, "Свяжитесь с поддержкой => @KusokMedi52.")

# Обработка кнопки "📝 Заметки" в главном меню
@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    user_id = message.from_user.id
    notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
    notes = []
    if os.path.exists(notes_file):
        with open(notes_file, "r", encoding="utf-8") as f:
            notes = [n for n in f.read().split("---note---") if n.strip()]
    if notes:
        bot.send_message(
            message.chat.id,
            f"📜 Ваши заметки (Страница 1/{(len(notes) + 4) // 5})",
            reply_markup=notes_list_keyboard(notes, 0, 5)
        )
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Новая заметка", callback_data="new_note"))
        bot.send_message(
            message.chat.id,
            "📝 У вас пока нет заметок. Нажмите ➕ Новая заметка, чтобы создать.",
            reply_markup=keyboard
        )

# Обработка callback кнопок
@bot.callback_query_handler(func=lambda call: not (call.data.startswith("emoji_") or call.data == "cancel"))
def callback_handler(call):
    user_id = call.from_user.id

    # Обработка начала редактирования заголовка
    if call.data.startswith("edit_title_"):
        try:
            index = int(call.data.split("_")[2])
            user_note_state[user_id] = f"edit_title_{index}"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Добавить в начало", callback_data=f"edit_mode_prepend_{index}"))
            keyboard.add(InlineKeyboardButton("Добавить в конец", callback_data=f"edit_mode_append_{index}"))
            keyboard.add(InlineKeyboardButton("Заменить полностью", callback_data=f"edit_mode_replace_{index}"))
            keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
            bot.edit_message_text(
                "Выберите способ редактирования заголовка:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        except (IndexError, ValueError, Exception):
            bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
        return

    # Обработка начала редактирования содержимого заметки
    if call.data.startswith("edit_body_"):
        try:
            index = int(call.data.split("_")[2])
            user_note_state[user_id] = f"edit_body_{index}"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Добавить в начало", callback_data=f"edit_mode_prepend_{index}"))
            keyboard.add(InlineKeyboardButton("Добавить в конец", callback_data=f"edit_mode_append_{index}"))
            keyboard.add(InlineKeyboardButton("Заменить полностью", callback_data=f"edit_mode_replace_{index}"))
            keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
            bot.edit_message_text(
                "Выберите способ редактирования заметки:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        except (IndexError, ValueError, Exception):
            bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
        return

    # Обработка выбора способа редактирования
    if call.data.startswith("edit_mode_"):
        try:
            parts = call.data.split("_")
            mode = parts[2]  # prepend, append, replace
            index = int(parts[3])
            state = user_note_state.get(user_id)
            if state and (state.startswith("edit_title_") or state.startswith("edit_body_")):
                # Update state to include mode
                user_note_state[user_id] = f"{state}_{mode}"
                bot.edit_message_text(
                    "📝 Введите текст для редактирования:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=cancel_inline_keyboard()
                )
            else:
                bot.answer_callback_query(call.id, "Ошибка: неверное состояние редактирования.")
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
        return
    # Обработка выбора эмодзи при редактировании
    if call.data.startswith("edit_emoji_"):
        try:
            index = int(call.data.split("_")[2])
            user_note_state[user_id] = f"change_emoji_{index}"
            bot.edit_message_text(
                "🎨 Выберите новый эмодзи для заметки:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=popular_emoji_keyboard()
            )
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
        return

    # Обработка подтверждения редактирования
    if call.data.startswith("edit_confirm_yes_"):
        try:
            index = int(call.data.split("_")[3])
            state = user_note_state.get(user_id)
            if not state or not state.startswith("edit_confirm_"):
                bot.answer_callback_query(call.id, "Ошибка: нет данных для подтверждения.")
                return
            # Save the edited note
            notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
            if not os.path.exists(notes_file):
                bot.answer_callback_query(call.id, "Ошибка: заметки не найдены.")
                user_note_state.pop(user_id, None)
                return
            with open(notes_file, "r", encoding="utf-8") as f:
                notes = [n for n in f.read().split("---note---") if n.strip()]
            if not (0 <= index < len(notes)):
                bot.answer_callback_query(call.id, "Ошибка: неверный индекс заметки.")
                user_note_state.pop(user_id, None)
                return
            note_parts = notes[index].split("::", 2)
            # Use the buffered edited data
            emoji = user_note_emoji.get(user_id, note_parts[0].strip())  # Default to original emoji if not updated
            title = user_note_title.get(user_id, note_parts[1].strip())  # Default to original title if not updated
            body = user_note_body.get(user_id, note_parts[2].strip())  # Default to original body if not updated
            try:
                bot.edit_message_text(
                    f"✏️ Заметка обновлена:\n\n{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="Markdown",
                    reply_markup=note_manage_keyboard(index, index // 5)
                )
            except Exception as e:
                bot.send_message(
                    call.message.chat.id,
                    f"Ошибка при обновлении заметки: {e}",
                    parse_mode="Markdown",
                    reply_markup=note_manage_keyboard(index, index // 5)
                )
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка при подтверждении: {e}")
    elif call.data == "cancel":
        user_note_state.pop(user_id, None)
        user_note_title.pop(user_id, None)
        user_note_emoji.pop(user_id, None)
        bot.answer_callback_query(call.id, "❌ Отменено.")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")
        bot.send_message(
            call.message.chat.id,
            "❌ Отменено. Возвращаюсь в главное меню.",
            reply_markup=main_menu()
        )
        return

    if call.data == "new_note":
        user_note_state[user_id] = "title"
        user_note_emoji[user_id] = "📄"  # Default emoji set to paper emoji
        bot.send_message(
            call.message.chat.id,
            "✍️ Введите заголовок новой заметки.",
            reply_markup=cancel_keyboard()
        )
        return


    notes_file = os.path.join(NOTES_DIR, f"notes_{call.from_user.id}.txt")
    if not os.path.exists(notes_file):
        try:
            bot.answer_callback_query(call.id, "Нет заметок.")
        except ApiTelegramException:
            pass  # Ignore expired callback query
        return

    with open(notes_file, "r", encoding="utf-8") as f:
        notes = [n for n in f.read().split("---note---") if n.strip()]

    notes_per_page = 5

    if call.data.startswith("open_"):
        try:
            index = int(call.data.split("_")[1])
            if 0 <= index < len(notes):
                note_parts = notes[index].split("::", 2)
                emoji = note_parts[0].strip()
                title = note_parts[1].strip()
                body = note_parts[2].strip()
                page = index // notes_per_page
                try:
                    bot.edit_message_text(
                        f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="Markdown",
                        reply_markup=note_manage_keyboard(index, page)
                    )
                except ApiTelegramException:
                    bot.send_message(
                        call.message.chat.id,
                        f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                        parse_mode="Markdown",
                        reply_markup=note_manage_keyboard(index, page)
                    )
        except (IndexError, ValueError):
            try:
                bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
            except ApiTelegramException:
                pass  # Ignore expired callback query
    elif call.data.startswith("page_"):
        try:
            page = int(call.data.split("_")[1])
            total_pages = (len(notes) + notes_per_page - 1) // notes_per_page
            try:
                bot.edit_message_text(
                    f"📜 Ваши заметки (Страница {page + 1}/{total_pages})",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=notes_list_keyboard(notes, page, notes_per_page)
                )
            except ApiTelegramException:
                bot.send_message(
                    call.message.chat.id,
                    f"📜 Ваши заметки (Страница {page + 1}/{total_pages})",
                    reply_markup=notes_list_keyboard(notes, page, notes_per_page)
                )
        except (IndexError, ValueError):
            try:
                bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
            except ApiTelegramException:
                pass  # Ignore expired callback query
    elif call.data.startswith("delete_"):
        try:
            parts = call.data.split("_")
            index = int(parts[1])
            page = int(parts[2])

            if 0 <= index < len(notes):
                del notes[index]
                with open(notes_file, "w", encoding="utf-8") as f:
                    for note in notes:
                        f.write(note.strip() + "\n---note---\n")
                try:
                    bot.answer_callback_query(call.id, "✅ Заметка удалена.")
                    # Удаляем сообщение с заметкой из чата
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except Exception:
                        pass
                except ApiTelegramException:
                    pass  # Ignore expired callback query

                if notes:
                    try:
                        bot.edit_message_text(
                            f"📜 Ваши заметки (Страница {page + 1})",
                            call.message.chat.id,
                            call.message.message_id,
                            reply_markup=notes_list_keyboard(notes, page, notes_per_page)
                        )
                    except ApiTelegramException:
                        bot.send_message(
                            call.message.chat.id,
                            f"📜 Ваши заметки (Страница {page + 1})",
                            reply_markup=notes_list_keyboard(notes, page, notes_per_page)
                        )
                else:
                    try:
                        bot.send_message(
                            call.message.chat.id,
                            "📝 Все заметки удалены. Создайте новую!",
                            reply_markup=main_menu()  # Use main menu keyboard here
                        )
                    except ApiTelegramException:
                        pass
            else:
                try:
                    bot.answer_callback_query(call.id, "Ошибка удаления.")
                except ApiTelegramException:
                    pass  # Ignore expired callback query
        except (IndexError, ValueError):
            try:
                bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
            except ApiTelegramException:
                pass  # Ignore expired callback query
            parts = call.data.split("_")
            index = int(parts[1])
            page = int(parts[2])

            if 0 <= index < len(notes):
                del notes[index]
                with open(notes_file, "w", encoding="utf-8") as f:
                    for note in notes:
                        f.write(note.strip() + "\n---note---\n")
                try:
                    bot.answer_callback_query(call.id, "✅ Заметка удалена.")
                    # Удаляем сообщение с заметкой из чата
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except Exception:
                        pass
                except ApiTelegramException:
                    pass  # Ignore expired callback query

                if notes:
                    bot.edit_message_text(
                        f"📜 Ваши заметки (Страница {page + 1})",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=notes_list_keyboard(notes, page, notes_per_page)
                    )
                else:
                    bot.edit_message_text(
                        "📝 Все заметки удалены. Создайте новую!",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=main_menu()  # Use main menu keyboard here
                    )
            else:
                try:
                    bot.answer_callback_query(call.id, "Ошибка удаления.")
                except ApiTelegramException:
                    pass  # Ignore expired callback query
        except (IndexError, ValueError):
            try:
                bot.answer_callback_query(call.id, "Ошибка: некорректный формат данных.")
            except ApiTelegramException:
                pass  # Ignore expired callback query

# Обработка callback кнопок для выбора эмодзи
@bot.callback_query_handler(func=lambda call: call.data.startswith("emoji_") or call.data == "cancel")
def emoji_selection_handler(call):
    user_id = call.from_user.id
    print(f"DEBUG: emoji_selection_handler called with call.data={call.data} and user_note_state={user_note_state.get(user_id)}")
    if call.data == "cancel":
        user_note_state.pop(user_id, None)
        bot.edit_message_text(
            "❌ Отменено. Возвращаюсь в главное меню.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )
    elif call.data.startswith("emoji_"):
        emoji = call.data[len("emoji_"):]
        state = user_note_state.get(user_id)
        print(f"DEBUG: emoji selected: {emoji}, current state: {state}")
        if state and state.startswith("change_emoji_"):
            index = int(state.split("_")[2])
            notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
            if os.path.exists(notes_file):
                with open(notes_file, "r", encoding="utf-8") as f:
                    notes = [n for n in f.read().split("---note---") if n.strip()]
                if 0 <= index < len(notes):
                    note_parts = notes[index].split("::", 2)
                    title = note_parts[1].strip()
                    body = note_parts[2].strip()
                    notes[index] = f"{emoji}::{title}::{body}"
                    with open(notes_file, "w", encoding="utf-8") as f:
                        for note in notes:
                            f.write(note.strip() + "\n---note---\n")
                    bot.answer_callback_query(call.id, "🎨 Эмодзи обновлено!")
                    # Instead of showing main menu, show updated note with note_manage_keyboard
                    try:
                        bot.edit_message_text(
                            f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                            call.message.chat.id,
                            call.message.message_id,
                            parse_mode="Markdown",
                            reply_markup=note_manage_keyboard(index, index // 5)
                        )
                    except Exception:
                        bot.send_message(
                            call.message.chat.id,
                            f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                            parse_mode="Markdown",
                            reply_markup=note_manage_keyboard(index, index // 5)
                        )
            user_note_state.pop(user_id, None)
            user_note_title.pop(user_id, None)
            user_note_emoji.pop(user_id, None)
            return
        elif state == "emoji":
            user_note_emoji[user_id] = emoji
            bot.answer_callback_query(call.id, "🎨 Эмодзи выбрано!")
            user_note_state[user_id] = "body"
            try:
                bot.edit_message_text(
                    "📝 Введите содержимое заметки.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=cancel_inline_keyboard()
                )
            except Exception:
                bot.send_message(call.message.chat.id, "📝 Введите содержимое заметки.", reply_markup=cancel_keyboard())
        else:
            user_note_emoji[user_id] = emoji
            bot.answer_callback_query(call.id, "🎨 Эмодзи выбрано!")
            user_note_state[user_id] = "body"
            try:
                bot.edit_message_text(
                    "📝 Введите содержимое заметки.",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=cancel_inline_keyboard()
                )
            except Exception:
                bot.send_message(call.message.chat.id, "📝 Введите содержимое заметки.", reply_markup=cancel_keyboard())

# Обработка ввода текста (заметка)
@bot.message_handler(func=lambda message: user_note_state.get(message.from_user.id) in ["title", "body", "emoji"] or (user_note_state.get(message.from_user.id) and user_note_state.get(message.from_user.id).startswith(("edit_title_", "edit_body_"))))
def note_text_handler(message):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ Отмена":
        user_note_state.pop(user_id, None)
        user_note_title.pop(user_id, None)
        user_note_emoji.pop(user_id, None)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass
        bot.send_message(
            message.chat.id,
            "❌ Отменено. Возвращаюсь в главное меню.",
            reply_markup=main_menu()
        )
        return

    state = user_note_state.get(user_id)
    if state == "title":
        user_note_title[user_id] = text
        log_command(message)  # Log note title input
        user_note_state[user_id] = "emoji"
        bot.send_message(
            message.chat.id,
            "🎨 Выберите эмодзи для заметки:",
            reply_markup=popular_emoji_keyboard()
        )
    elif state == "body":
        if user_id not in user_note_title:
            bot.send_message(message.chat.id, "Ошибка: заголовок заметки не найден. Пожалуйста, начните заново.", reply_markup=main_menu())
            user_note_state.pop(user_id, None)
            user_note_emoji.pop(user_id, None)
            return
        title = user_note_title[user_id]
        body = text
        emoji = user_note_emoji.get(user_id, "📄")  # Default emoji
        notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(f"{emoji}::{title.strip()}::{body.strip()}\n---note---\n")
        log_command(message)  # Log note body input and save
        user_note_state.pop(user_id, None)
        user_note_title.pop(user_id, None)
        user_note_emoji.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            "✅ Заметка сохранена!",
            reply_markup=main_menu()
        )
    elif state and (state.startswith("edit_title_") or state.startswith("edit_body_")):
        # Обработка редактирования заметки
        try:
            parts = state.split("_")
            part = parts[1]  # title or body
            index = int(parts[2])
            mode = parts[3]  # prepend, append, replace
            notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
            if not os.path.exists(notes_file):
                bot.send_message(message.chat.id, "Ошибка: заметки не найдены.", reply_markup=main_menu())
                user_note_state.pop(user_id, None)
                return
            with open(notes_file, "r", encoding="utf-8") as f:
                notes = [n for n in f.read().split("---note---") if n.strip()]
            if not (0 <= index < len(notes)):
                bot.send_message(message.chat.id, "Ошибка: неверный индекс заметки.", reply_markup=main_menu())
                user_note_state.pop(user_id, None)
                return
            note_parts = notes[index].split("::", 2)
            emoji = note_parts[0].strip()
            title = note_parts[1].strip()
            body = note_parts[2].strip()
            new_text = text.strip()
            if part == "title":
                if mode == "prepend":
                    title = new_text + title
                elif mode == "append":
                    title = title + new_text
                elif mode == "replace":
                    title = new_text
            elif part == "body":
                if mode == "prepend":
                    body = new_text + body
                elif mode == "append":
                    body = body + new_text
                elif mode == "replace":
                    body = new_text
            notes[index] = f"{emoji}::{title}::{body}"
            # Сохраняем изменения во временный буфер для подтверждения
            user_note_title[user_id] = title
            user_note_body[user_id] = body
            user_note_emoji[user_id] = emoji
            user_note_state[user_id] = f"edit_confirm_{index}"
            # Отправляем превью для подтверждения
            preview_text = f"✏️ Предпросмотр заметки:\n\n{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("✅ Подтвердить", callback_data=f"edit_confirm_yes_{index}"))
            keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
            bot.send_message(
                message.chat.id,
                preview_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User {user_id} edited note {index} ({part}, {mode})")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при редактировании: {e}", reply_markup=main_menu())

# Обработка любых других сообщений
@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    bot.send_message(message.chat.id, "Неверная команда/текст ❌", reply_markup=main_menu())

if __name__ == "__main__":
    bot.polling(none_stop=True)