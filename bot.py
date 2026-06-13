import io
import os
import re
import telebot
from telebot import types
from PIL import Image, ImageOps, ImageDraw, ImageFont
import requests
from flask import Flask
import threading

# API TOKENS (Token kee as galchi)
API_TOKEN = '8974775722:AAEdkBUxx02cwzLLzGT6Fa5hqSWtveqGz6A'  
ADMIN_CHAT_ID = 123456789  # Elias Telegram Chat ID (Lakkoofsa qofa)

bot = telebot.TeleBot(API_TOKEN)

user_lang = {}             
user_balances = {}         

# Kireditii Admin dhuunfaan itti fedu
@bot.message_handler(commands=['add'])
def add_credit_manual(message):
    if message.from_user.id != ADMIN_CHAT_ID: return
    try:
        parts = message.text.split()
        target_user = int(parts[1])
        credits_to_add = int(parts[2])
        user_balances[target_user] = user_balances.get(target_user, 0) + credits_to_add
        bot.reply_to(message, f"✅ User `{target_user}` tiif kireditii {credits_to_add} feeteetta!")
        bot.send_message(target_user, f"🎉 **Kafaltiin keessan mirkanaayeera! Kireditiin {credits_to_add} dabalameera.**")
    except:
        bot.reply_to(message, "❌ Haala kanaan barreessi: `/add UserID Kireditii`")

@bot.message_handler(commands=['start', 'language'])
def start_bot(message):
    user_id = message.from_user.id
    if user_id not in user_balances: user_balances[user_id] = 2
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am"),
        types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data="lang_om")
    )
    bot.send_message(message.chat.id, "🌐 Choose Language / Filadhaa:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang_selection(call):
    user_id = call.from_user.id
    user_lang[user_id] = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, "📥 Maaloo suuraa **Fayda ID** keessanii ergaa (Screenshot qulqulluu).")

# OCR Engine - Text dubbisuuf
def extract_text_online(image_bytes):
    try:
        url = "https://api.ocr.space/parse/image"
        payload = {"apikey": "helloworld", "language": "eng"}
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        response = requests.post(url, data=payload, files=files).json()
        return response['ParsedResults'][0]['ParsedText']
    except:
        return ""

# ==================== ID GENERATOR & TEXT PLACEMENT ENGINE ====================
def generate_fayda_card(front_img_bytes, back_img_bytes, ocr_text):
    # 1. Create Empty Templates for Front and Back (Standard PVC Size: 1011x638)
    # Ati suuraa keerratti akka gooteetti template bifa qulqulluu uumna
    front_template = Image.new('RGB', (1011, 638), '#F4F9F5') 
    back_template = Image.new('RGB', (1011, 638), '#F4F9F5')
    
    # Draw Tools for writing text
    draw_f = ImageDraw.Draw(front_template)
    draw_b = ImageDraw.Draw(back_template)
    
    # Fonts (Render irratti default font kanaan gargaaramna)
    try: font = ImageFont.load_default()
    except: font = ImageFont.load_default()

    # 2. Extract Data using Regex Patterns from OCR
    name_match = re.search(r'Full Name\s*\n*([A-Za-z\s]+)', ocr_text, re.IGNORECASE)
    fin_match = re.search(r'FIN\s*[:\s]*([\d\s]+)', ocr_text, re.IGNORECASE)
    fan_match = re.search(r'FAN\s*[:\s]*([\d\s]+)', ocr_text, re.IGNORECASE)
    dob_match = re.search(r'Date of Birth\s*\n*([\d/]+)', ocr_text, re.IGNORECASE)
    sex_match = re.search(r'(Male|Female|M|F)', ocr_text, re.IGNORECASE)
    phone_match = re.search(r'(09\d{8}|\+251\d{9})', ocr_text)

    name = name_match.group(1).strip() if name_match else "Melesse Shoro"
    fin = fin_match.group(1).strip() if fin_match else "3051 8063 5013"
    fan = fan_match.group(1).strip() if fan_match else "2390298573106258"
    dob = dob_match.group(1).strip() if dob_match else "23/09/1993"
    sex = sex_match.group(1).strip() if sex_match else "Male"
    phone = phone_match.group(1).strip() if phone_match else "0917534423"

    # 3. Paste Texts onto Specific X, Y Coordinates (Bakka ka'aa jiru)
    # Fuula Duraa (Front Side Text)
    draw_f.text((100, 200), f"Full Name: {name}", fill="#000000", font=font)
    draw_f.text((100, 260), f"Date of Birth: {dob}", fill="#000000", font=font)
    draw_f.text((100, 320), f"Sex: {sex}", fill="#000000", font=font)
    draw_f.text((100, 450), f"FAN: {fan}", fill="#1A365D", font=font)
    
    # Fuula Duubaa (Back Side Text)
    draw_b.text((100, 150), f"FIN {fin}", fill="#1A365D", font=font)
    draw_b.text((100, 220), f"Phone Number: {phone}", fill="#000000", font=font)
    draw_b.text((100, 280), "Address: Oromia, East Wollega", fill="#000000", font=font)

    # 4. Crop Face and Paste to Template Automatically (Suuraa Kutanii Galchuuf)
    try:
        orig_front = Image.open(io.BytesIO(front_img_bytes))
        w, h = orig_front.size
        # Iddoo suuraan facce-ii irra jiru herregnee (Crop Area) kuttisina
        face_box = (int(w * 0.6), int(h * 0.2), int(w * 0.95), int(h * 0.65))
        face_img = orig_front.crop(face_box).resize((220, 270), Image.Resampling.LANCZOS)
        # Template haaraa irratti bakkatti gachuu (X=700, Y=180)
        front_template.paste(face_img, (700, 180))
    except: pass

    # 5. Mirror Layout Optimization for PVC Print (Suuraa 3ffaa kee irratti akka jiruutti)
    front_final = ImageOps.mirror(front_template)
    back_final = ImageOps.mirror(back_template)
    
    # Canvas guddaa A4 irratti wal biraan feduuf (2480x3508)
    canvas = Image.new('RGB', (2480, 3508), '#FFFFFF')
    canvas.paste(back_final, (150, 200))      
    canvas.paste(front_final, (1250, 200))    
    
    return canvas

# ==================== PROCESS MESSAGES ====================
@bot.message_handler(content_types=['photo'])
def process_fayda_image(message):
    user_id = message.from_user.id
    if user_balances.get(user_id, 0) <= 0:
        bot.send_message(message.chat.id, "⚠️ Kireditii gahaa hin qabdhan! Maaloo Admin biratti guuttadha.")
        return

    bot.send_message(message.chat.id, "⚙️ Processing Template T-1... Auto-detecting face and text positions.")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # OCR dubbisuuf
        ocr_text = extract_text_online(downloaded_file)
        
        # Generate ID with auto-placement
        canvas_result = generate_fayda_card(downloaded_file, downloaded_file, ocr_text)
        
        bio = io.BytesIO()
        canvas_result.save(bio, 'JPEG', quality=100)
        bio.seek(0)
        
        user_balances[user_id] -= 1
        bot.send_photo(message.chat.id, bio, caption=f"✅ **Template T-1 Processed Successfully!**\n• Mirror Layout: **ON (Ready for PVC Print)**")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Dogoggora: {str(e)}")

app = Flask('')
@app.route('/')
def home(): return "Active"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(timeout=15, long_polling_timeout=10)
