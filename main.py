from config import API_TOKEN
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot.apihelper import ApiTelegramException
import psycopg2
from psycopg2 import pool
import os
import threading
from flask import Flask

# 1. إنشاء تطبيق سيرفر وهمي لإبقاء Render سعيداً
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

bot = telebot.TeleBot(token=API_TOKEN)

# أيديات الأدمن
ADMIN_IDS = [8886254489, 962620820, 6502101293]

user_states = {}

# --------------------------------------------------------- 
# إعداد مجمع الاتصالات (Connection Pool)
# ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
        print("PostgreSQL connection pool created successfully (from Render Environment)")
    except Exception as e:
        print(f"Error creating connection pool: {e}")
else:
    DB_PARAMS = {
        "dbname": "postgres",
        "user": "postgres",
        "password": "123",
        "host": "localhost",
        "port": "5432"
    }
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_PARAMS)
        print("PostgreSQL connection pool created successfully (Localhost)")
    except Exception as e:
        print(f"Error creating connection pool: {e}")

# ---------------------------------------------------------
# دالّات التعامل مع قاعدة البيانات (جدول المزودين)
# ---------------------------------------------------------
def get_providers_by_category(category_code):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "SELECT id, name, phone, details FROM providers WHERE category_code = %s LIMIT 20;"
        cursor.execute(query, (category_code,))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database Error: {e}")
        return []
    finally:
        if conn:
            db_pool.putconn(conn)

def add_provider_to_db(name, phone, details, category_code):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "INSERT INTO providers (name, phone, details, category_code) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (name, phone, details, category_code))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Database Insert Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db_pool.putconn(conn)

