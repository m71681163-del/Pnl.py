import requests
import telebot
from telebot import types
import json
import os
from datetime import datetime
import time
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Bot token
BOT_TOKEN = "7769287068:AAFAqGUUPw1nL_sNXyNzrHnrbLzGKoTF_04"
bot = telebot.TeleBot(BOT_TOKEN)

# API Base URL
BASE_URL = "https://apilerimya.onrender.com"

def api_request(url, params=None, max_retries=3):
    """API isteği gönderir - timeout 30 saniye ve otomatik yeniden deneme"""
    for attempt in range(max_retries):
        try:
            logging.debug(f"API isteği: {url}, params: {params}")
            response = requests.get(
                url, 
                params=params, 
                timeout=30
            )
            
            if response.status_code == 200:
                if response.text and response.text.strip():
                    logging.info(f"API başarılı, yanıt uzunluğu: {len(response.text)}")
                    return response.text
                else:
                    logging.warning("API boş yanıt döndü")
                    return None
            else:
                logging.warning(f"API hata kodu: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logging.warning(f"Zaman aşımı (deneme {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                return None
            time.sleep(2)
        except Exception as e:
            logging.error(f"API hatası: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(2)
    return None

# ==================== YENİ ENDPOINT'LER ====================

def api_sorgula_ad_soyad(name, surname):
    """Ad soyad ile sorgulama - /isegiris endpoint"""
    return api_request(f"{BASE_URL}/isegiris", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_tc(tc):
    """TC ile sorgulama - /tc-isegiris endpoint"""
    return api_request(f"{BASE_URL}/tc-isegiris", params={"tc": tc, "format": "text"})

def api_sorgula_gsm(gsm):
    """GSM ile sorgulama - /gsm endpoint"""
    return api_request(f"{BASE_URL}/gsm", params={"gsm": gsm, "format": "text"})

def api_sorgula_plaka(plaka):
    """Plaka ile sorgulama - /plaka endpoint"""
    return api_request(f"{BASE_URL}/plaka", params={"plaka": plaka, "format": "text"})

def api_sorgula_aile(tc):
    """Aile bilgisi sorgulama - /aile endpoint"""
    return api_request(f"{BASE_URL}/aile", params={"tc": tc, "format": "text"})

def api_sorgula_hane(tc):
    """Hane bilgisi sorgulama - /hane endpoint"""
    return api_request(f"{BASE_URL}/hane", params={"tc": tc, "format": "text"})

def api_sorgula_isyeri(tc):
    """İş yeri bilgisi sorgulama - /isyeri endpoint"""
    return api_request(f"{BASE_URL}/isyeri", params={"tc": tc, "format": "text"})

def api_sorgula_vesika(tc):
    """Vesika bilgisi sorgulama - /vesika endpoint"""
    return api_request(f"{BASE_URL}/vesika", params={"tc": tc, "format": "text"})

def api_sorgula_ikametgah(name, surname):
    """Ad soyad ile ikametgah sorgulama - /ikametgah endpoint"""
    return api_request(f"{BASE_URL}/ikametgah", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_ailebirey(name, surname):
    """Ad soyad ile aile bireyi sorgulama - /ailebirey endpoint"""
    return api_request(f"{BASE_URL}/ailebirey", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

def api_sorgula_medenicinsiyet(name, surname):
    """Ad soyad ile medeni durum ve cinsiyet sorgulama - /medenicinsiyet endpoint"""
    return api_request(f"{BASE_URL}/medenicinsiyet", params={"name": name.upper(), "surname": surname.upper(), "format": "text"})

# ==================== YARDIMCI FONKSİYONLAR ====================

def il_filter(data, il_adi):
    """Veriyi ile göre filtrele ve kayıtları ayır"""
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
    """Kayıtları ASCII kutu formatında düzenle"""
    if not records:
        return None
    
    formatted_text = ""
    for i, record in enumerate(records, 1):
        formatted_text += "╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        formatted_text += f"┃ 📌 KAYIT {i}\n"
        formatted_text += "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for line in record:
            if line.strip():
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        formatted_text += f"┃ {key} : {value}\n"
                else:
                    formatted_text += f"┃ {line}\n"
        
        formatted_text += "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    return formatted_text

def save_to_txt(data, filename):
    """Veriyi txt dosyasına kaydet"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(data)
        return True
    except Exception as e:
        logging.error(f"Dosya kaydetme hatası: {e}")
        return False

def parse_name_surname(text):
    """İsim ve soyismi parse et, + ile ayrılmış isimleri destekle"""
    parts = text.split()
    
    if len(parts) < 3:
        return None, None, None
    
    # Son kelime il olacak
    il = parts[-1].upper()
    
    # İlk kısım ad soyad kısmı
    name_surname_part = ' '.join(parts[:-1])
    
    # Ad ve soyadı ayır (son kelime soyad, öncekiler ad)
    surname = name_surname_part.split()[-1].upper()
    name_part = ' '.join(name_surname_part.split()[:-1]).upper()
    
    # Ad kısmında + varsa işle
    if '+' in name_part:
        name = name_part.replace('+', ' ').upper()
    else:
        name = name_part
    
    return name, surname, il

# ==================== BOT KOMUTLARI ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🎯 **Merhaba! Ben Bilgi Sorgulama Botu**

Size çeşitli bilgi sorgulama hizmetleri sunuyorum.

📌 **Komutları görmek için:** /komutlar

Hemen /komutlar yazarak başlayabilirsin!
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['komutlar'])
def show_commands(message):
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
• `/il Azam Muhammed Dilman Diyarbakır` - Tek isim
• `/il Azam+Muhammed Dilman Diyarbakır` - Çoklu isim (artı ile ayrılmış)

ℹ️ **Diğer:**
`/yardim` - Yardım menüsü
`/test` - Botun çalıştığını test eder
    """
    bot.reply_to(message, commands_text, parse_mode='Markdown')

@bot.message_handler(commands=['yardim'])
def help_command(message):
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

**Sonuçlar:** Tüm sorgu sonuçları size `.txt` dosyası olarak gönderilir.
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def test_command(message):
    try:
        bot.reply_to(message, "🔄 API bağlantısı test ediliyor...")
        response = api_request(f"{BASE_URL}/test")
        if response:
            bot.reply_to(message, f"✅ API çalışıyor!")
        else:
            bot.reply_to(message, "⚠️ API yanıt vermiyor.")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {str(e)}")

@bot.message_handler(commands=['adsoyad'])
def adsoyad_sorgula(message):
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
            filename = f"sorgu_{name}_{surname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *{name} {surname}* sorgu sonucu", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['tc'])
def tc_sorgula(message):
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
            filename = f"tc_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* sorgu sonucu", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['gsm'])
def gsm_sorgula(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/gsm NUMARA`\nÖrnek: `/gsm 5346149118`", parse_mode='Markdown')
            return
        
        gsm = args[1]
        
        bot.reply_to(message, f"🔍 *GSM: {gsm}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_gsm(gsm)
        
        if result and result.strip():
            filename = f"gsm_{gsm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *GSM: {gsm}* sorgu sonucu", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['plaka'])
def plaka_sorgula(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Hatalı kullanım!\nDoğru kullanım: `/plaka PLAKA`\nÖrnek: `/plaka 34AKP34`", parse_mode='Markdown')
            return
        
        plaka = args[1].upper()
        
        bot.reply_to(message, f"🔍 *Plaka: {plaka}* için sorgulama yapılıyor...", parse_mode='Markdown')
        
        result = api_sorgula_plaka(plaka)
        
        if result and result.strip():
            filename = f"plaka_{plaka}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *Plaka: {plaka}* sorgu sonucu", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['il'])
def il_sorgula(message):
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
            filename = f"aile_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* aile bilgileri", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['hane'])
def hane_sorgula(message):
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
            filename = f"hane_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* hane bilgileri", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['isyeri'])
def isyeri_sorgula(message):
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
            filename = f"isyeri_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* iş yeri bilgileri", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['vesika'])
def vesika_sorgula(message):
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
            filename = f"vesika_{tc_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            if save_to_txt(result, filename):
                with open(filename, 'rb') as file:
                    bot.send_document(message.chat.id, file, caption=f"📄 *TC: {tc_no}* vesika bilgileri", parse_mode='Markdown')
                os.remove(filename)
            else:
                if len(result) > 4000:
                    bot.reply_to(message, "⚠️ Sonuç çok uzun, dosya olarak gönderilemedi. Lütfen tekrar deneyin.")
                else:
                    bot.reply_to(message, f"📝 Sonuç:\n```\n{result}\n```", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ *Sonuç bulunamadı!*", parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ *Hata oluştu:* {str(e)}", parse_mode='Markdown')

# Bot'u başlat
if __name__ == "__main__":
    print("🤖 Bot başlatılıyor...")
    print("✅ Bot çalışıyor! /komutlar yazarak başlayabilirsiniz.")
    print("📝 Çoklu isim formatı: /il Azam+Muhammed Dilman Diyarbakır")
    print("⏱️ API timeout süresi: 30 saniye")
    print("🔄 Otomatik yeniden deneme: 3 kez")
    
    # Railway için health check endpoint
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Bot is running")
        
        def run_health_server():
            port = int(os.environ.get('PORT', 8080))
            server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
            server.serve_forever()
        
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        print(f"🏥 Health check server running on port {os.environ.get('PORT', 8080)}")
    except:
        pass
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
