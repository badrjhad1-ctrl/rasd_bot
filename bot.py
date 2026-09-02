import sqlite3
import asyncio
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "8394727713:AAHg61qPaps8vhO4vzvPeO_BEMOwsXZWPyc"
ADMIN_ID = 8026473540  

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            expiry_date TEXT,
            avatar_file_id TEXT
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_file_id TEXT")
    except:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instagram_monitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            ig_username TEXT,
            start_time TEXT
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE instagram_monitors ADD COLUMN start_time TEXT")
    except:
        pass
        
    conn.commit()
    conn.close()

init_db()

class AdminStates(StatesGroup):
    waiting_for_add_id = State()
    waiting_for_delete_id = State() # <-- تم إضافة حالة حذف الاشتراك هنا
    waiting_for_search_id = State()

class UserStates(StatesGroup):
    waiting_for_ig_username = State()
    waiting_for_avatar = State()

def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    expiry_date = datetime.strptime(result[0], "%Y-%m-%d")
    if datetime.now() > expiry_date:
        return False
    return True

def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("➕ إضافة اشتراك"),
        types.KeyboardButton("🗑️ حذف اشتراك"),
        types.KeyboardButton("📋 قائمة المشتركين"),
        types.KeyboardButton("🔍 بحث عن مستخدم"),
        types.KeyboardButton("⚙️ الإعدادات")
    )
    return keyboard

def get_user_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("📷 مراقبة حساب إنستغرام"),
        types.KeyboardButton("✨ تعيين أفتار متحرك"),
        types.KeyboardButton("👤 معلومات اشتراكي"),
        types.KeyboardButton("📞 تواصل مع الدعم")
    )
    return keyboard

def get_support_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    support_btn = types.InlineKeyboardButton("💬 اضغط هنا لمراسلة المطور وتفعيل الاشتراك", url="https://t.me/celvr")
    keyboard.add(support_btn)
    return keyboard

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        unsub_text = (
            "⚠️ **عذراً، اشتراكات البوت مدفوعة وغير مفعّلة لديك يا أخي.**\n\n"
            "إذا كنت ترغب في شراء اشتراك وتفعيل ميزات مراقبة إنستغرام والأفتار المتحرك، يرجى مراسلة المطور عبر الزر أدناه لشراء الاشتراك 📥"
        )
        await message.answer(unsub_text, parse_mode="Markdown", reply_markup=get_support_inline_keyboard())
        return
    
    if user_id == ADMIN_ID:
        await message.answer("أهلاً بك يا مطور البوت في لوحة التحكم الإدارية:", reply_markup=get_admin_keyboard())
    else:
        await message.answer("أهلاً بك عزيزي المشترك! ✅ تم التحقق من اشتراكك بنجاح.\nإليك لوحة التحكم الخاصة بك:", reply_markup=get_user_keyboard())

@dp.message_handler(lambda message: not check_subscription(message.from_user.id))
async def not_subscribed_handler(message: types.Message):
    unsub_text = (
        "❌ **عذراً، لا يمكنك استخدام أزرار البوت لأن حسابك غير مشترك.**\n\n"
        "للاشتراك وتفعيل البوت، يرجى التواصل مع المطور مباشرة عبر الزر أدناه 💬"
    )
    await message.answer(unsub_text, parse_mode="Markdown", reply_markup=get_support_inline_keyboard())

@dp.message_handler(lambda message: message.text == "📞 تواصل مع الدعم")
async def contact_support(message: types.Message):
    await message.answer("💬 للإبلاغ عن مشكلة أو الاستفسار، يمكنك مراسلة المطور (`@celvr`) مباشرة عبر الزر أدناه:", reply_markup=get_support_inline_keyboard())

