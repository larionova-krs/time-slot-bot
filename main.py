import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from store import db_session
from store.models import User, Appointment
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Stages
MAIN_MENU, CHOOSING_DATE, CHOOSING_TIME, CONFIRMING_DATETIME, VIEWING_APPOINTMENTS = range(5)
# Callback data
AVAILABLE_SLOTS, BOOK, MY_APPOINTMENTS, DATE_UNAVAILABLE, BUTTON_DISABLED = range(5)


# MONTHS = {"Январь": 31, "Февраль": 28, "Март": 31, "Апрель": 30, "Май": 31, "Июнь": 30, "Июль": 31, "Август": 31, "Сентябрь": 30, "Октябрь": 31, "Ноябрь": 30, "Декабрь": 31}


async def start(update, context):
    with db_session() as session:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()

        if not user:
            user = User(telegram_id=update.effective_user.id, name=update.effective_user.full_name)
            session.add(user)
            await update.message.reply_text("Welcome! You've been registered.")
        else:
            await update.message.reply_text(f"Welcome back, {user.name}!")

        logger.info("User %s started the conversation.", user.name)

        keyboard = [
            [
                InlineKeyboardButton("Посмотреть доступные слоты", callback_data=str(BOOK)),
            ],
            [
                InlineKeyboardButton("Мои записи", callback_data=str(MY_APPOINTMENTS)),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(
            photo="menu.jpg",
            reply_markup=reply_markup
        )
        # Tell ConversationHandler that we're in state `MAIN_MENU` now
        return MAIN_MENU


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("Посмотреть доступные слоты", callback_data=str(BOOK)),
        ],
        [
            InlineKeyboardButton("Мои записи", callback_data=str(MY_APPOINTMENTS)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_media(
        media=InputMediaPhoto(
            media=open("menu.jpg", "rb"),
        ),
        reply_markup=reply_markup
    )
    
    return MAIN_MENU


async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    
    dates = []
    for i in range(4):
        dates.append(InlineKeyboardButton(" ", callback_data=str(BUTTON_DISABLED)))
    for i in range(1, 7):
        dates.append(InlineKeyboardButton(str(i), callback_data=str(MAIN_MENU)))
    for i in range(7, 9):
        dates.append(InlineKeyboardButton("✖️", callback_data=str(DATE_UNAVAILABLE)))
    for i in range(9, 12):
        dates.append(InlineKeyboardButton(str(i), callback_data=str(MAIN_MENU)))
    for i in range(12, 15):
        dates.append(InlineKeyboardButton("✖️", callback_data=str(DATE_UNAVAILABLE)))
    for i in range(15, 29):
        dates.append(InlineKeyboardButton(str(i), callback_data=str(MAIN_MENU)))
    for i in range(29, 30):
        dates.append(InlineKeyboardButton("✖️", callback_data=str(DATE_UNAVAILABLE)))
    for i in range(30, 32):
        dates.append(InlineKeyboardButton(str(i), callback_data=str(MAIN_MENU)))
    
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Июль", callback_data=str(MAIN_MENU)),
            InlineKeyboardButton("Сентябрь ➡️", callback_data=str(MAIN_MENU)),
        ]
    ]
    for d in range(0, len(dates), 7):
        keyboard += [dates[d:d+7]]
    keyboard += [[
        InlineKeyboardButton("Вернуться в главное меню", callback_data=str(MAIN_MENU)),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=open("august.jpg", "rb"),
            caption="Для просмотра доступных временных слотов нажмите на соответствующую дату"
        ),
        reply_markup=reply_markup
    )
    return CHOOSING_DATE


async def view_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Вернуться в главное меню", callback_data=str(MAIN_MENU)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_media(
        media=InputMediaPhoto(
            media=open("other/pp", "rb"),
            caption="Новый текст описания"
        ),
        reply_markup=reply_markup
    )
    
    return VIEWING_APPOINTMENTS


async def button_disabled(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return


async def date_unavailable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer(text="На выбранную дату нет записи", show_alert=True)
    return


# async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Returns `ConversationHandler.END`, which tells the
#     ConversationHandler that the conversation is over.
#     """
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="See you next time!")
#     return ConversationHandler.END


# async def book_appointment(update, context):
#     with db_session() as session:
#         # Get or create user
#         user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
#         # Create a new appointment
#         new_appointment = Appointment(
#             user_id=user.id,
#             service_type="Consultation",
#             datetime=datetime(2023, 10, 1, 14, 0)
#         )
#         session.add(new_appointment)
#         await update.message.reply_text("✅ Appointment booked!")


def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(token).build()

    # application.add_handler(CommandHandler("book", book_appointment))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(choose_date, pattern="^" + str(BOOK) + "$"),
                CallbackQueryHandler(start_over, pattern="^" + str(MY_APPOINTMENTS) + "$"),
            ],
            CHOOSING_DATE: [
                CallbackQueryHandler(button_disabled, pattern="^" + str(BUTTON_DISABLED) + "$"),
                CallbackQueryHandler(date_unavailable, pattern="^" + str(DATE_UNAVAILABLE) + "$"),
                CallbackQueryHandler(start_over, pattern="^" + str(MAIN_MENU) + "$"),
            ],
            CHOOSING_TIME: [
                CallbackQueryHandler(choose_date, pattern="^" + str(AVAILABLE_SLOTS) + "$"),
                CallbackQueryHandler(start_over, pattern="^" + str(MAIN_MENU) + "$"),
            ],
            VIEWING_APPOINTMENTS: [
                CallbackQueryHandler(start_over, pattern="^" + str(MAIN_MENU) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()