import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo, MenuButtonDefault
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiogram import BaseMiddleware
from aiogram.types import BotCommand
from config import BOT_TOKEN, ADMINS, ADMIN_PASSWORD, WEBAPP_URL
from database import Database

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

class FastCallbackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            data_str = event.data or ""
            skip_pre_answer = any(data_str.startswith(prefix) for prefix in [
                "spin_wheel_action", "acc_", "rej_", "papp_approve_", "papp_reject_", 
                "delcomp_", "frzcomp_", "deladmin_", "delpromo_", "delcour_"
            ])
            if not skip_pre_answer:
                try:
                    await event.answer()
                except Exception:
                    pass
        return await handler(event, data)

dp.callback_query.outer_middleware(FastCallbackMiddleware())

db = Database()
BOT_USERNAME = "asakafood_bot"

LANGS = {
    "uz": {
        "start": "Assalomu alaykum", "menu": "🍔 Menyu", "back": "🔙 Asosiy menyu",
        "kafe": "🏢 Kafe + Bino", "masofaviy": "🛵 Buyurtma qilish", "kuryer": "📦 Kuryer bo'lish",
        "kabinet": "👤 Kabinetim", "aloqa": "☎️ Admin bilan aloqa", "xona": "🚪 Xona",
        "stollar": "🍽 Kafe", "cancel": "❌ Bekor qilish", "send_loc": "📍 Lokatsiyani yuborish",
        "skip": "⏩ O'tkazib yuborish", "send_phone": "📱 Raqamni yuborish",
        "main_menu": "Bosh menyuga qaytdingiz.", "choose_loc": "Joylashuvni tanlang:",
        "room_num": "Xona raqamini kiriting:", "table_num": "Stol raqamini kiriting:",
        "remote_order": "Buyurtma berish!\nPastdagi <b>🍔 Menyu</b> tugmasini bosib mahsulot tanlang:",
        "my_orders": "📦 Buyurtmalarim",
        "start_msg": "🍔 <b>Asaka Food Express</b>ga xush kelibsiz!\n<i>Asaka bo'ylab sevimli taomlar va tezkor yetkazib berish!</i> 🛵\n\n✨ <b>Siz uchun qulayliklar:</b>\n• 🍕 Saralangan kafelardan issiq taomlar\n• 💸 Har bir xariddan <b>3% keshbek</b> balansingizga\n• 🎁 Har kuni <b>bepul bonuslar va sovg'alar</b>\n\n👇 <b>Kerakli bo'limni tanlang:</b>",
        "comment_prompt": "Qo'shimcha izoh qoldiring (Yoki 'Yo'q' deb yozing):", "no": "Yo'q",
        "address_prompt": "Yetkazib berish uchun manzilingizni yozing (yoki lokatsiya yuboring):",
        "comment_prompt_short": "Qo'shimcha izoh qoldiring (Yoki 'Yo'q' deb yozing):",
        "cabinet_title": "👤 <b>Foydalanuvchi kabineti</b>", "name": "Ism",
        "total_orders": "Jami xaridlar soni", "total_spent": "Sarflangan summa",
        "no_orders": "Sizda hali buyurtmalar yo'q.", "last_orders": "📦 <b>Sizning oxirgi 5 ta buyurtmangiz:</b>",
        "order_num": "Buyurtma", "date": "Sana", "products": "Mahsulotlar", "total": "Jami",
        "status": "Holati", "order_accepted": "Buyurtmangiz yuborildi!", "your_purchase": "Xaridingiz",
        "admin_wait": "Adminlar tez orada ko'rib chiqishadi.", "change_lang": "⚙️ Tilni o'zgartirish",
        "delivery_type_remote": "🛍 <b>Yetkazib berish turi: Masofaviy</b>",
        "you_selected": "Siz quyidagi mahsulotlarni tanladingiz:", "order_preparing": "qabul qilindi, tayyorlanmoqda tez orada tayyor bo'ladi.",
        "cart_accepted": "🛍 <b>Savat qabul qilindi!</b>\n\nIltimos, buyurtmani rasmiylashtirish uchun yetkazib berish turini tanlang:",
        "cart_empty": "Savat bo'sh.", "checkout_error": "Buyurtmani qayta ishlashda xatolik yuz berdi.",
        "phone_prompt": "Iltimos, tasdiqlash uchun <b>📱 Raqamni yuborish</b> tugmasi orqali telefoningizni yuboring:",
        "confirmed": "Tasdiqlandi",
        "courier_pw_prompt": "Kuryer bo'lish uchun kompaniya tanlang va parolni kiriting:",
        "courier_pw_correct": "✅ Parol to'g'ri!\n\nIltimos, ism va familiyangizni kiriting:",
        "courier_pw_wrong": "❌ Noto'g'ri parol!", "courier_phone_prompt": "Telefon raqamingizni yuboring:",
        "courier_success": "✅ Siz kuryer sifatida ro'yxatdan o'tdingiz!\nSizning ID raqamingiz: <b>{id}</b>\nBuyurtmalar tushishini kuting.",
        "contact_admin_title": "📞 <b>Admin bilan bog'lanish:</b>\n\n",
        "contact_name": "👨‍💼 Ism:", "contact_phone": "📱 Telefon:", "contact_tg": "💬 Telegram:",
        "order_rejected": "❌ Uzr, sizning #{id} buyurtmangiz bekor qilindi.",
        "courier_assigned": "Sizning kuryeringiz", "arriving_soon": "Tez orada yetib boradi!",
        "choose_company": "🏪 O'zingiz xohlagan kafeni tanlang:",
        "daily_bonus": "🎁 Kunlik bonus", "referral": "🔗 Do'stlarni taklif qilish",
        "wheel": "🎡 Omadli Baraban", "promocode": "🎟 Promokod", "top_referrals": "🏆 Liderlar",
        "guide": "📖 Qo'llanma", "order_btn": "🛵 Buyurtma"
    },
    "ru": {
        "start": "Здравствуйте", "menu": "🍔 Меню", "back": "🔙 Главное меню",
        "kafe": "🏢 Кафе + Здание", "masofaviy": "🛵 Сделать заказ", "kuryer": "📦 Стать курьером",
        "kabinet": "👤 Мой кабинет", "aloqa": "☎️ Связь с админом", "xona": "🚪 Комната",
        "stollar": "🍽 Кафе", "cancel": "❌ Отмена", "send_loc": "📍 Отправить локацию",
        "skip": "⏩ Пропустить", "send_phone": "📱 Отправить номер",
        "main_menu": "Вы вернулись в главное меню.", "choose_loc": "Выберите место:",
        "room_num": "Введите номер комнаты:", "table_num": "Введите номер стола:",
        "remote_order": "Сделать заказ!\nВыберите продукты через кнопку <b>🍔 Меню</b>:",
        "my_orders": "📦 Мои заказы",
        "start_msg": "🍔 Добро пожаловать в <b>Asaka Food Express</b>!\n<i>Быстрая доставка вкусной еды по всему городу Асака!</i> 🛵\n\n✨ <b>Преимущества:</b>\n• 🍕 Горячая еда из лучших заведений города\n• 💸 <b>3% кэшбэк</b> с каждого заказа на баланс\n• 🎁 Ежедневные <b>бесплатные бонусы и призы</b>\n\n👇 <b>Выберите нужный раздел:</b>",
        "comment_prompt": "Оставьте комментарий (Или напишите 'Нет'):", "no": "Нет",
        "address_prompt": "Напишите адрес доставки (или отправьте локацию):",
        "comment_prompt_short": "Оставьте комментарий (Или напишите 'Нет'):",
        "cabinet_title": "👤 <b>Личный кабинет</b>", "name": "Имя",
        "total_orders": "Общее количество покупок", "total_spent": "Потраченная сумма",
        "no_orders": "У вас пока нет заказов.", "last_orders": "📦 <b>Ваши последние 5 заказов:</b>",
        "order_num": "Заказ", "date": "Дата", "products": "Продукты", "total": "Итого",
        "status": "Статус", "order_accepted": "Ваш заказ принят!", "your_purchase": "Ваша покупка",
        "admin_wait": "Админы скоро рассмотрят.", "change_lang": "⚙️ Изменить язык",
        "delivery_type_remote": "🛍 <b>Тип доставки: Удаленно</b>",
        "you_selected": "Вы выбрали следующие продукты:", "order_preparing": "принят и готовится!",
        "cart_accepted": "🛍 <b>Корзина принята!</b>\n\nВыберите тип доставки:",
        "cart_empty": "Корзина пуста.", "checkout_error": "Произошла ошибка при обработке заказа.",
        "phone_prompt": "Отправьте ваш телефон для подтверждения заказа:",
        "confirmed": "Подтверждено", "courier_pw_prompt": "Выберите компанию и введите пароль курьера:",
        "courier_pw_correct": "✅ Правильный пароль!\n\nВведите ваше имя:", "courier_pw_wrong": "❌ Неверный пароль!",
        "courier_phone_prompt": "Отправьте номер телефона:",
        "courier_success": "✅ Вы зарегистрированы как курьер!\nВаш ID: <b>{id}</b>\nОжидайте заказов.",
        "contact_admin_title": "📞 <b>Связь с админом:</b>\n\n",
        "contact_name": "👨‍💼 Имя:", "contact_phone": "📱 Телефон:", "contact_tg": "💬 Телеграм:",
        "order_rejected": "❌ Ваш заказ #{id} отменен.",
        "courier_assigned": "Ваш курьер", "arriving_soon": "Скоро прибудет!",
        "choose_company": "🏪 Выберите желаемое кафе:",
        "daily_bonus": "🎁 Ежедневный бонус", "referral": "🔗 Пригласить друзей",
        "wheel": "🎡 Колесо фортуны", "promocode": "🎟 Промокод", "top_referrals": "🏆 Лидеры",
        "guide": "📖 Инструкция", "order_btn": "🛵 Заказ"
    },
    "en": {
        "start": "Hello", "menu": "🍔 Menu", "back": "🔙 Main menu",
        "kafe": "🏢 Cafe + Building", "masofaviy": "🛵 Order Now", "kuryer": "📦 Become Courier",
        "kabinet": "👤 My Profile", "aloqa": "☎️ Contact Admin", "xona": "🚪 Room",
        "stollar": "🍽 Cafe", "cancel": "❌ Cancel", "send_loc": "📍 Send Location",
        "skip": "⏩ Skip", "send_phone": "📱 Send Number",
        "main_menu": "Returned to main menu.", "choose_loc": "Choose location:",
        "room_num": "Enter room number:", "table_num": "Enter table number:",
        "remote_order": "Remote delivery!\nChoose items via the <b>🍔 Menu</b> button:",
        "my_orders": "📦 My Orders",
        "start_msg": "🍔 Welcome to <b>Asaka Food Express</b>!\n<i>Fast and delicious food delivery across Asaka city!</i> 🛵\n\n✨ <b>Features:</b>\n• 🍕 Hot meals delivered straight to your door\n• 💸 <b>3% cashback</b> on every single order\n• 🎁 Daily <b>free bonuses & prizes</b> in Profile\n\n👇 <b>Please choose an option:</b>",
        "comment_prompt": "Leave a comment (Or write 'No'):", "no": "No",
        "address_prompt": "Write your delivery address (or send location):",
        "comment_prompt_short": "Leave a comment (Or write 'No'):",
        "cabinet_title": "👤 <b>User Profile</b>", "name": "Name",
        "total_orders": "Total orders", "total_spent": "Total spent",
        "no_orders": "You have no orders yet.", "last_orders": "📦 <b>Your last 5 orders:</b>",
        "order_num": "Order", "date": "Date", "products": "Products", "total": "Total",
        "status": "Status", "order_accepted": "Your order is accepted!", "your_purchase": "Your purchase",
        "admin_wait": "Admins will review shortly.", "change_lang": "⚙️ Change language",
        "delivery_type_remote": "🛍 <b>Delivery type: Remote</b>",
        "you_selected": "You selected the following items:", "order_preparing": "is accepted and being prepared!",
        "cart_accepted": "🛍 <b>Cart accepted!</b>\n\nPlease select the delivery type:",
        "cart_empty": "Cart is empty.", "checkout_error": "An error occurred while processing the order.",
        "phone_prompt": "Please send your phone number to confirm:",
        "confirmed": "Confirmed", "courier_pw_prompt": "Select company and enter courier password:",
        "courier_pw_correct": "✅ Password correct!\n\nPlease enter your name:", "courier_pw_wrong": "❌ Wrong password!",
        "courier_phone_prompt": "Send your phone number:",
        "courier_success": "✅ You are registered as a courier!\nYour ID: <b>{id}</b>\nWait for new orders.",
        "contact_admin_title": "📞 <b>Contact Admin:</b>\n\n",
        "contact_name": "👨‍💼 Name:", "contact_phone": "📱 Phone:", "contact_tg": "💬 Telegram:",
        "order_rejected": "❌ Your order #{id} has been canceled.",
        "courier_assigned": "Your courier", "arriving_soon": "Arriving soon!",
        "choose_company": "🏪 Choose your desired cafe:",
        "daily_bonus": "🎁 Daily Bonus", "referral": "🔗 Invite Friends",
        "wheel": "🎡 Lucky Wheel", "promocode": "🎟 Promo code", "top_referrals": "🏆 Leaders",
        "guide": "📖 Guide", "order_btn": "🛵 Order"
    }
}

def get_text(lang, key):
    return LANGS.get(lang, LANGS["uz"]).get(key, LANGS["uz"].get(key, ""))

async def is_admin(user_id):
    db_admins = await db.get_admins()
    return user_id in ADMINS or user_id in db_admins

# --- FSM States ---
class AdminLogin(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

class AdminContact(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_username = State()

class AdminManage(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_name = State()

class CompanyManage(StatesGroup):
    waiting_for_name = State()
    waiting_for_login = State()
    waiting_for_password = State()

class CategoryManage(StatesGroup):
    waiting_for_new_category = State()

class AddProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_category = State()
    waiting_for_desc = State()
    waiting_for_price = State()
    waiting_for_image = State()

class EditProduct(StatesGroup):
    waiting_for_desc = State()
    waiting_for_price = State()
    waiting_for_image = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()

class OrderFlow(StatesGroup):
    waiting_for_company = State()
    waiting_for_room = State()
    waiting_for_table = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_comment = State()
    waiting_for_type_after_checkout = State()
    waiting_for_room_after_checkout = State()
    waiting_for_table_after_checkout = State()

class AdminAddCourier(StatesGroup):
    waiting_for_company = State()
    waiting_for_tg_id = State()
    waiting_for_name = State()
    waiting_for_phone = State()

class AssignCourier(StatesGroup):
    waiting_for_courier_id = State()

class PromoFlow(StatesGroup):
    waiting_for_code = State()

class AdminPromo(StatesGroup):
    waiting_for_code = State()
    waiting_for_amount = State()
    waiting_for_limit = State()

class TransferFlow(StatesGroup):
    waiting_for_target = State()
    waiting_for_amount = State()

class SearchFoodFlow(StatesGroup):
    waiting_for_query = State()

class NearbySearchFlow(StatesGroup):
    waiting_for_location = State()

class AdminCompanyLocation(StatesGroup):
    waiting_for_location_or_address = State()
    waiting_for_address_text = State()

class PartnerApplyFlow(StatesGroup):
    waiting_for_store_name = State()
    waiting_for_category = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_comment = State()

async def _async_clear_reply_kb(chat_id: int):
    try:
        rm = await bot.send_message(chat_id, ".", reply_markup=ReplyKeyboardRemove())
        await rm.delete()
    except Exception:
        pass

def clear_reply_kb_bg(chat_id: int):
    asyncio.create_task(_async_clear_reply_kb(chat_id))

# --- Keyboards ---
def get_start_keyboard(lang='uz', user_id=0, is_admin_user=False):
    keyboard = [
        [
            InlineKeyboardButton(text=get_text(lang, "masofaviy"), callback_data="nav_order"),
            InlineKeyboardButton(text=get_text(lang, "kabinet"), callback_data="nav_cabinet")
        ],
        [
            InlineKeyboardButton(text=get_text(lang, "guide"), callback_data="nav_guide"),
            InlineKeyboardButton(text=get_text(lang, "aloqa"), callback_data="nav_contact")
        ]
    ]
    if is_admin_user:
        keyboard.append([InlineKeyboardButton(text="👑 Admin panel", callback_data="nav_admin")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_start_inline_keyboard(lang='uz', user_id=0, is_admin_user=False):
    return get_start_keyboard(lang, user_id, is_admin_user)

def get_kafe_bino_keyboard(lang='uz'):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ]
    )

def get_webapp_keyboard(lang='uz', user_id=0, company_id=None):
    url = f"{WEBAPP_URL}?lang={lang}&user_id={user_id}"
    if company_id:
        url += f"&company_id={company_id}"
    if url.startswith("http://"):
        url = url.replace("http://", "https://")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "menu"), web_app=WebAppInfo(url=url))],
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ]
    )

def get_admin_keyboard(is_superadmin=False):
    base = [
        [KeyboardButton(text="➕ MENU qo'shish"), KeyboardButton(text="📝 O'chirish / Tahrirlash")],
        [KeyboardButton(text="📢 Reklama tarqatish"), KeyboardButton(text="👥 Foydalanuvchilar")],
        [KeyboardButton(text="📍 Oshxona manzili & Lokatsiyasi"), KeyboardButton(text="🎟 Promokodlar")],
        [KeyboardButton(text="🚚 Kuryerlar ma'lumotlari"), KeyboardButton(text="⚙️ Aloqa sozlamalari")],
        [KeyboardButton(text="👨‍💻 Adminlar"), KeyboardButton(text="🏷 Kategoriyalar")],
        [KeyboardButton(text="📊 Analiz"), KeyboardButton(text="🔄 Balansni nolga tushirish")],
        [KeyboardButton(text="🔗 Do'kon havolasi va QR"), KeyboardButton(text="🔄 Saytni yangilash")],
        [KeyboardButton(text="🔙 Foydalanuvchi menyusi")]
    ]
    if is_superadmin:
        base.insert(0, [KeyboardButton(text="🏢 Kompaniyalar"), KeyboardButton(text="➕ Kompaniya qo'shish")])
        base.insert(1, [KeyboardButton(text="📋 Hamkorlik arizalari")])
    return ReplyKeyboardMarkup(keyboard=base, resize_keyboard=True)

def get_contact_keyboard(lang='uz'):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(lang, "send_phone"), request_contact=True)],
                  [KeyboardButton(text=get_text(lang, "cancel"))]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_location_keyboard(lang='uz'):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "send_loc"), request_location=True)],
            [KeyboardButton(text=get_text(lang, "skip"))],
            [KeyboardButton(text=get_text(lang, "cancel"))]
        ],
        resize_keyboard=True
    )

# =================== USER HANDLERS ===================
@dp.message(F.text.in_([LANGS["uz"]["change_lang"], LANGS["ru"]["change_lang"], LANGS["en"]["change_lang"]]))
async def cmd_change_lang(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="nav_main")]
    ])
    clear_reply_kb_bg(message.chat.id)
    await message.answer("Tilni tanlang / Выберите язык / Choose language:", reply_markup=keyboard)

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Referal va Do'kon parametrini tekshirish (/start ref_12345678 yoki /start shop_1)
    ref_id = None
    shop_id = None
    if message.text and len(message.text.split()) > 1:
        arg = message.text.split()[1].strip()
        if arg.startswith("shop_") and arg[5:].isdigit():
            shop_id = int(arg[5:])
        elif arg.startswith("ref_") and arg[4:].isdigit():
            ref_id = int(arg[4:])

    is_new = await db.add_user(message.from_user.id, message.from_user.full_name, username=message.from_user.username)
    
    # Agar yangi user referal orqali kirgan bo'lsa
    if is_new and ref_id and ref_id != message.from_user.id:
        success, bonus, referrer = await db.add_referral(ref_id, message.from_user.id, bonus=400)
        if success and referrer:
            try:
                await bot.send_message(
                    ref_id,
                    f"🎉 <b>Yangi do'stingiz botga qo'shildi!</b>\n\n"
                    f"👤 Do'stingiz: <b>{message.from_user.full_name}</b>\n"
                    f"💰 Hisobingizga <b>+400 so'm</b> qo'shildi!\n\n"
                    f"💳 Joriy balansingiz: <b>{referrer.get('balance', 0):,} so'm</b>\n"
                    f"👥 Jami taklif qilgan do'stlaringiz: <b>{referrer.get('referrals_count', 1)} ta</b>".replace(",", " ")
                )
            except Exception:
                pass
            try:
                await message.answer("🎁 <b>Xush kelibsiz!</b> Siz do'stingizning taklif havolasi orqali qo'shildingiz.")
            except Exception:
                pass

    # Admin /start bossa, to'g'ridan-to'g'ri admin paneliga o'tadi
    if await is_admin(message.from_user.id):
        session = await db.get_admin_session(message.from_user.id)
        if not session:
            await db.set_admin_session(message.from_user.id, "opetito321")
        is_super = await db.is_superadmin_session(message.from_user.id)
        await message.answer("👑 <b>Admin paneliga xush kelibsiz!</b>", reply_markup=get_admin_keyboard(is_superadmin=is_super))
        return

    # Pastdagi eski reply tugmalarni orqa fonda tez tozalash
    clear_reply_kb_bg(message.chat.id)

    user = await db.get_user(message.from_user.id)
    lang = user.get("lang") if user else None
    if not lang:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")]
        ])
        await message.answer("Tilni tanlang / Выберите язык / Choose language:", reply_markup=keyboard)
        return

    # Agar do'kon deep-linki orqali kirilgan bo'lsa (/start shop_1)
    if shop_id:
        company = await db.get_company(shop_id)
        if company and not company.get("is_frozen"):
            u_lang = lang or "uz"
            url = f"{WEBAPP_URL}?lang={u_lang}&user_id={message.from_user.id}&company_id={shop_id}"
            if url.startswith("http://"):
                url = url.replace("http://", "https://")
            
            cat_desc = f"\n🏷 <b>Toifa:</b> {company.get('category')}" if company.get('category') else ""
            addr_desc = f"\n📍 <b>Manzil:</b> {company.get('address')}" if company.get('address') else ""
            
            shop_text = (
                f"🏪 <b>{company['name']}</b> do'koniga xush kelibsiz!{cat_desc}{addr_desc}\n"
                f"🛵 <i>Yetkazib berish va qulay onlayn buyurtma!</i>\n\n"
                f"👇 <i>Mahsulotlarni ko'rish va xarid qilish uchun pastdagi tugmani bosing:</i>"
            )
            shop_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🍔 {company['name']} Menyusi", web_app=WebAppInfo(url=url))],
                [InlineKeyboardButton(text="🏪 Barcha do'konlarni ko'rish", callback_data="nav_order")],
                [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="nav_main")]
            ])
            await message.answer(shop_text, reply_markup=shop_kb)
            return

    is_adm = await is_admin(message.from_user.id)
    text = get_text(lang, "start") + f", <b>{message.from_user.full_name}</b>!\n\n" + get_text(lang, "start_msg")
    await message.answer(text, reply_markup=get_start_keyboard(lang, message.from_user.id, is_admin_user=is_adm))

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    lang = call.data.split("_")[1]
    await db.set_user_lang(call.from_user.id, lang)
    is_adm = await is_admin(call.from_user.id)
    text = get_text(lang, "start") + f", <b>{call.from_user.full_name}</b>!\n\n" + get_text(lang, "start_msg")
    await call.message.edit_text(text, reply_markup=get_start_keyboard(lang, call.from_user.id, is_admin_user=is_adm))

