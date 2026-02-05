import logging
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Тарифы
PLANS = {
    'starter': {
        'name': '💎 BOT STARTER',
        'price': 99,
        'monthly': 19,
        'max_positions': 2,
        'description': '💎 STARTER\n\n✅ 2 позиции\n✅ 3 стратегии\n✅ Минимум: $100'
    },
    'pro': {
        'name': '💠 BOT PRO',
        'price': 299,
        'monthly': 49,
        'max_positions': 3,
        'description': '💠 PRO\n\n✅ 3 позиции\n✅ Все стратегии\n✅ Минимум: $200'
    },
    'elite': {
        'name': '👑 BOT ELITE',
        'price': 799,
        'monthly': 99,
        'max_positions': 5,
        'description': '👑 ELITE\n\n✅ 5 позиций\n✅ VIP функции\n✅ Минимум: $500'
    }
}

# База данных
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        bot_type TEXT DEFAULT 'free',
        api_connected INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_db()

def main_menu_keyboard(user_type='free', is_admin=False):
    buttons = [
        [InlineKeyboardButton("💎 STARTER", callback_data="plan_starter")],
        [InlineKeyboardButton("💠 PRO", callback_data="plan_pro")],
        [InlineKeyboardButton("👑 ELITE", callback_data="plan_elite")],
    ]
    if user_type != 'free':
        buttons.append([InlineKeyboardButton("🏠 Кабинет", callback_data="cabinet")])
    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Админ", callback_data="admin")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Сохраняем пользователя
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
              (user.id, user.username))
    conn.commit()
    conn.close()
    
    is_admin = user.id == ADMIN_USER_ID
    
    await update.message.reply_text(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🤖 Crypto Trading Bot\n"
        f"Автоматическая торговля 24/7\n\n"
        f"Выбери тарифный план:",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard('free', is_admin)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('plan_'):
        plan_key = data.replace('plan_', '')
        plan = PLANS.get(plan_key)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💵 Купить навсегда", callback_data=f"buy_{plan_key}_forever")],
            [InlineKeyboardButton("📅 Месячная подписка", callback_data=f"buy_{plan_key}_monthly")],
            [InlineKeyboardButton("← Назад", callback_data="menu")]
        ])
        
        await query.edit_message_text(
            f"<b>{plan['description']}</b>\n\n"
            f"💰 Навсегда: ${plan['price']}\n"
            f"📅 Месяц: ${plan['monthly']}",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    elif data == 'cabinet':
        await query.edit_message_text(
            "🏠 <b>МОЙ КАБИНЕТ</b>\n\n"
            "Здесь будет ваша статистика и управление ботом",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("← Меню", callback_data="menu")
            ]])
        )
    
    elif data == 'menu':
        await query.edit_message_text(
            "🏠 <b>ГЛАВНОЕ МЕНЮ</b>",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard()
        )

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        exit(1)
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling()
