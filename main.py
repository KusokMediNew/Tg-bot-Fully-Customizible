import telebot
import os
import datetime
from telebot.apihelper import ApiTelegramException
from config import BOT_TOKEN, ADMIN_IDS, DEBUG

# Configurations
TOKEN = BOT_TOKEN

print("\nBot Started...\n")

bot = telebot.TeleBot(TOKEN)

# Keyboards
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Для создания заметок
user_note_state = {}
user_note_title = {}
user_note_emoji = {}
user_note_body = {}
feedback_storage = []
# Структура каждого элемента в feedback_storage:
# {
#     "username": имя пользователя,
#     "text": текст сообщения,
#     "status": "в ожидании" | "прочитано" | "отвечено",
#     "admin_response": текст ответа администратора (если есть)
# }

NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes")

if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

# Utility functions
def log_command(message):
    if DEBUG:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] {message.from_user.id} - {message.text}")

def is_admin(user_id):
    return user_id in ADMIN_IDS

def escape_markdown(text):
    """Escapes special characters in Markdown text to prevent formatting issues."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text

def safe_callback_answer(call, text):
    """Safely answer callback query, ignoring expired queries."""
    try:
        bot.answer_callback_query(call.id, text)
    except ApiTelegramException:
        pass

def safe_edit_message(call, text, reply_markup=None, parse_mode=None):
    """Safely edit message, fallback to send if edit fails."""
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             reply_markup=reply_markup, parse_mode=parse_mode)
    except ApiTelegramException:
        bot.send_message(call.message.chat.id, text, reply_markup=reply_markup, parse_mode=parse_mode)

def get_notes(user_id):
    """Get user notes from file."""
    notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
    if not os.path.exists(notes_file):
        return []
    with open(notes_file, "r", encoding="utf-8") as f:
        return [n for n in f.read().split("---note---") if n.strip()]

def save_notes(user_id, notes):
    """Save user notes to file."""
    notes_file = os.path.join(NOTES_DIR, f"notes_{user_id}.txt")
    with open(notes_file, "w", encoding="utf-8") as f:
        for note in notes:
            f.write(note.strip() + "\n---note---\n")

def clear_user_state(user_id):
    """Clear user state data."""
    user_note_state.pop(user_id, None)
    user_note_title.pop(user_id, None)
    user_note_emoji.pop(user_id, None)
    user_note_body.pop(user_id, None)

# Keyboard functions
def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📝 Заметки"))
    keyboard.add(KeyboardButton("📄 Команды"), KeyboardButton("ℹ️ О боте"))
    keyboard.add(KeyboardButton("💬 Поддержка"))
    return keyboard

def notes_list_keyboard(notes, page, notes_per_page=5):
    keyboard = InlineKeyboardMarkup()
    start = page * notes_per_page
    end = start + notes_per_page

    for i, note in enumerate(notes[start:end], start=start):
        parts = note.split("::", 2)
        emoji = parts[0].strip()
        title = parts[1].strip()
        keyboard.add(InlineKeyboardButton(f"{emoji} {title}", callback_data=f"open_{i}"))

    # Navigation buttons
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
    keyboard = InlineKeyboardMarkup(row_width=3)
    topic_emojis = ["📚", "📝", "💡", "📅", "✅", "❌", "🎯", "📊", "📌", "🔍"]
    for i in range(0, len(topic_emojis), 3):
        row = [InlineKeyboardButton(emoji, callback_data=f"emoji_{emoji}") for emoji in topic_emojis[i:i+3]]
        keyboard.row(*row)
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

def edit_mode_keyboard(index):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Добавить в начало", callback_data=f"edit_mode_prepend_{index}"))
    keyboard.add(InlineKeyboardButton("Добавить в конец", callback_data=f"edit_mode_append_{index}"))
    keyboard.add(InlineKeyboardButton("Заменить полностью", callback_data=f"edit_mode_replace_{index}"))
    keyboard.add(InlineKeyboardButton("Отмена", callback_data="cancel"))
    return keyboard

# Command handlers
@bot.message_handler(commands=['start'])
def start(message):
    log_command(message)
    bot.send_message(message.chat.id, "👋 Привет! Добро пожаловать в бота!", reply_markup=main_menu())

@bot.message_handler(commands=['admin'])
def admin(message):
    log_command(message)
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🛠 Вы админ. Спецкоманды доступны.\n\n/crash — Перезапуск бота\n/feedbackview — Просмотр и ответ на обратную связь")
    else:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")

@bot.message_handler(commands=['crash'])
def crash(message):
    log_command(message)
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "💥 Бот остановлен. Запустите скрипт вручную для перезапуска.")
        print("\n=== Бот остановлен командой /crash ===\n")
        os._exit(0)
    else:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")

@bot.message_handler(commands=['feedbackview'])
def handle_feedback_view(message):
    if is_admin(message.from_user.id):
        if feedback_storage:
            feedback_list = "\n\n".join([f"📩 От @{fb['username']}:\n{fb['text']}\nСтатус: {fb['status']}\nОтвет администратора: {fb['admin_response'] if fb['admin_response'] else 'Нет ответа'}" for fb in feedback_storage])
            bot.send_message(message.chat.id, f"Все сообщения обратной связи:\n\n{feedback_list}")
        else:
            bot.send_message(message.chat.id, "Обратная связь: Пусто.")
    else:
        bot.send_message(message.chat.id, "🚫 У вас нет прав.")

# Menu handlers
@bot.message_handler(func=lambda m: m.text == '📄 Команды')
def commands(message):
    log_command(message)
    bot.send_message(message.chat.id, "Команды:\n\n/start — Запуск бота\n/admin — Панель администратора\n/crash — Остановить бота")

@bot.message_handler(func=lambda m: m.text == "ℹ️ О боте")
def about(message):
    log_command(message)
    bot.send_message(message.chat.id, "Этот бот создан для управления личными заметками.\nРазработчик: @KusokMedi52")

@bot.message_handler(func=lambda m: m.text == '💬 Поддержка')
def support(message):
    log_command(message)
    bot.send_message(message.chat.id, "Свяжитесь с поддержкой => @KusokMedi52.")

@bot.message_handler(func=lambda m: m.text == "📝 Заметки")
def notes_menu(message):
    user_id = message.from_user.id
    notes = get_notes(user_id)

    if notes:
        total_pages = (len(notes) + 4) // 5
        bot.send_message(
            message.chat.id,
            f"📜 Ваши заметки (Страница 1/{total_pages})",
            reply_markup=notes_list_keyboard(notes, 0)
        )
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("➕ Новая заметка", callback_data="new_note"))
        bot.send_message(
            message.chat.id,
            "📝 У вас пока нет заметок. Нажмите ➕ Новая заметка, чтобы создать.",
            reply_markup=keyboard
        )

# Callback handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith("emoji_") or call.data == "cancel")
def emoji_selection_handler(call):
    user_id = call.from_user.id

    if call.data == "cancel":
        clear_user_state(user_id)
        safe_callback_answer(call, "❌ Отменено.")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, "❌ Отменено. Возвращаюсь в главное меню.", reply_markup=main_menu())
        return

    emoji = call.data[len("emoji_"):]
    state = user_note_state.get(user_id)

    if state and state.startswith("change_emoji_"):
        # Change existing note emoji
        index = int(state.split("_")[2])
        notes = get_notes(user_id)
        if 0 <= index < len(notes):
            note_parts = notes[index].split("::", 2)
            title = note_parts[1].strip()
            body = note_parts[2].strip()
            notes[index] = f"{emoji}::{title}::{body}"
            save_notes(user_id, notes)
            safe_callback_answer(call, "🎨 Эмодзи обновлено!")
            safe_edit_message(call, f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                            note_manage_keyboard(index, index // 5), "Markdown")
        clear_user_state(user_id)
    else:
        # New note emoji selection
        user_note_emoji[user_id] = emoji
        safe_callback_answer(call, "🎨 Эмодзи выбрано!")
        user_note_state[user_id] = "body"
        safe_edit_message(call, "📝 Введите содержимое заметки.", cancel_inline_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    # Handle edit operations
    if call.data.startswith(("edit_title_", "edit_body_")):
        try:
            index = int(call.data.split("_")[2])
            user_note_state[user_id] = call.data
            safe_edit_message(call, f"Выберите способ редактирования {'заголовка' if 'title' in call.data else 'заметки'}:",
                            edit_mode_keyboard(index))
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")
        return

    if call.data.startswith("edit_mode_"):
        try:
            parts = call.data.split("_")
            mode, index = parts[2], int(parts[3])
            state = user_note_state.get(user_id)
            if state and (state.startswith("edit_title_") or state.startswith("edit_body_")):
                user_note_state[user_id] = f"{state}_{mode}"
                safe_edit_message(call, "📝 Введите текст для редактирования:", cancel_inline_keyboard())
            else:
                safe_callback_answer(call, "Ошибка: неверное состояние редактирования.")
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")
        return

    if call.data.startswith("edit_emoji_"):
        try:
            index = int(call.data.split("_")[2])
            user_note_state[user_id] = f"change_emoji_{index}"
            safe_edit_message(call, "🎨 Выберите новый эмодзи для заметки:", popular_emoji_keyboard())
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")
        return

    if call.data.startswith("edit_confirm_yes_"):
        try:
            index = int(call.data.split("_")[3])
            notes = get_notes(user_id)
            if 0 <= index < len(notes):
                note_parts = notes[index].split("::", 2)
                emoji = user_note_emoji.get(user_id, note_parts[0].strip())
                title = user_note_title.get(user_id, note_parts[1].strip())
                body = user_note_body.get(user_id, note_parts[2].strip())
                notes[index] = f"{emoji}::{title}::{body}"
                save_notes(user_id, notes)
                safe_edit_message(call, f"✏️ Заметка обновлена:\n\n{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                                note_manage_keyboard(index, index // 5), "Markdown")
            clear_user_state(user_id)
        except Exception as e:
            safe_callback_answer(call, f"Ошибка при подтверждении: {e}")
        return

    if call.data == "new_note":
        user_note_state[user_id] = "title"
        user_note_emoji[user_id] = "📄"
        bot.send_message(call.message.chat.id, "✍️ Введите заголовок новой заметки.", reply_markup=cancel_keyboard())
        return

    # Handle note operations
    notes = get_notes(user_id)
    if not notes:
        safe_callback_answer(call, "Нет заметок.")
        return

    if call.data.startswith("open_"):
        try:
            index = int(call.data.split("_")[1])
            if 0 <= index < len(notes):
                note_parts = notes[index].split("::", 2)
                emoji, title, body = note_parts[0].strip(), note_parts[1].strip(), note_parts[2].strip()
                page = index // 5
                safe_edit_message(call, f"{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}",
                                note_manage_keyboard(index, page), "Markdown")
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")

    elif call.data.startswith("page_"):
        try:
            page = int(call.data.split("_")[1])
            total_pages = (len(notes) + 4) // 5
            safe_edit_message(call, f"📜 Ваши заметки (Страница {page + 1}/{total_pages})",
                            notes_list_keyboard(notes, page))
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")

    elif call.data.startswith("delete_"):
        try:
            parts = call.data.split("_")
            index, page = int(parts[1]), int(parts[2])
            if 0 <= index < len(notes):
                del notes[index]
                save_notes(user_id, notes)
                safe_callback_answer(call, "✅ Заметка удалена.")
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass

                if notes:
                    safe_edit_message(call, f"📜 Ваши заметки (Страница {page + 1})",
                                    notes_list_keyboard(notes, page))
                else:
                    bot.send_message(call.message.chat.id, "📝 Все заметки удалены. Создайте новую!", reply_markup=main_menu())
            else:
                safe_callback_answer(call, "Ошибка удаления.")
        except (IndexError, ValueError):
            safe_callback_answer(call, "Ошибка: некорректный формат данных.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("feedback_reply_"))
def feedback_reply_handler(call):
    """Handle replying to feedback."""
    try:
        index = int(call.data.split("_")[2])
        user_note_state[call.from_user.id] = f"feedback_reply_{index}"
        bot.send_message(call.message.chat.id, "✏️ Введите ваш ответ:", reply_markup=cancel_keyboard())
    except (IndexError, ValueError):
        safe_callback_answer(call, "Ошибка: некорректный индекс.")

@bot.message_handler(func=lambda message: user_note_state.get(message.from_user.id, "").startswith("feedback_reply_"))
def feedback_reply_text_handler(message):
    """Handle saving the admin's reply to feedback."""
    try:
        state = user_note_state.pop(message.from_user.id)
        index = int(state.split("_")[2])
        feedback_storage[index]["admin_response"] = message.text
        feedback_storage[index]["status"] = "отвечено"

        # Notify the user who submitted the feedback
        username = feedback_storage[index]["username"]
        try:
            bot.send_message(username, f"Ваше сообщение: {feedback_storage[index]['text']}\nОтвет администратора: {message.text}")
        except Exception:
            bot.send_message(message.chat.id, "⚠️ Не удалось уведомить пользователя.")

        bot.send_message(message.chat.id, "✅ Ответ сохранен.", reply_markup=main_menu())
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Ошибка: некорректный индекс.", reply_markup=main_menu())

