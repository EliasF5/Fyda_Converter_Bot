import io
import os
import re
import telebot
from telebot import types
from PIL import Image, ImageOps
import requests
from flask import Flask
import threading

# ==================== CONFIGURATION ====================
API_TOKEN = '8974775722:AAEdkBUxx02cwzLLzGT6Fa5hqSWtveqGz6A'  # Token Bot keetii as galchi
ADMIN_CHAT_ID = 123456789  # Telegram Chat ID kee (Elias) lakkoofsa qofa
CHANNEL_USERNAME = '@A_ToolsX'  # Maqaa Chanaalii kee force join gochisiistu

bot = telebot.TeleBot(API_TOKEN)

user_lang = {}             
user_balances = {}         
user_states = {}

# ==================== MAIN KEYBOARD (BAAFATA) ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📄 Print from PDF"),
        types.KeyboardButton("📸 Print from Screenshot"),
        types.KeyboardButton("📦 Bulk Screenshot (auto-match)"),
        types.KeyboardButton("🔢 Print from OTP"),
        types.KeyboardButton("🖨️ Group to A4"),
        types.KeyboardButton("💰 Balance"),
        types.KeyboardButton("📦 Top Up")
    )
    return markup

# ==================== CHANAALII CHECK GOCHUU (FORCE JOIN) ====================
def check_must_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        # Yoo bot-in chanaalicha keessatti admin ta'uu baate ykn chanaaliin hin jirre hojii akka hin dhowwineef
        return True

def send_join_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    # Chanaalii keetiif liinkii uumuu
    link = f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
    markup.add(types.InlineKeyboardButton("🚀 Join Our Channel", url=link))
    
    msg = (
        f"🚀 **To use this bot, you must join our channel first!**\n\n"
        f"Maaloo tajaajila kana fayyadamuuf jalqaba chanaalii keenya join godhaa.\n"
        f"👉 Link: {CHANNEL_USERNAME}"
    )
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode='Markdown')

# ==================== START & LANG COMMANDS ====================
@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 2  # Kireditii 2 bilisaan
        
    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return
        
    user_lang[user_id] = 'om' # Default Afaan Oromoo
    bot.send_message(
        message.chat.id, 
        "👋 **Baga nagaan dhuftan! Maaloo baafata gadii irratti tajaajila barbaaddan filadhaa.**", 
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

# ==================== TEXT & MENU BUTTON HANDLERS ====================
@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    user_id = message.from_user.id
    text = message.text

    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return

    if text == "💰 Balance":
        bal = user_balances.get(user_id, 0)
        bot.send_message(message.chat.id, f"💳 **Kireditii Keessan:** `{bal} credits`", parse_mode='Markdown')
        
    elif text == "📦 Top Up":
        msg = (
            f"💳 **Kireditii Guuttachuuf:**\n\n"
            f"Maaloo kaffaltii erga raawwattanii booda Admin dubbisaa.\n"
            f"• TeleBirr: `0913701367` (Elias Fikadu)\n"
            f"• CBE: `1000270143788`\n\n"
            f"User ID keessan kanaan Adminitti ergaa: `{user_id}`"
        )
        bot.send_message(message.chat.id, msg, parse_mode='Markdown')
        
    elif text == "📸 Print from Screenshot":
        user_states[user_id] = 'WAITING_SCREENSHOT'
        bot.send_message(message.chat.id, "📥 **Maaloo amma screenshot Fayda ID (Fuula duraa fi duubaa wal bira jiru) ergaa.**", parse_mode='Markdown')
        
    elif text in ["📄 Print from PDF", "📦 Bulk Screenshot (auto-match)", "🔢 Print from OTP", "🖨️ Group to A4"]:
        bot.send_message(message.chat.id, f"⚙️ Tajaajilli **{text}** yeroof qophii irra jira. Maaloo `Print from Screenshot` fayyadamaa.")

# ==================== ADMIN ADD CREDIT COMMAND ====================
# Admin dhuunfaatti kireditii guutuuf: /add UserID Kireditii
@bot.message_handler(commands=['add'])
def add_credit_manual(message):
    if message.from_user.id != ADMIN_CHAT_ID: return
    try:
        parts = message.text.split()
        target_user = int(parts[1])
        credits_to_add = int(parts[2])
        user_balances[target_user] = user_balances.get(target_user, 0) + credits_to_add
        bot.reply_to(message, f"✅ User `{target_user}` tiif kireditii {credits_to_add} feeteetta!")
        bot.send_message(target_user, f"🎉 **Kafaltiin keessan mirkanaayeera! Kireditiin {credits_to_add} dabalameera.**", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Haala kanaan barreessi: `/add UserID Kireditii`")

# ==================== CORE ID PROCESSING ENGINE ====================
@bot.message_handler(content_types=['photo'])
def process_fayda_image(message):
    user_id = message.from_user.id
    
    if not check_must_join(user_id):
        send_join_message(message.chat.id)
        return

    if user_balances.get(user_id, 0) <= 0:
        bot.send_message(message.chat.id, "⚠️ **Kireditii gahaa hin qabdhan! Maaloo kireditii bitachuuf /topup jedhaa.**", parse_mode='Markdown')
        return

    bot.send_message(message.chat.id, "⚙️ **Kaardii keessan qulqullinaan piriintiif ijaarbaa jira... Maaloo obsaan eegaa.**", parse_mode='Markdown')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        full_img = Image.open(io.BytesIO(downloaded_file))
        W, H = full_img.size
        
        # Screenshot walakkaan qoruu (Left & Right split)
        if W > H:
            front_side = full_img.crop((0, 0, int(W * 0.5), H))
            back_side = full_img.crop((int(W * 0.5), 0, W, H))
        else:
            front_side = full_img
            back_side = full_img
        
        # Hamma PVC standard kaardii (1011x638)
        card_w, card_h = 1011, 638
        front_final = front_side.resize((card_w, card_h), Image.Resampling.LANCZOS)
        back_final = back_side.resize((card_w, card_h), Image.Resampling.LANCZOS)
        
        # MIRROR ON (🪞 Piriintiif dahuu)
        front_final = ImageOps.mirror(front_final)
        back_final = ImageOps.mirror(back_final)
        
        # Canvas A4 Guddaa (2480x3508 pixels)
        canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
        
        # A4 irratti bitaa fi mirga hiriirsuu (Dugda bitaatti, Fuula dura mirgatti)
        canvas.paste(back_final, (150, 200))      
        canvas.paste(front_final, (1250, 200))    
        
        bio = io.BytesIO()
        canvas.save(bio, 'JPEG', quality=100)
        bio.seek(0)
        
        user_balances[user_id] -= 1
        
        caption_msg = f"✅ **Fayda ID Processed Successfully!**\n• Credit Left: {user_balances[user_id]}\n\n🪞 Mirror Layout: **ON (Ready for PVC Print)**"
        bot.send_photo(message.chat.id, bio, caption=caption_msg, parse_mode='Markdown', reply_markup=get_main_keyboard())
        
    except Exception as e:
        bot.reply_to(message, f"❌ Dogoggora: {str(e)}", reply_markup=get_main_keyboard())

# Web Server Render irratti active akka ta'uuf
app = Flask('')
@app.route('/')
def home(): return "Active"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=15, long_polling_timeout=10)