# --- أمر الاختبار التجريبي للأفتار ---
@dp.message_handler(commands=['test_avatar'])
async def test_avatar_send(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT avatar_file_id FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    avatar_id = res[0] if res else None
    
    ig_username = "2r05"
    tat_str = "4 ساعات و 32 دقيقة و 44 ثانية"
    time_str = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')
    
    caption_text = (
        f"🎉 تم فك الحظر عن الحساب: @{ig_username}\n"
        f"⏱️ مدة الحظر (TAT): {tat_str}\n"
        f"📅 وقت الفك: {time_str}\n"
        f"👤 بواسطة: @celvr"
    )
    
    if avatar_id:
        await bot.send_animation(user_id, animation=avatar_id, caption=caption_text)
    else:
        await message.answer("يرجى تعيين أفتار متحرك أولاً عبر زر (✨ تعيين أفتار متحرك) يا أخي!")

@dp.message_handler(lambda message: message.text == "✨ تعيين أفتار متحرك")
async def set_avatar_prompt(message: types.Message):
    await message.answer("🎬 يرجى إرسال الصورة المتحركة (GIF) أو الفيديو القصير الذي تريد إرفاقه مع رسائل التنبيه:", parse_mode="Markdown")
    await UserStates.waiting_for_avatar.set()

@dp.message_handler(content_types=['animation', 'video', 'photo'], state=UserStates.waiting_for_avatar)
async def save_user_avatar(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    file_id = None
    
    if message.animation:
        file_id = message.animation.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
        
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar_file_id = ? WHERE user_id = ?", (file_id, user_id))
    conn.commit()
    conn.close()
    
    await message.answer("✅ تم حفظ الأفتار المتحرك بنجاح! جرب إرسال الأمر `/test_avatar` لرؤية النتيجة.", reply_markup=get_user_keyboard())
    await state.finish()

@dp.message_handler(lambda message: message.text == "📷 مراقبة حساب إنستغرام")
async def request_ig_monitor(message: types.Message):
    await message.answer("أرسل معرف (يوزر) حساب إنستغرام الذي تريد مراقبته:", parse_mode="Markdown")
    await UserStates.waiting_for_ig_username.set()

@dp.message_handler(state=UserStates.waiting_for_ig_username)
async def process_ig_monitor(message: types.Message, state: FSMContext):
    ig_user = message.text.strip().replace("@", "")
    user_id = message.from_user.id
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO instagram_monitors (owner_id, ig_username, start_time) VALUES (?, ?, ?)", (user_id, ig_user, current_time_str))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ تم بدء مراقبة الحساب `@{ig_user}` بنجاح!\nسيرسل لك البوت التنبيه مع الأفتار والمدة فور فك الحظر.", reply_markup=get_user_keyboard(), parse_mode="Markdown")
    await state.finish()

@dp.message_handler(lambda message: message.text == "👤 معلومات اشتراكي")
async def my_sub_info(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("أنت مطور البوت (اشتراك دائم ومفتوح ♾️).")
        return
        
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date, avatar_file_id FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        has_avatar = "مفعل ✅" if res[1] else "غير متوفر ❌"
        await message.answer(f"📅 تاريخ انتهاء اشتراكك: {res[0]}\n🎨 الأفتار المتحرك: {has_avatar}")
    else:
        await message.answer("ليس لديك اشتراك فعال مسجل.")

# --- لوحة التحكم: إضافة اشتراك ---
@dp.message_handler(lambda message: message.text == "➕ إضافة اشتراك" and message.from_user.id == ADMIN_ID)
async def add_single_start(message: types.Message):
    await message.answer("أرسل آيدي (ID) المستخدم مع عدد أيام الاشتراك (مثال: `123456789 30`):", parse_mode="Markdown")
    await AdminStates.waiting_for_add_id.set()

@dp.message_handler(state=AdminStates.waiting_for_add_id)
async def process_add_user(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        days = int(parts[1])
        
        expiry = datetime.now() + timedelta(days=days)
        expiry_str = expiry.strftime("%Y-%m-%d")
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO users (user_id, expiry_date) VALUES (?, ?)", (target_id, expiry_str))
        conn.commit()
        conn.close()
        
        await message.answer(f"تم تفعيل الاشتراك للمستخدم `{target_id}` حتى تاريخ {expiry_str} بنجاح ✅", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
    except Exception:
        await message.answer("خطأ في الصيغة! أرسل هكذا: `ID الأيام` (مثال: `123456789 30`)", parse_mode="Markdown")
    
    await state.finish()

# --- لوحة التحكم: حذف اشتراك (مضاف حديثاً ليعمل الزر) ---
@dp.message_handler(lambda message: message.text == "🗑️ حذف اشتراك" and message.from_user.id == ADMIN_ID)
async def delete_sub_start(message: types.Message):
    await message.answer("أرسل آيدي (ID) المستخدم الذي تريد حذف اشتراكه:", parse_mode="Markdown")
    await AdminStates.waiting_for_delete_id.set()

@dp.message_handler(state=AdminStates.waiting_for_delete_id)
async def process_delete_user(message: types.Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
            conn.commit()
            conn.close()
            await message.answer(f"✅ تم حذف اشتراك المستخدم `{target_id}` بنجاح وإزالته من قاعدة البيانات.", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        else:
            conn.close()
            await message.answer(f"❌ المستخدم `{target_id}` غير موجود في قائمة المشتركين أصلاً.", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
            
    except Exception:
        await message.answer("❌يرجى إرسال آيدي صحيح يتكون من أرقام فقط يا أخي.", reply_markup=get_admin_keyboard())
        
    await state.finish()

# --- لوحة التحكم: قائمة المشتركين ---
@dp.message_handler(lambda message: message.text == "📋 قائمة المشتركين" and message.from_user.id == ADMIN_ID)
async def list_users(message: types.Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expiry_date FROM users")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await message.answer("لا يوجد أي مستخدمين مسجلين حالياً.")
        return
    
    text = "📋 قائمة المشتركين:\n"
    for u in users:
        text += f"🆔 `{u[0]}` 📅 ينتهي في: {u[1]}\n"
    
    await message.answer(text, parse_mode="Markdown")

# --- لوحة التحكم: بحث عن مستخدم ---
@dp.message_handler(lambda message: message.text == "🔍 بحث عن مستخدم" and message.from_user.id == ADMIN_ID)
async def search_start(message: types.Message):
    await message.answer("أرسل آيدي (ID) المستخدم للبحث عن حالته:")
    await AdminStates.waiting_for_search_id.set()

@dp.message_handler(state=AdminStates.waiting_for_search_id)
async def process_search(message: types.Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT expiry_date FROM users WHERE user_id = ?", (target_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            await message.answer(f"المستخدم `{target_id}` موجود.\n📅 تاريخ انتهاء الاشتراك: {result[0]}", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        else:
            await message.answer(f"المستخدم `{target_id}` غير موجود في قاعدة البيانات أو ليس لديه اشتراك مسجل.", reply_markup=get_admin_keyboard())
    except Exception:
        await message.answer("يرجى إرسال آيدي صحيح يتكون من أرقام فقط.", reply_markup=get_admin_keyboard())
        
    await state.finish()

@dp.message_handler(lambda message: message.text == "⚙️ الإعدادات" and message.from_user.id == ADMIN_ID)
async def settings_menu(message: types.Message):
    await message.answer("⚙️ إعدادات البوت:\n- نظام الأفتار: مفعل ✅\n- حساب مدة الحظر (TAT): مفعل ✅")

async def check_instagram_status_loop():
    while True:
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, owner_id, ig_username, start_time FROM instagram_monitors")
            records = cursor.fetchall()
            
            async with aiohttp.ClientSession() as session:
                for row in records:
                    rec_id, owner_id, ig_username, start_time_str = row
                    url = f"https://www.instagram.com/{ig_username}/?__a=1&__d=dis"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    
                    try:
                        async with session.get(url, headers=headers, timeout=10) as resp:
                            if resp.status == 200:
                                start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                                now_dt = datetime.now()
                                diff = now_dt - start_dt
                                
                                hours = int(diff.total_seconds() // 3600)
                                minutes = int((diff.total_seconds() % 3600) // 60)
                                seconds = int(diff.total_seconds() % 60)
                                tat_str = f"{hours}ساعة و {minutes}دقيقة و {seconds}ثانية"
                                
                                time_str = now_dt.strftime('%d/%m/%Y %I:%M:%S %p')
                                
                                cursor.execute("SELECT avatar_file_id FROM users WHERE user_id = ?", (owner_id,))
                                user_res = cursor.fetchone()
                                avatar_id = user_res[0] if user_res else None
                                
                                caption_text = (
                                    f"🎉 تم فك الحظر عن الحساب: @{ig_username}\n"
                                    f"⏱️ مدة الحظر (TAT): {tat_str}\n"
                                    f"📅 وقت الفك: {time_str}\n"
                                    f"👤 بواسطة: @celvr"
                                )
                                
                                if avatar_id:
                                    await bot.send_animation(owner_id, animation=avatar_id, caption=caption_text)
                                else:
                                    await bot.send_message(owner_id, caption_text)
                                
                                cursor.execute("DELETE FROM instagram_monitors WHERE id = ?", (rec_id,))
                                conn.commit()
                    except:
                        pass
            conn.close()
        except Exception as e:
            print(f"Error in IG monitor loop: {e}")
            
        await asyncio.sleep(30)

async def on_startup(dp):
    asyncio.create_task(check_instagram_status_loop())

if __name__ == '__main__':
    print("Instagram Monitor Bot is running...")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