def delete_provider_from_db(provider_id):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "DELETE FROM providers WHERE id = %s;"
        cursor.execute(query, (provider_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    except Exception as e:
        print(f"Database Delete Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db_pool.putconn(conn)

def search_providers_in_db(search_term):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "SELECT id, name, phone, details, category_code FROM providers WHERE name ILIKE %s OR phone ILIKE %s LIMIT 10;"
        cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database Search Error: {e}")
        return []
    finally:
        if conn:
            db_pool.putconn(conn)

def update_provider_in_db(provider_id, name, phone, details, category_code):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "UPDATE providers SET name = %s, phone = %s, details = %s, category_code = %s WHERE id = %s;"
        cursor.execute(query, (name, phone, details, category_code, provider_id))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    except Exception as e:
        print(f"Database Update Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db_pool.putconn(conn)

# ---------------------------------------------------------
# دالّات التعامل مع أسعار الهواتف بحسب البراند (phone_prices)
# ---------------------------------------------------------
def get_phone_prices_by_brand(brand_code):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "SELECT id, model, price FROM phone_prices WHERE brand = %s ORDER BY id DESC;"
        cursor.execute(query, (brand_code,))
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database Error (get_phone_prices_by_brand): {e}")
        return []
    finally:
        if conn:
            db_pool.putconn(conn)

def get_all_phone_prices():
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "SELECT id, brand, model, price FROM phone_prices ORDER BY id DESC LIMIT 30;"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"Database Error (get_all_phone_prices): {e}")
        return []
    finally:
        if conn:
            db_pool.putconn(conn)

def add_phone_price_to_db(brand, model, price):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "INSERT INTO phone_prices (brand, model, price) VALUES (%s, %s, %s);"
        cursor.execute(query, (brand.lower().strip(), model, price))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Database Phone Price Insert Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db_pool.putconn(conn)

def delete_phone_price_from_db(price_id):
    conn = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        query = "DELETE FROM phone_prices WHERE id = %s;"
        cursor.execute(query, (price_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    except Exception as e:
        print(f"Database Phone Price Delete Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            db_pool.putconn(conn)

# ---------------------------------------------------------
# 1. القوائم الشفافة الثابتة
# ---------------------------------------------------------
med_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("أطباء 👨‍⚕️", callback_data="doctors"),
    InlineKeyboardButton("صيدليات ⚕️", callback_data="pharmacies"),
    InlineKeyboardButton("مخابر وتحاليل 🔬", callback_data="labaratory"),
    InlineKeyboardButton("عيادات وأسنان 🦷", callback_data="dentist"),
    InlineKeyboardButton("اسعاف/طوارئ 🚨", callback_data="emergency"),
    InlineKeyboardButton("ممرضين 🧑‍⚕️", callback_data="nurses"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_services")
)

trans_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("تكاسي 🚕", callback_data="taxi"),
    InlineKeyboardButton("ميكرو باص 🚌", callback_data="microbus"),
    InlineKeyboardButton("فانات 🚐", callback_data="vans"),
    InlineKeyboardButton("ميكانيكيون 🔧", callback_data="mechanics"),
    InlineKeyboardButton("كهرباء سيارات 🧑‍🔧", callback_data="elec"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_services")
)

home_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("صحية 🧑‍🔧", callback_data="plumber"),
    InlineKeyboardButton("كهرباء منزلية 👨‍🔧", callback_data="home_elect"),
    InlineKeyboardButton("نجار 🪚", callback_data="carpenter"),
    InlineKeyboardButton("دهان 🪣", callback_data="painter"),
    InlineKeyboardButton("خياط 🪡", callback_data="tailor"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_services")
)

doc_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("قلبية ❤️", callback_data="heart"),
    InlineKeyboardButton("عظمية 🦴", callback_data="bones"),
    InlineKeyboardButton("جلدية 🩹", callback_data="skin"),
    InlineKeyboardButton("أطفال 👶", callback_data="children"),
    InlineKeyboardButton("أسنان 🦷", callback_data="dentist"),
    InlineKeyboardButton("عيون 👁️", callback_data="eyes"),
    InlineKeyboardButton("أعصاب 🧠", callback_data="nerves"),
    InlineKeyboardButton("نساء وتوليد 🤰", callback_data="women"),
    InlineKeyboardButton("أذن أنف حنجرة 👂", callback_data="ear"),
    InlineKeyboardButton("مسالك بولية 🚻", callback_data="urinary"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_services")
)

private_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("بكالوريا", callback_data="bakaloria"),
    InlineKeyboardButton("ثانوي", callback_data="secondary"),
    InlineKeyboardButton("اعدادي", callback_data="e3dady"),
    InlineKeyboardButton("ابتدائي", callback_data="primary"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_study")
)

bakaloria_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("علمي", callback_data="scientific"),
    InlineKeyboardButton("ادبي", callback_data="literary"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_private_lessons")
)

scientific_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math"),
    InlineKeyboardButton("فيزياء ⚛️", callback_data="physics"),
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry"),
    InlineKeyboardButton("أحياء 🧬", callback_data="biology"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_bakaloria")
)

literary_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("فلسفة 🧠", callback_data="philosophy"),
    InlineKeyboardButton("تاريخ 🏺", callback_data="history"),
    InlineKeyboardButton("جغرافيا 🌍", callback_data="geography"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic_lit"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english_lit"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french_lit"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_bakaloria")
)

secondary_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("حادي عشر علمي", callback_data="science-11"),
    InlineKeyboardButton("حادي عشر أدبي", callback_data="literary-11"),
    InlineKeyboardButton("عاشر علمي", callback_data="science-10"),
    InlineKeyboardButton("عاشر أدبي", callback_data="literary-10"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_private_lessons")
)

science_11_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math-11"),
    InlineKeyboardButton("فيزياء ⚛️", callback_data="physics-11"),
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry-11"),
    InlineKeyboardButton("أحياء 🧬", callback_data="biology-11"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-11"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-11"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_secondary")
)

literary_11_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("تاريخ 🏺", callback_data="history-11"),
    InlineKeyboardButton("جغرافيا 🌍", callback_data="geography-11"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-11"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-11"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french-11"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_secondary")
)

science_10_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math-10"),
    InlineKeyboardButton("فيزياء ⚛️️", callback_data="physics-10"),
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry-10"),
    InlineKeyboardButton("أحياء 🧬", callback_data="biology-10"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-10"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-10"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_secondary")
)

literary_10_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("تاريخ 🏺", callback_data="history-10"),
    InlineKeyboardButton("جغرافيا 🌍", callback_data="geography-10"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-10"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-10"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french-10"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_secondary")
)

e3dady_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("تاسع", callback_data="grade-9"),
    InlineKeyboardButton("ثامن", callback_data="grade-8"),
    InlineKeyboardButton("سابع", callback_data="grade-7"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_private_lessons")
)

grade_9_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math-9"),
    InlineKeyboardButton("علوم 🔬", callback_data="science-9"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-9"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-9"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french-9"),
    InlineKeyboardButton("اجتماعيات 🏺", callback_data="history-9"),
    InlineKeyboardButton("كيمياء ⚗️️", callback_data="chemistry-9"),
    InlineKeyboardButton("فيزياء ⚡", callback_data="physics-9"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_e3dady")
)

grade_8_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math-8"),
    InlineKeyboardButton("علوم 🔬", callback_data="science-8"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-8"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-8"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french-8"),
    InlineKeyboardButton("اجتماعيات 🏺", callback_data="history-8"),
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry-8"),
    InlineKeyboardButton("فيزياء ⚡", callback_data="physics-8"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_e3dady")
)

grade_7_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("رياضيات 📐", callback_data="math-7"),
    InlineKeyboardButton("علوم 🔬", callback_data="science-7"),
    InlineKeyboardButton("لغة إنجليزية 📝", callback_data="english-7"),
    InlineKeyboardButton("لغة عربية 📝", callback_data="arabic-7"),
    InlineKeyboardButton("لغة فرنسية 📝", callback_data="french-7"),
    InlineKeyboardButton("اجتماعيات 🏺", callback_data="history-7"),
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry-7"),
    InlineKeyboardButton("فيزياء ⚡", callback_data="physics-7"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_e3dady")
)

mobile_services_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("أسعار الهواتف 📱", callback_data="phone_brands_menu"),
    InlineKeyboardButton("إكسسوارات 🎧", callback_data="phone_acc"),
    InlineKeyboardButton("صيانة 🛠️", callback_data="phone_repair"),
    InlineKeyboardButton("شحن برامج وألعاب 🎮", callback_data="apps_charging")
)

# قائمة ماركات الهواتف
brands_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Samsung 📱", callback_data="brand_samsung"),
    InlineKeyboardButton("Xiaomi 📱", callback_data="brand_xiaomi"),
    InlineKeyboardButton("iPhone 🍏", callback_data="brand_iphone"),
    InlineKeyboardButton("Infinix ⚡", callback_data="brand_infinix"),
    InlineKeyboardButton("Tecno 📱", callback_data="brand_tecno"),
    InlineKeyboardButton("Realme 📱", callback_data="brand_realme"),
    InlineKeyboardButton("Honor 📱", callback_data="brand_honor"),
    InlineKeyboardButton("Blackview 🛡️", callback_data="brand_blackview"),
    InlineKeyboardButton("G-Tab 📱", callback_data="brand_gtab"),
    InlineKeyboardButton("Itel 📱", callback_data="brand_itel"),
    InlineKeyboardButton("Nokia 📞", callback_data="brand_nokia"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_mobile_services")
)

# قائمة شحن برامج وألعاب
apps_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("ألعاب 🎮", callback_data="games_charging"),
    InlineKeyboardButton("تطبيقات 📱", callback_data="app_charging"),
    InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_mobile_services")
)

main_services_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("طبية 💉", callback_data="medicine"),
    InlineKeyboardButton("وسائل نقل 🚕", callback_data="transport"),
    InlineKeyboardButton("منزلية 🏚️", callback_data="home")
)

main_study_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("دروس خصوصية 📘", callback_data="private_lessons"),
    InlineKeyboardButton("مراكز تعليمية 🏫", callback_data="educational_centers")
)

# نص الترويسة لخدمات الهواتف المحمولة
MOBILE_HEADER_TEXT = (
    "🏬 **محل: المجرة**\n"
    "📞 **للتواصل والطلب:** `0938405073`\n"
    "📍 **العنوان:** وادي المشاريع قبل ساحة الشهداء\n\n"
    "-----------------------------------\n"
    "📱 **قسم خدمات الهواتف المحمولة:**\n"
    "اختر الخدمة المطلوبة من القائمة أدناه:"
)

navigation_callbacks = {
    "medicine": ("اختر الخدمة الطبية التي تريدها:", med_markup),
    "transport": ("اختر خدمة النقل التي تريدها:", trans_markup),
    "home": ("اختر الخدمة المنزلية التي تريدها:", home_markup),
    "back_to_services": ("ما الخدمة التي تريدها:", main_services_markup),
    "doctors": ("قائمة الأطباء 👨‍⚕️:", doc_markup),
    "private_lessons": ("اختر نوع الدروس الخصوصية التي تريدها:", private_markup),
    "back_to_study": ("ما الخدمة التي تريدها:", main_study_markup),
    "bakaloria": ("قائمة الدروس الخصوصية للبكالوريا:", bakaloria_markup),
    "back_to_private_lessons": ("اختر نوع الدروس الخصوصية التي تريدها:", private_markup),
    "scientific": ("قائمة الدروس الخصوصية للبكالوريا العلمي:", scientific_markup),
    "back_to_bakaloria": ("قائمة الدروس الخصوصية للبكالوريا:", bakaloria_markup),
    "literary": ("قائمة الدروس الخصوصية للبكالوريا الأدبي:", literary_markup),
    "secondary": ("قائمة الدروس الخصوصية للثانوي:", secondary_markup),
    "science-11": ("قائمة الدروس الخصوصية للثانوي العلمي (حادي عشر):", science_11_markup),
    "literary-11": ("قائمة الدروس الخصوصية للثانوي الأدبي (حادي عشر):", literary_11_markup),
    "back_to_secondary": ("قائمة الدروس الخصوصية للثانوي:", secondary_markup),
    "science-10": ("قائمة الدروس الخصوصية للثانوي العلمي (عاشر):", science_10_markup),
    "literary-10": ("قائمة الدروس الخصوصية للثانوي الأدبي (عاشر):", literary_10_markup),
    "e3dady": ("قائمة الدروس الخصوصية للمرحلة الإعدادية:", e3dady_markup),
    "grade-9": ("قائمة الدروس الخصوصية للصف التاسع:", grade_9_markup),
    "grade-8": ("قائمة الدروس الخصوصية للصف الثامن:", grade_8_markup),
    "grade-7": ("قائمة الدروس الخصوصية للصف السابع:", grade_7_markup),
    "back_to_e3dady": ("قائمة الصفوف:", e3dady_markup),
    "phone_brands_menu": ("اختر ماركة الهاتف لعرض قائمة الأسعار:", brands_markup),
    "back_to_mobile_services": (MOBILE_HEADER_TEXT, mobile_services_markup),
    "apps_charging": ("📱 شحن برامج وألعاب:\nاختر نوع الشحن:", apps_markup)
}

# ---------------------------------------------------------
# 2. لوحة تحكم الأدمن
# ---------------------------------------------------------
def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("➕ إضافة مزود جديد"),
        KeyboardButton("🔍 بحث وتعديل/حذف")
    )
    markup.add(
        KeyboardButton("📱➕ إضافة سعر هاتف"),
        KeyboardButton("📱❌ حذف سعر هاتف")
    )
    markup.add(
        KeyboardButton("خدمات ⚙️"),
        KeyboardButton("صالونات نسائية 💄"),
        KeyboardButton("حلاقين رجالي 💈")
    )
    markup.add(
        KeyboardButton("خدمات الهواتف المحمولة 📱"),
        KeyboardButton("عطورات ⚱️💨"),
        KeyboardButton("خدمات تدريس 📗")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "👑 أهلاً بك يا أدمن! تم تفعيل لوحة التحكم:", reply_markup=get_admin_keyboard())
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("خدمات ⚙️"),
            KeyboardButton("صالونات نسائية 💄"),
            KeyboardButton("حلاقين رجالي 💈"),
            KeyboardButton("خدمات الهواتف المحمولة 📱"),
            KeyboardButton("عطورات ⚱️💨"),
            KeyboardButton("خدمات تدريس 📗")
        )
        bot.send_message(message.chat.id, "أهلاً بك! اختر الخدمة التي تريدها:", reply_markup=markup)