@dp.message(F.text.in_(["🇺🇿 O'zbek", "🇷🇺 Русский", "🇬🇧 English"]))
async def lang_selected(message: Message, state: FSMContext):
    lang_map = {"🇺🇿 O'zbek": "uz", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    lang = lang_map[message.text]
    await db.set_user_lang(message.from_user.id, lang)
    try:
        await bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonDefault())
    except Exception:
        pass
    clear_reply_kb_bg(message.chat.id)
    is_adm = await is_admin(message.from_user.id)
    await message.answer(get_text(lang, "start") + f", <b>{message.from_user.full_name}</b>!\n\n" + get_text(lang, "start_msg"), reply_markup=get_start_keyboard(lang, message.from_user.id, is_admin_user=is_adm))

@dp.message(F.text.in_([LANGS["uz"]["back"], LANGS["ru"]["back"], LANGS["en"]["back"], "🔙 Foydalanuvchi menyusi", "🔙 Asosiy menyu"]))
@dp.message(F.text.in_([LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"]]))
async def back_to_main(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    await state.clear()
    is_adm = await is_admin(message.from_user.id)
    clear_reply_kb_bg(message.chat.id)
    text = get_text(lang, "start") + f", <b>{message.from_user.full_name}</b>!\n\n" + get_text(lang, "start_msg")
    await message.answer(text, reply_markup=get_start_keyboard(lang, message.from_user.id, is_admin_user=is_adm))

@dp.callback_query(F.data == "nav_main")
async def nav_main_callback(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()
    except Exception:
        pass
    await state.clear()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    is_adm = await is_admin(call.from_user.id)
    text = get_text(lang, "start") + f", <b>{call.from_user.full_name}</b>!\n\n" + get_text(lang, "start_msg")
    try:
        await call.message.edit_text(text, reply_markup=get_start_keyboard(lang, call.from_user.id, is_admin_user=is_adm))
    except Exception:
        pass

async def get_order_menu_view(lang, user_id):
    companies = await db.get_companies()
    active_companies = [c for c in companies if not c.get('is_frozen')]
    
    keyboard = []
    main_url = f"{WEBAPP_URL}?lang={lang}&user_id={user_id}"
    if main_url.startswith("http://"):
        main_url = main_url.replace("http://", "https://")
    
    keyboard.append([
        InlineKeyboardButton(text="🍔 Umumiy Menyu (Mini App)", web_app=WebAppInfo(url=main_url))
    ])
    
    for c in active_companies:
        url = f"{WEBAPP_URL}?lang={lang}&user_id={user_id}&company_id={c['id']}"
        if url.startswith("http://"):
            url = url.replace("http://", "https://")
        cat_badge = f" • {c.get('category')}" if c.get('category') else ""
        keyboard.append([
            InlineKeyboardButton(text=f"🏪 {c['name']}{cat_badge} (Menyu)", web_app=WebAppInfo(url=url))
        ])
        
    keyboard.append([
        InlineKeyboardButton(text="🔍 Taom qidirish", callback_data="nav_search_food"),
        InlineKeyboardButton(text="📍 Yaqin oshxonalar", callback_data="nav_nearby_cafes")
    ])
    keyboard.append([InlineKeyboardButton(text="🏪 Hamkor bo'lish (Do'kon qo'shish)", callback_data="nav_partner_apply")])
    keyboard.append([InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")])
    
    if lang == "ru":
        text = (
            "🛵 <b>ASAKA FOOD — Заказ еды и товаров</b>\n\n"
            "📍 <i>Быстрая доставка вкусных блюд по городу Асака!</i>\n\n"
            "✨ <b>Возможности:</b>\n"
            "• 🍔 Откройте <b>Mini App</b> и соберите заказ;\n"
            "• ⚡️ Курьеры доставят горячие блюда за 30-45 минут;\n"
            "• 💸 <b>3% кэшбэк</b> с каждого заказа возвращается на баланс.\n\n"
            "👇 <i>Откройте меню или выберите нужное заведение:</i>"
        )
    elif lang == "en":
        text = (
            "🛵 <b>ASAKA FOOD — Food & Grocery Delivery</b>\n\n"
            "📍 <i>Fast delivery from best cafes and restaurants in Asaka!</i>\n\n"
            "✨ <b>Features:</b>\n"
            "• 🍔 Open <b>Mini App</b> to explore menu and checkout;\n"
            "• ⚡️ Fresh and hot delivery in 30-45 minutes;\n"
            "• 💸 <b>3% cashback</b> on every single purchase.\n\n"
            "👇 <i>Open menu or choose a restaurant:</i>"
        )
    else:
        text = (
            "🛵 <b>ASAKA FOOD — Taom va Mahsulotlar buyurtmasi</b>\n\n"
            "📍 <i>Asaka shahri bo'ylab eng sara oshxona va kafelardan yetkazish!</i>\n\n"
            "✨ <b>Qulay imkoniyatlar:</b>\n"
            "• 🍔 <b>Mini App</b> menyusini ochib, taomlarni tanlang;\n"
            "• ⚡️ Kuryerlarimiz taomlarni issiq holida tez yetkazadi;\n"
            "• 💸 Har bir xaridingizdan <b>3% keshbek</b> balansingizga qaytadi.\n\n"
            "👇 <i>Menyuni oching yoki o'zingizga qulay bo'limni tanlang:</i>"
        )
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(F.data == "nav_order")
async def nav_order_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    text, kb = await get_order_menu_view(lang, call.from_user.id)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass

@dp.message(StateFilter(None), F.text.in_([LANGS["uz"]["masofaviy"], LANGS["ru"]["masofaviy"], LANGS["en"]["masofaviy"]]))
async def choose_masofaviy_message(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    text, kb = await get_order_menu_view(lang, message.from_user.id)
    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_cabinet")
async def nav_cabinet_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    stats = await db.get_user_stats(call.from_user.id)
    balance = user.get("balance", 0) if user else 0
    ref_count = user.get("referrals_count", 0) if user else 0
    text = (
        f"{get_text(lang, 'cabinet_title')}\n\n"
        f"👤 <b>{get_text(lang, 'name')}:</b> {call.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{call.from_user.id}</code>\n\n"
        f"💳 <b>Hisobingiz (Balans):</b> {balance:,} so'm\n"
        f"👥 <b>Taklif qilgan do'stlaringiz:</b> {ref_count} ta\n\n"
        f"📦 <b>{get_text(lang, 'total_orders')}:</b> {stats['order_count']}\n"
        f"💸 <b>{get_text(lang, 'total_spent')}:</b> {stats['total_spent']:,} so'm\n\n"
        f"<i>💡 Balansingizdagi pullar buyurtma berishda avtomatik hisobdan chegiriladi!</i>"
    ).replace(",", " ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Oxirgi buyurtmani takrorlash", callback_data="nav_reorder_last")],
        [
            InlineKeyboardButton(text="📍 Yaqin oshxonalar", callback_data="nav_nearby_cafes"),
            InlineKeyboardButton(text="🔍 Taom qidirish", callback_data="nav_search_food")
        ],
        [
            InlineKeyboardButton(text=get_text(lang, "wheel"), callback_data="nav_wheel"),
            InlineKeyboardButton(text=get_text(lang, "daily_bonus"), callback_data="nav_daily_bonus")
        ],
        [
            InlineKeyboardButton(text=get_text(lang, "promocode"), callback_data="nav_promocode"),
            InlineKeyboardButton(text=get_text(lang, "referral"), callback_data="nav_referral")
        ],
        [
            InlineKeyboardButton(text="💸 Do'stga pul o'tkazish", callback_data="nav_transfer_balance"),
            InlineKeyboardButton(text="🏆 Liderlar reytingi", callback_data="nav_top_referrals")
        ],
        [
            InlineKeyboardButton(text=get_text(lang, "my_orders"), callback_data="nav_my_orders"),
            InlineKeyboardButton(text=get_text(lang, "aloqa"), callback_data="nav_contact")
        ],
        [InlineKeyboardButton(text="🏪 Hamkor bo'lish (Do'kon qo'shish)", callback_data="nav_partner_apply")],
        [InlineKeyboardButton(text=get_text(lang, "change_lang"), callback_data="nav_lang")],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_guide")
async def nav_guide_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    if lang == "ru":
        guide_text = (
            "📖 <b>Asaka Food — Краткая инструкция по боту</b>\n\n"
            "🛵 <b>Как сделать заказ:</b>\n"
            "• Нажмите кнопку <b>🛵 Заказ</b> и выберите заведение или магазин;\n"
            "• В удобном Mini App соберите корзину и оформите доставку.\n\n"
            "💸 <b>3% Кэшбэк с каждого заказа:</b>\n"
            "• С каждого выполненного заказа <b>3% суммы</b> возвращается на ваш баланс;\n"
            "• Накопленный кэшбэк можно использовать для оплаты следующих заказов!\n\n"
            "🎁 <b>Ежедневный бонус:</b>\n"
            "• В разделе <b>👤 Кабинет</b> получайте бесплатный денежный бонус каждые 24 часа.\n\n"
            "🎡 <b>Колесо Фортуны:</b>\n"
            "• Крутите колесо бесплатно 2 раза в день и выигрывайте до 10 000 сум!\n\n"
            "🔗 <b>Приглашение друзей (Рефералы):</b>\n"
            "• Отправьте свою ссылку другу — получите <b>+400 сум</b> на баланс за каждого!\n\n"
            "🎟 <b>Промокоды:</b>\n"
            "• Активируйте промокоды в кабинете и получайте мгновенные скидки.\n\n"
            "🏪 <b>Для владельцев заведений:</b>\n"
            "• Подключайте своё кафе или магазин к боту с <b>0% комиссией</b>!\n\n"
            "☎️ <b>Поддержка:</b> @sobirjonov_web"
        )
    elif lang == "en":
        guide_text = (
            "📖 <b>Asaka Food — Quick User Guide</b>\n\n"
            "🛵 <b>How to Order:</b>\n"
            "• Tap <b>🛵 Order</b> and pick your favorite cafe or store;\n"
            "• Select items in the Mini App and complete delivery checkout.\n\n"
            "💸 <b>3% Cashback on every order:</b>\n"
            "• <b>3% of each order</b> is credited back to your balance automatically;\n"
            "• Use your accumulated balance to pay for future orders!\n\n"
            "🎁 <b>Daily Bonus:</b>\n"
            "• Claim free bonus money every 24 hours in <b>👤 My Profile</b>.\n\n"
            "🎡 <b>Lucky Wheel:</b>\n"
            "• Spin 2 times every day for free to win up to 10,000 UZS!\n\n"
            "🔗 <b>Invite Friends (Referral):</b>\n"
            "• Share your personal link and get <b>+400 UZS</b> for each friend invited!\n\n"
            "🎟 <b>Promo Codes:</b>\n"
            "• Enter active promo codes in Profile to get instant discounts.\n\n"
            "🏪 <b>Partner With Us:</b>\n"
            "• Add your store/restaurant with 0% commission and boost your sales!\n\n"
            "☎️ <b>Support:</b> @sobirjonov_web"
        )
    else:
        guide_text = (
            "📖 <b>Asaka Food — Botdan foydalanish qo'llanmasi</b>\n\n"
            "🛵 <b>Buyurtma berish:</b>\n"
            "• <b>🛵 Buyurtma</b> tugmasini bosing va o'zingizga yoqqan oshxona yoki do'konni tanlang;\n"
            "• <b>Mini App</b> menyusidan taomlarni savatga qo'shing va manzilni kiritib buyurtma bering.\n\n"
            "💸 <b>3% Keshbek tizimi:</b>\n"
            "• Har bitta buyurtmangizdan <b>3% summa</b> to'g'ridan-to'g'ri balansingizga qaytadi;\n"
            "• Yig'ilgan keshbek mablag'larini keyingi buyurtmalarni to'lashda to'liq ishlatishingiz mumkin!\n\n"
            "🎁 <b>Kunlik bonus:</b>\n"
            "• <b>👤 Kabinetim</b> bo'limida har 24 soatda 1 marta bepul pul bonusini yig'ib oling.\n\n"
            "🎡 <b>Omadli Baraban:</b>\n"
            "• Har kuni <b>2 marta bepul</b> barabanni aylantiring va 10 000 so'mgacha pul yutug'ini oling!\n\n"
            "🔗 <b>Do'stlarni taklif qilish (Referal):</b>\n"
            "• Shaxsiy havolangiz orqali do'stlaringizni taklif qiling — har bir do'st uchun <b>+400 so'm</b> oling!\n\n"
            "🎟 <b>Promokodlar:</b>\n"
            "• Aksiya va bayram kodlarini kiritib, chegirmalardan foydalaning.\n\n"
            "🏪 <b>Do'kon va Kafe egalari uchun:</b>\n"
            "• O'z biznesingizni botga <b>0% komissiya</b> bilan ulab, daromadingizni oshiring!\n\n"
            "☎️ <b>Admin / Qo'llab-quvvatlash:</b> @sobirjonov_web"
        )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text(lang, "order_btn"), callback_data="nav_order"),
            InlineKeyboardButton(text=get_text(lang, "kabinet"), callback_data="nav_cabinet")
        ],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(guide_text, reply_markup=kb)

spinning_wheel_users = set()

@dp.callback_query(F.data == "nav_wheel")
async def nav_wheel_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    balance = user.get("balance", 0) if user else 0
    
    can_spin, remaining, wait_sec = await db.can_spin_wheel(call.from_user.id)
    
    text = (
        f"🎡 <b>OMADLI BARABAN O'YINI</b>\n\n"
        f"Har bir foydalanuvchi kuniga <b>2 marta</b> barabanni bepul aylantirishi mumkin! 🎯\n\n"
        f"🎁 <b>Barabandagi sovg'alar va bo'lakchalar:</b>\n"
        f"• 🥇 <b>10 000 so'm</b> (Super Sovg'a)\n"
        f"• 🥈 <b>3 000 so'm</b> (O'rtacha Sovg'a)\n"
        f"• 🥉 <b>1 000 so'm</b> (Kichik Sovg'a)\n"
        f"• 💣 <b>Bankrot</b> (0 so'm)\n\n"
        f"📊 <b>Bugungi qolgan imkoniyatingiz:</b> <b>{remaining} / 2 ta</b>\n"
        f"💳 <b>Hisobingiz (Balans):</b> <b>{balance:,} so'm</b>\n\n"
    ).replace(",", " ")
    
    if can_spin:
        text += "<i>👇 O'ynash uchun 'Barabanni aylantirish' tugmasini bosing:</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Barabanni aylantirish! 🎯", callback_data="spin_wheel_action")],
            [
                InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus"),
                InlineKeyboardButton(text="🔗 Taklif qilish", callback_data="nav_referral")
            ],
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ])
    else:
        hours = wait_sec // 3600
        minutes = (wait_sec % 3600) // 60
        text += (
            f"⏳ <b>Bugungi 2 ta imkoniyatdan to'liq foydalandingiz!</b>\n"
            f"Keyingi aylantirishgacha qolgan vaqt: <b>{hours} soat {minutes} daqiqa</b>.\n\n"
            f"<i>💡 Eslatma: Ertaga yana 2 ta bepul imkoniyat beriladi!\n"
            f"Hozir esa Kunlik bonus yoki Do'stlarni taklif qilish orqali balansingizni to'ldirishingiz mumkin.</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus"),
                InlineKeyboardButton(text="🔗 Do'stlarni taklif qilish", callback_data="nav_referral")
            ],
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "spin_wheel_action")
async def spin_wheel_action_callback(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in spinning_wheel_users:
        return await call.answer("⏳ Baraban aylanmoqda, kuting...", show_alert=True)
        
    can_spin, remaining, wait_sec = await db.can_spin_wheel(user_id)
    if not can_spin:
        hours = wait_sec // 3600
        minutes = (wait_sec % 3600) // 60
        return await call.answer(
            f"⏳ Bugungi 2 ta imkoniyat tugagan! Keyingi aylantirishgacha: {hours} soat {minutes} daqiqa.",
            show_alert=True
        )
        
    await call.answer()
    spinning_wheel_users.add(user_id)
    try:
        user = await db.get_user(user_id)
        lang = user.get("lang", "uz") if user else "uz"
        
        success, selected, rem_spins, new_bal, _ = await db.spin_wheel(user_id)
        if not success:
            await call.answer("Xatolik yuz berdi, qaytadan urinib ko'ring.", show_alert=True)
            return

        frame_1 = (
            "🎡 <b>Baraban aylanmoqda...</b> 🌀\n\n"
            "<code>[ 💣 Bankrot ]  ➡️  [ 🎁 1 000 so'm ]  ➡️  [ 🎁 3 000 so'm ]</code>\n\n"
            "<i>⏳ Omad siz tomondami? Kuting...</i>"
        )
        try:
            await call.message.edit_text(frame_1)
            await asyncio.sleep(0.6)
        except Exception:
            pass

        frame_2 = (
            "🎡 <b>Baraban aylanmoqda...</b> 🌪\n\n"
            "<code>[ 🎁 3 000 so'm ]  ➡️  [ 🌟 10 000 so'm ]  ➡️  [ 💣 Bankrot ]</code>\n\n"
            "<i>🌀 Aylanish tezlashmoqda...</i>"
        )
        try:
            await call.message.edit_text(frame_2)
            await asyncio.sleep(0.6)
        except Exception:
            pass

        frame_3 = (
            "🎡 <b>Sekinlashmoqda...</b> 🎯\n\n"
            f"<code>➡️ 🎯 [  {selected['name']}  ] 🎯 ⬅️</code>\n\n"
            "<i>To'xtamoqda...</i>"
        )
        try:
            await call.message.edit_text(frame_3)
            await asyncio.sleep(0.5)
        except Exception:
            pass

        if selected["type"] == "bankrot":
            result_text = (
                f"💣 <b>BANKROT!</b>\n\n"
                f"Afsuski, bu safar ko'rsatkich <b>Bankrot</b> bo'lakchasiga to'xtadi! 💥\n"
                f"Hisobingizga mablag' qo'shilmadi.\n\n"
                f"📊 <b>Bugungi qolgan imkoniyat:</b> <b>{rem_spins} / 2 ta</b>\n"
                f"💳 <b>Joriy balansingiz:</b> <b>{new_bal:,} so'm</b>\n\n"
                f"<i>Xafa bo'lmang, omadingizni yana sinab ko'ring! ✨</i>"
            ).replace(",", " ")
        else:
            result_text = (
                f"🎉 <b>TABRIKLAYMIZ! YUTUQ!</b> 🏆\n\n"
                f"Baraban ko'rsatkichi to'xtadi: <b>{selected['name']}</b>! 🎁\n"
                f"Balansingizga <b>+{selected['amount']:,} so'm</b> muvaffaqiyatli qo'shildi! 🥳\n\n"
                f"📊 <b>Bugungi qolgan imkoniyat:</b> <b>{rem_spins} / 2 ta</b>\n"
                f"💳 <b>Yangi balansingiz:</b> <b>{new_bal:,} so'm</b>\n\n"
                f"<i>💡 To'plangan barcha mablag'lar buyurtma berishda hisobingizdan avtomatik chegiriladi!</i>"
            ).replace(",", " ")

        if rem_spins > 0:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🎡 Yana aylantirish ({rem_spins} ta qoldi) 🎯", callback_data="spin_wheel_action")],
                [InlineKeyboardButton(text="👤 Kabinetim", callback_data="nav_cabinet")],
                [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Kabinetim", callback_data="nav_cabinet")],
                [
                    InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus"),
                    InlineKeyboardButton(text="🔗 Taklif qilish", callback_data="nav_referral")
                ],
                [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
            ])
            
        await call.message.edit_text(result_text, reply_markup=kb)
    finally:
        spinning_wheel_users.discard(user_id)

@dp.message(Command("baraban", "wheel"))
async def cmd_wheel(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    balance = user.get("balance", 0) if user else 0
    can_spin, remaining, wait_sec = await db.can_spin_wheel(message.from_user.id)
    
    text = (
        f"🎡 <b>OMADLI BARABAN O'YINI</b>\n\n"
        f"Har bir foydalanuvchi kuniga <b>2 marta</b> barabanni bepul aylantirishi mumkin! 🎯\n\n"
        f"🎁 <b>Barabandagi sovg'alar va bo'lakchalar:</b>\n"
        f"• 🥇 <b>10 000 so'm</b> (Super Sovg'a)\n"
        f"• 🥈 <b>3 000 so'm</b> (O'rtacha Sovg'a)\n"
        f"• 🥉 <b>1 000 so'm</b> (Kichik Sovg'a)\n"
        f"• 💣 <b>Bankrot</b> (0 so'm)\n\n"
        f"📊 <b>Bugungi qolgan imkoniyatingiz:</b> <b>{remaining} / 2 ta</b>\n"
        f"💳 <b>Hisobingiz (Balans):</b> <b>{balance:,} so'm</b>\n\n"
    ).replace(",", " ")
    
    if can_spin:
        text += "<i>👇 O'ynash uchun 'Barabanni aylantirish' tugmasini bosing:</i>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Barabanni aylantirish! 🎯", callback_data="spin_wheel_action")],
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ])
    else:
        hours = wait_sec // 3600
        minutes = (wait_sec % 3600) // 60
        text += (
            f"⏳ <b>Bugungi 2 ta imkoniyatdan to'liq foydalandingiz!</b>\n"
            f"Keyingi aylantirishgacha qolgan vaqt: <b>{hours} soat {minutes} daqiqa</b>."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
        ])
    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_daily_bonus")
