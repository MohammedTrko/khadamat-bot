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
    # Render يمرر البورت تلقائياً عبر المتغير البيئي PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. تشغيل السيرفر في Thread منفصل
threading.Thread(target=run_flask).start()

bot = telebot.TeleBot(token=API_TOKEN)

# 🛑 أضف أيديات الأدمونية هنا داخل القائمة
ADMIN_IDS = [8886254489]  # ضع المعرف الثاني هنا (مثال: [8886254489, 123456789])

# قاموس لحفظ حالة الأدمن عند الإضافة والتعديل
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
# دالّات التعامل مع قاعدة البيانات
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
# 1. القوائم الشفافة الثابتة
# ---------------------------------------------------------
med_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("أطباء 👨‍⚕️", callback_data="doctors"),
    InlineKeyboardButton("صيدليات ⚕️", callback_data="pharmacies"),
    InlineKeyboardButton("مخابر وتحاليل 🔬", callback_data="labaratory"),
    InlineKeyboardButton("عيادات وأسنان 🦷", callback_data="dentist"),
    InlineKeyboardButton("اسعاف/طوارئ 🚨", callback_data="emergency"),
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
    InlineKeyboardButton("فيزياء ⚛️", callback_data="physics-10"),
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
    InlineKeyboardButton("كيمياء ⚗️", callback_data="chemistry-9"),
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

main_services_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("طبية 💉", callback_data="medicine"),
    InlineKeyboardButton("وسائل نقل 🚕", callback_data="transport"),
    InlineKeyboardButton("منزلية 🏚️", callback_data="home")
)

main_study_markup = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("دروس خصوصية 📘", callback_data="private_lessons"),
    InlineKeyboardButton("مراكز تعليمية 🏫", callback_data="educational_centers")
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
    "back_to_e3dady": ("قائمة الصفوف:", e3dady_markup)
}

# ---------------------------------------------------------
# 2. لوحة تحكم الأدمن والعدّاد الإداري
# ---------------------------------------------------------
def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("➕ إضافة مزود جديد"),
        KeyboardButton("🔍 بحث وتعديل/حذف")
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
        "`heart | د. سامر العلي | 0911223344 | عيادة الشعلان - دوام 4 لـ 8`\n\n"
        "💡 **أكواد شائعة:**\n"
        "• `heart` (قلبية), `children` (أطفال), `dentist` (أسنان)\n"
        "• `taxi` (تكسي), `plumber` (صحية), `math` (رياضيات)\n"
        "• `women_salon` (صالون نسائي), `men_barber` (حلاق)"
    )
    user_states[message.chat.id] = "WAITING_ADD_DATA"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

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
        bot.reply_to(message, "⚠️ الرقم المعرف يجب أن يكون رقماً صحبحاً.")

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

    # إلغاء العملية إذا ضغط على أحد أزرار اللوحة
    if message.text in ["خدمات ⚙️", "صالونات نسائية 💄", "حلاقين رجالي 💈", "خدمات الهواتف المحمولة 📱", "عطورات ⚱️💨", "خدمات تدريس 📗", "➕ إضافة مزود جديد", "🔍 بحث وتعديل/حذف"]:
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
# 5. أزرار اللوحة الرئيسية والتصفح العام (Text Handlers)
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "خدمات ⚙️")
def service_cmd(message):
    bot.send_message(message.chat.id, "اختر القسم المطلوب من الخدمات:", reply_markup=main_services_markup)

@bot.message_handler(func=lambda message: message.text == "خدمات تدريس 📗")
def study_cmd(message):
    bot.send_message(message.chat.id, "اختر قسم التدريس الذي تريده:", reply_markup=main_study_markup)

@bot.message_handler(func=lambda message: message.text in [
    "صالونات نسائية 💄", "حلاقين رجالي 💈", "خدمات الهواتف المحمولة 📱", "عطورات ⚱️💨"
])
def direct_category_handler(message):
    category_map = {
        "صالونات نسائية 💄": "women_salon",
        "حلاقين رجالي 💈": "men_barber",
        "خدمات الهواتف المحمولة 📱": "mobile_services",
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
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)
        else:
            providers = get_providers_by_category(data)
            if providers:
                response = f"📋 **النتائج المتوفرة ({len(providers)}):**\n\n"
                for p_id, name, phone, details in providers:
                    response += f"👤 **الاسم:** {name}\n📞 **الهاتف:** `{phone}`\nℹ️ **التفاصيل:** {details}\n-------------------\n"
            else:
                response = "⚠️ لا يوجد مقدمو خدمات مسجلون في هذا التصنيف حالياً."

            bot.send_message(chat_id, response, parse_mode="Markdown")

    except ApiTelegramException as e:
        if "message is not modified" not in str(e):
            print(f"Telegram API Error: {e}")

# تشغيل البوت
if __name__ == "__main__":
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