# ---------------------------------------------------------
# 3. أوامر الإدارة (إضافة / بحث / تعديل / حذف)
# ---------------------------------------------------------
@bot.message_handler(func=lambda msg: msg.text == "➕ إضافة مزود جديد" and msg.from_user.id in ADMIN_IDS)
def admin_add_start(message):
    text = (
        "✍️ **طريقة إضافة مزود جديد:**\n\n"
        "أرسل بيانات المزود بفيشة واحدة كالتالي:\n"
        "`الكود | الاسم | الهاتف | التفاصيل`\n\n"
        "**مثال:**\n"
        "`heart | د. سامر العلي | 0911223344 | عيادة الشعلان - دوام 4 لـ 8`"
    )
    user_states[message.chat.id] = "WAITING_ADD_DATA"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📱➕ إضافة سعر هاتف" and msg.from_user.id in ADMIN_IDS)
def admin_add_phone_price_start(message):
    text = (
        "📲 **إضافة سعر هاتف جديد:**\n\n"
        "أرسل البيانات بالشكل التالي:\n"
        "`الكود | الموديل | السعر`\n\n"
        "💡 **أكواد الماركات المتاحة:**\n"
        "`samsung`, `xiaomi`, `iphone`, `infinix`, `tecno`, `realme`, `honor`, `blackview`, `gtab`, `itel`, `nokia`\n\n"
        "**مثال:**\n"
        "`samsung | Galaxy A55 | 3,200,000 ل.س`\n"
        "`iphone | 15 Pro Max 256GB | 14,500,000 ل.س`"
    )
    user_states[message.chat.id] = "WAITING_ADD_PHONE_PRICE"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📱❌ حذف سعر هاتف" and msg.from_user.id in ADMIN_IDS)
