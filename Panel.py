import requests
import telebot
from telebot import types
import json
import os
from datetime import datetime
import time
import logging
import random
import string

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot token
BOT_TOKEN = "7769287068:AAG8CZGXNwisayOLDwBlQWbK0Bg6_L3cjIM"
bot = telebot.TeleBot(BOT_TOKEN)

# API Base URL
BASE_URL = "https://apilerimya.onrender.com"

# Admin ID
ADMIN_IDS = [7709693701]

# Zorunlu kanal
REQUIRED_CHANNEL = "@gottenvurdurankurtbio"
CHANNEL_LINK = "https://t.me/gottenvurdurankurtbio"

# Dosyalar
BANNED_USERS_FILE = "banned_users.json"
CODES_FILE = "access_codes.json"
USER_CODES_FILE = "user_codes.json"

# Dosyaları oluştur
for file in [BANNED_USERS_FILE, CODES_FILE, USER_CODES_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

def load_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    banned = load_json(BANNED_USERS_FILE)
    return str(user_id) in banned

def ban_user(user_id):
    banned = load_json(BANNED_USERS_FILE)
    banned[str(user_id)] = True
    save_json(BANNED_USERS_FILE, banned)

def unban_user(user_id):
    banned = load_json(BANNED_USERS_FILE)
    if str(user_id) in banned:
        del banned[str(user_id)]
        save_json(BANNED_USERS_FILE, banned)

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def save_code(code):
    codes = load_json(CODES_FILE)
    codes[code] = {"created_at": datetime.now().isoformat(), "used": False, "used_by": None}
    save_json(CODES_FILE, codes)
    return code

def verify_code(user_id, code):
    codes = load_json(CODES_FILE)
    user_codes = load_json(USER_CODES_FILE)
    
    if str(user_id) in user_codes:
        return True
    
    if code in codes and not codes[code]["used"]:
        codes[code]["used"] = True
        codes[code]["used_by"] = user_id
        save_json(CODES_FILE, codes)
        
        user_codes[str(user_id)] = code
        save_json(USER_CODES_FILE, user_codes)
        return True
    return False

def has_access(user_id):
    if is_admin(user_id):
        return True
    if is_banned(user_id):
        return False
    user_codes = load_json(USER_CODES_FILE)
    return str(user_id) in user_codes

def check_channel_membership(user_id):
    try:
        chat_member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

# API fonksiyonları (AYNEN)
def api_request(url, params=None, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                if response.text and response.text.strip():
                    return response.text
                return None
            return None
        except:
            if attempt == max_retries - 1:
                return None
            time.sleep(2)
    return None

def api_sorgula_ad_soyad(name, surname):
    return api_request(f"{BASE_URL}/isegiris", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_tc(tc):
    return api_request(f"{BASE_URL}/tc-isegiris", params={"tc": tc, "format": "text"})

def api_sorgula_gsm(gsm):
    return api_request(f"{BASE_URL}/gsm", params={"gsm": gsm, "format": "text"})

def api_sorgula_plaka(plaka):
    return api_request(f"{BASE_URL}/plaka", params={"plaka": plaka, "format": "text"})

def api_sorgula_aile(tc):
    return api_request(f"{BASE_URL}/aile", params={"tc": tc, "format": "text"})

def api_sorgula_hane(tc):
    return api_request(f"{BASE_URL}/hane", params={"tc": tc, "format": "text"})

def api_sorgula_isyeri(tc):
    return api_request(f"{BASE_URL}/isyeri", params={"tc": tc, "format": "text"})

def api_sorgula_vesika(tc):
    return api_request(f"{BASE_URL}/vesika", params={"tc": tc, "format": "text"})

def api_sorgula_ikametgah(name, surname):
    return api_request(f"{BASE_URL}/ikametgah", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_ailebirey(name, surname):
    return api_request(f"{BASE_URL}/ailebirey", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_medenicinsiyet(name, surname):
    return api_request(f"{BASE_URL}/medenicinsiyet", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

# Yardımcı fonksiyonlar (AYNEN)
def il_filter(data, il_adi):
    if not data:
        return None
    
    lines = data.split('\n')
    current_record = []
    records = []
    
    for line in lines:
        if line.strip() == "":
            if current_record:
                records.append(current_record)
                current_record = []
        else:
            current_record.append(line)
    
    if current_record:
        records.append(current_record)
    
    filtered_records = []
    for record in records:
        record_text = ' '.join(record)
        if il_adi.upper() in record_text.upper():
            filtered_records.append(record)
    
    return filtered_records

def format_records_as_ascii(records):
    """Kayıtları KAYIT 1, KAYIT 2 diye düzenli göster"""
    if not records:
        return None
    
    formatted_text = ""
    for i, record in enumerate(records, 1):
        formatted_text += "╔══════════════════════════════════════════════════════════╗\n"
        formatted_text += f"║                      📌 KAYIT {i}                          ║\n"
        formatted_text += "╠══════════════════════════════════════════════════════════╣\n"
        
        for line in record:
            if line.strip():
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        formatted_text += f"║ {key:<20} : {value:<45} ║\n"
                else:
                    formatted_text += f"║ {line.strip():<60} ║\n"
        
        formatted_text += "╚══════════════════════════════════════════════════════════╝\n\n"
    
    return formatted_text

def save_to_txt(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        return True
    except Exception as e:
        logging.error(f"Dosya kaydetme hatası: {e}")
        return False

def parse_name_surname(text):
    parts = text.split()
    
    if len(parts) < 3:
        return None, None, None
    
    il = parts[-1].upper()
    name_surname_part = ' '.join(parts[:-1])
    surname = name_surname_part.split()[-1].upper()
    name_part = ' '.join(name_surname_part.split()[:-1]).upper()
    
    if '+' in name_part:
        name = name_part.replace('+', ' ').upper()
    else:
        name = name_part
    
    return name, surname, il

# ==================== BOT KOMUTLARI ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Kanal kontrolü
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ KATILDIM", callback_data="check_membership"))
        bot.reply_to(message, f"❌ Bu botu kullanmak için {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    # Kod kontrolü
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "🔐 **Hoş Geldin!**\n\nBu botu kullanmak için bir erişim koduna ihtiyacın var.\nKodu admin'den alabilirsin.", reply_markup=markup, parse_mode='Markdown')
        return
    
    welcome_text = """
🎯 **Merhaba! Ben Bilgi Sorgulama Botu**

Size çeşitli bilgi sorgulama hizmetleri sunuyorum.

📌 **Komutları görmek için:** /komutlar

Hemen /komutlar yazarak başlayabilirsin!
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['komutlar'])
def show_commands(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    commands_text = """
📚 **Kullanılabilir Komutlar:**

🔍 **Sorgulama Komutları:**
`/adsoyad [ad] [soyad]` - Ad soyad ile sorgulama
`/tc [tc_no]` - TC kimlik numarası ile sorgulama
`/gsm [numara]` - GSM numarası ile sorgulama
`/plaka [plaka]` - Plaka ile sorgulama

👨‍👩‍👧‍👦 **Detaylı Sorgular (TC ile):**
`/aile [tc]` - Aile bilgileri
`/hane [tc]` - Hane bilgileri
`/isyeri [tc]` - İş yeri bilgileri
`/vesika [tc]` - Vesika bilgileri

🎯 **Özel Sorgulama (Çoklu İsim Desteği):**
`/il [ad1+ad2] [soyad] [il]` - Belirtilen ildeki kayıtları getirir

Örnekler:
• `/il Azam Muhammed Diyarbakır` - Tek isim
• `/il Azam+Muhammed Dilman Diyarbakır` - Çoklu isim (artı ile ayrılmış)

ℹ️ **Diğer:**
`/yardim` - Yardım menüsü
    """
    bot.reply_to(message, commands_text, parse_mode='Markdown')

@bot.message_handler(commands=['yardim'])
def help_command(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    help_text = """
❓ **Yardım Menüsü**

**Nasıl kullanırım?**

1️⃣ **Ad Soyad Sorgulama:**
`/adsoyad EYMEN YAVUZ`

2️⃣ **TC Sorgulama:**
`/tc 11111111110`

3️⃣ **İl Bazlı Sorgulama (Tek İsim):**
`/il Azam Muhammed Diyarbakır`

4️⃣ **İl Bazlı Sorgulama (Çoklu İsim):**
`/il Azam+Muhammed Dilman Diyarbakır`

5️⃣ **GSM Sorgulama:**
`/gsm 5346149118`

6️⃣ **Plaka Sorgulama:**
`/plaka 34AKP34`

**Sonuçlar:** Tüm sorgu sonuçları size `.txt` dosyası olarak gönderilir ve KAYIT 1, KAYIT 2 şeklinde düzenli çıkar.
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['adminpanel'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Bu komut sadece adminler içindir!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_ban = types.InlineKeyboardButton("🚫 BANLA", callback_data="admin_ban")
    btn_unban = types.InlineKeyboardButton("✅ UNBAN", callback_data="admin_unban")
    btn_code = types.InlineKeyboardButton("🎫 KOD OLUŞTUR", callback_data="admin_code")
    markup.add(btn_ban, btn_unban, btn_code)
    
    bot.reply_to(message, "👑 **Admin Paneli**\n\nYapmak istediğin işlemi seç:", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "check_membership":
        user_id = call.from_user.id
        if check_channel_membership(user_id):
            bot.edit_message_text("✅ Kanal üyeliğiniz onaylandı! Artık /komutlar yazarak başlayabilirsiniz.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Hala kanala katılmamışsın!", show_alert=True)
    
    elif call.data == "enter_code":
        msg = bot.send_message(call.message.chat.id, "🎫 **Erişim kodunu girin:**", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_code_entry)
    
    elif call.data == "admin_ban":
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Yetkin yok!")
            return
        msg = bot.send_message(call.message.chat.id, "🚫 **Banlamak istediğin kullanıcının ID'sini yaz:**", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_ban_user)
    
    elif call.data == "admin_unban":
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Yetkin yok!")
            return
        msg = bot.send_message(call.message.chat.id, "✅ **Unbanlamak istediğin kullanıcının ID'sini yaz:**", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_unban_user)
    
    elif call.data == "admin_code":
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Yetkin yok!")
            return
        code = generate_code()
        save_code(code)
        bot.send_message(call.message.chat.id, f"🎫 **Yeni kod oluşturuldu:**\n\n`{code}`\n\nBu kodu kullanıcılara verebilirsin.", parse_mode='Markdown')
    
    bot.answer_callback_query(call.id)

def process_code_entry(message):
    user_id = message.from_user.id
    code = message.text.strip().upper()
    
    if verify_code(user_id, code):
        bot.reply_to(message, "✅ **Kod doğrulandı! Artık botu kullanabilirsin.**\n\n/komutlar yazarak başlayabilirsin.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ **Geçersiz kod!**", parse_mode='Markdown')

def process_ban_user(message):
    try:
        user_id = int(message.text.strip())
        ban_user(user_id)
        bot.reply_to(message, f"✅ **Kullanıcı ID {user_id} banlandı!**", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Geçersiz ID!")

def process_unban_user(message):
    try:
        user_id = int(message.text.strip())
        unban_user(user_id)
        bot.reply_to(message, f"✅ **Kullanıcı ID {user_id} banı kaldırıldı!**", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Geçersiz ID!")

# ==================== SORGULAMA KOMUTLARI (AYNEN, HİÇ DEĞİŞMEDİ) ====================

@bot.message_handler(commands=['adsoyad'])
def adsoyad_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/adsoyad AD SOYAD`\nÖrnek: `/adsoyad EYMEN YAVUZ`", parse_mode='Markdown')
            return
        
        name = args[1].upper()
        surname = args[2].upper()
        
        bot.reply_to(message, f"🔍 *{name} {surname}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_ad_soyad(name, surname)
        
        if result and result.strip():
            # Kayıtları ayır
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"sorgu_{name}_{surname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *{name} {surname}* sorgu sonucu\n📊 Toplam kayıt: {len(records)}", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['tc'])
def tc_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/tc TC_NO`\nÖrnek: `/tc 11111111110`", parse_mode='Markdown')
            return
        
        tc_no = args[1]
        
        if not tc_no.isdigit() or len(tc_no) != 11:
            bot.reply_to(message, "❌ Geçersiz TC numarası! TC 11 haneli rakamlardan oluşmalıdır.", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *TC: {tc_no}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_tc(tc_no)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"tc_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* sorgu sonucu", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['gsm'])
def gsm_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/gsm NUMARA`\nÖrnek: `/gsm 5346149118`", parse_mode='Markdown')
            return
        
        gsm = args[1]
        
        bot.reply_to(message, f"🔍 *GSM: {gsm}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_gsm(gsm)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"gsm_{gsm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *GSM: {gsm}* sorgu sonucu", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['plaka'])
def plaka_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/plaka PLAKA`\nÖrnek: `/plaka 34AKP34`", parse_mode='Markdown')
            return
        
        plaka = args[1].upper()
        
        bot.reply_to(message, f"🔍 *Plaka: {plaka}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_plaka(plaka)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"plaka_{plaka}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *Plaka: {plaka}* sorgu sonucu", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['il'])
def il_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/il AD SOYAD İL`\nÖrnekler:\n• `/il Azam Muhammed Diyarbakır`\n• `/il Azam+Muhammed Dilman Diyarbakır`", parse_mode='Markdown')
            return
        
        full_text = ' '.join(args[1:])
        name, surname, il = parse_name_surname(full_text)
        
        if not name or not surname or not il:
            bot.reply_to(message, "❌ Hatalı format!\nDoğru kullanım: `/il AD SOYAD İL`\nÖrnek: `/il Azam Muhammed Diyarbakır`", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *{name} {surname}* - *{il}* için sorgulama yapılıyor...\n📝 Not: Birden fazla isim varsa hepsi aranacak.", parse_mode='Markdown')
        
        result = api_sorgula_ad_soyad(name, surname)
        
        if result and result.strip():
            filtered_records = il_filter(result, il)
            
            if filtered_records:
                formatted_result = format_records_as_ascii(filtered_records)
                
                if formatted_result:
                    clean_name = name.replace(' ', '_').replace('+', '_')
                    filename = f"{il}_{clean_name}_{surname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    if save_to_txt(formatted_result, filename):
                        with open(filename, 'rb') as file:
                            bot.send_document(message.chat.id, file, caption=f"📄 *{il}* ilinde bulunan *{name} {surname}* kayıtları\n📊 Toplam: {len(filtered_records)} kayıt", parse_mode='Markdown')
                        os.remove(filename)
                    else:
                        if len(formatted_result) > 4000:
                            bot.reply_to(message, f"📝 *{il}* ilindeki sonuçlar çok uzun, dosya olarak gönderilemedi.\n\nİlk 4000 karakter:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
                        else:
                            bot.reply_to(message, f"📝 *{il}* ilindeki sonuçlar:\n```\n{formatted_result}\n```", parse_mode='Markdown')
                else:
                    bot.reply_to(message, "❌ *Sonuç formatlanamadı!*", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"❌ *{il}* ilinde *{name} {surname}* için kayıt bulunamadı!", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['aile'])
def aile_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/aile TC_NO`\nÖrnek: `/aile 11111111110`", parse_mode='Markdown')
            return
        
        tc_no = args[1]
        
        if not tc_no.isdigit() or len(tc_no) != 11:
            bot.reply_to(message, "❌ Geçersiz TC numarası! TC 11 haneli rakamlardan oluşmalıdır.", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *TC: {tc_no}* için aile bilgileri sorgulanıyor...", parse_mode='Markdown')
        
        result = api_sorgula_aile(tc_no)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"aile_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* aile bilgileri", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['hane'])
def hane_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/hane TC_NO`\nÖrnek: `/hane 11111111110`", parse_mode='Markdown')
            return
        
        tc_no = args[1]
        
        if not tc_no.isdigit() or len(tc_no) != 11:
            bot.reply_to(message, "❌ Geçersiz TC numarası! TC 11 haneli rakamlardan oluşmalıdır.", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *TC: {tc_no}* için hane bilgileri sorgulanıyor...", parse_mode='Markdown')
        
        result = api_sorgula_hane(tc_no)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"hane_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* hane bilgileri", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['isyeri'])
def isyeri_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/isyeri TC_NO`\nÖrnek: `/isyeri 11111111110`", parse_mode='Markdown')
            return
        
        tc_no = args[1]
        
        if not tc_no.isdigit() or len(tc_no) != 11:
            bot.reply_to(message, "❌ Geçersiz TC numarası! TC 11 haneli rakamlardan oluşmalıdır.", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *TC: {tc_no}* için iş yeri bilgileri sorgulanıyor...", parse_mode='Markdown')
        
        result = api_sorgula_isyeri(tc_no)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"isyeri_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* iş yeri bilgileri", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['vesika'])
def vesika_sorgula(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 KANALA KATIL", url=CHANNEL_LINK))
        bot.reply_to(message, f"❌ Önce {REQUIRED_CHANNEL} kanalına katılmalısın!", reply_markup=markup)
        return
    
    if not is_admin(user_id) and not has_access(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎫 KOD GİR", callback_data="enter_code"))
        bot.reply_to(message, "❌ Önce erişim kodunu girmelisin!", reply_markup=markup)
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/vesika TC_NO`\nÖrnek: `/vesika 11111111110`", parse_mode='Markdown')
            return
        
        tc_no = args[1]
        
        if not tc_no.isdigit() or len(tc_no) != 11:
            bot.reply_to(message, "❌ Geçersiz TC numarası! TC 11 haneli rakamlardan oluşmalıdır.", parse_mode='Markdown')
            return
        
        bot.reply_to(message, f"🔍 *TC: {tc_no}* için vesika bilgileri sorgulanıyor...", parse_mode='Markdown')
        
        result = api_sorgula_vesika(tc_no)
        
        if result and result.strip():
            lines = result.split('\n')
            current_record = []
            records = []
            
            for line in lines:
                if line.strip() == "":
                    if current_record:
                        records.append(current_record)
                        current_record = []
                else:
                    current_record.append(line)
            if current_record:
                records.append(current_record)
            
            if records:
                formatted_result = format_records_as_ascii(records)
                filename = f"vesika_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                if save_to_txt(formatted_result, filename):
                    with open(filename, 'rb') as file:
                        bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* vesika bilgileri", parse_mode='Markdown')
                    os.remove(filename)
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{formatted_result[:4000]}\n```", parse_mode='Markdown')
            else:
                bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

# Bot'u başlat
if __name__ == "__main__":
    print("🤖 Bot başlatılıyor...")
    print("✅ Bot çalışıyor! /komutlar yazarak başlayabilirsiniz.")
    print("📝 Çoklu isim formatı: /il Azam+Muhammed Dilman Diyarbakır")
    print("👑 Admin ID: 7709693701")
    print("📢 Zorunlu Kanal: @gottenvurdurankurtbio")
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