async def nav_daily_bonus_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    can_claim, wait_sec = await db.can_claim_daily_bonus(call.from_user.id)
    if can_claim:
        success, bonus, new_bal = await db.claim_daily_bonus(call.from_user.id, min_amount=2, max_amount=10000)
        text = (
            f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            f"Siz bugungi kunlik bonus sifatida <b>+{bonus:,} so'm</b> yutib oldingiz! 🎁\n\n"
            f"💳 Sizning joriy balansingiz: <b>{new_bal:,} so'm</b>\n\n"
            f"<i>💡 Eslatma: Keyingi bonusni 24 soatdan so'ng olishingiz mumkin.\n"
            f"To'plangan mablag'ingiz bilan taomlarga to'liq yoki qisman buyurtma berishingiz mumkin!</i>"
        ).replace(",", " ")
    else:
        hours = wait_sec // 3600
        minutes = (wait_sec % 3600) // 60
        bal = user.get("balance", 0) if user else 0
        text = (
            f"⏳ <b>Kunlik bonus allaqachon olingan!</b>\n\n"
            f"Siz bugungi bonusni qabul qilgansiz.\n"
            f"Keyingi bonusga qolgan vaqt: <b>{hours} soat {minutes} daqiqa</b>.\n\n"
            f"💳 Joriy balansingiz: <b>{bal:,} so'm</b>\n\n"
            f"<i>💡 Ko'proq pul ishlash uchun 'Do'stlarni taklif qilish' bo'limidan foydalaning (har bir do'st uchun +400 so'm)!</i>"
        ).replace(",", " ")
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎡 Omadli Baraban", callback_data="nav_wheel"),
            InlineKeyboardButton(text="🔗 Do'stlarni taklif qilish", callback_data="nav_referral")
        ],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_referral")
async def nav_referral_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    balance = user.get("balance", 0) if user else 0
    referrals_count = user.get("referrals_count", 0) if user else 0
    ref_earned = referrals_count * 400
    
    global BOT_USERNAME
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{call.from_user.id}"
    import urllib.parse
    share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote('Asaka Food botida eng mazali taomlar markazi va kunlik bonuslar!')}"
    
    text = (
        f"🔗 <b>Do'stlarni taklif qilib, pul ishlang!</b>\n\n"
        f"Har bir taklif qilgan do'stingiz uchun hisobingizga <b>400 so'm</b> beriladi! 💸\n"
        f"Yig'ilgan pullarni botda istalgan taomga buyurtma berishda ishlatishingiz mumkin! 🍔🍕\n\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{referrals_count} ta</b>\n"
        f"💰 Takliflardan ishlangan: <b>{ref_earned:,} so'm</b>\n"
        f"💳 Jami balansingiz: <b>{balance:,} so'm</b>\n\n"
        f"👇 <b>Sizning shaxsiy referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>Ushbu havolani nusxalab, do'stlaringiz va guruhlarga yuboring!</i>"
    ).replace(",", " ")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)],
        [
            InlineKeyboardButton(text="🏆 Liderlar reytingi (TOP-10)", callback_data="nav_top_referrals"),
            InlineKeyboardButton(text="🎟 Promokod", callback_data="nav_promocode")
        ],
        [
            InlineKeyboardButton(text="🎡 Omadli Baraban", callback_data="nav_wheel"),
            InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus")
        ],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_top_referrals")
async def nav_top_referrals_callback(call: CallbackQuery):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    my_ref_count = user.get("referrals_count", 0) if user else 0
    my_earned = my_ref_count * 400
    
    top_users = await db.get_top_referrers(limit=10)
    
    text = (
        "🏆 <b>ENG FAOL TAKLIF QILUVCHILAR (TOP-10)</b>\n\n"
        "Do'stlarini taklif qilib, eng ko'p mukofot olgan yetakchilar:\n\n"
    )
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    if not top_users:
        text += "<i>Hozircha yetakchilar yo'q. Birinchi bo'lib do'stlaringizni taklif qiling va 1-o'ringa chiqing! 🚀</i>\n\n"
    else:
        for idx, u in enumerate(top_users):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}."
            raw_name = u.get("fullname") or "Foydalanuvchi"
            name = (raw_name[:15] + '..') if len(raw_name) > 17 else raw_name
            cnt = int(u.get("referrals_count", 0))
            earned = cnt * 400
            text += f"{medal} <b>{name}</b> — <b>{cnt} ta do'st</b> (+{earned:,} so'm)\n".replace(",", " ")
        text += "\n"
        
    text += (
        f"📊 <b>Sizning ko'rsatkichingiz:</b> <b>{my_ref_count} ta do'st</b> (+{my_earned:,} so'm)\n\n"
        f"🔥 <i>Har bir taklif uchun <b>+400 so'm</b> oling va reytingda yuqoriga ko'tariling!</i>"
    ).replace(",", " ")
    
    global BOT_USERNAME
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{call.from_user.id}"
    import urllib.parse
    share_url = f"https://t.me/share/url?url={ref_link}&text={urllib.parse.quote('Asaka Food botida eng mazali taomlar markazi va kunlik bonuslar!')}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Do'stlarni taklif qilish", url=share_url)],
        [InlineKeyboardButton(text="🔗 Referal havolam", callback_data="nav_referral")],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "nav_promocode")
async def nav_promocode_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    balance = user.get("balance", 0) if user else 0
    text = (
        f"🎟 <b>PROMOKOD KIRTISH</b>\n\n"
        f"Kanalimiz, guruhimiz yoki aksiyalardagi maxsus promokodingiz bormi? Uni kiriting va hisobingizga qo'shimcha mablag' oling! 💰\n\n"
        f"💳 <b>Joriy balansingiz:</b> {balance:,} so'm\n\n"
        f"<i>👇 Promokod matnini chatga yozib yuboring (Masalan: <code>ASAKA</code>):</i>"
    ).replace(",", " ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(PromoFlow.waiting_for_code)

@dp.message(PromoFlow.waiting_for_code, F.text)
async def process_promocode_input(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["back"], "/cancel", "🔙 Asosiy menyu", "❌ Bekor qilish"]:
        await state.clear()
        return await back_to_main(message, state)
    
    code = message.text.strip()
    success, msg, amount, new_bal = await db.use_promocode(message.from_user.id, code)
    await state.clear()
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    if success:
        text = (
            f"🎉 <b>MUVAFFAQIYATLI!</b>\n\n"
            f"{msg}\n\n"
            f"💳 Yangi balansingiz: <b>{new_bal:,} so'm</b>\n\n"
            f"<i>💡 To'plangan balansingiz bilan istalgan taomga buyurtma berishingiz mumkin!</i>"
        ).replace(",", " ")
    else:
        text = (
            f"{msg}\n\n"
            f"<i>Iltimos, promokod to'g'ri yozilganligini tekshiring yoki yangi aksiyalarni kuting!</i>"
        )
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎡 Omadli Baraban", callback_data="nav_wheel"),
            InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus")
        ],
        [
            InlineKeyboardButton(text="👤 Kabinetim", callback_data="nav_cabinet"),
            InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")
        ]
    ])
    await message.answer(text, reply_markup=kb)

@dp.message(Command("promokod", "promo"))
async def cmd_promocode(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    balance = user.get("balance", 0) if user else 0
    text = (
        f"🎟 <b>PROMOKOD KIRTISH</b>\n\n"
        f"Aksiya promokodingizni kiriting va balansingizga pul oling! 💰\n\n"
        f"💳 <b>Joriy balansingiz:</b> {balance:,} so'm\n\n"
        f"<i>👇 Promokod matnini yozib yuboring (Masalan: <code>ASAKA</code>):</i>"
    ).replace(",", " ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await message.answer(text, reply_markup=kb)
    await state.set_state(PromoFlow.waiting_for_code)

# =================== NEARBY CAFES (YAQIN OSHXONALAR) ===================
@dp.callback_query(F.data == "nav_nearby_cafes")
async def nav_nearby_cafes_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    text = (
        "📍 <b>YAQIN ATROFDAGI OSHXONA VA KAFELARNI TOPISH</b>\n\n"
        "Sizga eng yaqin masofadagi oshxonalarni ko'rish va yetib borish vaqtini aniqlash uchun turgan joyingiz (lokatsiya)ni yuboring! 🛵\n\n"
        "<i>👇 Pastdagi '📍 Lokatsiyani yuborish' tugmasini bosing:</i>"
    )
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    await call.message.answer(text, reply_markup=kb)
    await state.set_state(NearbySearchFlow.waiting_for_location)

@dp.message(NearbySearchFlow.waiting_for_location, F.location | F.text)
async def process_nearby_location_step(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["back"], "🔙 Asosiy menyu", "/cancel"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        is_adm = await is_admin(message.from_user.id)
        return await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_start_keyboard('uz', message.from_user.id, is_admin_user=is_adm))
        
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    if message.location:
        u_lat = message.location.latitude
        u_lon = message.location.longitude
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        
        nearby_list = await db.get_nearby_companies(u_lat, u_lon)
        if not nearby_list:
            is_adm = await is_admin(message.from_user.id)
            return await message.answer(
                "Hozircha faol kafelar mavjud emas.",
                reply_markup=get_start_keyboard(lang, message.from_user.id, is_admin_user=is_adm)
            )
            
        header = "📍 <b>SIZGA ENG YAQIN OSHXONA VA KAFELAR:</b>\n\n"
        keyboard = []
        for idx, c in enumerate(nearby_list[:6]):
            dist_km = c.get('distance_km')
            if dist_km is not None:
                if dist_km < 1.0:
                    dist_text = f"📍 {int(dist_km * 1000)} metr"
                    time_text = "~10-15 daqiqa"
                else:
                    dist_text = f"📍 {dist_km:.1f} km"
                    time_text = "~20-30 daqiqa"
            else:
                dist_text = "📍 Masofa hisoblanmoqda"
                time_text = "Yetkazib beriladi"
                
            addr = c.get("address", "Asaka shahar")
            phone = c.get("admin_contact", {}).get("phone") or "Mavjud"
            
            header += (
                f"{idx+1}️⃣ 🏪 <b>{c['name']}</b>\n"
                f"   {dist_text} ({time_text})\n"
                f"   📫 Manzil: <i>{addr}</i>\n"
                f"   📞 Telefon: {phone}\n\n"
            )
            
            row_btns = []
            if c.get('id'):
                row_btns.append(InlineKeyboardButton(text=f"🍔 {c['name']} menyusi", callback_data=f"selcomp_{c['id']}"))
            else:
                row_btns.append(InlineKeyboardButton(text=f"🍔 {c['name']} menyusi", callback_data="nav_order"))
            if c.get("latitude") and c.get("longitude"):
                map_url = f"https://www.google.com/maps?q={c['latitude']},{c['longitude']}"
                row_btns.append(InlineKeyboardButton(text="🗺 Xarita", url=map_url))
            keyboard.append(row_btns)
            
        keyboard.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="nav_main")])
        
        is_adm = await is_admin(message.from_user.id)
        await message.answer(header, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        companies = await db.get_companies()
        active = [c for c in companies if not c.get('is_frozen')]
        header = f"📍 <b>Manzil: '{message.text}'</b>\n\nQuyidagi kafelardan birini tanlab, buyurtma berishingiz mumkin:\n\n"
        keyboard = []
        for c in active[:6]:
            addr = c.get("address", "Asaka shahar")
            header += f"🏪 <b>{c['name']}</b> — <i>{addr}</i>\n"
            keyboard.append([InlineKeyboardButton(text=f"🍔 {c['name']} menyusi", callback_data=f"selcomp_{c['id']}")])
        keyboard.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="nav_main")])
        await message.answer(header, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# =================== 1-CLICK REORDER ===================
@dp.callback_query(F.data == "nav_reorder_last")
async def nav_reorder_last_callback(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    lang = user.get("lang", "uz") if user else "uz"
    
    last_order = await db.get_last_user_order(user_id)
    if not last_order:
        return await call.answer("⚠️ Sizda hali buyurtmalar tarixi yo'q! Avval menyudan taom tanlang.", show_alert=True)
        
    comp_id = last_order.get("company_id")
    company = await db.get_company(comp_id) if comp_id else None
    comp_name = company["name"] if company else "Umumiy Kafe"
    
    total = last_order.get("original_price") or last_order.get("total_price", 0)
    user_bal = await db.get_user_balance(user_id)
    
    loc_val = format_location(last_order.get('location', "Yo'q"))
    phone_val = last_order.get('phone', "Yo'q")
    text = (
        f"⚡ <b>OXIRGI BUYURTMANI 1 TA BOSISHDA TAKRORLASH</b>\n\n"
        f"🏪 <b>Kafe:</b> {comp_name}\n"
        f"📊 <b>Buyurtma turi:</b> {last_order.get('order_type', 'Masofaviy')}\n"
        f"📍 <b>Manzil:</b> {loc_val}\n"
        f"📱 <b>Telefon:</b> {phone_val}\n\n"
        f"🛍 <b>Mahsulotlar:</b>\n"
    )
    for item in last_order.get("items", []):
        text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
        
    text += f"\n💰 <b>Jami summa:</b> <b>{total:,} so'm</b>\n".replace(",", " ")
    if user_bal > 0:
        used_calc = min(user_bal, total)
        rem_calc = total - used_calc
        text += f"🎁 Balansingizdan chegiriladi: -{used_calc:,} so'm\n".replace(",", " ")
        text += f"💵 To'lanadigan naqd: {rem_calc:,} so'm\n".replace(",", " ")
    text += f"💸 Buyurtmadan keyin sizga <b>+{int(total * 0.03):,} so'm (3%) keshbek</b> qaytadi!\n\n".replace(",", " ")
    text += "<i>Buyurtmani darhol tasdiqlash uchun pastdagi tugmani bosing:</i>"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Ha, darhol buyurtma qilish! 🍔", callback_data=f"reorder_confirm_{last_order['id']}_{comp_id or 0}")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("reorder_confirm_"))
async def reorder_confirm_callback(call: CallbackQuery):
    await call.answer()
    parts = call.data.split("_")
    old_order_id = int(parts[2])
    comp_id = int(parts[3]) if len(parts) > 3 and parts[3] != "0" else None
    
    old_order = db.find_order(old_order_id, comp_id)
    if not old_order:
        return await call.answer("Buyurtma topilmadi!", show_alert=True)
        
    user_id = call.from_user.id
    items = old_order.get("items", [])
    total = old_order.get("original_price") or old_order.get("total_price", 0)
    order_type = old_order.get("order_type", "Masofaviy")
    room_table = old_order.get("room_table", "Yo'q")
    phone = old_order.get("phone", "Kiritilmagan")
    location = old_order.get("location", "Yo'q")
    comment = f"⚡ Tezkor takroriy buyurtma (#{old_order_id} dan)"
    
    user_bal = await db.get_user_balance(user_id)
    used_balance = 0
    payable_total = total
    if user_bal > 0:
        used_balance = min(user_bal, total)
        payable_total = total - used_balance
        await db.update_user_balance(user_id, -used_balance)
        
    cashback_amount = int(total * 0.03)
    if cashback_amount > 0:
        await db.update_user_balance(user_id, cashback_amount)
        
    new_order_id = await db.create_order(
        user_id, payable_total, location, phone, items,
        order_type, room_table, comment, company_id=comp_id,
        used_balance=used_balance, original_price=total
    )
    
    company = await db.get_company(comp_id) if comp_id else None
    comp_name = company["name"] if company else "Umumiy"
    
    # Notify Admin
    admin_text = f"🆕 <b>⚡ TEZKOR TAKRORIY BUYURTMA #{new_order_id}</b>\n"
    if company: admin_text += f"🏪 <b>Kompaniya:</b> {comp_name}\n"
    admin_text += f"\n📊 <b>Turi:</b> {order_type}\n📍 <b>Manzil:</b> {format_location(location)}\n"
    admin_text += f"👤 Ism: {call.from_user.full_name}\n📱 Tel: {phone}\n💬 Izoh: {comment}\n\n"
    admin_text += "🛍 <b>Mahsulotlar:</b>\n"
    for item in items:
        admin_text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']} so'm\n"
    admin_text += f"\n💰 <b>Mahsulotlar: {total:,} so'm</b>\n".replace(",", " ")
    if used_balance > 0:
        admin_text += f"🎁 <b>Mijoz balansidan to'landi:</b> -{used_balance:,} so'm\n".replace(",", " ")
        admin_text += f"💵 <b>Mijozdan olinadigan naqd summa: {payable_total:,} so'm</b>\n".replace(",", " ")
    if cashback_amount > 0:
        admin_text += f"💸 <b>Mijozga keshbek berildi:</b> +{cashback_amount:,} so'm (3%)\n".replace(",", " ")
        
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"acc_{new_order_id}_{comp_id or 0}"),
         InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"rej_{new_order_id}_{comp_id or 0}")]
    ])
    
    sent_ids = set()
    if comp_id:
        for acc in db.admin_accounts:
            if acc.get("company_id") == comp_id:
                for uid, login in db.admin_sessions.items():
                    if login == acc.get("login"):
                        try:
                            await bot.send_message(chat_id=int(uid), text=admin_text, reply_markup=markup)
                            sent_ids.add(int(uid))
                        except Exception: pass
    else:
        for admin_id in set(ADMINS + await db.get_admins()):
            if admin_id not in sent_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup)
                except Exception: pass
                
    # Confirm to customer
    new_user_bal = await db.get_user_balance(user_id)
    succ_text = (
        f"⚡ <b>BUYURTMA #{new_order_id} BIR ZUMDA QABUL QILINDI!</b>\n\n"
        f"🏪 Kafe: <b>{comp_name}</b>\n"
        f"💰 Jami: {total:,} so'm\n"
    ).replace(",", " ")
    if used_balance > 0:
        succ_text += f"🎁 Balansdan to'landi: -{used_balance:,} so'm\n".replace(",", " ")
        succ_text += f"💵 Naqd to'lov: {payable_total:,} so'm\n".replace(",", " ")
    succ_text += (
        f"💸 Keshbek: <b>+{cashback_amount:,} so'm (3%)</b> hisobingizga tushdi!\n"
        f"💳 Joriy balansingiz: <b>{new_user_bal:,} so'm</b>\n\n"
        f"<i>Oshxonamiz buyurtmani tayyorlashni boshladi! 🍕🚀</i>"
    ).replace(",", " ")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="nav_main")]
    ])
    await call.message.edit_text(succ_text, reply_markup=kb)