def admin_delete_phone_price_start(message):
    prices = get_all_phone_prices()
    if not prices:
        bot.send_message(message.chat.id, "⚠️ لا توجد أجهزة مسجلة في قائمة الأسعار حالياً.")
        return
    
    response = "📋 **قائمة أسعار الهواتف (آخر المسجلات):**\n\n"
    for p_id, brand, model, price in prices:
        response += f"🆔 **ID:** `{p_id}` | [{brand.upper()}] {model} - 💰 {price}\n"
    
    response += "\n💡 **للحذف:** أرسل الأمر `/delphone ID` (مثال: `/delphone 3`)"
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

@bot.message_handler(commands=['delphone'])
def cmd_delete_phone_price(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ الاستخدام الصحيح:\n`/delphone ID`\nمثال: `/delphone 2`", parse_mode="Markdown")
            return
        p_id = int(parts[1])
        if delete_phone_price_from_db(p_id):
            bot.reply_to(message, f"✅ تم حذف الهاتف ذو الرقم `{p_id}` بنجاح!", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ لم يتم العثور على هاتف بالرقم المعرف `{p_id}`.", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "⚠️ الرقم المعرف يجب أن يكون رقماً صحيحاً.")

@bot.message_handler(func=lambda msg: msg.text == "🔍 بحث وتعديل/حذف" and msg.from_user.id in ADMIN_IDS)
def admin_search_start(message):
    user_states[message.chat.id] = "WAITING_SEARCH_TERM"
    bot.send_message(message.chat.id, "🔎 أرسل اسم المزود أو رقم هاتفه للبحث عنه:")

@bot.message_handler(commands=['delete'])
def cmd_delete_provider(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ طريقة الاستخدام الصحيحة:\n`/delete [الرقم المعرف ID]`\nمثال: `/delete 5`", parse_mode="Markdown")
            return
        provider_id = int(parts[1])
        if delete_provider_from_db(provider_id):
            bot.reply_to(message, f"✅ تم حذف المزود ذو الرقم `{provider_id}` بنجاح!", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ لم يتم العثور على مزود بالرقم `{provider_id}`.", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "⚠️ الرقم المعرف يجب أن يكون رقماً صحيحاً.")

@bot.message_handler(commands=['edit'])
def cmd_edit_provider(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = (
        "✏️ **طريقة تعديل بيانات مزود:**\n\n"
        "أرسل الأمر والبيانات بالشكل التالي:\n"
        "`ID | الكود | الاسم | الهاتف | التفاصيل`\n\n"
        "**مثال:**\n"
        "`5 | heart | د. سامر العلي | 0999999999 | عيادة المالكي - دوام 5 لـ 9`"
    )
    user_states[message.chat.id] = "WAITING_EDIT_DATA"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ---------------------------------------------------------
# 4. استقبال النصوص وإدارة الحالات (States Handler)
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id] is not None)
def handle_admin_states(message):
    state = user_states.get(message.chat.id)

    if message.text in ["خدمات ⚙️", "صالونات نسائية 💄", "حلاقين رجالي 💈", "خدمات الهواتف المحمولة 📱", "عطورات ⚱️💨", "خدمات تدريس 📗", "➕ إضافة مزود جديد", "🔍 بحث وتعديل/حذف", "📱➕ إضافة سعر هاتف", "📱❌ حذف سعر هاتف"]:
        user_states[message.chat.id] = None
        return

    if state == "WAITING_ADD_DATA":
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) < 4:
            bot.reply_to(message, "⚠️ تنسيق خاطئ! تأكد من فصل البيانات بعلامة `|` بشكل صحيح:\n`الكود | الاسم | الهاتف | التفاصيل`", parse_mode="Markdown")
            return

        cat_code, name, phone, details = parts[0], parts[1], parts[2], parts[3]
        if add_provider_to_db(name, phone, details, cat_code):
            bot.reply_to(message, f"✅ **تمت الإضافة بنجاح!**\n\n👤 **الاسم:** {name}\n📞 **الهاتف:** {phone}\n🏷️ **التصنيف:** `{cat_code}`", parse_mode="Markdown")
            user_states[message.chat.id] = None
        else:
            bot.reply_to(message, "❌ حدث خطأ أثناء إضافة البيانات في قاعدة البيانات.")

    elif state == "WAITING_ADD_PHONE_PRICE":
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ تنسيق خاطئ! أرسل البيانات بهذا الشكل:\n`الكود | الموديل | السعر`\nمثال:\n`samsung | Galaxy A55 | 3,200,000 ل.س`", parse_mode="Markdown")
            return

        brand, model, price = parts[0], parts[1], parts[2]
        if add_phone_price_to_db(brand, model, price):
            bot.reply_to(message, f"✅ **تمت إضافة سعر الهاتف بنجاح!**\n\n🏷️ **البراند:** `{brand.upper()}`\n📱 **الموديل:** {model}\n💰 **السعر:** {price}", parse_mode="Markdown")
            user_states[message.chat.id] = None
        else:
            bot.reply_to(message, "❌ حدث خطأ أثناء إضافة السعر.")

    elif state == "WAITING_SEARCH_TERM":
        term = message.text.strip()
        results = search_providers_in_db(term)
        user_states[message.chat.id] = None

        if results:
            response = f"🔍 **نتائج البحث عن ({term}):**\n\n"
            for p_id, name, phone, details, cat in results:
                response += f"🆔 **ID:** `{p_id}`\n👤 **الاسم:** {name}\n📞 **الهاتف:** `{phone}`\n🏷️ **الكود:** `{cat}`\nℹ️ **التفاصيل:** {details}\n-------------------\n"
            response += "\n💡 **للحذف:** أرسل `/delete ID` (مثال: `/delete 3`)\n💡 **لتعديل البيانات:** أرسل `/edit` وستصلك التعليمات."
        else:
            response = "⚠️ لم يتم العثور على أية نتائج تطابق البحث."

        bot.send_message(message.chat.id, response, parse_mode="Markdown")

    elif state == "WAITING_EDIT_DATA":
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) < 5:
            bot.reply_to(message, "⚠️ تنسيق خاطئ! أرسل البيانات بهذا الشكل:\n`ID | الكود | الاسم | الهاتف | التفاصيل`", parse_mode="Markdown")
            return

        try:
            p_id = int(parts[0])
            cat_code, name, phone, details = parts[1], parts[2], parts[3], parts[4]

            if update_provider_in_db(p_id, name, phone, details, cat_code):
                bot.reply_to(message, f"✅ **تم تعديل بيانات المزود ذو الرقم ({p_id}) بنجاح!**", parse_mode="Markdown")
                user_states[message.chat.id] = None
            else:
                bot.reply_to(message, f"❌ لم يتم التعديل. تأكد من صحة رقم الـ ID (`{p_id}`).", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "⚠️ رقم الـ ID يجب أن يكون رقماً صحيحاً.")

# ---------------------------------------------------------
# 5. أزرار اللوحة الرئيسية والتصفح العام
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "خدمات ⚙️")
def service_cmd(message):
    bot.send_message(message.chat.id, "اختر القسم المطلوب من الخدمات:", reply_markup=main_services_markup)

