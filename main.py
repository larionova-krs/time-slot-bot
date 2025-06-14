import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from store import db_session
from store.models import User, Appointment
from datetime import datetime

async def start(update, context):
    with db_session() as session:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            user = User(telegram_id=update.effective_user.id, name=update.effective_user.full_name)
            session.add(user)
            await update.message.reply_text("Welcome! You've been registered.")
        else:
            await update.message.reply_text(f"Welcome back, {user.name}!")

async def book_appointment(update, context):
    with db_session() as session:
        # Get or create user
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        # Create a new appointment
        new_appointment = Appointment(
            user_id=user.id,
            service_type="Consultation",
            datetime=datetime(2023, 10, 1, 14, 0)
        )
        session.add(new_appointment)
        await update.message.reply_text("✅ Appointment booked!")

def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("book", book_appointment))

    application.run_polling()


if __name__ == "__main__":
    main()