# =================== TRANSFER BALANCE ===================
@dp.callback_query(F.data == "nav_transfer_balance")
async def nav_transfer_balance_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    balance = user.get("balance", 0) if user else 0
    
    if balance < 1000:
        return await call.answer("⚠️ Pul o'tkazish uchun hisobingizda kamida 1 000 so'm bo'lishi kerak!", show_alert=True)
        
    text = (
        f"💸 <b>DO'STINGIZGA BALANS O'TKAZING (SOVG'A QILING)</b>\n\n"
        f"💳 Sizning balansingiz: <b>{balance:,} so'm</b>\n\n"
        f"<i>Do'stlaringizga o'z hisobingizdan pul o'tkazib bering, ular mazali taomlar buyurtma qilishsin! 🍔🎁</i>\n\n"
        f"👇 <b>Do'stingizning Telegram ID raqami, @username yoki telefon raqamini yozing:</b>"
    ).replace(",", " ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_cabinet")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(TransferFlow.waiting_for_target)

@dp.message(TransferFlow.waiting_for_target, F.text)
async def process_transfer_target_step(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["back"], "/cancel", "🔙 Asosiy menyu", "❌ Bekor qilish"]:
        await state.clear()
        return await back_to_main(message, state)
        
    target = message.text.strip()
    await state.update_data(transfer_target=target)
    
    user = await db.get_user(message.from_user.id)
    balance = user.get("balance", 0) if user else 0
    
    await message.answer(
        f"👤 Qabul qiluvchi: <b>{target}</b>\n"
        f"💳 Sizning balansingiz: <b>{balance:,} so'm</b>\n\n"
        f"Endi o'tkazmoqchi bo'lgan <b>summani (so'mda)</b> yozing (Masalan: <code>5000</code>):".replace(",", " ")
    )
    await state.set_state(TransferFlow.waiting_for_amount)

@dp.message(TransferFlow.waiting_for_amount, F.text)
async def process_transfer_amount_step(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["back"], "/cancel", "🔙 Asosiy menyu", "❌ Bekor qilish"]:
        await state.clear()
        return await back_to_main(message, state)
        
    try:
        amount = int(message.text.replace(" ", ""))
        if amount <= 0: raise ValueError
    except ValueError:
        return await message.answer("❌ Iltimos, musbat son kiriting (Masalan: 5000):")
        
    data = await state.get_data()
    target = data.get("transfer_target")
    
    success, msg, new_sender_bal, target_user = await db.transfer_balance(message.from_user.id, target, amount)
    await state.clear()
    
    if not success:
        return await message.answer(f"{msg}\n\nQaytadan urinib ko'rish uchun Kabinetga kiring.")
        
    target_name = target_user.get("fullname", "Do'stingiz")
    target_id = target_user.get("telegram_id")
    
    succ_text = (
        f"✅ <b>PUL MUVAFFAQIYATLI O'TKAZILDI!</b>\n\n"
        f"👤 Qabul qiluvchi: <b>{target_name}</b>\n"
        f"💸 O'tkazilgan summa: <b>{amount:,} so'm</b>\n"
        f"💳 Sizning qolgan balansingiz: <b>{new_sender_bal:,} so'm</b>\n\n"
        f"<i>Do'stingizga sovg'angiz yetkazildi! 🎉</i>"
    ).replace(",", " ")
    await message.answer(succ_text)
    
    try:
        recipient_text = (
            f"🎉 <b>SIZGA SOVG'A YUBORILDI!</b> 🎁\n\n"
            f"👤 <b>{message.from_user.full_name}</b> hisobingizga <b>+{amount:,} so'm</b> o'tkazdi!\n\n"
            f"💳 Sizning yangi balansingiz: <b>{target_user.get('balance', 0):,} so'm</b>\n\n"
            f"<i>💡 To'plangan pullar bilan botda istalgan taomga buyurtma berishingiz mumkin! 🍔🍕</i>"
        ).replace(",", " ")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛵 Taom buyurtma qilish", callback_data="nav_order")],
            [InlineKeyboardButton(text="👤 Kabinetim", callback_data="nav_cabinet")]
        ])
        await bot.send_message(target_id, recipient_text, reply_markup=kb)
    except Exception:
        pass

# =================== SMART FOOD SEARCH ===================
@dp.callback_query(F.data == "nav_search_food")
async def nav_search_food_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    text = (
        "🔍 <b>AQLI TAOM QIDIRUVI</b>\n\n"
        "Qaysi taomni qidiryapsiz? Nomini yozib yuboring (Masalan: <i>Lavash, Burger, Pizza, Shashlik, Kola, Somsa</i>):\n\n"
        "<i>Barcha kafelardagi narxlar va menyularni bir zumda topib beramiz! ⚡</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text(text, reply_markup=kb)
    await state.set_state(SearchFoodFlow.waiting_for_query)

@dp.message(SearchFoodFlow.waiting_for_query, F.text)
async def process_search_food_step(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["back"], "/cancel", "🔙 Asosiy menyu", "❌ Bekor qilish"]:
        await state.clear()
        return await back_to_main(message, state)
        
    query = message.text.strip()
    await state.clear()
    
    results = db.search_products(query)
    if not results:
        text = (
            f"🔍 <b>'{query}'</b> bo'yicha hech qanday taom topilmadi.\n\n"
            f"Boshqa so'z bilan qidirib ko'ring yoki umumiy menyuga kiring!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 To'liq menyuni ochish", callback_data="nav_order")],
            [InlineKeyboardButton(text="🔍 Qaytadan qidirish", callback_data="nav_search_food")],
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="nav_main")]
        ])
        return await message.answer(text, reply_markup=kb)
        
    text = f"🔍 <b>'{query}' bo'yicha topilgan taomlar:</b>\n\n"
    for p in results:
        text += (
            f"🍽 <b>{p['name']}</b> — <b>{p['price']:,} so'm</b>\n"
            f"🏪 Kafe: <b>{p.get('company_name', 'Umumiy')}</b>\n"
        ).replace(",", " ")
        if p.get("description"):
            text += f"📝 <i>{p['description']}</i>\n"
        text += "\n"
        
    keyboard = [
        [InlineKeyboardButton(text="🛵 Taomnomani ochish va buyurtma berish", callback_data="nav_order")],
        [InlineKeyboardButton(text="🔍 Boshqa taom qidirish", callback_data="nav_search_food")],
        [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="nav_main")]
    ]
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# =================== COURIER DELIVERED & RATING ===================
@dp.callback_query(F.data.startswith("cour_deliv_"))
async def courier_delivered_action(call: CallbackQuery):
    parts = call.data.split("_")
    order_id = int(parts[2])
    company_id = int(parts[3]) if len(parts) > 3 and parts[3] != "0" else None
    
    await db.update_order_status(order_id, "Yetkazildi", company_id=company_id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ <b>Buyurtma #{order_id} yetkazildi deb belgilandi!</b> Rahmat!")
    await call.answer("Yetkazildi deb belgilandi!")
    
    order = db.find_order(order_id, company_id)
    if order:
        try:
            order_user = await db.get_user(order["user_id"])
            lang = order_user.get("lang", "uz") if order_user else "uz"
            rate_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="⭐️ 1", callback_data=f"rate_{order_id}_1_{company_id or 0}"),
                    InlineKeyboardButton(text="⭐️ 2", callback_data=f"rate_{order_id}_2_{company_id or 0}"),
                    InlineKeyboardButton(text="⭐️ 3", callback_data=f"rate_{order_id}_3_{company_id or 0}"),
                    InlineKeyboardButton(text="⭐️ 4", callback_data=f"rate_{order_id}_4_{company_id or 0}"),
                    InlineKeyboardButton(text="⭐️ 5", callback_data=f"rate_{order_id}_5_{company_id or 0}")
                ]
            ])
            text = (
                f"🎉 <b>BUYURTMA #{order_id} YETKAZIB BERILDI!</b>\n\n"
                f"Yoqimli ishtaha tilaymiz! 😋\n\n"
                f"⭐️ <b>Xizmatimiz va taom sifatini baholang:</b>\n"
                f"<i>(Baholaganingiz uchun balansingizga <b>+500 so'm</b> bonus beriladi!)</i>"
            )
            await bot.send_message(order["user_id"], text, reply_markup=rate_kb)
        except Exception:
            pass

@dp.callback_query(F.data.startswith("rate_"))
async def customer_rate_action(call: CallbackQuery):
    parts = call.data.split("_")
    order_id = int(parts[1])
    stars = int(parts[2])
    company_id = int(parts[3]) if len(parts) > 3 and parts[3] != "0" else None
    
    success, msg, new_bal = await db.add_order_review(order_id, call.from_user.id, stars, company_id=company_id)
    await call.answer()
    if success:
        text = (
            f"⭐️ <b>Sizning bahoingiz: {stars} / 5 yulduz</b>\n\n"
            f"🎉 <b>KATTA RAHMAT!</b>\n"
            f"Fikringiz biz uchun juda muhim!\n"
            f"Balansingizga <b>+500 so'm</b> sharh bonusi qo'shildi! 🎁\n\n"
            f"💳 Joriy balansingiz: <b>{new_bal:,} so'm</b>"
        ).replace(",", " ")
    else:
        text = f"{msg}\n\nKeyingi buyurtmalaringizda ham sizga xizmat qilishdan xursandmiz! 😊"
    await call.message.edit_text(text)

@dp.callback_query(F.data == "nav_my_orders")
async def nav_my_orders_callback(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    orders = await db.get_user_orders(call.from_user.id, limit=5)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_cabinet")]
    ])
    if not orders:
        await call.message.edit_text(get_text(lang, "no_orders"), reply_markup=kb)
        await call.answer()
        return
    text = f"{get_text(lang, 'last_orders')}\n\n"
    for o in orders:
        text += f"🔖 <b>{get_text(lang, 'order_num')} #{o['id']}</b> ({o.get('order_type', 'Oddiy')})\n"
        text += f"📅 {get_text(lang, 'date')}: {o['created_at']}\n"
        text += f"🛍 <b>{get_text(lang, 'products')}:</b>\n"
        for item in o.get("items", []):
            text += f"  ▪️ {item['name']} x {item['quantity']}\n"
        text += f"💰 {get_text(lang, 'total')}: {o['total_price']:,} so'm\n".replace(",", " ")
        text += f"📊 {get_text(lang, 'status')}: <b>{o['status']}</b>\n\n"
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == "nav_contact")
async def nav_contact_callback(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    contact = await db.get_admin_contact()
    if not contact:
        contact = {"name": "Asaka Food Admin", "phone": "+998 90 123 45 67", "username": "@sobirjonov_web"}
    
    admin_tg = contact.get('username', '@sobirjonov_web')
    clean_tg = admin_tg.replace('@', '') if admin_tg else 'sobirjonov_web'
    phone = contact.get('phone', '+998 90 123 45 67')
    name = contact.get('name', 'Asaka Food Admin')
    
    if lang == "ru":
        text = (
            "☎️ <b>СЛУЖБА ПОДДЕРЖКИ И СВЯЗЬ С АДМИНИСТРАЦИЕЙ</b>\n\n"
            "Нужна помощь по заказу или есть вопросы и предложения? Мы всегда на связи!\n\n"
            f"👨‍💼 <b>Администратор:</b> {name}\n"
            f"📱 <b>Телефон:</b> {phone}\n"
            f"💬 <b>Telegram:</b> @{clean_tg}\n"
            "⏰ <b>Время работы:</b> 09:00 — 23:00 (Ежедневно)\n\n"
            "<i>👇 Нажмите кнопку ниже, чтобы написать администратору в Telegram:</i>"
        )
        btn_tg = "💬 Написать в Telegram"
        btn_partner = "🏪 Стать партнером (Добавить заведение)"
    elif lang == "en":
        text = (
            "☎️ <b>CUSTOMER SUPPORT & ADMIN CONTACT</b>\n\n"
            "Need help with your order or have a proposal? We are here to help!\n\n"
            f"👨‍💼 <b>Admin:</b> {name}\n"
            f"📱 <b>Phone:</b> {phone}\n"
            f"💬 <b>Telegram:</b> @{clean_tg}\n"
            "⏰ <b>Working Hours:</b> 09:00 — 23:00 (Daily)\n\n"
            "<i>👇 Tap the button below to message the admin directly on Telegram:</i>"
        )
        btn_tg = "💬 Message via Telegram"
        btn_partner = "🏪 Partner With Us (Add Shop)"
    else:
        text = (
            "☎️ <b>QO'LLAB-QUVVATLASH VA ALOQA MARKAZI</b>\n\n"
            "Savol, taklif yoki buyurtma bo'yicha yordam kerakmi? Biz sizga mamnuniyat bilan yordam beramiz!\n\n"
            f"👨‍💼 <b>Admin:</b> {name}\n"
            f"📱 <b>Telefon:</b> {phone}\n"
            f"💬 <b>Telegram:</b> @{clean_tg}\n"
            "⏰ <b>Ish vaqti:</b> 09:00 — 23:00 (Har kuni)\n\n"
            "<i>👇 Quyidagi tugma orqali to'g'ridan-to'g'ri Telegram orqali yozishingiz mumkin:</i>"
        )
        btn_tg = "💬 Telegram orqali yozish"
        btn_partner = "🏪 Hamkor bo'lish (Do'kon qo'shish)"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_tg, url=f"https://t.me/{clean_tg}")],
        [InlineKeyboardButton(text=btn_partner, callback_data="nav_partner_apply")],
        [InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")]
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass

@dp.callback_query(F.data == "nav_lang")
async def nav_lang_callback(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")],
        [InlineKeyboardButton(text=get_text("uz", "back"), callback_data="nav_main")]
    ])
    await call.message.edit_text("Tilni tanlang / Выберите язык / Choose language:", reply_markup=keyboard)
    await call.answer()

@dp.callback_query(F.data == "nav_courier")
async def nav_courier_callback(call: CallbackQuery):
    await call.answer("Kuryerlikka qabul faqat admin paneli orqali amalga oshiriladi.", show_alert=True)

@dp.callback_query(F.data == "nav_admin")
async def nav_admin_callback(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Siz admin emassiz!", show_alert=True)
        return
    is_super = await db.is_superadmin_session(call.from_user.id)
    try: await call.message.delete()
    except Exception: pass
    await call.message.answer("👑 <b>Admin paneliga xush kelibsiz!</b>", reply_markup=get_admin_keyboard(is_superadmin=is_super))
    await call.answer()

# --- ORDER FLOW: user selects Kafe/Bino ---
@dp.message(StateFilter(None), F.text.in_([LANGS["uz"]["kafe"], LANGS["ru"]["kafe"], LANGS["en"]["kafe"]]))
async def kafe_bino(message: Message, state: FSMContext):
    await choose_masofaviy_message(message, state)

@dp.callback_query(OrderFlow.waiting_for_company, F.data.startswith("selcomp_"))
async def user_company_selected(call: CallbackQuery, state: FSMContext):
    company_id = int(call.data.split("_")[1])
    company = await db.get_company(company_id)
    if not company:
        await call.answer("Kompaniya topilmadi!", show_alert=True)
        return
    data = await state.get_data()
    lang = data.get("lang", "uz")
    url = f"{WEBAPP_URL}?lang={lang}&user_id={call.from_user.id}&company_id={company_id}"
    if url.startswith("http://"):
        url = url.replace("http://", "https://")
    await call.message.edit_text(
        f"🏪 <b>{company['name']}</b> tanlandi!\n\nPastdagi tugma orqali taomnomani oching:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 " + get_text(lang, "menu"), web_app=WebAppInfo(url=url))],
            [InlineKeyboardButton(text="🔙 " + get_text(lang, "back"), callback_data="nav_main")]
        ])
    )
    await state.set_state(None)
    await call.answer()

@dp.message(StateFilter(None), F.text.in_([LANGS["uz"]["xona"], LANGS["ru"]["xona"], LANGS["en"]["xona"]]))
async def choose_xona(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    await state.update_data(order_type="Xona")
    await message.answer(get_text(lang, "room_num"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "back"))]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_room)

@dp.message(OrderFlow.waiting_for_room, F.text)
async def process_room(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text in [LANGS["uz"]["back"], LANGS["ru"]["back"], LANGS["en"]["back"]]:
        return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    data = await state.get_data()
    company_id = data.get("company_id")
    await message.answer(f"{get_text(lang, 'xona')}: {message.text}.\n\nBuyurtma uchun quyidagi tugmani bosing!", reply_markup=get_webapp_keyboard(lang, message.from_user.id, company_id))

@dp.message(StateFilter(None), F.text.in_([LANGS["uz"]["stollar"], LANGS["ru"]["stollar"], LANGS["en"]["stollar"]]))
async def choose_kafe(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    await state.update_data(order_type="Kafe")
    await message.answer(get_text(lang, "table_num"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "back"))]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_table)

@dp.message(OrderFlow.waiting_for_table, F.text)
async def process_table(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text in [LANGS["uz"]["back"], LANGS["ru"]["back"], LANGS["en"]["back"]]:
        return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    data = await state.get_data()
    company_id = data.get("company_id")
    await message.answer(f"{get_text(lang, 'stollar')}: {message.text}.\n\nBuyurtma uchun quyidagi tugmani bosing!", reply_markup=get_webapp_keyboard(lang, message.from_user.id, company_id))



# --- CABINET & ORDERS ---
@dp.message(F.text.in_([LANGS["uz"]["kabinet"], LANGS["ru"]["kabinet"], LANGS["en"]["kabinet"]]))
async def cmd_cabinet(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    stats = await db.get_user_stats(message.from_user.id)
    balance = user.get("balance", 0) if user else 0
    ref_count = user.get("referrals_count", 0) if user else 0
    text = (
        f"{get_text(lang, 'cabinet_title')}\n\n"
        f"👤 <b>{get_text(lang, 'name')}:</b> {message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"💳 <b>Hisobingiz (Balans):</b> {balance:,} so'm\n"
        f"👥 <b>Taklif qilgan do'stlaringiz:</b> {ref_count} ta\n\n"
        f"📦 <b>{get_text(lang, 'total_orders')}:</b> {stats['order_count']}\n"
        f"💸 <b>{get_text(lang, 'total_spent')}:</b> {stats['total_spent']:,} so'm\n\n"
        f"<i>💡 To'plangan balans bilan taomlarga buyurtma berishingiz mumkin!</i>"
    ).replace(",", " ")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Oxirgi buyurtmani takrorlash", callback_data="nav_reorder_last")],
        [
            InlineKeyboardButton(text="💸 Do'stga pul o'tkazish", callback_data="nav_transfer_balance"),
            InlineKeyboardButton(text="🎟 Promokod", callback_data="nav_promocode")
        ],
        [
            InlineKeyboardButton(text="🎡 Omadli Baraban", callback_data="nav_wheel"),
            InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="nav_daily_bonus")
        ],
        [
            InlineKeyboardButton(text="🏆 Liderlar reytingi", callback_data="nav_top_referrals"),
            InlineKeyboardButton(text="📦 " + get_text(lang, "my_orders"), callback_data="nav_my_orders")
        ],
        [InlineKeyboardButton(text="🔙 " + get_text(lang, "back"), callback_data="nav_main")]
    ])
    await message.answer(text, reply_markup=kb)

@dp.message(F.text.in_([LANGS["uz"]["my_orders"], LANGS["ru"]["my_orders"], LANGS["en"]["my_orders"]]))
async def cmd_my_orders(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    orders = await db.get_user_orders(message.from_user.id, limit=5)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 " + get_text(lang, "back"), callback_data="nav_main")]
    ])
    if not orders:
        return await message.answer(get_text(lang, "no_orders"), reply_markup=kb)
    text = f"{get_text(lang, 'last_orders')}\n\n"
    for o in orders:
        text += f"🔖 <b>{get_text(lang, 'order_num')} #{o['id']}</b> ({o.get('order_type', 'Oddiy')})\n"
        text += f"📅 {get_text(lang, 'date')}: {o['created_at']}\n"
        text += f"🛍 <b>{get_text(lang, 'products')}:</b>\n"
        for item in o.get("items", []):
            text += f"  ▪️ {item['name']} x {item['quantity']}\n"
        text += f"💰 {get_text(lang, 'total')}: {o['total_price']:,} so'm\n".replace(",", " ")
        text += f"📊 {get_text(lang, 'status')}: <b>{o['status']}</b>\n\n"
    await message.answer(text, reply_markup=kb)

@dp.message(F.text.in_([LANGS["uz"]["aloqa"], LANGS["ru"]["aloqa"], LANGS["en"]["aloqa"]]))
async def cmd_contact_admin(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    companies = await db.get_companies()
    active_companies = [c for c in companies if not c.get('is_frozen')]
    
    if not active_companies or len(active_companies) == 1:
        company_id = active_companies[0]['id'] if active_companies else None
        contact = await db.get_admin_contact(company_id=company_id)
        if not contact:
            contact = {"name": "Admin", "phone": "Kiritilmagan", "username": "@admin"}
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 " + get_text(lang, "back"), callback_data="nav_main")]])
        await message.answer(
            get_text(lang, "contact_admin_title") +
            f"{get_text(lang, 'contact_name')} {contact.get('name', 'Admin')}\n"
            f"{get_text(lang, 'contact_phone')} {contact.get('phone', 'Kiritilmagan')}\n"
            f"{get_text(lang, 'contact_tg')} {contact.get('username', '')}\n\n",
            reply_markup=kb
        )
        return

    keyboard = []
    for c in active_companies:
        keyboard.append([InlineKeyboardButton(text=f"🏪 {c['name']}", callback_data=f"contactcomp_{c['id']}")])
    keyboard.append([InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_main")])
    text = "Qaysi kafening admini bilan bog'lanmoqchisiz?" if lang=="uz" else ("Выберите кафе для связи с админом:" if lang=="ru" else "Choose a cafe to contact admin:")
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("contactcomp_"))
async def contactcomp_callback(call: CallbackQuery):
    company_id = int(call.data.split("_")[1])
    user = await db.get_user(call.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    contact = await db.get_admin_contact(company_id=company_id)
    if not contact:
        contact = {"name": "Admin", "phone": "Kiritilmagan", "username": "@admin"}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=get_text(lang, "back"), callback_data="nav_contact")]])
    await call.message.edit_text(
        get_text(lang, "contact_admin_title") +
        f"{get_text(lang, 'contact_name')} {contact.get('name', 'Admin')}\n"
        f"{get_text(lang, 'contact_phone')} {contact.get('phone', 'Kiritilmagan')}\n"
        f"{get_text(lang, 'contact_tg')} {contact.get('username', '')}\n\n",
        reply_markup=kb
    )
    await call.answer()

