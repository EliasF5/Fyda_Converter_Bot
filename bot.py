import os
import telebot
from telebot import types
import requests
from flask import Flask
import threading

API_TOKEN = '8974775722:AAEdkBUxx02cwzLLzGT6Fa5hqSWtveqGz6A'  # Token kee as galchi
ADMIN_CHAT_ID = 123456789  # Chat ID kee lakkoofsa qofa
CHANNEL_USERNAME = '@A_ToolsX'  # Chanaalii kee

bot = telebot.TeleBot(API_TOKEN)
user_balances = {}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📸 Print from Screenshot"),
        types.KeyboardButton("💰 Balance"),
        types.KeyboardButton("📦 Top Up")
    )
    return markup

def check_must_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return True

def send_join_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("🚀 Join Our Channel", url=link))
    bot.send_message(
        chat_id, 
        f"🚀 **To use this bot, you must join our channel first!**\n\n👉 Channel: {CHANNEL_USERNAME}", 
        reply_markup=markup, 
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['start'])
def start_bot(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 2
    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return
    bot.send_message(message.chat.id, "👋 **Baga nagaan dhuftan!**", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    user_id = message.from_user.id
    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return

    if message.text == "💰 Balance":
        bal = user_balances.get(user_id, 0)
        bot.send_message(message.chat.id, f"💳 **Kireditii Keessan:** `{bal} credits`", parse_mode='Markdown')
    elif message.text == "📦 Top Up":
        msg = f"💳 **Kireditii Guuttachuuf:**\n\n• TeleBirr: `0913701367` (Elias Fikadu)\n• User ID keessan: `{user_id}`"
        bot.send_message(message.chat.id, msg, parse_mode='Markdown')
    elif message.text == "📸 Print from Screenshot":
        bot.send_message(message.chat.id, "📥 **Maaloo amma screenshot Fayda ID keessan ergaa.**")

@bot.message_handler(content_types=['photo'])
def process_fayda_image(message):
    user_id = message.from_user.id
    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return
    # Amma kallattiin suuraa sun deebisee dhufeera piriintiif
    bot.send_message(message.chat.id, "⚙️ **Kaardii keessan ijaarbaa jira...**")
    bot.send_photo(message.chat.id, message.photo[-1].file_id, caption="✅ **Processed Successfully! (Ready for PVC Print)**")

app = Flask('')
@app.route('/')
def home(): return "Active"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=15, long_polling_timeout=10)