# Text handlers
@bot.message_handler(func=lambda message: user_note_state.get(message.from_user.id) in ["title", "body"] or
                     (user_note_state.get(message.from_user.id) and
                      user_note_state.get(message.from_user.id).startswith(("edit_title_", "edit_body_"))))
def note_text_handler(message):
    user_id = message.from_user.id
    text = message.text

    if text == "❌ Отмена":
        clear_user_state(user_id)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass
        bot.send_message(message.chat.id, "❌ Отменено. Возвращаюсь в главное меню.", reply_markup=main_menu())
        return

    state = user_note_state.get(user_id)

    if state == "title":
        user_note_title[user_id] = text
        log_command(message)
        user_note_state[user_id] = "emoji"
        bot.send_message(message.chat.id, "🎨 Выберите эмодзи для заметки:", reply_markup=popular_emoji_keyboard())

    elif state == "body":
        if user_id not in user_note_title:
            bot.send_message(message.chat.id, "Ошибка: заголовок заметки не найден. Пожалуйста, начните заново.",
                           reply_markup=main_menu())
            clear_user_state(user_id)
            return

        title = user_note_title[user_id]
        emoji = user_note_emoji.get(user_id, "📄")
        notes = get_notes(user_id)
        notes.append(f"{emoji}::{title.strip()}::{text.strip()}")
        save_notes(user_id, notes)

        log_command(message)
        clear_user_state(user_id)
        bot.send_message(message.chat.id, "✅ Заметка сохранена!", reply_markup=main_menu())

    elif state and (state.startswith("edit_title_") or state.startswith("edit_body_")):
        try:
            parts = state.split("_")
            part, index, mode = parts[1], int(parts[2]), parts[3]
            notes = get_notes(user_id)

            if not (0 <= index < len(notes)):
                bot.send_message(message.chat.id, "Ошибка: неверный индекс заметки.", reply_markup=main_menu())
                clear_user_state(user_id)
                return

            note_parts = notes[index].split("::", 2)
            emoji, title, body = note_parts[0].strip(), note_parts[1].strip(), note_parts[2].strip()
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

            # Save to temporary buffer for confirmation
            user_note_title[user_id] = title
            user_note_body[user_id] = body
            user_note_emoji[user_id] = emoji
            user_note_state[user_id] = f"edit_confirm_{index}"

            # Send preview for confirmation
            preview_text = f"✏️ Предпросмотр заметки:\n\n{emoji} *{escape_markdown(title)}*\n{escape_markdown(body)}"
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("✅ Подтвердить", callback_data=f"edit_confirm_yes_{index}"))
            keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
            bot.send_message(message.chat.id, preview_text, parse_mode="Markdown", reply_markup=keyboard)

            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User {user_id} edited note {index} ({part}, {mode})")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при редактировании: {e}", reply_markup=main_menu())

    elif state.startswith("feedback_reply_"):
        try:
            index = int(state.split("_")[2])
            feedback_storage[index]["admin_response"] = text
            feedback_storage[index]["status"] = "отвечено"

            # Notify the user who submitted the feedback
            bot.send_message(feedback_storage[index]["username"], f"Ваше сообщение: {feedback_storage[index]['text']}\nОтвет администратора: {text}")

            bot.send_message(message.chat.id, "✅ Ответ отправлен.", reply_markup=main_menu())
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Ошибка: некорректный индекс.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def fallback_handler(message):
    bot.send_message(message.chat.id, "Неверная команда/текст ❌", reply_markup=main_menu())

if __name__ == "__main__":
    bot.polling(none_stop=True)