# =================== CHECKOUT FLOW ===================
def format_location(loc):
    if loc != "Yo'q" and loc != "Kiritilmagan" and "," in loc and not any(c.isalpha() for c in loc):
        return f"https://maps.google.com/?q={loc}"
    return loc

@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    order_type = data.get("order_type")
    company_id = data.get("company_id")
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"

    if message.web_app_data.data:
        try:
            web_data = json.loads(message.web_app_data.data)
            if web_data.get("action") == "checkout":
                items = web_data.get("items", [])
                if not items:
                    return await message.answer(get_text(lang, "cart_empty"))
                
                if not company_id:
                    company_id = web_data.get("company_id")
                    if company_id:
                        company_id = int(company_id)
                        
                db_products = await db.get_products(company_id=company_id)
                product_dict = {p["id"]: p["price"] for p in db_products}
                total = 0
                for item in items:
                    real_price = product_dict.get(int(item["id"]), item.get("price", 0))
                    if real_price is None:
                        real_price = 0
                    item["price"] = real_price
                    total += real_price * int(item["quantity"])
                    
                if not order_type:
                    order_type = "Masofaviy"
                text = f"🛍 <b>{get_text(lang, 'you_selected')}</b>\n\n"
                for item in items:
                    text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
                text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n\n".replace(",", " ")
                text += get_text(lang, "phone_prompt")
                await message.answer(text, reply_markup=get_contact_keyboard(lang))
                await state.set_state(OrderFlow.waiting_for_phone)
        except Exception as e:
            logging.error(f"WebApp Data Error: {e}")
            await message.answer(get_text(lang, "checkout_error"))

@dp.message(OrderFlow.waiting_for_type_after_checkout, F.text)
async def process_type_after_checkout(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    data = await state.get_data()
    items = data.get("items", [])
    total = data.get("total", 0)
    if message.text in [LANGS["uz"]["kafe"], LANGS["ru"]["kafe"], LANGS["en"]["kafe"]]:
        await message.answer(get_text(lang, "choose_loc"), reply_markup=get_kafe_bino_keyboard(lang))
    elif message.text in [LANGS["uz"]["xona"], LANGS["ru"]["xona"], LANGS["en"]["xona"]]:
        await state.update_data(order_type="Xona")
        await message.answer(get_text(lang, "room_num"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "back"))]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_room_after_checkout)
    elif message.text in [LANGS["uz"]["stollar"], LANGS["ru"]["stollar"], LANGS["en"]["stollar"]]:
        await state.update_data(order_type="Kafe")
        await message.answer(get_text(lang, "table_num"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "back"))]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_table_after_checkout)
    elif message.text in [LANGS["uz"]["masofaviy"], LANGS["ru"]["masofaviy"], LANGS["en"]["masofaviy"]]:
        await state.update_data(order_type="Masofaviy", room_table="Yo'q")
        text = f"{get_text(lang, 'delivery_type_remote')}\n{get_text(lang, 'you_selected')}\n\n"
        for item in items:
            text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
        text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n\n".replace(",", " ")
        text += get_text(lang, "phone_prompt")
        await message.answer(text, reply_markup=get_contact_keyboard(lang))
        await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_room_after_checkout, F.text)
async def process_room_after_checkout(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text in [LANGS["uz"]["back"], LANGS["ru"]["back"], LANGS["en"]["back"]]:
        return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    data = await state.get_data()
    items = data["items"]
    total = data["total"]
    text = f"🏢 <b>{get_text(lang, 'xona')}: {message.text}</b> {get_text(lang, 'confirmed')}!\n\n"
    for item in items:
        text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
    text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n\n".replace(",", " ")
    text += get_text(lang, "phone_prompt")
    await message.answer(text, reply_markup=get_contact_keyboard(lang))
    await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_table_after_checkout, F.text)
async def process_table_after_checkout(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text in [LANGS["uz"]["back"], LANGS["ru"]["back"], LANGS["en"]["back"]]:
        return await back_to_main(message, state)
    await state.update_data(room_table=message.text)
    data = await state.get_data()
    items = data["items"]
    total = data["total"]
    text = f"🍽 <b>{get_text(lang, 'stollar')}: {message.text}</b> {get_text(lang, 'confirmed')}!\n\n"
    for item in items:
        text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
    text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n\n".replace(",", " ")
    text += get_text(lang, "phone_prompt")
    await message.answer(text, reply_markup=get_contact_keyboard(lang))
    await state.set_state(OrderFlow.waiting_for_phone)

@dp.message(OrderFlow.waiting_for_phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text and message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"]]:
        return await back_to_main(message, state)
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    data = await state.get_data()
    if data.get("order_type") == "Masofaviy":
        await message.answer(get_text(lang, "address_prompt"), reply_markup=get_location_keyboard(lang))
        await state.set_state(OrderFlow.waiting_for_address)
    else:
        await message.answer(get_text(lang, "comment_prompt"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "no"))]], resize_keyboard=True))
        await state.set_state(OrderFlow.waiting_for_comment)

@dp.message(OrderFlow.waiting_for_address, F.location | F.text)
async def process_address(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    if message.text and message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"]]:
        return await back_to_main(message, state)
    location = "Kiritilmagan"
    if message.location:
        location = f"{message.location.latitude},{message.location.longitude}"
    elif message.text and message.text not in [LANGS["uz"]["skip"], LANGS["ru"]["skip"], LANGS["en"]["skip"]]:
        location = message.text
    await state.update_data(location=location)
    await message.answer(get_text(lang, "comment_prompt_short"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=get_text(lang, "no"))]], resize_keyboard=True))
    await state.set_state(OrderFlow.waiting_for_comment)

@dp.message(OrderFlow.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text
    data = await state.get_data()
    order_type = data.get("order_type", "Oddiy")
    room_table = data.get("room_table", "Yo'q")
    phone = data.get("phone")
    location = data.get("location", "Yo'q")
    items = data["items"]
    total = data["total"]
    company_id = data.get("company_id")
    
    # Balansdan to'lovni avtomatik tekshirish va chegirish
    user_id = message.from_user.id
    user_bal = await db.get_user_balance(user_id)
    used_balance = 0
    payable_total = total
    if user_bal > 0:
        used_balance = min(user_bal, total)
        payable_total = total - used_balance
        await db.update_user_balance(user_id, -used_balance)

    # 3% Avtomatik Keshbek (har bir buyurtmadan balansga qaytariladi)
    cashback_amount = int(total * 0.03)
    if cashback_amount > 0:
        await db.update_user_balance(user_id, cashback_amount)

    order_id = await db.create_order(
        user_id, payable_total, location, phone, items,
        order_type, room_table, comment, company_id=company_id,
        used_balance=used_balance, original_price=total
    )

    company = await db.get_company(company_id) if company_id else None
    comp_name = company["name"] if company else "Umumiy"

    admin_text = f"🆕 <b>YANGI BUYURTMA #{order_id}</b>\n"
    if company:
        admin_text += f"🏪 <b>Kompaniya:</b> {comp_name}\n"
    admin_text += f"\n📊 <b>Turi:</b> {order_type}\n"
    if order_type == "Xona":
        admin_text += f"🚪 <b>Xona:</b> {room_table}\n"
    elif order_type == "Kafe":
        admin_text += f"🍽 <b>Stol:</b> {room_table}\n"
    elif order_type == "Masofaviy":
        admin_text += f"📍 <b>Manzil:</b> {format_location(location)}\n"
    admin_text += f"👤 Ism: {message.from_user.full_name}\n"
    admin_text += f"📱 Tel: {phone}\n"
    admin_text += f"💬 Izoh: {comment}\n\n"
    admin_text += "🛍 <b>Mahsulotlar:</b>\n"
    for item in items:
        admin_text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']} so'm\n"
    admin_text += f"\n💰 <b>Mahsulotlar: {total:,} so'm</b>\n".replace(",", " ")
    if used_balance > 0:
        admin_text += f"🎁 <b>Mijoz balansidan to'landi:</b> -{used_balance:,} so'm\n".replace(",", " ")
        admin_text += f"💵 <b>Mijozdan olinadigan naqd summa: {payable_total:,} so'm</b>\n".replace(",", " ")
    if cashback_amount > 0:
        admin_text += f"💸 <b>Mijozga keshbek berildi:</b> +{cashback_amount:,} so'm (3%)\n".replace(",", " ")

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"acc_{order_id}_{company_id or 0}"),
         InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"rej_{order_id}_{company_id or 0}")]
    ])

    sent_ids = set()
    if company_id:
        for acc in db.admin_accounts:
            if acc.get("company_id") == company_id:
                for uid, login in db.admin_sessions.items():
                    if login == acc.get("login"):
                        try:
                            await bot.send_message(chat_id=int(uid), text=admin_text, reply_markup=markup)
                            sent_ids.add(int(uid))
                        except Exception:
                            pass
    else:                        
        all_admins = set(ADMINS + await db.get_admins())
        for admin_id in all_admins:
            if admin_id not in sent_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup)
                except Exception:
                    pass

    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    await state.clear()
    
    success_text = f"✅ <b>{get_text(lang, 'order_accepted')}</b>\n\n"
    success_text += f"🔖 <b>{get_text(lang, 'order_num')}:</b> #{order_id}\n"
    if company:
        success_text += f"🏪 <b>Kompaniya:</b> {comp_name}\n"
    success_text += f"🛍 <b>{get_text(lang, 'your_purchase')}:</b>\n"
    for item in items:
        success_text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
    
    if used_balance > 0:
        success_text += f"\n💰 <b>Mahsulotlar:</b> {total:,} so'm\n".replace(",", " ")
        success_text += f"🎁 <b>Balansingizdan to'landi:</b> -{used_balance:,} so'm\n".replace(",", " ")
        if payable_total == 0:
            success_text += f"🎉 <b>Buyurtma balansingiz hisobidan TO'LIQ TO'LANDI! (0 so'm)</b>\n"
        else:
            success_text += f"💵 <b>Yetkazilganda to'lanadigan summa:</b> {payable_total:,} so'm\n".replace(",", " ")
    else:
        success_text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n".replace(",", " ")
        
    if cashback_amount > 0:
        new_user_bal = await db.get_user_balance(user_id)
        success_text += f"💸 <b>Keshbek:</b> Ushbu buyurtmangizdan <b>+{cashback_amount:,} so'm (3%)</b> hisobingizga qaytdi!\n"
        success_text += f"💳 <b>Joriy balansingiz:</b> {new_user_bal:,} so'm\n\n".replace(",", " ")
        
    clear_reply_kb_bg(message.chat.id)
    is_adm = await is_admin(message.from_user.id)
    await message.answer(success_text, reply_markup=get_start_keyboard(lang, message.from_user.id, is_admin_user=is_adm))