@bot.message_handler(func=lambda message: message.text == "خدمات تدريس 📗")
def study_cmd(message):
    bot.send_message(message.chat.id, "اختر قسم التدريس الذي تريده:", reply_markup=main_study_markup)

@bot.message_handler(func=lambda message: message.text == "خدمات الهواتف المحمولة 📱")
def mobile_services_cmd(message):
    bot.send_message(
        message.chat.id, 
        MOBILE_HEADER_TEXT, 
        reply_markup=mobile_services_markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text in [
    "صالونات نسائية 💄", "حلاقين رجالي 💈", "عطورات ⚱️💨"
])
def direct_category_handler(message):
    category_map = {
        "صالونات نسائية 💄": "women_salon",
        "حلاقين رجالي 💈": "men_barber",
        "عطورات ⚱️💨": "perfumes"
    }
    
    code = category_map.get(message.text)
    providers = get_providers_by_category(code)
    
    if providers:
        response = f"📋 **النتائج المتوفرة لـ ({message.text}):**\n\n"
        for p_id, name, phone, details in providers:
            response += f"👤 **الاسم:** {name}\n📞 **الهاتف:** `{phone}`\nℹ️ **التفاصيل:** {details}\n-------------------\n"
    else:
        response = "⚠️ لا يوجد مقدمو خدمات مسجلون في هذا التصنيف حالياً."

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# ---------------------------------------------------------
# 6. معالجة كافة الأزرار الشفافة (Inline Callbacks)
# ---------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    try:
        if data in navigation_callbacks:
            text, markup = navigation_callbacks[data]
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        
        # معالجة أزرار أسعار الماركات المختلفة
        elif data.startswith("brand_"):
            brand_code = data.replace("brand_", "")
            prices = get_phone_prices_by_brand(brand_code)
            
            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data="phone_brands_menu")
            )

            if prices:
                response = f"📱 **أسعار هواتف {brand_code.upper()}:**\n\n"
                for _, model, price in prices:
                    response += f"▪️ **{model}:** {price}\n"
            else:
                response = f"⚠️ لا توجد أسعار مسجلة لماركة {brand_code.upper()} حالياً."

            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

        # معالجة الأقسام الفرعية لخدمات الهواتف المحمولة
        elif data == "phone_acc":
            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_mobile_services")
            )
            response = (
                "🎧 **قسم إكسسوارات الهواتف:**\n\n"
                "متوفر لدينا كافة الإكسسوارات الأصلية:\n"
                "▪️ سماعات بلوتوث وسلكية عالي الجودة.\n"
                "▪️ شواحن سريعة ورؤوس أصلية (Type-C & Lightning).\n"
                "▪️ كفرات حماية متنوعة ومجنابة.\n"
                "▪️ لزقات حماية شاشة (حراري، نانو، زجاج).\n\n"
                "📞 للتواصل والطلب: `0938405073`"
            )
            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

        elif data == "phone_repair":
            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data="back_to_mobile_services")
            )
            response = (
                "🛠️ **قسم صيانة الهواتف المحمولة:**\n\n"
                "نقدم خدمات الصيانة الفورية بأيدي أخصائيين:\n"
                "▪️ تبديل شاشات أصلية ومكفولة.\n"
                "▪️ تبديل بطاريات وبطاريات أصلية.\n"
                "▪️ صيانة أعطال البورد والشحن.\n"
                "▪️ حل مشاكل السوفتوير وفك الحماية.\n\n"
                "📞 للتواصل والاستفسار: `0938405073`"
            )
            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

        elif data == "games_charging":
            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data="apps_charging")
            )
            response = (
                "🎮 **شحن رصيد الألعاب:**\n\n"
                "▪️ شحن شدات ببجي موبايل (PUBG Mobile UC).\n"
                "▪️ شحن جواهر فري فاير (Free Fire).\n"
                "▪️ شحن العاب أخرى (Roblox, Call of Duty).\n\n"
                "📞 للطلب والشحن الفوري تواصل معنا: `0938405073`"
            )
            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

        elif data == "app_charging":
            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data="apps_charging")
            )
            response = (
                "📱 **شحن وتفعيل التطبيقات:**\n\n"
                "▪️ تفعيل اشتراكات نتفلكس (Netflix).\n"
                "▪️ تفعيل يوتيوب بريميوم (YouTube Premium).\n"
                "▪️ تفعيل تطبيقات البث والبرامج المدفوعة.\n\n"
                "📞 للطلب والتفعيل الفوري تواصل معنا: `0938405073`"
            )
            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

        # معالجة بقية التصنيفات العامة (جلب من جدول المزودين providers) وتوجيه زر الرجوع
        else:
            providers = get_providers_by_category(data)
            
            # تحديد وجهة زر الرجوع ديناميكياً
            if data in ["math", "physics", "chemistry", "biology", "english", "french", "arabic"]:
                back_target = "scientific"
            elif data in ["philosophy", "history", "geography", "arabic_lit", "english_lit", "french_lit"]:
                back_target = "literary"
            elif data in ["math-11", "physics-11", "chemistry-11", "biology-11"]:
                back_target = "science-11"
            elif data in ["history-11", "geography-11", "french-11"]:
                back_target = "literary-11"
            elif data in ["arabic-11", "english-11"]:
                back_target = "secondary"
            elif data in ["math-10", "physics-10", "chemistry-10", "biology-10"]:
                back_target = "science-10"
            elif data in ["history-10", "geography-10", "french-10"]:
                back_target = "literary-10"
            elif data in ["arabic-10", "english-10"]:
                back_target = "secondary"
            elif data.endswith("-9"):
                back_target = "grade-9"
            elif data.endswith("-8"):
                back_target = "grade-8"
            elif data.endswith("-7"):
                back_target = "grade-7"
            elif data == "educational_centers":
                back_target = "back_to_study"
            else:
                back_target = "back_to_services"

            back_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("رجوع ⬅️", callback_data=back_target)
            )

            if providers:
                response = f"📋 **النتائج المتوفرة:**\n\n"
                for _, name, phone, details in providers:
                    response += f"👤 **الاسم:** {name}\n📞 **الهاتف:** `{phone}`\nℹ️ **التفاصيل:** {details}\n-------------------\n"
            else:
                response = "⚠️ لا يوجد مقدمو خدمات مسجلون في هذا القسم حالياً."

            bot.edit_message_text(response, chat_id, msg_id, reply_markup=back_markup, parse_mode="Markdown")

    except ApiTelegramException as e:
        print(f"Telegram API Exception: {e}")
    except Exception as e:
        print(f"Error handling callback query: {e}")

# ---------------------------------------------------------
# تشغيل البوت
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Bot started successfully!")
    bot.infinity_polling(skip_pending=True)
