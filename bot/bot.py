import logging
import os
import requests
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурация логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определение состояний для ConversationHandler
SELECTING_TYPE, ENTERING_VALUE, ENTERING_META = range(3)

# Получение конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Проверка наличия обязательных переменных
if not TELEGRAM_BOT_TOKEN or not API_URL:
    raise ValueError("TELEGRAM_BOT_TOKEN и API_URL должны быть установлены в .env файле")

# --- Функции-обработчики диалога ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог сбора данных о событии."""
    reply_keyboard = [["food", "symptom"], ["mood", "energy", "activity"]]
    await update.message.reply_text(
        "Активирован протокол записи события. Выберите тип события.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Тип события?"
        ),
    )
    return SELECTING_TYPE

async def select_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет выбранный тип события и запрашивает значение."""
    user_choice = update.message.text
    context.user_data['event_type'] = user_choice
    await update.message.reply_text(
        f"Тип: {user_choice}. Введите значение.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ENTERING_VALUE

async def enter_event_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет значение и запрашивает метаданные."""
    event_value = update.message.text
    context.user_data['event_value'] = event_value
    await update.message.reply_text(
        "Значение сохранено. Введите метаданные (например, 'калории: 250, белки: 20') или отправьте /skip для пропуска."
    )
    return ENTERING_META

async def enter_meta_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет метаданные, формирует JSON и отправляет на API."""
    meta_data = update.message.text
    context.user_data['meta_data'] = meta_data
    await update.message.reply_text("Данные приняты. Инициирую отправку на API.")
    
    # Вызов функции отправки
    await send_to_api(update, context)
    
    return ConversationHandler.END

async def skip_meta_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пропускает ввод метаданных, формирует JSON и отправляет на API."""
    context.user_data['meta_data'] = None
    await update.message.reply_text("Метаданные пропущены. Инициирую отправку на API.")
    
    # Вызов функции отправки
    await send_to_api(update, context)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущую операцию сбора данных."""
    context.user_data.clear()
    await update.message.reply_text(
        "Операция отменена.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- Логика взаимодействия с API ---

async def send_to_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Формирует и отправляет POST-запрос на бэкенд API."""
    payload = {
        "user_id": update.message.from_user.id,
        "event_type": context.user_data.get('event_type'),
        "event_value": context.user_data.get('event_value'),
        "meta_data": context.user_data.get('meta_data')
    }
    
    logger.info(f"Отправка payload на {API_URL}: {payload}")

    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Успешный ответ от API: {response.json()}")
            await update.message.reply_text(f"Статус: Успех. ID записи: {response.json().get('id')}")
        else:
            logger.error(f"Ошибка от API: Статус {response.status_code}, Тело {response.text}")
            await update.message.reply_text(f"Статус: Ошибка. Код: {response.status_code}. Ответ: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка соединения с API: {e}")
        await update.message.reply_text(f"Ошибка соединения с API. Проверьте доступность сервиса.")
    
    finally:
        context.user_data.clear()


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event_type)],
            ENTERING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_event_value)],
            ENTERING_META: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_meta_data),
                CommandHandler("skip", skip_meta_data)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()