# =================== ADMIN PANEL ===================
@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        is_super = await db.is_superadmin_session(message.from_user.id)
        await message.answer("Admin paneliga xush kelibsiz!", reply_markup=get_admin_keyboard(is_superadmin=is_super))
    else:
        await message.answer("Siz admin emassiz.\n\nLoginni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
        await state.set_state(AdminLogin.waiting_for_login)

@dp.message(AdminLogin.waiting_for_login)
async def admin_login_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu":
        return await back_to_main(message, state)
    await state.update_data(admin_login=message.text)
    await message.answer("Parolni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminLogin.waiting_for_password)

@dp.message(AdminLogin.waiting_for_password)
async def admin_password_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu":
        return await back_to_main(message, state)
    login = (await state.get_data()).get("admin_login")
    password = message.text
    accounts = await db.get_admin_accounts()
    valid = False
    name = ""
    is_super = False
    for acc in accounts:
        if acc["login"] == login and acc["password"] == password:
            valid = True
            name = acc["name"]
            is_super = acc.get("is_superadmin", False)
            break
    if valid or (login == "superadmin" and password == ADMIN_PASSWORD):
        session_name = name if valid else "Asosiy Admin"
        if not valid:
            is_super = True
        await db.set_admin_session(message.from_user.id, login if valid else "superadmin")
        await message.answer(f"✅ Muvaffaqiyatli kirdingiz, {session_name}!", reply_markup=get_admin_keyboard(is_superadmin=is_super))
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri login yoki parol.")
        await state.clear()

# --- COMPANY MANAGEMENT (superadmin only) ---
@dp.message(F.text == "🏢 Kompaniyalar")
async def admin_companies_list(message: Message):
    if not await is_admin(message.from_user.id):
        return
    is_super = await db.is_superadmin_session(message.from_user.id)
    if not is_super:
        await message.answer("Bu funksiya faqat superadmin uchun.")
        return
    companies = await db.get_companies()
    if not companies:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Kompaniya qo'shish", callback_data="add_company_start")]])
        await message.answer("Hozircha kompaniyalar yo'q.", reply_markup=keyboard)
        return
    text = "🏢 <b>Kompaniyalar ro'yxati:</b>\n\n"
    keyboard = []
    for c in companies:
        prod_count = len(c.get("products", []))
        cour_count = len(c.get("couriers", []))
        ord_count = len(c.get("orders", []))
        status = "❄️ Muzlatilgan" if c.get("is_frozen") else "✅ Faol"
        cat_str = f" • {c.get('category')}" if c.get('category') else ""
        text += f"🏪 <b>{c['name']}</b>{cat_str} (ID: {c['id']}) - {status}\n"
        text += f"   Mahsulotlar: {prod_count} | Kuryerlar: {cour_count} | Zakazlar: {ord_count}\n\n"
        btn_link = InlineKeyboardButton(text="🔗 Havola & QR", callback_data=f"linkcomp_{c['id']}")
        btn_frz = InlineKeyboardButton(text="♻️ Faollashtirish" if c.get("is_frozen") else "❄️ Muzlatish", callback_data=f"frzcomp_{c['id']}")
        btn_del = InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delcomp_{c['id']}")
        keyboard.append([btn_link])
        keyboard.append([btn_frz, btn_del])
    keyboard.insert(0, [InlineKeyboardButton(text="➕ Yangi kompaniya qo'shish", callback_data="add_company_start")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.message(F.text == "➕ Kompaniya qo'shish")
async def add_company_btn(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    is_super = await db.is_superadmin_session(message.from_user.id)
    if not is_super:
        await message.answer("Bu funksiya faqat superadmin uchun.")
        return
    await message.answer("Yangi kompaniya nomini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(CompanyManage.waiting_for_name)

@dp.callback_query(F.data == "add_company_start")
async def add_company_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        return
    await call.message.answer("Yangi kompaniya nomini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(CompanyManage.waiting_for_name)
    await call.answer()

@dp.message(CompanyManage.waiting_for_name)
async def company_add_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu":
        return await back_to_main(message, state)
    await state.update_data(company_name=message.text)
    await message.answer("Bu kompaniya admini uchun LOGIN kiriting:")
    await state.set_state(CompanyManage.waiting_for_login)

@dp.message(CompanyManage.waiting_for_login)
async def company_add_login(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu":
        return await back_to_main(message, state)
    accounts = await db.get_admin_accounts()
    if any(a["login"] == message.text for a in accounts):
        await message.answer("❌ Bu login allaqachon mavjud! Boshqa login kiriting:")
        return
    await state.update_data(company_login=message.text)
    await message.answer("Bu kompaniya admini uchun PAROL kiriting:")
    await state.set_state(CompanyManage.waiting_for_password)

@dp.message(CompanyManage.waiting_for_password)
async def company_add_password(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu":
        return await back_to_main(message, state)
    data = await state.get_data()
    company = await db.add_company(data["company_name"], data["company_login"], message.text)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
    await message.answer(
        f"✅ Kompaniya qo'shildi!\n\n"
        f"🏪 Nom: <b>{company['name']}</b>\n"
        f"🔑 Login: <b>{data['company_login']}</b>\n"
        f"🔒 Parol: <b>{message.text}</b>\n\n"
        f"🔗 Shaxsiy havola:\n<code>{deep_link}</code>\n\n"
        f"Bu login/parol bilan do'kon admini panelga kirishi mumkin.",
        reply_markup=get_admin_keyboard(is_superadmin=is_super)
    )

@dp.callback_query(F.data.startswith("delcomp_"))
async def delete_company(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    is_super = await db.is_superadmin_session(call.from_user.id)
    if not is_super:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    company_id = int(call.data.split("_")[1])
    company = await db.get_company(company_id)
    name = company["name"] if company else "?"
    await db.delete_company(company_id)
    await call.answer(f"{name} o'chirildi!")
    try: await call.message.delete()
    except: pass
    await admin_companies_list(call.message)

@dp.callback_query(F.data.startswith("frzcomp_"))
async def freeze_company(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    is_super = await db.is_superadmin_session(call.from_user.id)
    if not is_super:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    company_id = int(call.data.split("_")[1])
    await db.toggle_company_freeze(company_id)
    await call.answer("Holat o'zgartirildi!")
    try: await call.message.delete()
    except: pass
    await admin_companies_list(call.message)

# =================== DO'KON HAVOLASI & QR VA HAMKORLIK ===================

@dp.callback_query(F.data.startswith("linkcomp_"))
async def admin_link_company(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return await call.answer("Faqat admin uchun!")
    await call.answer()
    
    comp_id = int(call.data.split("_")[1])
    company = await db.get_company(comp_id)
    if not company:
        return await call.message.answer("Kompaniya topilmadi.")
    
    deep_link = f"https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
    
    caption = (
        f"🏪 <b>{company['name']}</b> do'koni uchun shaxsiy havola va QR-kod:\n\n"
        f"🔗 <b>Shaxsiy havola:</b>\n<code>{deep_link}</code>\n\n"
        f"📱 <b>Qanday ishlatiladi?</b>\n"
        f"1. Ushbu havolani Instagram, Telegram kanal yoki do'kon profiliga qo'ying.\n"
        f"2. QR-kodni chop etib (printerdan chiqarib), do'kon peshtaxtasi yoki eshigiga yopishtiring.\n"
        f"3. Xaridorlar telefonida skaner qilishi bilan to'g'ridan-to'g'ri faqat sizning tovarlaringiz ochiladi!"
    )
    try:
        await call.message.answer_photo(photo=qr_url, caption=caption)
    except Exception:
        await call.message.answer(caption)

@dp.message(F.text == "🔗 Do'kon havolasi va QR")
async def admin_store_link_menu(message: Message):
    if not await is_admin(message.from_user.id):
        return
    
    comp_id = await db.get_company_id_for_admin(message.from_user.id)
    if comp_id:
        company = await db.get_company(comp_id)
        if not company:
            return await message.answer("Do'koningiz ma'lumotlari topilmadi.")
        
        deep_link = f"https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
        caption = (
            f"🏪 <b>{company['name']}</b> do'koningiz havolasi va QR-kodi!\n\n"
            f"🔗 <b>Shaxsiy havola:</b>\n<code>{deep_link}</code>\n\n"
            f"💡 <i>Ushbu QR-kodni do'kon peshtaxtasiga yoki stolga qo'ysangiz, mijozlaringiz navbatsiz uydan yoki joyida tez buyurtma bera oladi.</i>"
        )
        try:
            await message.answer_photo(photo=qr_url, caption=caption)
        except Exception:
            await message.answer(caption)
    else:
        companies = await db.get_companies()
        if not companies:
            return await message.answer("Hozircha tizimda kompaniyalar mavjud emas.")
        kb = []
        for c in companies:
            kb.append([InlineKeyboardButton(text=f"🔗 {c['name']} (QR olish)", callback_data=f"linkcomp_{c['id']}")])
        await message.answer("Qaysi do'konning havola va QR-kodini olmoqchisiz? Tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.message(F.text == "📋 Hamkorlik arizalari")
async def admin_partner_requests_menu(message: Message):
    if not await is_admin(message.from_user.id):
        return
    is_super = await db.is_superadmin_session(message.from_user.id)
    if not is_super:
        return await message.answer("Bu bo'lim faqat superadmin uchun.")
    
    reqs = await db.get_partner_requests()
    if not reqs:
        return await message.answer("Hozircha birorta hamkorlik arizasi kelib tushmagan.")
    
    pending = [r for r in reqs if r.get('status') == 'pending']
    text = f"📋 <b>Hamkorlik arizalari ({len(pending)} ta kutilmoqda / Jami: {len(reqs)} ta):</b>\n\n"
    
    kb = []
    for r in reqs[-10:]:
        st_icon = "⏳" if r.get('status') == 'pending' else ("✅" if r.get('status') == 'approved' else "❌")
        text += f"{st_icon} <b>#{r['id']} {r['store_name']}</b> ({r.get('category')})\n"
        text += f"   👤 {r.get('fullname')} | 📱 {r.get('phone')}\n"
        text += f"   📍 {r.get('address')} | 🕒 {r.get('created_at')}\n"
        if r.get('status') == 'pending':
            kb.append([
                InlineKeyboardButton(text=f"✅ #{r['id']} Tasdiqlash", callback_data=f"papp_approve_{r['id']}"),
                InlineKeyboardButton(text=f"❌ #{r['id']} Rad etish", callback_data=f"papp_reject_{r['id']}")
            ])
        text += "\n"
    
    if kb:
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        await message.answer(text)

@dp.callback_query(F.data.startswith("papp_approve_"))
async def admin_approve_partner(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return await call.answer("Faqat admin uchun!", show_alert=True)
    
    req_id = int(call.data.split("_")[2])
    req, company = await db.approve_partner_request(req_id)
    if not req or not company:
        return await call.answer("Bu ariza allaqachon ko'rib chiqilgan yoki topilmadi.", show_alert=True)
    
    await call.answer("✅ Do'kon yaratildi!", show_alert=True)
    deep_link = f"https://t.me/{BOT_USERNAME}?start=shop_{company['id']}"
    
    edited_text = (
        f"✅ <b>HAMKORLIK ARIZASI TASDIQLANDI!</b>\n\n"
        f"🏪 Do'kon: <b>{company['name']}</b> (ID: {company['id']})\n"
        f"🏷 Toifa: <b>{company.get('category')}</b>\n"
        f"🔑 Admin logini: <code>{req['login']}</code>\n"
        f"🔒 Parol: <code>{req['password']}</code>\n"
        f"🔗 Shaxsiy havola: <code>{deep_link}</code>\n\n"
        f"<i>Do'kondorga login va parol avtomatik yuborildi!</i>"
    )
    await call.message.edit_text(edited_text)
    
    try:
        store_owner_text = (
            f"🎉 <b>TABRIKLAYMIZ! Arizangiz tasdiqlandi!</b>\n\n"
            f"Sizning <b>{company['name']}</b> do'koningiz Asaka Food platformasiga muvaffaqiyatli ulandi!\n\n"
            f"🔑 <b>Do'kon boshqaruv logini:</b> <code>{req['login']}</code>\n"
            f"🔒 <b>Paroli:</b> <code>{req['password']}</code>\n\n"
            f"🔗 <b>Sizning shaxsiy brend havolangiz:</b>\n"
            f"<code>{deep_link}</code>\n\n"
            f"💡 <i>Ushbu havolani Instagram yoki Telegram kanalingizga qo'ying. Xaridorlar bu havola orqali to'g'ridan-to'g'ri sizning menyungizga kirishadi!</i>\n\n"
            f"📲 <b>Do'koningizni boshqarish:</b>\n"
            f"Botga /admin buyrug'ini yuboring va yuqoridagi login/parol orqali kiring. U yerda yangi tovar qo'shishingiz, narxlarni o'zgartirishingiz va buyurtmalarni qabul qilishingiz mumkin."
        )
        await bot.send_message(chat_id=req["user_id"], text=store_owner_text)
    except Exception as e:
        logging.error(f"Error sending credentials to partner: {e}")

@dp.callback_query(F.data.startswith("papp_reject_"))
async def admin_reject_partner(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return await call.answer("Faqat admin uchun!", show_alert=True)
    
    req_id = int(call.data.split("_")[2])
    req = await db.reject_partner_request(req_id)
    if not req:
        return await call.answer("Ariza topilmadi.", show_alert=True)
    
    await call.answer("Rad etildi.")
    await call.message.edit_text(f"❌ <b>Ariza #{req_id} ({req.get('store_name')}) rad etildi.</b>")

# =================== PARTNER APPLICATION USER FLOW ===================

@dp.callback_query(F.data == "nav_partner_apply")
async def nav_partner_apply_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    
    pitch_text = (
        "🏪 <b>Asaka Food & Market platformasida o'z do'koningizni oching!</b>\n\n"
        "🚀 <b>Do'kon va Restoranlar uchun imkoniyatlar:</b>\n"
        "• <b>0% Komissiya:</b> Birinchi 1 oy mutlaqo bepul xizmat\n"
        "• <b>Yetkazib berish xizmati:</b> Buyurtmalarni kuryerlarimiz o'zlari yetkazadi\n"
        "• <b>Shaxsiy havola & QR-kod:</b> Har bir do'konga alohida havola va vitrina uchun QR beriladi\n"
        "• <b>Bepul reklama:</b> Botdagi barcha mijozlarga do'koningiz haqida xabar beriladi\n"
        "• <b>Smartfondan boshqarish:</b> Telegram orqali narx va tovarlarni oson yangilaysiz\n\n"
        "📝 <i>Hamkor bo'lish uchun qisqa anketani to'ldiring (1 daqiqa vaqt oladi).</i>\n\n"
        "👇 <b>1-qadam:</b> Do'koningiz yoki muassasangiz nomini kiriting:\n"
        "<i>(Masalan: 'Oazis Supermarket' yoki 'Burger House')</i>"
    )
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="nav_main")]
    ])
    await call.message.answer(pitch_text, reply_markup=cancel_kb)
    await state.set_state(PartnerApplyFlow.waiting_for_store_name)

@dp.message(PartnerApplyFlow.waiting_for_store_name)
async def partner_apply_store_name(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"], "❌ Bekor qilish"]:
        await state.clear()
        return await back_to_main(message, state)
    
    store_name = message.text.strip()
    if len(store_name) < 2:
        return await message.answer("Iltimos, do'kon nomini to'liqroq kiriting:")
    
    await state.update_data(store_name=store_name)
    
    cat_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Oziq-ovqat / Supermarket", callback_data="partcat_supermarket")],
        [InlineKeyboardButton(text="🍔 Fast-food & Kafe", callback_data="partcat_fastfood")],
        [InlineKeyboardButton(text="🍰 Shirinliklar / Nonvoyxona", callback_data="partcat_bakery")],
        [InlineKeyboardButton(text="🥩 Go'sht / Somsa / Oshxona", callback_data="partcat_meat")],
        [InlineKeyboardButton(text="💊 Dorixona", callback_data="partcat_pharmacy")],
        [InlineKeyboardButton(text="📦 Boshqa savdo do'koni", callback_data="partcat_other")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="nav_main")]
    ])
    await message.answer(
        f"✅ Do'kon nomi: <b>{store_name}</b>\n\n"
        f"🏷 <b>2-qadam:</b> Faoliyat turini tanlang:",
        reply_markup=cat_kb
    )
    await state.set_state(PartnerApplyFlow.waiting_for_category)

@dp.callback_query(PartnerApplyFlow.waiting_for_category, F.data.startswith("partcat_"))
async def partner_apply_category_cb(call: CallbackQuery, state: FSMContext):
    await call.answer()
    cat_map = {
        "partcat_supermarket": "🛒 Oziq-ovqat / Supermarket",
        "partcat_fastfood": "🍔 Fast-food & Kafe",
        "partcat_bakery": "🍰 Shirinliklar / Nonvoyxona",
        "partcat_meat": "🥩 Go'sht / Somsa / Oshxona",
        "partcat_pharmacy": "💊 Dorixona",
        "partcat_other": "📦 Savdo do'koni"
    }
    category = cat_map.get(call.data, "📦 Savdo do'koni")
    await state.update_data(category=category)
    
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await call.message.answer(
        f"✅ Toifa: <b>{category}</b>\n\n"
        f"📱 <b>3-qadam:</b> Bog'lanish uchun telefon raqamingizni yuboring:\n"
        f"<i>(Pastdagi <b>📱 Raqamni yuborish</b> tugmasini bosing yoki yozma ravishda yuboring)</i>",
        reply_markup=phone_kb
    )
    await state.set_state(PartnerApplyFlow.waiting_for_phone)

@dp.message(PartnerApplyFlow.waiting_for_phone)
async def partner_apply_phone(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"], "❌ Bekor qilish"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        return await back_to_main(message, state)
    
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        phone = message.text.strip()
    
    await state.update_data(phone=phone)
    
    loc_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)],
            [KeyboardButton(text="⏩ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"✅ Telefon: <b>{phone}</b>\n\n"
        f"📍 <b>4-qadam:</b> Do'koningiz manzilini yozing yoki lokatsiyani yuboring:\n"
        f"<i>(Masalan: 'Asaka shahar, Bobur shoh ko'chasi 15-uy')</i>",
        reply_markup=loc_kb
    )
    await state.set_state(PartnerApplyFlow.waiting_for_address)

@dp.message(PartnerApplyFlow.waiting_for_address)
async def partner_apply_address(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"], "❌ Bekor qilish"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        return await back_to_main(message, state)
    
    address = "Asaka shahar"
    if message.location:
        address = f"GPS: {message.location.latitude:.5f}, {message.location.longitude:.5f}"
    elif message.text and message.text != "⏩ O'tkazib yuborish":
        address = message.text.strip()
    
    await state.update_data(address=address)
    
    comment_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Yo'q")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"✅ Manzil: <b>{address}</b>\n\n"
        f"💬 <b>5-qadam:</b> Qo'shimcha izoh yoki taklifingiz bo'lsa yozing (yoki <b>'Yo'q'</b> tugmasini bosing):",
        reply_markup=comment_kb
    )
    await state.set_state(PartnerApplyFlow.waiting_for_comment)

@dp.message(PartnerApplyFlow.waiting_for_comment)
async def partner_apply_comment(message: Message, state: FSMContext):
    if message.text in [LANGS["uz"]["cancel"], LANGS["ru"]["cancel"], LANGS["en"]["cancel"], "❌ Bekor qilish"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        return await back_to_main(message, state)
    
    comment = message.text.strip() if message.text and message.text != "Yo'q" else "Yo'q"
    data = await state.get_data()
    await state.clear()
    clear_reply_kb_bg(message.chat.id)
    
    store_name = data.get("store_name", "Do'kon")
    category = data.get("category", "Savdo do'koni")
    phone = data.get("phone", "")
    address = data.get("address", "Asaka shahar")
    
    req = await db.add_partner_request(
        user_id=message.from_user.id,
        store_name=store_name,
        category=category,
        phone=phone,
        address=address,
        comment=comment,
        username=message.from_user.username,
        fullname=message.from_user.full_name
    )
    
    user = await db.get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    success_text = (
        "🎉 <b>Arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🏪 <b>Do'kon nomi:</b> {store_name}\n"
        f"🏷 <b>Toifa:</b> {category}\n"
        f"📱 <b>Bog'lanish uchun:</b> {phone}\n"
        f"📍 <b>Manzil:</b> {address}\n\n"
        "✨ <i>Bizning mutaxassisimiz tez orada siz bilan bog'lanadi va do'koningizni tizimga ulab beradi. Dastlabki 1 oy xizmat mutlaqo bepul!</i>\n\n"
        "Savollaringiz bo'lsa: @sobirjonov_web"
    )
    await message.answer(success_text, reply_markup=get_start_keyboard(lang, message.from_user.id))
    
    admin_alert = (
        f"📢 <b>YANGI HAMKORLIK ARIZASI! (Do'kon qo'shish)</b>\n\n"
        f"🆔 Ariza: <b>#{req['id']}</b>\n"
        f"🏪 Do'kon: <b>{store_name}</b>\n"
        f"🏷 Toifa: <b>{category}</b>\n"
        f"👤 Egasi: <b>{message.from_user.full_name}</b> (@{message.from_user.username or 'yo_q'})\n"
        f"📱 Telefon: <b>{phone}</b>\n"
        f"📍 Manzil: <b>{address}</b>\n"
        f"💬 Izoh: <i>{comment}</i>\n"
        f"🕒 Vaqt: <b>{req['created_at']}</b>\n\n"
        f"<i>Tasdiqlash tugmasini bossangiz, do'kon avtomatik yaratiladi va do'kondorga login/parol yuboriladi!</i>"
    )
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash va Do'kon ochish", callback_data=f"papp_approve_{req['id']}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"papp_reject_{req['id']}")
        ]
    ])
    
    all_superadmins = set(ADMINS + await db.get_admins())
    for aid in all_superadmins:
        try:
            await bot.send_message(chat_id=aid, text=admin_alert, reply_markup=adm_kb)
        except Exception:
            pass

# --- ORDER CALLBACKS ---
@dp.callback_query(F.data.startswith("acc_"))
async def accept_order(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    order_id = int(parts[1])
    company_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None
    await db.update_order_status(order_id, "Qabul qilindi va tayyorlanmoqda", company_id=company_id)
    order = db.find_order(order_id, company_id)
    inline_keyboard = []
    if order and order.get("order_type") == "Masofaviy":
        inline_keyboard.append([InlineKeyboardButton(text="🚚 Kuryerga berish", callback_data=f"sendcour_{order_id}_{company_id or 0}")])
    admin_name = await db.get_admin_session(call.from_user.id)
    await call.message.edit_text(call.message.text + f"\n\n✅ Qabul qildi: <b>{admin_name}</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard) if inline_keyboard else None)
    await call.answer("Buyurtma qabul qilindi.")
    if order:
        try:
            order_user = await db.get_user(order["user_id"])
            lang = order_user.get("lang", "uz") if order_user else "uz"
            await bot.send_message(chat_id=order["user_id"], text=f"🎉 <b>{get_text(lang, 'order_num')} #{order_id}</b> {get_text(lang, 'order_preparing')}")
        except Exception:
            pass

@dp.callback_query(F.data.startswith("rej_"))
async def reject_order(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    order_id = int(parts[1])
    company_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None
    admin_name = await db.get_admin_session(call.from_user.id)
    await db.update_order_status(order_id, "Bekor qilingan", company_id=company_id)
    await call.answer("Buyurtma bekor qilindi.")
    await call.message.edit_text(call.message.text + f"\n\n❌ Bekor qildi: <b>{admin_name}</b>")
    order = db.find_order(order_id, company_id)
    if order:
        try:
            order_user = await db.get_user(order["user_id"])
            lang = order_user.get("lang", "uz") if order_user else "uz"
            await bot.send_message(chat_id=order["user_id"], text=get_text(lang, "order_rejected").format(id=order_id))
        except Exception:
            pass

@dp.callback_query(F.data.startswith("sendcour_"))
async def prompt_courier_id(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    order_id = int(parts[1])
    company_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None
    await state.update_data(assign_order_id=order_id, assign_company_id=company_id)
    await state.set_state(AssignCourier.waiting_for_courier_id)
    
    couriers = await db.get_couriers(company_id=company_id)
    if not couriers:
        await call.message.answer("⚠️ Hozircha kuryerlar mavjud emas. Avval 'Kuryerlar ma'lumotlari' bo'limidan kuryer qo'shing!")
        await state.clear()
        return

    kb = []
    for c in couriers:
        kb.append([InlineKeyboardButton(text=f"🛵 #{c['id']} {c['fullname']} ({c['phone']})", callback_data=f"selassign_{c['id']}_{order_id}_{company_id or 0}")])
    kb.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_dismiss")])
    await call.message.answer(f"Buyurtma #{order_id} qaysi kuryerga biriktiriladi?\nTanlang yoki ID raqamini yozing:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

async def execute_assign_courier(target_msg: Message, courier_id: int, order_id: int, company_id=None):
    couriers = await db.get_couriers(company_id=company_id)
    courier = next((c for c in couriers if c["id"] == courier_id), None)
    if not courier:
        return await target_msg.answer("⚠️ Bunday ID li kuryer topilmadi!")
    order = db.find_order(order_id, company_id)
    if order:
        c_text = f"📦 <b>YANGI MASOFAVIY BUYURTMA #{order_id}</b>\n\n"
        c_text += f"📍 Manzil: {format_location(order['location'])}\n"
        c_text += f"📱 Mijoz tel: {order['phone']}\n"
        ord_comment = order.get('comment', "Yo'q")
        c_text += f"💬 Izoh: {ord_comment}\n\n"
        c_text += "🛍 <b>Mahsulotlar:</b>\n"
        for item in order["items"]:
            c_text += f"▪️ {item['name']} x {item['quantity']}\n"
        if order.get("used_balance"):
            c_text += f"\n💰 Olinadigan summa: {order['total_price']:,} so'm ({order['used_balance']:,} so'm balansdan to'langan)".replace(",", " ")
        else:
            c_text += f"\n💰 Olinadigan summa: {order['total_price']:,} so'm".replace(",", " ")
        cour_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏁 Buyurtma yetkazildi ✅", callback_data=f"cour_deliv_{order_id}_{company_id or 0}")]
        ])
        try:
            await bot.send_message(courier["telegram_id"], c_text, reply_markup=cour_kb)
            await target_msg.answer(f"✅ Buyurtma #{order_id} tayyor bo'ldi va kuryer #{courier_id} ({courier['fullname']}) ga topshirildi!")
            order_user = await db.get_user(order["user_id"])
            lang = order_user.get("lang", "uz") if order_user else "uz"
            cust_text = f"✅ <b>Buyurtmangiz tayyor bo'ldi va kuryerga topshirildi!</b>\n\n"
            cust_text += f"🛵 <b>{get_text(lang, 'courier_assigned')}:</b>\n"
            cust_text += f"👤 {get_text(lang, 'name')}: {courier['fullname']}\n"
            cust_text += f"📱 {get_text(lang, 'contact_phone')} {courier['phone']}\n\n{get_text(lang, 'arriving_soon')}"
            await bot.send_message(order["user_id"], cust_text)
        except Exception as e:
            await target_msg.answer(f"Xabar yuborishda xatolik: {e}")

@dp.callback_query(F.data.startswith("selassign_"))
async def callback_assign_courier(call: CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.split("_")
    courier_id = int(parts[1])
    order_id = int(parts[2])
    company_id = int(parts[3]) if len(parts) > 3 and parts[3] != "0" else None
    await execute_assign_courier(call.message, courier_id, order_id, company_id)
    await state.clear()

@dp.message(AssignCourier.waiting_for_courier_id)
async def assign_courier(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting!")
    courier_id = int(message.text)
    data = await state.get_data()
    order_id = data["assign_order_id"]
    company_id = data.get("assign_company_id")
    await execute_assign_courier(message, courier_id, order_id, company_id)
    await state.clear()

# =================== COURIERS (ADMIN PANEL) ===================
async def render_admin_couriers(user_id: int, target_message: Message, edit: bool = False):
    if not await is_admin(user_id): return
    company_id = await db.get_company_id_for_admin(user_id)
    is_super = await db.is_superadmin_session(user_id)
    
    keyboard = [
        [InlineKeyboardButton(text="➕ Yangi kuryer qo'shish", callback_data="admin_add_courier_start")]
    ]
    if is_super:
        companies = await db.get_companies()
        text = "🚚 <b>Barcha kuryerlar ro'yxati:</b>\n\n"
        has_any = False
        for c in companies:
            couriers = c.get("couriers", [])
            if couriers:
                has_any = True
                text += f"🏪 <b>{c['name']}</b>:\n"
                for cur in couriers:
                    text += f"  🆔 #{cur['id']} | TG: <code>{cur.get('telegram_id')}</code> | {cur['fullname']} | {cur['phone']}\n"
                    keyboard.append([InlineKeyboardButton(text=f"❌ #{cur['id']} {cur['fullname']} ({c['name']}) ni o'chirish", callback_data=f"delcour_{cur['id']}_{c['id']}")])
                text += "\n"
        global_couriers = getattr(db, 'couriers', [])
        if global_couriers:
            has_any = True
            text += "🌐 <b>Umumiy kuryerlar:</b>\n"
            for cur in global_couriers:
                text += f"  🆔 #{cur['id']} | TG: <code>{cur.get('telegram_id')}</code> | {cur['fullname']} | {cur['phone']}\n"
                keyboard.append([InlineKeyboardButton(text=f"❌ #{cur['id']} {cur['fullname']} ni o'chirish", callback_data=f"delcour_{cur['id']}_0")])
        if not has_any:
            text = "🚚 <b>Kuryerlar ma'lumotlari:</b>\n\nHozircha kuryerlar mavjud emas.\nKuryer qo'shish uchun quyidagi tugmani bosing 👇"
    else:
        couriers = await db.get_couriers(company_id=company_id)
        if not couriers:
            text = "🚚 <b>Kuryerlar ma'lumotlari:</b>\n\nHozircha kuryerlar mavjud emas.\nKuryer qo'shish uchun quyidagi tugmani bosing 👇"
        else:
            text = f"🚚 <b>Kuryerlar ({len(couriers)} ta):</b>\n\n"
            for c in couriers:
                text += f"🆔 #{c['id']} | TG: <code>{c.get('telegram_id')}</code> | {c['fullname']} | {c['phone']}\n"
                keyboard.append([InlineKeyboardButton(text=f"❌ #{c['id']} {c['fullname']} ni o'chirish", callback_data=f"delcour_{c['id']}_{company_id or 0}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    if edit:
        try:
            await target_message.edit_text(text, reply_markup=markup)
            return
        except Exception:
            pass
    await target_message.answer(text, reply_markup=markup)

@dp.message(F.text == "🚚 Kuryerlar ma'lumotlari")
async def admin_couriers_cmd(message: Message, state: FSMContext):
    await state.clear()
    await render_admin_couriers(message.from_user.id, message, edit=False)

@dp.callback_query(F.data == "admin_couriers_list")
async def admin_couriers_cb(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await render_admin_couriers(call.from_user.id, call.message, edit=True)

@dp.callback_query(F.data == "admin_dismiss")
async def admin_dismiss_cb(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    try: await call.message.delete()
    except Exception: pass

@dp.callback_query(F.data == "admin_add_courier_start")
async def admin_add_courier_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if not await is_admin(call.from_user.id): return
    await state.clear()
    
    is_super = await db.is_superadmin_session(call.from_user.id)
    if is_super:
        companies = await db.get_companies()
        active = [c for c in companies if not c.get('is_frozen')]
        if len(active) > 1:
            kb = []
            for c in active:
                kb.append([InlineKeyboardButton(text=f"🏪 {c['name']}", callback_data=f"addcour_comp_{c['id']}")])
            kb.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")])
            await call.message.edit_text("Kuryer qaysi kafe/kompaniyaga biriktiriladi? Tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            await state.set_state(AdminAddCourier.waiting_for_company)
            return
        else:
            comp_id = active[0]['id'] if active else None
            await state.update_data(cour_company_id=comp_id)
    else:
        comp_id = await db.get_company_id_for_admin(call.from_user.id)
        await state.update_data(cour_company_id=comp_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")]])
    await call.message.edit_text(
        "👤 <b>Yangi kuryer qo'shish (1/3)</b>\n\n"
        "Kuryerning <b>Telegram ID</b> raqamini kiriting (masalan: <code>123456789</code>):\n\n"
        "<i>💡 Eslatma: Kuryerdan yuborilgan xabarni bu yerga Forward (uzatish) qilishingiz ham mumkin.\n"
        "Kuryer o'z ID sini @userinfobot orqali bilib olishi mumkin.</i>",
        reply_markup=kb
    )
    await state.set_state(AdminAddCourier.waiting_for_tg_id)

@dp.callback_query(AdminAddCourier.waiting_for_company, F.data.startswith("addcour_comp_"))
async def admin_add_courier_company_selected(call: CallbackQuery, state: FSMContext):
    await call.answer()
    comp_id = int(call.data.split("_")[-1])
    await state.update_data(cour_company_id=comp_id)
    comp = await db.get_company(comp_id)
    comp_name = comp['name'] if comp else "Tanlangan kafe"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")]])
    await call.message.edit_text(
        f"🏪 <b>{comp_name}</b> tanlandi.\n\n"
        "👤 <b>Yangi kuryer qo'shish (1/3)</b>\n\n"
        "Kuryerning <b>Telegram ID</b> raqamini kiriting (masalan: <code>123456789</code>):\n\n"
        "<i>💡 Eslatma: Kuryerdan yuborilgan xabarni bu yerga Forward qilishingiz ham mumkin.</i>",
        reply_markup=kb
    )
    await state.set_state(AdminAddCourier.waiting_for_tg_id)

@dp.message(AdminAddCourier.waiting_for_tg_id)
async def admin_add_courier_tg_id(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    if message.text in [LANGS["uz"]["cancel"], "❌ Bekor qilish", "/cancel"]:
        await state.clear()
        return await render_admin_couriers(message.from_user.id, message, edit=False)
    
    tg_id = None
    if message.forward_from:
        tg_id = message.forward_from.id
    elif message.text and message.text.strip().isdigit():
        tg_id = int(message.text.strip())
    
    if not tg_id:
        return await message.answer(
            "⚠️ Noto'g'ri ID. Iltimos, faqat raqamdan iborat Telegram ID kiriting yoki kuryerdan xabar forward qiling:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")]])
        )
    
    await state.update_data(cour_tg_id=tg_id)
    await message.answer(
        f"✅ Telegram ID: <code>{tg_id}</code> qabul qilindi.\n\n"
        "👤 <b>Kuryerning to'liq ism-sharifini kiriting (2/3):</b>\n"
        "<i>Masalan: Ali Valiyev</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")]])
    )
    await state.set_state(AdminAddCourier.waiting_for_name)

@dp.message(AdminAddCourier.waiting_for_name, F.text)
async def admin_add_courier_name(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    if message.text in [LANGS["uz"]["cancel"], "❌ Bekor qilish", "/cancel"]:
        await state.clear()
        return await render_admin_couriers(message.from_user.id, message, edit=False)
    
    name = message.text.strip()
    await state.update_data(cour_name=name)
    await message.answer(
        f"✅ Ism: <b>{name}</b>\n\n"
        "📱 <b>Kuryerning telefon raqamini kiriting (3/3):</b>\n"
        "<i>Masalan: +998901234567</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_couriers_list")]])
    )
    await state.set_state(AdminAddCourier.waiting_for_phone)

@dp.message(AdminAddCourier.waiting_for_phone, F.text)
async def admin_add_courier_phone(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    if message.text in [LANGS["uz"]["cancel"], "❌ Bekor qilish", "/cancel"]:
        await state.clear()
        return await render_admin_couriers(message.from_user.id, message, edit=False)
    
    phone = message.text.strip()
    data = await state.get_data()
    tg_id = data["cour_tg_id"]
    name = data["cour_name"]
    company_id = data.get("cour_company_id")
    
    new_courier = await db.add_courier(tg_id, name, phone, company_id=company_id)
    await state.clear()
    
    comp = await db.get_company(company_id) if company_id else None
    comp_name = comp['name'] if comp else "Umumiy"
    
    success_text = (
        "✅ <b>Kuryer muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🆔 Kuryer ID: <b>#{new_courier['id']}</b>\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n"
        f"💬 Telegram ID: <code>{tg_id}</code>\n"
        f"🏪 Biriktirilgan kafe: <b>{comp_name}</b>\n\n"
        "Kuryer tizimga kiritildi va yangi buyurtmalarni qabul qilishi mumkin."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Kuryerlar ro'yxatiga qaytish", callback_data="admin_couriers_list")],
        [InlineKeyboardButton(text="➕ Yana kuryer qo'shish", callback_data="admin_add_courier_start")]
    ])
    await message.answer(success_text, reply_markup=kb)
    
    # Kuryerga xabar yuborish
    try:
        await bot.send_message(
            tg_id,
            f"🎉 <b>Assalomu alaykum, {name}!</b>\n\n"
            f"Siz <b>{comp_name}</b> uchun rasmiy kuryer sifatida tayinlandingiz!\n"
            f"Buyurtmalar qabul qilinganda va tayyor bo'lganda, sizga yetkazib berish haqida avtomatik xabar yuboriladi."
        )
    except Exception:
        pass

@dp.callback_query(F.data.startswith("delcour_"))
async def admin_delete_courier(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    await call.answer("Kuryer o'chirildi!")
    parts = call.data.split("_")
    courier_id = int(parts[1])
    company_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None
    await db.delete_courier(courier_id, company_id=company_id)
    await render_admin_couriers(call.from_user.id, call.message, edit=True)

# =================== PROMOCODES (ADMIN) ===================
@dp.message(F.text == "🎟 Promokodlar")
async def admin_promocodes_list(message: Message):
    if not await is_admin(message.from_user.id): return
    promos = await db.get_all_promocodes()
    text = "🎟 <b>Faol Promokodlar:</b>\n\n"
    if not promos:
        text += "Hozircha hech qanday promokod yo'q.\n"
    else:
        for code, data in promos.items():
            used_cnt = len(data.get("used_by", []))
            max_cnt = data.get("max_uses", 100)
            amt = data.get("amount", 0)
            text += f"🔹 <code>{code}</code> — <b>+{amt:,} so'm</b> ({used_cnt}/{max_cnt} ta ishlatildi)\n".replace(",", " ")
    text += "\n<i>Yangi promokod qo'shish yoki o'chirish uchun tanlang:</i>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi promokod qo'shish", callback_data="admin_add_promo_start")],
        [InlineKeyboardButton(text="🗑 Promokodni o'chirish", callback_data="admin_del_promo_start")]
    ])
    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "admin_add_promo_start")
async def admin_add_promo_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await call.message.answer(
        "Yangi promokod nomini kiriting (Masalan: <code>ASAKA5000</code>):",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True)
    )
    await state.set_state(AdminPromo.waiting_for_code)
    await call.answer()

@dp.message(AdminPromo.waiting_for_code, F.text)
async def admin_promo_code_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    code = message.text.strip().upper()
    await state.update_data(promo_code=code)
    await message.answer(f"Promokod: <b>{code}</b>\n\nEndi ushbu promokod beradigan <b>summani (so'mda)</b> kiriting (Masalan: <code>5000</code>):")
    await state.set_state(AdminPromo.waiting_for_amount)

@dp.message(AdminPromo.waiting_for_amount, F.text)
async def admin_promo_amount_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    try:
        amount = int(message.text.replace(" ", ""))
        if amount <= 0: raise ValueError
    except ValueError:
        return await message.answer("❌ Iltimos, musbat son kiriting (Masalan: 5000):")
    await state.update_data(promo_amount=amount)
    await message.answer("Ushbu promokoddan ko'pi bilan <b>nechta odam</b> foydalana olishini kiriting (Masalan: <code>50</code>):")
    await state.set_state(AdminPromo.waiting_for_limit)

@dp.message(AdminPromo.waiting_for_limit, F.text)
async def admin_promo_limit_step(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    try:
        limit = int(message.text.replace(" ", ""))
        if limit <= 0: raise ValueError
    except ValueError:
        return await message.answer("❌ Iltimos, musbat son kiriting (Masalan: 50):")
    data = await state.get_data()
    code = data["promo_code"]
    amount = data["promo_amount"]
    await db.add_promocode(code, amount, limit)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer(
        f"✅ <b>Promokod yaratildi!</b>\n\n"
        f"🎟 Kod: <code>{code}</code>\n"
        f"💰 Mukofot: <b>+{amount:,} so'm</b>\n"
        f"👥 Maksimal limit: <b>{limit} ta odam</b>\n\n"
        f"Ushbu promokodni kanal yoki guruhlarda e'lon qilishingiz mumkin!".replace(",", " "),
        reply_markup=get_admin_keyboard(is_superadmin=is_super)
    )

@dp.callback_query(F.data == "admin_del_promo_start")
async def admin_del_promo_start(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    promos = await db.get_all_promocodes()
    if not promos:
        return await call.answer("O'chirish uchun promokodlar yo'q!", show_alert=True)
    keyboard = []
    for code in promos.keys():
        keyboard.append([InlineKeyboardButton(text=f"🗑 {code}", callback_data=f"delpromo_{code}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_promos_cancel")])
    await call.message.edit_text("O'chirmoqchi bo'lgan promokodingizni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await call.answer()

@dp.callback_query(F.data.startswith("delpromo_"))
async def admin_del_promo_action(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    code = call.data.split("_")[1]
    await db.delete_promocode(code)
    await call.answer(f"Promokod {code} o'chirildi!", show_alert=True)
    try: await call.message.delete()
    except: pass
    await admin_promocodes_list(call.message)

@dp.callback_query(F.data == "admin_promos_cancel")
async def admin_del_promo_cancel(call: CallbackQuery):
    try: await call.message.delete()
    except: pass
    await call.answer()

# =================== USERS ===================
@dp.message(F.text == "👥 Foydalanuvchilar")
async def admin_users(message: Message):
    if not await is_admin(message.from_user.id): return
    users = await db.get_all_users()
    text = f"👥 <b>Barcha foydalanuvchilar ({len(users)} ta):</b>\n\n"
    for u in users[:40]:
        username = f"| @{u.get('username')} " if u.get('username') else ""
        text += f"ID: {u.get('telegram_id')} | Ism: {u.get('fullname')} {username}\n"
    await message.answer(text)

# =================== BALANCE RESET ===================
@dp.message(F.text == "🔄 Balansni nolga tushirish")
async def admin_reset_revenue(message: Message):
    if not await is_admin(message.from_user.id): return
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    await db.reset_revenue(company_id=company_id)
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer("✅ Barcha daromadlar nolga tushirildi (Archivlandi).", reply_markup=get_admin_keyboard(is_superadmin=is_super))

# =================== CONTACT SETTINGS ===================
@dp.message(F.text == "⚙️ Aloqa sozlamalari")
async def admin_update_contact_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    contact = await db.get_admin_contact(company_id=company_id)
    await message.answer(f"Hozirgi ism: {contact.get('name','')}\n\nYangi ismni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminContact.waiting_for_name)

@dp.message(AdminContact.waiting_for_name)
async def admin_update_contact_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(contact_name=message.text)
    await message.answer("Yangi telefon raqamni kiriting:")
    await state.set_state(AdminContact.waiting_for_phone)

@dp.message(AdminContact.waiting_for_phone)
async def admin_update_contact_phone(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(contact_phone=message.text)
    await message.answer("Yangi Telegram usernameni kiriting (masalan: @admin):")
    await state.set_state(AdminContact.waiting_for_username)

@dp.message(AdminContact.waiting_for_username)
async def admin_update_contact_username(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    await db.update_admin_contact(data["contact_name"], data["contact_phone"], message.text, company_id=company_id)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer("✅ Aloqa ma'lumotlari yangilandi!", reply_markup=get_admin_keyboard(is_superadmin=is_super))

# =================== ADMIN COMPANY LOCATION ===================
@dp.message(F.text == "📍 Oshxona manzili & Lokatsiyasi")
async def admin_company_location_view(message: Message):
    if not await is_admin(message.from_user.id): return
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    comp = await db.get_company(company_id) if company_id else None
    
    if comp:
        name = comp.get("name", "Kafe")
        addr = comp.get("address", "Kiritilmagan")
        lat = comp.get("latitude")
        lon = comp.get("longitude")
    else:
        name = "Asosiy Oshxona"
        loc = getattr(db, 'admin_location', {})
        addr = loc.get("address", "Asaka shahar")
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        
    coords_text = f"{lat}, {lon}" if lat and lon else "Kiritilmagan"
    map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None
    
    text = (
        f"📍 <b>{name} MANZILI VA GPS LOKATSIYASI</b>\n\n"
        f"📫 <b>Hozirgi manzil matni:</b> {addr}\n"
        f"🌐 <b>GPS Koordinatalar:</b> <code>{coords_text}</code>\n\n"
        f"<i>Mijozlar 'Yaqin atrofdagi oshxonalar' bo'limida sizgacha bo'lgan masofani aniq ko'rishlari uchun manzil va lokatsiyani to'g'ri kiritib qo'ying!</i>"
    )
    kb = []
    if map_link:
        kb.append([InlineKeyboardButton(text="🗺 Xaritada tekshirish", url=map_link)])
    kb.append([InlineKeyboardButton(text="✏️ Manzil va Lokatsiyani o'zgartirish", callback_data="admin_set_loc_start")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data == "admin_set_loc_start")
async def admin_set_loc_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await call.answer()
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Oshxonaning jonli GPS lokatsiyasini yuborish", request_location=True)],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    text = (
        "📍 <b>Oshxona GPS lokatsiyasini yuboring:</b>\n\n"
        "Pastdagi <b>'📍 Oshxonaning jonli GPS lokatsiyasini yuborish'</b> tugmasini bosing yoki lokatsiya belgilab yuboring.\n"
        "(Yoki shunchaki manzil matnini yozib yuborishingiz mumkin)"
    )
    await call.message.answer(text, reply_markup=kb)
    await state.set_state(AdminCompanyLocation.waiting_for_location_or_address)

@dp.message(AdminCompanyLocation.waiting_for_location_or_address, F.location | F.text)
async def admin_set_loc_process(message: Message, state: FSMContext):
    if message.text in ["🔙 Asosiy menyu", "/cancel"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        is_super = await db.is_superadmin_session(message.from_user.id)
        return await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_admin_keyboard(is_superadmin=is_super))
        
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        await state.update_data(loc_lat=lat, loc_lon=lon)
        await message.answer(
            f"✅ GPS koordinatalar olindi: <code>{lat:.5f}, {lon:.5f}</code>\n\n"
            f"Endi oshxonaning <b>to'liq manzil matnini</b> yozib yuboring (Masalan: <i>Asaka shahar, Bobur shoh ko'chasi, 24-uy</i>):",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True)
        )
        await state.set_state(AdminCompanyLocation.waiting_for_address_text)
    else:
        address = message.text.strip()
        await db.update_company_location(company_id, address=address)
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        is_super = await db.is_superadmin_session(message.from_user.id)
        await message.answer(
            f"✅ <b>Manzil muvaffaqiyatli saqlandi!</b>\n\n📫 Manzil: <b>{address}</b>",
            reply_markup=get_admin_keyboard(is_superadmin=is_super)
        )

@dp.message(AdminCompanyLocation.waiting_for_address_text, F.text)
async def admin_set_loc_text_step(message: Message, state: FSMContext):
    if message.text in ["🔙 Asosiy menyu", "/cancel"]:
        await state.clear()
        clear_reply_kb_bg(message.chat.id)
        is_super = await db.is_superadmin_session(message.from_user.id)
        return await message.answer("Bosh menyuga qaytdingiz.", reply_markup=get_admin_keyboard(is_superadmin=is_super))
        
    address = message.text.strip()
    data = await state.get_data()
    lat = data.get("loc_lat")
    lon = data.get("loc_lon")
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    
    await db.update_company_location(company_id, address=address, latitude=lat, longitude=lon)
    await state.clear()
    clear_reply_kb_bg(message.chat.id)
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer(
        f"✅ <b>Oshxona manzili va GPS lokatsiyasi muvaffaqiyatli saqlandi!</b>\n\n"
        f"📫 Manzil: <b>{address}</b>\n"
        f"🌐 GPS: <code>{lat:.5f}, {lon:.5f}</code>\n\n"
        f"Endi barcha mijozlar 'Yaqin atrofdagi oshxonalar' bo'limida sizgacha bo'lgan masofani aniq ko'rishlari mumkin!",
        reply_markup=get_admin_keyboard(is_superadmin=is_super)
    )

# =================== ADMIN ACCOUNTS ===================
@dp.message(F.text == "👨‍💻 Adminlar")
async def admin_manage_accounts(message: Message):
    if not await is_admin(message.from_user.id): return
    is_super = await db.is_superadmin_session(message.from_user.id)
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    accounts = await db.get_admin_accounts()
    text = "👨‍💻 <b>Adminlar ro'yxati:</b>\n\n"
    keyboard = []
    for acc in accounts:
        if not is_super and acc.get("company_id") != company_id:
            continue
        comp_info = ""
        if acc.get("company_id"):
            comp = await db.get_company(acc["company_id"])
            comp_info = f" [{comp['name'] if comp else '?'}]"
        role = "👑 Superadmin" if acc.get("is_superadmin") else "🏪 Kompaniya admin"
        text += f"{role}{comp_info}\n👤 {acc['name']} (Login: {acc['login']})\n\n"
        if not acc.get("is_superadmin") and is_super:
            keyboard.append([InlineKeyboardButton(text=f"❌ {acc['name']} ni o'chirish", callback_data=f"deladmin_{acc['login']}")])
    if is_super:
        keyboard.insert(0, [InlineKeyboardButton(text="➕ Yangi Admin qo'shish", callback_data="add_admin_acc")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None)

@dp.callback_query(F.data == "add_admin_acc")
async def add_admin_acc_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    is_super = await db.is_superadmin_session(call.from_user.id)
    if not is_super:
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return
    await call.message.answer("Yangi admin uchun LOGIN kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AdminManage.waiting_for_login)
    await call.answer()

@dp.message(AdminManage.waiting_for_login)
async def add_admin_login(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(new_login=message.text)
    await message.answer("Yangi admin uchun PAROL kiriting:")
    await state.set_state(AdminManage.waiting_for_password)

@dp.message(AdminManage.waiting_for_password)
async def add_admin_password(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(new_pass=message.text)
    await message.answer("Adminning ismini kiriting:")
    await state.set_state(AdminManage.waiting_for_name)

@dp.message(AdminManage.waiting_for_name)
async def add_admin_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    await db.add_admin_account(data["new_login"], data["new_pass"], message.text, is_superadmin=False)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer(f"✅ Yangi admin qo'shildi!\nLogin: {data['new_login']}\nParol: {data['new_pass']}", reply_markup=get_admin_keyboard(is_superadmin=is_super))

@dp.callback_query(F.data.startswith("deladmin_"))
async def delete_admin_acc(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    login = call.data.split("_", 1)[1]
    await db.remove_admin_account(login)
    await call.answer("Admin o'chirildi.")
    await admin_manage_accounts(call.message)

# =================== CATEGORIES ===================
@dp.message(F.text == "🏷 Kategoriyalar")
async def admin_manage_categories(message: Message):
    if not await is_admin(message.from_user.id): return
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    cats = await db.get_categories(company_id=company_id)
    text = "🏷 <b>Mavjud Kategoriyalar:</b>\n\n"
    keyboard = []
    for c in cats:
        text += f"▪️ {c}\n"
        keyboard.append([InlineKeyboardButton(text=f"❌ {c} ni o'chirish", callback_data=f"delcat_{c}")])
    keyboard.insert(0, [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="add_cat_start")])
    await message.answer(text or "Kategoriyalar yo'q.", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "add_cat_start")
async def add_cat_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    await call.message.answer("Yangi kategoriya nomini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(CategoryManage.waiting_for_new_category)
    await call.answer()

@dp.message(CategoryManage.waiting_for_new_category)
async def add_cat_finish(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    await db.add_category(message.text, company_id=company_id)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer(f"✅ Kategoriya qo'shildi: {message.text}", reply_markup=get_admin_keyboard(is_superadmin=is_super))

@dp.callback_query(F.data.startswith("delcat_"))
async def delete_cat(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    cat = call.data.split("_", 1)[1]
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    await db.remove_category(cat, company_id=company_id)
    await call.answer("Kategoriya o'chirildi.")
    await admin_manage_categories(call.message)

# =================== PRODUCTS ===================
@dp.message(F.text == "➕ MENU qo'shish")
async def admin_add_product_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("🍔 Yangi mahsulot nomini kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AddProduct.waiting_for_name)

@dp.message(AddProduct.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(name=message.text)
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    categories = await db.get_categories(company_id=company_id)
    kb_buttons = []
    row = []
    for cat in categories:
        row.append(KeyboardButton(text=cat))
        if len(row) == 2:
            kb_buttons.append(row)
            row = []
    if row: kb_buttons.append(row)
    kb_buttons.append([KeyboardButton(text="🔙 Asosiy menyu")])
    await message.answer("Kategoriyani tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True))
    await state.set_state(AddProduct.waiting_for_category)

@dp.message(AddProduct.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(category=message.text)
    await message.answer("📝 Mahsulot tavsifini yozing:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(AddProduct.waiting_for_desc)

@dp.message(AddProduct.waiting_for_desc)
async def add_product_desc(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(desc=message.text)
    await message.answer("💰 Narxini kiriting (raqamda):")
    await state.set_state(AddProduct.waiting_for_price)

@dp.message(AddProduct.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    price_text = message.text.replace(" ", "").replace(",", "").replace(".", "")
    if not price_text.isdigit(): return await message.answer("Faqat raqam kiriting!")
    await state.update_data(price=int(price_text))
    await message.answer("🖼 Mahsulot rasmini yuboring (yoki URL link bering):")
    await state.set_state(AddProduct.waiting_for_image)

@dp.message(AddProduct.waiting_for_image)
async def add_product_image(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    import os
    image_url = ""
    if message.photo:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        os.makedirs("images", exist_ok=True)
        file_path = f"images/{file_id}.jpg"
        await bot.download_file(file.file_path, file_path)
        image_url = f"images/{file_id}.jpg"
    elif message.document:
        ext = os.path.splitext(message.document.file_name)[1].lower() if message.document.file_name else ".png"
        if message.document.mime_type and message.document.mime_type.startswith("image/") or ext in [".jpg",".jpeg",".png",".webp"]:
            file_id = message.document.file_id
            file = await bot.get_file(file_id)
            os.makedirs("images", exist_ok=True)
            file_path = f"images/{file_id}{ext}"
            await bot.download_file(file.file_path, file_path)
            image_url = f"images/{file_id}{ext}"
        else:
            return await message.answer("Noto'g'ri rasm formati!")
    elif message.text and message.text.startswith("http"):
        image_url = message.text
    else:
        return await message.answer("Rasm yoki URL link bering!")
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    await db.add_product(data["name"], data["desc"], data["price"], category=data["category"], image=image_url, company_id=company_id)
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer("✅ Mahsulot qo'shildi!", reply_markup=get_admin_keyboard(is_superadmin=is_super))

@dp.message(F.text == "📝 O'chirish / Tahrirlash")
async def admin_edit_products(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await state.update_data(edited_products=[])
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    cats = await db.get_categories(company_id=company_id)
    keyboard = [[InlineKeyboardButton(text="📋 Barchasi", callback_data="editcat_all")]]
    for c in cats:
        keyboard.append([InlineKeyboardButton(text=f"📂 {c}", callback_data=f"editcat_{c}")])
    await message.answer("Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "editcats_back")
async def admin_edit_cats_back(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    cats = await db.get_categories(company_id=company_id)
    keyboard = [[InlineKeyboardButton(text="📋 Barchasi", callback_data="editcat_all")]]
    for c in cats: keyboard.append([InlineKeyboardButton(text=f"📂 {c}", callback_data=f"editcat_{c}")])
    await call.message.edit_text("Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("editcat_"))
async def admin_show_category_products(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    cat = call.data.split("_", 1)[1]
    await state.update_data(current_edit_cat=cat)
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    if company_id:
        company = await db.get_company(company_id)
        all_products = company.get("products", []) if company else []
    else:
        all_products = getattr(db, "products", [])
    cat_products = all_products if cat == "all" else [p for p in all_products if p.get("category") == cat]
    display_cat_name = "Barchasi" if cat == "all" else cat
    if not cat_products:
        return await call.answer("Bu kategoriyada mahsulotlar yo'q!", show_alert=True)
    data = await state.get_data()
    edited_products = data.get("edited_products", [])
    keyboard = []
    for p in cat_products:
        status = "✅" if p.get("is_active", 1) else "❌"
        edit_mark = "✏️ " if p["id"] in edited_products else ""
        keyboard.append([InlineKeyboardButton(text=f"{edit_mark}{status} {p['name']}", callback_data=f"prodmanage_{p['id']}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Kategoriyalarga qaytish", callback_data="editcats_back")])
    await call.message.edit_text(f"📂 <b>{display_cat_name}</b> bo'limidagi mahsulotlar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("prodmanage_"))
async def admin_manage_product_options(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    product_id = int(call.data.split("_")[1])
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    if company_id:
        company = await db.get_company(company_id)
        products = company.get("products", []) if company else []
    else:
        products = db.products
    product = next((p for p in products if p["id"] == product_id), None)
    if not product: return await call.answer("Mahsulot topilmadi!")
    data = await state.get_data()
    back_cat = data.get("current_edit_cat", product.get("category", "Boshqa"))
    status_text = "Vaqtinchalik O'chirish" if product.get("is_active", 1) else "Vaqtinchalik Yoqish"
    keyboard = [
        [InlineKeyboardButton(text=f"👁 {status_text}", callback_data=f"del_{product_id}")],
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"editprod_{product_id}")],
        [InlineKeyboardButton(text="🗑 Butunlay o'chirish", callback_data=f"harddel_{product_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"editcat_{back_cat}")]
    ]
    status_display = "✅ Faol" if product.get("is_active", 1) else "❌ O'chirilgan"
    price_val = product.get("price") or 0
    await call.message.edit_text(f"🍔 <b>{product['name']}</b>\n💰 {price_val:,} so'm\n📊 {status_display}".replace(",", " "), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("del_"))
async def admin_toggle_product(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    product_id = int(call.data.split("_")[1])
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    await db.toggle_product(product_id, company_id=company_id)
    await call.answer("Holati o'zgartirildi!")
    await admin_manage_product_options(call, state)

@dp.callback_query(F.data.startswith("harddel_"))
async def admin_hard_delete_product(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    product_id = int(call.data.split("_")[1])
    company_id = await db.get_company_id_for_admin(call.from_user.id)
    await db.delete_product(product_id, company_id=company_id)
    await call.answer("Butunlay o'chirildi!")
    await call.message.delete()

@dp.callback_query(F.data.startswith("editprod_"))
async def admin_edit_product_start(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id): return
    product_id = int(call.data.split("_")[1])
    await state.update_data(edit_product_id=product_id)
    await call.message.answer("📝 Yangi tavsif yozing (o'zgartirmaslik uchun 'O'tkazib yuborish'):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏩ O'tkazib yuborish")], [KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(EditProduct.waiting_for_desc)

@dp.message(EditProduct.waiting_for_desc)
async def admin_edit_product_desc(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    await state.update_data(edit_desc=None if message.text == "⏩ O'tkazib yuborish" else message.text)
    await message.answer("✏️ Yangi narxni kiriting (yoki 'O'tkazib yuborish'):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏩ O'tkazib yuborish")], [KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(EditProduct.waiting_for_price)

@dp.message(EditProduct.waiting_for_price)
async def admin_edit_product_price(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    if message.text != "⏩ O'tkazib yuborish":
        price_text = message.text.replace(" ", "").replace(",", "").replace(".", "")
        if not price_text.isdigit(): return await message.answer("Faqat raqam kiriting!")
        await state.update_data(edit_price=int(price_text))
    else:
        await state.update_data(edit_price=None)
    await message.answer("🖼 Yangi rasmni yuboring (yoki 'O'tkazib yuborish'):", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏩ O'tkazib yuborish")], [KeyboardButton(text="🔙 Asosiy menyu")]], resize_keyboard=True))
    await state.set_state(EditProduct.waiting_for_image)

@dp.message(EditProduct.waiting_for_image)
async def admin_edit_product_image(message: Message, state: FSMContext):
    if message.text == "🔙 Asosiy menyu": return await back_to_main(message, state)
    data = await state.get_data()
    product_id = data["edit_product_id"]
    new_price = data.get("edit_price")
    new_desc = data.get("edit_desc")
    import os
    image_url = ""
    if message.text == "⏩ O'tkazib yuborish": pass
    elif message.photo:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        os.makedirs("images", exist_ok=True)
        await bot.download_file(file.file_path, f"images/{file_id}.jpg")
        image_url = f"images/{file_id}.jpg"
    elif message.document:
        ext = os.path.splitext(message.document.file_name)[1].lower() if message.document.file_name else ".png"
        if message.document.mime_type and message.document.mime_type.startswith("image/") or ext in [".jpg",".jpeg",".png",".webp"]:
            file_id = message.document.file_id
            file = await bot.get_file(file_id)
            os.makedirs("images", exist_ok=True)
            await bot.download_file(file.file_path, f"images/{file_id}{ext}")
            image_url = f"images/{file_id}{ext}"
    elif message.text and message.text.startswith("http"):
        image_url = message.text
    else:
        return await message.answer("Noto'g'ri! Rasm yoki URL bering, yoki 'O'tkazib yuborish'.")
    company_id = await db.get_company_id_for_admin(message.from_user.id)
    await db.edit_product(product_id, new_price=new_price, new_image=image_url, new_desc=new_desc, company_id=company_id)
    await state.set_state(None)
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer("✅ Mahsulot tahrirlandi!", reply_markup=get_admin_keyboard(is_superadmin=is_super))

# =================== BROADCAST ===================
@dp.message(F.text == "📢 Reklama tarqatish")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id): return
    await message.answer("Reklama materialini yuboring (Matn, Rasm, Video yoki Audio - hammasi qo'llab-quvvatlanadi):")
    await state.set_state(Broadcast.waiting_for_message)

@dp.message(Broadcast.waiting_for_message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    users = await db.get_all_users()
    count = 0
    for u in users:
        try:
            await bot.copy_message(chat_id=u.get("telegram_id"), from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except Exception: pass
    await state.clear()
    is_super = await db.is_superadmin_session(message.from_user.id)
    await message.answer(f"✅ {count} ta foydalanuvchiga yuborildi!", reply_markup=get_admin_keyboard(is_superadmin=is_super))

# =================== WEBSITE UPDATE ===================
@dp.message(F.text == "🔄 Saytni yangilash")
async def update_website_data(message: Message):
    if not await is_admin(message.from_user.id): return
    try:
        db.export_webapp_products()
        await message.answer("✅ Sayt ma'lumotlari yangilandi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")

# =================== ANALYTICS ===================
@dp.message(F.text == "📊 Analiz")
async def admin_analiz_start(message: Message):
    if not await is_admin(message.from_user.id): return
    months = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]
    keyboard = []
    row = []
    for i, m in enumerate(months):
        row.append(InlineKeyboardButton(text=m, callback_data=f"analiz_m_{i+1}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    await message.answer("📊 Qaysi oyni analiz qilmoqchisiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("analiz_m_"))
async def admin_analiz_month(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    month = int(call.data.split("_")[2])
    months = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]
    month_name = months[month-1]
    keyboard = [
        [InlineKeyboardButton(text="1-hafta (1-7)", callback_data=f"analiz_p_{month}_w1"), InlineKeyboardButton(text="2-hafta (8-14)", callback_data=f"analiz_p_{month}_w2")],
        [InlineKeyboardButton(text="3-hafta (15-21)", callback_data=f"analiz_p_{month}_w3"), InlineKeyboardButton(text="4-hafta (22+)", callback_data=f"analiz_p_{month}_w4")],
        [InlineKeyboardButton(text="1-10 kunlik", callback_data=f"analiz_p_{month}_t1")],
        [InlineKeyboardButton(text="11-20 kunlik", callback_data=f"analiz_p_{month}_t2")],
        [InlineKeyboardButton(text="21+ kunlik", callback_data=f"analiz_p_{month}_t3")],
        [InlineKeyboardButton(text="🔙 Oylarga qaytish", callback_data="analiz_back_m")]
    ]
    await call.message.edit_text(f"📊 <b>{month_name}</b> uchun davr tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data == "analiz_back_m")
async def admin_analiz_back(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    months = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]
    keyboard = []
    row = []
    for i, m in enumerate(months):
        row.append(InlineKeyboardButton(text=m, callback_data=f"analiz_m_{i+1}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    await call.message.edit_text("📊 Qaysi oyni analiz qilmoqchisiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("analiz_p_"))
async def admin_analiz_result(call: CallbackQuery):
    if not await is_admin(call.from_user.id): return
    parts = call.data.split("_")
    month = int(parts[2])
    period = parts[3]
    months = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]
    month_name = months[month-1]
    if period == "w1": p_text, p_func = "1-hafta", lambda d: 1<=d<=7
    elif period == "w2": p_text, p_func = "2-hafta", lambda d: 8<=d<=14
    elif period == "w3": p_text, p_func = "3-hafta", lambda d: 15<=d<=21
    elif period == "w4": p_text, p_func = "4-hafta", lambda d: d>=22
    elif period == "t1": p_text, p_func = "1-10 kun", lambda d: 1<=d<=10
    elif period == "t2": p_text, p_func = "11-20 kun", lambda d: 11<=d<=20
    elif period == "t3": p_text, p_func = "21+ kun", lambda d: d>=21
    else: return

    company_id = await db.get_company_id_for_admin(call.from_user.id)
    if company_id:
        company = await db.get_company(company_id)
        orders = company.get("orders", []) if company else []
    else:
        orders = db.orders

    from collections import defaultdict
    product_counts = defaultdict(int)
    for o in orders:
        if o.get("status") == "Bekor qilingan": continue
        date_str = o.get("created_at", "")
        if not date_str: continue
        try:
            d_str, m_str, _ = date_str.split(" ")[0].split(".")
            d, m = int(d_str), int(m_str)
            if m == month and p_func(d):
                for item in o.get("items", []):
                    product_counts[item["name"]] += int(item["quantity"])
        except Exception: continue

    if not product_counts:
        return await call.answer("Bunday davr uchun xaridlar topilmadi!", show_alert=True)

    sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
    text = f"📊 <b>Analiz: {month_name} / {p_text}</b>\n\n"
    text += "📈 <b>Eng ko'p sotilgan:</b>\n"
    for p_name, p_qty in sorted_products[:5]:
        text += f"▪️ {p_name} — {p_qty} ta\n"
    shown = set(p[0] for p in sorted_products[:5])
    bottom = [(n,q) for n,q in reversed(sorted_products) if n not in shown][:5]
    if bottom:
        text += "\n📉 <b>Eng kam sotilgan:</b>\n"
        for p_name, p_qty in reversed(bottom):
            text += f"▪️ {p_name} — {p_qty} ta\n"
    text += f"\n<i>Jami: {len(sorted_products)} xil mahsulot sotilgan.</i>"
    keyboard = [[InlineKeyboardButton(text="🔙 Oylarga qaytish", callback_data="analiz_back_m")]]
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# =================== WEB SERVER ===================
async def start_webapp():
    from aiohttp import web
    import os

    webapp_dir = os.path.dirname(os.path.abspath(__file__))

    async def index_handler(request):
        index_file = os.path.join(webapp_dir, "index.html")
        if os.path.exists(index_file):
            return web.FileResponse(index_file)
        return web.Response(text="Bot is running!", content_type="text/html")

    async def health_handler(request):
        return web.Response(text="OK")

    async def static_file_handler(request):
        filename = request.match_info.get("filename", "")
        allowed_files = ["app.js", "style.css", "products.json"]
        if filename in allowed_files:
            file_path = os.path.join(webapp_dir, filename)
            if os.path.exists(file_path):
                return web.FileResponse(file_path)
        return web.Response(status=404)

    async def api_checkout_handler(request):
        pass # Not used directly like this since it conflicts with aiohttp routing if not correctly setup. 
             # We define it inline here.

    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", index_handler)
    app.router.add_get("/{filename}", static_file_handler)
    
    images_dir = os.path.join(webapp_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    app.router.add_static("/images", images_dir)

    async def api_checkout(request):
        try:
            data = await request.json()
            user_id = int(data.get("user_id", 0))
            items = data.get("items", [])
            company_id = data.get("company_id")
            if company_id: company_id = int(company_id)
            if not items or not user_id:
                return web.json_response({"status": "error", "message": "Bo'sh savat yoki user topilmadi"})
            user = await db.get_user(user_id)
            lang = user.get("lang", "uz") if user else "uz"
            db_products = await db.get_products(company_id=company_id)
            product_dict = {p["id"]: p["price"] for p in db_products}
            total = 0
            for item in items:
                real_price = product_dict.get(int(item["id"]), item.get("price", 0))
                if real_price is None: real_price = 0
                item["price"] = real_price
                total += real_price * int(item["quantity"])
                
            from aiogram.fsm.storage.base import StorageKey
            state = FSMContext(
                storage=dp.storage,
                key=StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
            )
            await state.update_data(items=items, total=total, company_id=company_id)
            state_data = await state.get_data()
            order_type = state_data.get("order_type") or "Masofaviy"
            await state.update_data(items=items, total=total, company_id=company_id, order_type=order_type)
            
            text = f"🛍 <b>{get_text(lang, 'you_selected')}</b>\n\n"
            for item in items:
                text += f"▪️ {item['name']} x {item['quantity']} = {item['price'] * item['quantity']:,} so'm\n".replace(",", " ")
            text += f"\n💰 <b>{get_text(lang, 'total')}:</b> {total:,} so'm\n\n".replace(",", " ")
            text += get_text(lang, "phone_prompt")
            await bot.send_message(user_id, text, reply_markup=get_contact_keyboard(lang))
            await state.set_state(OrderFlow.waiting_for_phone)
                
            return web.json_response({"status": "ok"})
        except Exception as e:
            print("API Checkout Error:", e)
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    app.router.add_post("/api/checkout", api_checkout)

    runner = web.AppRunner(app)
    await runner.setup()
    port_str = os.environ.get("PORT")
    if port_str:
        port = int(port_str)
    else:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            port = s.getsockname()[1]
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"[WEB] Server {port}-portda ishga tushdi")
    return runner, port

localtunnel_process = None

async def auto_start_localtunnel(port):
    global WEBAPP_URL, localtunnel_process
    print(f"\n[*] LocalTunnel ishga tushirilmoqda (Port: {port})...")
    try:
        localtunnel_process = await asyncio.create_subprocess_shell(
            f"npx --yes localtunnel --port {port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        async def _read():
            while True:
                line = await localtunnel_process.stdout.readline()
                if not line: break
                text = line.decode("utf-8", errors="ignore").strip()
                if "your url is:" in text:
                    url = text.split("your url is:")[1].strip()
                    print(f"✅ URL: {url}\n")
                    return url
            return None

        try:
            url = await asyncio.wait_for(_read(), timeout=15)
            if url:
                WEBAPP_URL = url
        except Exception:
            print(f"[*] LocalTunnel kutish vaqti tugadi. Standart WEBAPP_URL ishlatiladi: {WEBAPP_URL}")
    except Exception as e:
        print(f"[*] LocalTunnel xatosi: {e}")

async def main():
    global BOT_USERNAME
    await db.connect()
    runner = None
    try:
        logging.info("Bot ishga tushmoqda...")
        try:
            bot_info = await bot.get_me()
            if bot_info.username:
                BOT_USERNAME = bot_info.username
            await bot.set_my_description(
                description=(
                    "🛵 Asaka Food Express — Asaka shahridagi barcha kafe, restoran va do'konlardan tezkor yetkazib berish xizmati!\n\n"
                    "🍔 Mazali va issiq taomlar\n"
                    "⚡️ 30-45 daqiqada tezkor yetkazish\n"
                    "💸 Har bir xaridingizdan 3% keshbek\n"
                    "🎁 Har kuni bepul bonuslar va sovg'alar!"
                )
            )
            await bot.set_my_short_description(
                short_description="Asaka bo'yicha tezkor taom va mahsulotlar yetkazib berish xizmati 🛵"
            )
            await bot.set_my_commands([
                BotCommand(command="start", description="Bosh menyu / Главное меню"),
                BotCommand(command="menu", description="Taomnoma / Меню"),
                BotCommand(command="help", description="Qo'llanma / Инструкция"),
            ])
        except Exception as e:
            logging.warning(f"Bot meta sozlashda xatolik: {e}")
        await bot.delete_webhook(drop_pending_updates=True)
        runner, port = await start_webapp()
        if not os.environ.get("PORT"):
            asyncio.create_task(auto_start_localtunnel(port))
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logging.error(f"Xatolik: {e}")
    finally:
        logging.info("Xavfsiz to'xtatish...")
        await bot.session.close()
        await db.close()
        if runner:
            await runner.cleanup()
        if localtunnel_process:
            try: localtunnel_process.terminate()
            except: pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
