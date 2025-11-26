import os
import json
import asyncio
import logging
import random
import base64
from datetime import datetime, timedelta
from threading import Thread

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    InlineQueryHandler
)
from telegram.constants import ChatMemberStatus
from groq import Groq
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEVELOPER_ID = 123456789
DEVELOPER_USERNAME = "Dev_Mido"
REQUIRED_CHANNEL = "@TepthonHelp"

flask_app = Flask(__name__)
main_scheduler = AsyncIOScheduler()

ADHKAR_LIST = [
    "سبحان الله وبحمده، سبحان الله العظيم",
    "لا اله الا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
    "سبحان الله، والحمد لله، ولا اله الا الله، والله اكبر",
    "لا حول ولا قوة الا بالله العلي العظيم",
    "استغفر الله العظيم الذي لا اله الا هو الحي القيوم واتوب اليه",
    "اللهم صل وسلم على نبينا محمد",
    "سبحان الله عدد ما خلق، سبحان الله ملء ما خلق، سبحان الله عدد ما في الارض والسماء",
    "الحمد لله حمدا كثيرا طيبا مباركا فيه",
    "اللهم اني اسالك العفو والعافية في الدنيا والاخرة",
    "رب اغفر لي وتب علي انك انت التواب الرحيم",
    "اللهم انك عفو تحب العفو فاعف عني",
    "يا حي يا قيوم برحمتك استغيث",
    "لا اله الا انت سبحانك اني كنت من الظالمين",
    "حسبي الله لا اله الا هو عليه توكلت وهو رب العرش العظيم",
    "اللهم اني اعوذ بك من الهم والحزن والعجز والكسل",
    "رب اشرح لي صدري ويسر لي امري",
    "اللهم لا سهل الا ما جعلته سهلا وانت تجعل الحزن اذا شئت سهلا",
    "رب زدني علما",
    "اللهم اني اسالك الهدى والتقى والعفاف والغنى",
    "اللهم اصلح لي ديني الذي هو عصمة امري",
    "اللهم ارحمني بترك المعاصي ابدا ما ابقيتني",
    "اللهم ارزقني حبك وحب من يحبك وحب عمل يقربني الى حبك",
    "اللهم اجعل القران ربيع قلبي ونور صدري وجلاء حزني وذهاب همي",
    "اللهم اني اعوذ بك من علم لا ينفع ومن قلب لا يخشع",
    "رب هب لي من لدنك رحمة انك انت الوهاب",
    "اللهم اتنا في الدنيا حسنة وفي الاخرة حسنة وقنا عذاب النار",
    "سبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته",
    "اللهم اغفر لي ذنبي كله دقه وجله واوله واخره وعلانيته وسره",
    "اللهم اني اسالك من الخير كله عاجله واجله ما علمت منه وما لم اعلم",
    "اللهم اني اعوذ بك من الشر كله عاجله واجله ما علمت منه وما لم اعلم",
    "اللهم اني اسالك الجنة وما قرب اليها من قول او عمل",
    "اللهم اني اعوذ بك من النار وما قرب اليها من قول او عمل",
    "اللهم باعلمك الغيب وقدرتك على الخلق احيني ما علمت الحياة خيرا لي",
    "اللهم اني اسالك خشيتك في الغيب والشهادة",
    "اللهم اني اسالك كلمة الحق في الرضا والغضب",
    "اللهم اني اسالك القصد في الفقر والغنى",
    "اللهم اني اسالك نعيما لا ينفد وقرة عين لا تنقطع",
    "اللهم اني اسالك الرضا بعد القضاء وبرد العيش بعد الموت",
    "اللهم زينا بزينة الايمان واجعلنا هداة مهتدين",
    "رب اوزعني ان اشكر نعمتك التي انعمت علي وعلى والدي",
    "اقرأ القران وارتق ورتل كما كنت ترتل في الدنيا",
    "ان الله وملائكته يصلون على النبي يا ايها الذين امنوا صلوا عليه وسلموا تسليما",
    "واذكر ربك في نفسك تضرعا وخيفة ودون الجهر من القول بالغدو والاصال ولا تكن من الغافلين",
    "الذين امنوا وتطمئن قلوبهم بذكر الله الا بذكر الله تطمئن القلوب",
    "فاذكروني اذكركم واشكروا لي ولا تكفرون",
    "يا ايها الذين امنوا اذكروا الله ذكرا كثيرا وسبحوه بكرة واصيلا",
    "واذكر ربك كثيرا وسبح بالعشي والابكار",
    "ان في خلق السماوات والارض واختلاف الليل والنهار لايات لاولي الالباب",
    "الذين يذكرون الله قياما وقعودا وعلى جنوبهم ويتفكرون في خلق السماوات والارض",
    "ربنا ما خلقت هذا باطلا سبحانك فقنا عذاب النار",
    "والذاكرين الله كثيرا والذاكرات اعد الله لهم مغفرة واجرا عظيما",
    "واصبر نفسك مع الذين يدعون ربهم بالغداة والعشي يريدون وجهه",
    "ولا تطرد الذين يدعون ربهم بالغداة والعشي يريدون وجهه",
    "اللهم رب السماوات ورب الارض ورب العرش العظيم ربنا ورب كل شيء",
    "فالق الحب والنوى منزل التوراة والانجيل والفرقان اعوذ بك من شر كل شيء انت اخذ بناصيته",
    "اللهم انت الاول فليس قبلك شيء وانت الاخر فليس بعدك شيء",
    "وانت الظاهر فليس فوقك شيء وانت الباطن فليس دونك شيء",
    "اقض عنا الدين واغننا من الفقر",
    "اللهم قني عذابك يوم تبعث عبادك",
    "باسمك اللهم اموت واحيا",
    "الحمد لله الذي احيانا بعد ما اماتنا واليه النشور",
    "الحمد لله الذي اطعمنا وسقانا وكفانا واوانا",
    "فكم ممن لا كافي له ولا مأوي",
    "اللهم عالم الغيب والشهادة فاطر السماوات والارض",
    "رب كل شيء ومليكه اشهد ان لا اله الا انت",
    "اعوذ بك من شر نفسي ومن شر الشيطان وشركه",
    "بسم الله الذي لا يضر مع اسمه شيء في الارض ولا في السماء وهو السميع العليم",
    "اللهم انا نسالك العافية في الدنيا والاخرة",
    "اللهم انا نسالك العفو والعافية في ديننا ودنيانا واهلنا ومالنا",
    "اللهم استر عوراتنا وامن روعاتنا",
    "اللهم احفظنا من بين ايدينا ومن خلفنا وعن ايماننا وعن شمائلنا ومن فوقنا",
    "ونعوذ بعظمتك ان نغتال من تحتنا",
    "اللهم انت ربي لا اله الا انت خلقتني وانا عبدك",
    "وانا على عهدك ووعدك ما استطعت اعوذ بك من شر ما صنعت",
    "ابوء لك بنعمتك علي وابوء بذنبي فاغفر لي فانه لا يغفر الذنوب الا انت",
    "رضيت بالله ربا وبالاسلام دينا وبمحمد صلى الله عليه وسلم نبيا",
    "اللهم اني اصبحت اشهدك واشهد حملة عرشك وملائكتك وجميع خلقك",
    "انك انت الله لا اله الا انت وحدك لا شريك لك وان محمدا عبدك ورسولك",
    "يا رب لك الحمد كما ينبغي لجلال وجهك ولعظيم سلطانك",
    "اللهم ما اصبح بي من نعمة او باحد من خلقك فمنك وحدك لا شريك لك",
    "فلك الحمد ولك الشكر"
]

DATA_DIR = "data"
BOTS_FILE = os.path.join(DATA_DIR, "bots.json")
SCHEDULES_FILE = os.path.join(DATA_DIR, "schedules.json")
USER_CHATS_FILE = os.path.join(DATA_DIR, "user_chats.json")
MEMBER_FILE = "member.json"
REMEMBER_FILE = "remember.json"
BANNED_USERS_FILE = os.path.join(DATA_DIR, "banned_users.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json_file(filename, data):
    ensure_data_dir()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_bots_data():
    return load_json_file(BOTS_FILE)

def save_bots_data(data):
    save_json_file(BOTS_FILE, data)

def get_schedules_data():
    return load_json_file(SCHEDULES_FILE)

def save_schedules_data(data):
    save_json_file(SCHEDULES_FILE, data)

def get_member_data():
    return load_json_file(MEMBER_FILE)

def save_member_data(data):
    save_json_file(MEMBER_FILE, data)

def get_remember_data():
    return load_json_file(REMEMBER_FILE)

def save_remember_data(data):
    save_json_file(REMEMBER_FILE, data)

def get_user_chats_data():
    return load_json_file(USER_CHATS_FILE)

def save_user_chats_data(data):
    save_json_file(USER_CHATS_FILE, data)

def get_banned_users_data():
    return load_json_file(BANNED_USERS_FILE)

def save_banned_users_data(data):
    save_json_file(BANNED_USERS_FILE, data)

def add_user_chat(bot_token: str, user_id: int, chat_id: int, chat_title: str, chat_type: str):
    data = get_user_chats_data()
    key = f"{bot_token}_{user_id}"
    if key not in data:
        data[key] = {"channels": [], "groups": []}
    
    chat_info = {"chat_id": chat_id, "title": chat_title}
    list_key = "channels" if chat_type == "channel" else "groups"
    
    existing_ids = [c["chat_id"] for c in data[key][list_key]]
    if chat_id not in existing_ids:
        data[key][list_key].append(chat_info)
        save_user_chats_data(data)

def get_user_chats(bot_token: str, user_id: int, chat_type: str):
    data = get_user_chats_data()
    key = f"{bot_token}_{user_id}"
    if key not in data:
        return []
    list_key = "channels" if chat_type == "channel" else "groups"
    return data[key].get(list_key, [])

running_bot_apps = {}
user_states = {}

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
        [InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("ذكاء اصطناعي", callback_data="create_ai"),
            InlineKeyboardButton("اذكار", callback_data="create_adhkar")
        ],
        [
            InlineKeyboardButton("منع تصفية", callback_data="create_guard")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user is None:
        return
    user_id = user.id
    first_name = user.first_name or "صديقي"
    
    is_subscribed = await check_subscription(user_id, context.bot)
    
    if not is_subscribed:
        text = f"""※ اهلا وسهلا يا {first_name}

يجب عليك الاشتراك في القناة اولا لاستخدام البوت"""
        await update.message.reply_text(text, reply_markup=get_subscription_keyboard())
        return
    
    member_data = get_member_data()
    if str(user_id) not in member_data:
        member_data[str(user_id)] = {
            "first_name": first_name,
            "username": user.username,
            "joined": datetime.now().isoformat(),
            "bots_created": 0
        }
        save_member_data(member_data)
    
    text = f"""※ اهلا وسهلا يا {first_name}

قم باختيار نوع بوتك"""
    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    
    user = query.from_user
    if user is None:
        return
    user_id = user.id
    first_name = user.first_name or "صديقي"
    data = query.data
    
    if data == "check_sub":
        is_subscribed = await check_subscription(user_id, context.bot)
        if is_subscribed:
            text = f"""※ اهلا وسهلا يا {first_name}

قم باختيار نوع بوتك"""
            await query.edit_message_text(text, reply_markup=get_main_menu_keyboard())
        else:
            await query.answer("لم تشترك في القناة بعد", show_alert=True)
        return
    
    if data == "create_ai":
        text = """※ انشاء بوت ذكاء اصطناعي

ارسل توكن البوت الخاص بك
احصل عليه من @BotFather"""
        user_states[user_id] = {'creating': 'ai'}
        keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "create_adhkar":
        text = """※ انشاء بوت اذكار

ارسل توكن البوت الخاص بك
احصل عليه من @BotFather"""
        user_states[user_id] = {'creating': 'adhkar'}
        keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "create_guard":
        text = """※ انشاء بوت منع تصفية

ارسل توكن البوت الخاص بك
احصل عليه من @BotFather"""
        user_states[user_id] = {'creating': 'guard'}
        keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "back_main":
        user_states.pop(user_id, None)
        text = f"""※ اهلا وسهلا يا {first_name}

قم باختيار نوع بوتك"""
        await query.edit_message_text(text, reply_markup=get_main_menu_keyboard())
        return

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    user_id = user.id
    first_name = user.first_name or "صديقي"
    token = message.text.strip() if message.text else ""
    
    logger.info(f"handle_token called by user {user_id}, token starts with: {token[:20] if len(token) > 20 else token}")
    
    is_subscribed = await check_subscription(user_id, context.bot)
    if not is_subscribed:
        logger.info(f"User {user_id} not subscribed")
        await message.reply_text(
            "يجب عليك الاشتراك في القناة اولا",
            reply_markup=get_subscription_keyboard()
        )
        return
    
    user_state = user_states.get(user_id, {})
    creating_type = user_state.get('creating')
    logger.info(f"User {user_id} state: {user_state}, creating_type: {creating_type}")
    if not creating_type:
        return
    
    if not token or ':' not in token:
        await message.reply_text("التوكن غير صالح، حاول مرة اخرى")
        return
    
    try:
        test_bot = Bot(token=token)
        bot_info = await test_bot.get_me()
        bot_username = bot_info.username
        
        member_data = get_member_data()
        if str(user_id) in member_data:
            member_data[str(user_id)]['bots_created'] = member_data[str(user_id)].get('bots_created', 0) + 1
        save_member_data(member_data)
        
        bots_data = get_bots_data()
        bots_data[token] = {
            "type": creating_type,
            "owner_id": user_id,
            "owner_name": first_name,
            "bot_username": bot_username,
            "created": datetime.now().isoformat(),
            "active": True,
            "required_channel": REQUIRED_CHANNEL
        }
        save_bots_data(bots_data)
        
        if creating_type == 'ai':
            asyncio.create_task(start_ai_bot(token, user_id))
            text = f"""※ تم انشاء بوت الذكاء الاصطناعي بنجاح

البوت: @{bot_username}
النوع: ذكاء اصطناعي
المالك: {first_name}

البوت يعمل الان"""
        elif creating_type == 'adhkar':
            asyncio.create_task(start_adhkar_bot(token, user_id))
            text = f"""※ تم انشاء بوت الاذكار بنجاح

البوت: @{bot_username}
النوع: اذكار
المالك: {first_name}

البوت يعمل الان"""
        elif creating_type == 'guard':
            asyncio.create_task(start_guard_bot(token, user_id))
            text = f"""※ تم انشاء بوت منع التصفية بنجاح

البوت: @{bot_username}
النوع: حماية من التصفية
المالك: {first_name}

البوت يعمل الان"""
        else:
            text = "نوع البوت غير معروف"
        
        keyboard = [[InlineKeyboardButton("رجوع للقائمة", callback_data="back_main")]]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        user_states.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        await message.reply_text("حدث خطأ اثناء انشاء البوت\nتأكد من صحة التوكن")

async def developer_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    
    if user.id != DEVELOPER_ID and user.username != DEVELOPER_USERNAME:
        return
    
    bots_data = get_bots_data()
    total_bots = len(bots_data)
    active_bots = sum(1 for b in bots_data.values() if b.get('active', True))
    member_data = get_member_data()
    total_users = len(member_data)
    
    text = f"""※ لوحة تحكم المطور

عدد البوتات المصنوعة: {total_bots}
البوتات النشطة: {active_bots}
عدد المستخدمين: {total_users}

قائمة البوتات:"""
    
    keyboard = []
    for token, bot_data in bots_data.items():
        status = "شغال" if bot_data.get('active', True) else "متوقف"
        bot_name = bot_data.get('bot_username', 'غير معروف')
        bot_type = "ذكاء" if bot_data['type'] == 'ai' else "اذكار"
        short_token = token[:15] + "..."
        keyboard.append([
            InlineKeyboardButton(
                f"{bot_name} - {bot_type} - {status}",
                callback_data=f"toggle_{token[:30]}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("اذاعة للجميع", callback_data="broadcast_all")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_ai_bot(token: str, owner_id: int):
    try:
        app = Application.builder().token(token).build()
        ai_user_states = {}
        
        async def ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            message = update.message
            if user is None or message is None:
                return
            first_name = user.first_name or "صديقي"
            
            bots_data = get_bots_data()
            bot_data = bots_data.get(token, {})
            required_channel = bot_data.get('required_channel', REQUIRED_CHANNEL)
            owner_name = bot_data.get('owner_name', DEVELOPER_USERNAME)
            
            try:
                is_subscribed = await check_subscription(user.id, context.bot)
            except:
                is_subscribed = True
            
            if not is_subscribed:
                keyboard = [
                    [InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{required_channel[1:]}")],
                    [InlineKeyboardButton("تحقق", callback_data="check_sub_ai")]
                ]
                await message.reply_text(
                    f"※ اهلا يا {first_name}\n\nاشترك في القناة اولا",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if user.id == owner_id:
                keyboard = [
                    [
                        InlineKeyboardButton("الاحصائيات 👥", callback_data="ai_stats"),
                        InlineKeyboardButton("لوحة الادمن 🎖️", callback_data="admin_panel")
                    ],
                    [
                        InlineKeyboardButton("حظر مستخدم ❌", callback_data="ban_user"),
                        InlineKeyboardButton("فك حظر مستخدم ✅", callback_data="unban_user")
                    ],
                    [InlineKeyboardButton("اذاعه للكل", callback_data="broadcast")]
                ]
                
                text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🌐
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور @{DEVELOPER_USERNAME}"""
            else:
                keyboard = []
                
                text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🪩
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور {owner_name}
⏎ انا المنافس الوحيد القوي هنا 🏆"""
            
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
        
        async def ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            message = update.message
            if user is None or message is None or message.text is None:
                return
            user_id = str(user.id)
            message_text = message.text
            
            user_state = ai_user_states.get(user.id, {})
            
            if user_state.get('banning') and user.id == owner_id:
                try:
                    ban_id = int(message_text.strip())
                    banned_data = get_banned_users_data()
                    bot_key = f"ai_{token[:20]}"
                    if bot_key not in banned_data:
                        banned_data[bot_key] = []
                    if ban_id not in banned_data[bot_key]:
                        banned_data[bot_key].append(ban_id)
                        save_banned_users_data(banned_data)
                        await message.reply_text(f"✅ تم حظر المستخدم {ban_id} بنجاح")
                    else:
                        await message.reply_text("هذا المستخدم محظور بالفعل")
                except ValueError:
                    await message.reply_text("ارسل ايدي صحيح")
                ai_user_states.pop(user.id, None)
                return
            
            if user_state.get('unbanning') and user.id == owner_id:
                try:
                    unban_id = int(message_text.strip())
                    banned_data = get_banned_users_data()
                    bot_key = f"ai_{token[:20]}"
                    if bot_key in banned_data and unban_id in banned_data[bot_key]:
                        banned_data[bot_key].remove(unban_id)
                        save_banned_users_data(banned_data)
                        await message.reply_text(f"✅ تم فك حظر المستخدم {unban_id} بنجاح")
                    else:
                        await message.reply_text("هذا المستخدم غير محظور")
                except ValueError:
                    await message.reply_text("ارسل ايدي صحيح")
                ai_user_states.pop(user.id, None)
                return
            
            if user_state.get('broadcasting') and user.id == owner_id:
                remember_data = get_remember_data()
                success = 0
                failed = 0
                for uid in remember_data.keys():
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=message_text)
                        success += 1
                    except:
                        failed += 1
                await message.reply_text(f"✅ تم الارسال\nنجح: {success}\nفشل: {failed}")
                ai_user_states.pop(user.id, None)
                return
            
            if user_state.get('changing_channel') and user.id == owner_id:
                new_channel = message_text.strip()
                if new_channel.startswith('@'):
                    bots_data = get_bots_data()
                    if token in bots_data:
                        bots_data[token]['required_channel'] = new_channel
                        save_bots_data(bots_data)
                        await message.reply_text(f"✅ تم تغيير قناة الاشتراك الى {new_channel}")
                    else:
                        await message.reply_text("حدث خطأ")
                else:
                    await message.reply_text("ارسل يوزر القناة بشكل صحيح مثال: @ChannelName")
                ai_user_states.pop(user.id, None)
                return
            
            banned_data = get_banned_users_data()
            bot_key = f"ai_{token[:20]}"
            if bot_key in banned_data and user.id in banned_data[bot_key]:
                await message.reply_text("⛔ انت محظور من استخدام هذا البوت")
                return
            
            if not GROQ_API_KEY:
                await message.reply_text("عذرا، خدمة الذكاء الاصطناعي غير متاحة حاليا")
                return
            
            try:
                remember_data = get_remember_data()
                if user_id not in remember_data:
                    remember_data[user_id] = []
                
                remember_data[user_id].append({
                    "role": "user",
                    "content": message_text
                })
                
                if len(remember_data[user_id]) > 20:
                    remember_data[user_id] = remember_data[user_id][-20:]
                
                client = Groq(api_key=GROQ_API_KEY)
                
                messages = [
                    {"role": "system", "content": "انت مساعد ذكي ومفيد. اجب باللغة العربية بلهجة مصرية واردنية مختلطة. كن ودودا ومساعدا."}
                ]
                messages.extend(remember_data[user_id])
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content or "عذرا، لم استطع الرد"
                
                remember_data[user_id].append({
                    "role": "assistant",
                    "content": ai_response
                })
                save_remember_data(remember_data)
                
                await message.reply_text(ai_response)
                
            except Exception as e:
                logger.error(f"AI Error: {e}")
                await message.reply_text("حدث خطأ، حاول مرة اخرى")
        
        async def ai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            if query is None:
                return
            await query.answer()
            user = query.from_user
            if user is None:
                return
            data = query.data
            
            if data == "check_sub_ai":
                try:
                    is_subscribed = await check_subscription(user.id, context.bot)
                except:
                    is_subscribed = True
                
                if is_subscribed:
                    first_name = user.first_name or "صديقي"
                    bots_data = get_bots_data()
                    bot_data = bots_data.get(token, {})
                    owner_name = bot_data.get('owner_name', DEVELOPER_USERNAME)
                    
                    if user.id == owner_id:
                        keyboard = [
                            [
                                InlineKeyboardButton("الاحصائيات 👥", callback_data="ai_stats"),
                                InlineKeyboardButton("لوحة الادمن 🎖️", callback_data="admin_panel")
                            ],
                            [
                                InlineKeyboardButton("حظر مستخدم ❌", callback_data="ban_user"),
                                InlineKeyboardButton("فك حظر مستخدم ✅", callback_data="unban_user")
                            ],
                            [InlineKeyboardButton("اذاعه للكل", callback_data="broadcast")]
                        ]
                        
                        text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🌐
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور @{DEVELOPER_USERNAME}"""
                    else:
                        keyboard = []
                        
                        text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🪩
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور {owner_name}
⏎ انا المنافس الوحيد القوي هنا 🏆"""
                    
                    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
                else:
                    await query.answer("اشترك في القناة اولا", show_alert=True)
                return
            
            if data == "admin_panel":
                if user.id != owner_id:
                    await query.answer("لوحة الادمن للمالك فقط", show_alert=True)
                    return
                
                keyboard = [
                    [InlineKeyboardButton("اذاعة للمستخدمين", callback_data="broadcast")],
                    [InlineKeyboardButton("تغيير قناة الاشتراك", callback_data="change_channel")],
                    [InlineKeyboardButton("رجوع", callback_data="back_ai")]
                ]
                await query.edit_message_text(
                    "※ لوحة الادمن\n\nاختر من القائمة",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "ai_stats":
                remember_data = get_remember_data()
                total_messages = sum(len(msgs) for msgs in remember_data.values())
                total_users = len(remember_data)
                
                text = f"""※ احصائيات البوت

عدد المستخدمين: {total_users}
عدد الرسائل: {total_messages}"""
                
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_ai")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data == "back_ai":
                first_name = user.first_name or "صديقي"
                bots_data = get_bots_data()
                bot_data = bots_data.get(token, {})
                owner_name = bot_data.get('owner_name', DEVELOPER_USERNAME)
                
                if user.id == owner_id:
                    keyboard = [
                        [
                            InlineKeyboardButton("الاحصائيات 👥", callback_data="ai_stats"),
                            InlineKeyboardButton("لوحة الادمن 🎖️", callback_data="admin_panel")
                        ],
                        [
                            InlineKeyboardButton("حظر مستخدم ❌", callback_data="ban_user"),
                            InlineKeyboardButton("فك حظر مستخدم ✅", callback_data="unban_user")
                        ],
                        [InlineKeyboardButton("اذاعه للكل", callback_data="broadcast")]
                    ]
                    
                    text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🌐
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور @{DEVELOPER_USERNAME}"""
                else:
                    keyboard = []
                    
                    text = f"""※ اهلا وسهلا يا {first_name}

⏎ افضل بوت ذكاء اصطناعي متكامل 🪩
⏎ تقدر تستخدمني بدون حدود
⏎ سرعه القصوي واداء ممتاز 🛸
⏎ المطور {owner_name}
⏎ انا المنافس الوحيد القوي هنا 🏆"""
                
                ai_user_states.pop(user.id, None)
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
                return
            
            if data == "ban_user":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                ai_user_states[user.id] = {'banning': True}
                keyboard = [[InlineKeyboardButton("الغاء", callback_data="back_ai")]]
                await query.edit_message_text(
                    "※ حظر مستخدم\n\nارسل ايدي المستخدم الذي تريد حظره",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "unban_user":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                ai_user_states[user.id] = {'unbanning': True}
                keyboard = [[InlineKeyboardButton("الغاء", callback_data="back_ai")]]
                await query.edit_message_text(
                    "※ فك حظر مستخدم\n\nارسل ايدي المستخدم الذي تريد فك حظره",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "broadcast":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                ai_user_states[user.id] = {'broadcasting': True}
                keyboard = [[InlineKeyboardButton("الغاء", callback_data="cancel_broadcast")]]
                await query.edit_message_text(
                    "ارسل الرسالة اللي عايز تذيعها للجميع",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "change_channel":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                ai_user_states[user.id] = {'changing_channel': True}
                keyboard = [[InlineKeyboardButton("الغاء", callback_data="back_ai")]]
                await query.edit_message_text(
                    "ارسل يوزر القناة الجديدة\nمثال: @ChannelName",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "cancel_broadcast":
                ai_user_states.pop(user.id, None)
                keyboard = [
                    [InlineKeyboardButton("اذاعة للمستخدمين", callback_data="broadcast")],
                    [InlineKeyboardButton("تغيير قناة الاشتراك", callback_data="change_channel")],
                    [InlineKeyboardButton("رجوع", callback_data="back_ai")]
                ]
                await query.edit_message_text(
                    "※ لوحة الادمن\n\nاختر من القائمة",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        
        async def ai_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            message = update.message
            if message is None:
                return
            user = message.from_user
            if user is None:
                return
            
            user_id = str(user.id)
            
            banned_data = get_banned_users_data()
            bot_key = f"ai_{token[:20]}"
            if bot_key in banned_data and user.id in banned_data[bot_key]:
                await message.reply_text("⛔ انت محظور من استخدام هذا البوت")
                return
            
            if not GROQ_API_KEY:
                await message.reply_text("عذرا، خدمة الذكاء الاصطناعي غير متاحة حاليا")
                return
            
            try:
                photo = message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                photo_bytes = await file.download_as_bytearray()
                
                photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                
                caption = message.caption or "وصف الصورة دي وحللها"
                
                client = Groq(api_key=GROQ_API_KEY)
                
                messages = [
                    {"role": "system", "content": "انت مساعد ذكي ومفيد متخصص في تحليل الصور. اجب باللغة العربية بلهجة مصرية واردنية مختلطة. كن ودودا ومساعدا. حلل الصور بدقة ووضوح."},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": caption
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{photo_base64}"
                                }
                            }
                        ]
                    }
                ]
                
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content or "عذرا، لم استطع تحليل الصورة"
                
                remember_data = get_remember_data()
                if user_id not in remember_data:
                    remember_data[user_id] = []
                remember_data[user_id].append({"role": "user", "content": f"[صورة] {caption}"})
                remember_data[user_id].append({"role": "assistant", "content": ai_response})
                if len(remember_data[user_id]) > 20:
                    remember_data[user_id] = remember_data[user_id][-20:]
                save_remember_data(remember_data)
                
                await message.reply_text(ai_response)
                
            except Exception as e:
                logger.error(f"AI Photo Error: {e}")
                await message.reply_text("حدث خطأ في تحليل الصورة، حاول مرة اخرى")
        
        app.add_handler(CommandHandler('start', ai_start))
        app.add_handler(CallbackQueryHandler(ai_callback))
        app.add_handler(MessageHandler(filters.PHOTO, ai_photo_message))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message))
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        running_bot_apps[token] = app
        logger.info(f"AI Bot started successfully")
        
    except Exception as e:
        logger.error(f"Error starting AI bot: {e}")

def get_guard_data():
    try:
        with open('guard_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_guard_data(data):
    with open('guard_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_guard_admins():
    try:
        with open('guard_admins.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_guard_admins(data):
    with open('guard_admins.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_kick_counts():
    try:
        with open('kick_counts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_kick_counts(data):
    with open('kick_counts.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start_guard_bot(token: str, owner_id: int):
    try:
        app = Application.builder().token(token).build()
        guard_user_states = {}
        
        async def guard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            message = update.message
            if user is None or message is None:
                return
            first_name = user.first_name or "صديقي"
            
            bots_data = get_bots_data()
            bot_data = bots_data.get(token, {})
            bot_username = bot_data.get('bot_username', 'Bot')
            
            guard_data = get_guard_data()
            bot_key = f"guard_{token[:20]}"
            if bot_key not in guard_data:
                guard_data[bot_key] = {
                    'kick_limit': 5,
                    'channels': [],
                    'groups': [],
                    'users': []
                }
                save_guard_data(guard_data)
            
            if str(user.id) not in guard_data[bot_key].get('users', []):
                guard_data[bot_key]['users'] = guard_data[bot_key].get('users', []) + [str(user.id)]
                save_guard_data(guard_data)
            
            channels_count = len(guard_data[bot_key].get('channels', []))
            groups_count = len(guard_data[bot_key].get('groups', []))
            users_count = len(guard_data[bot_key].get('users', []))
            
            if user.id == owner_id:
                keyboard = [
                    [InlineKeyboardButton("قسم التحكم بالبوت", callback_data="guard_control")]
                ]
                
                text = f"""※ اهلا وسهلا يا مطور {first_name}

⏎ انا اعمل الان - im Just Work ✅
⏎ عدد القنوات : {channels_count}
⏎ عدد المجموعات : {groups_count}
⏎ عدد الاعضاء : {users_count}"""
            else:
                keyboard = [
                    [InlineKeyboardButton("اضف البوت الي مجموعتك ✅", url=f"https://t.me/{bot_username}?startgroup=true")]
                ]
                
                text = f"""※ اهلا وسهلا يا {first_name}

⏎ بوت حماية المجموعات والقنوات من المخربين ✅

⏎ فقط ارفع البوت بداخل قناتك او مجموعتك وسيتم تفعيل البوت تلقائيا

⏎ تاكد اعطائي صلاحيات للاستخدام السليم

⏎ المطور @{DEVELOPER_USERNAME}
⏎ الدعم @TepthonHelp"""
            
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        async def guard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            if query is None:
                return
            await query.answer()
            user = query.from_user
            if user is None:
                return
            data = query.data
            first_name = user.first_name or "صديقي"
            
            guard_data = get_guard_data()
            bot_key = f"guard_{token[:20]}"
            if bot_key not in guard_data:
                guard_data[bot_key] = {'kick_limit': 5, 'channels': [], 'groups': [], 'users': []}
            
            channels_count = len(guard_data[bot_key].get('channels', []))
            groups_count = len(guard_data[bot_key].get('groups', []))
            users_count = len(guard_data[bot_key].get('users', []))
            kick_limit = guard_data[bot_key].get('kick_limit', 5)
            
            if data == "guard_control":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                keyboard = [
                    [
                        InlineKeyboardButton("الاحصائيات 📊", callback_data="guard_stats"),
                        InlineKeyboardButton("تغيير حد التصفية ⚙️", callback_data="change_kick_limit")
                    ],
                    [
                        InlineKeyboardButton("المشرفين المسجلين 👥", callback_data="list_admins"),
                        InlineKeyboardButton("اذاعة للكل 📢", callback_data="guard_broadcast")
                    ],
                    [InlineKeyboardButton("رجوع", callback_data="guard_back")]
                ]
                
                text = f"""※ لوحة التحكم

⏎ حد التصفية الحالي: {kick_limit} طرد
⏎ عدد القنوات: {channels_count}
⏎ عدد المجموعات: {groups_count}
⏎ عدد المستخدمين: {users_count}"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data == "guard_stats":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="guard_control")]]
                
                text = f"""※ احصائيات البوت

⏎ عدد القنوات: {channels_count}
⏎ عدد المجموعات: {groups_count}
⏎ عدد المستخدمين: {users_count}
⏎ حد التصفية: {kick_limit} طرد"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data == "change_kick_limit":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                keyboard = [
                    [
                        InlineKeyboardButton("3", callback_data="set_limit_3"),
                        InlineKeyboardButton("5", callback_data="set_limit_5"),
                        InlineKeyboardButton("10", callback_data="set_limit_10")
                    ],
                    [
                        InlineKeyboardButton("15", callback_data="set_limit_15"),
                        InlineKeyboardButton("20", callback_data="set_limit_20")
                    ],
                    [InlineKeyboardButton("رجوع", callback_data="guard_control")]
                ]
                
                text = f"""※ تغيير حد التصفية

الحد الحالي: {kick_limit} طرد

اختر الحد الجديد:"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data.startswith("set_limit_"):
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                new_limit = int(data.split("_")[2])
                guard_data[bot_key]['kick_limit'] = new_limit
                save_guard_data(guard_data)
                
                await query.answer(f"تم تغيير الحد الى {new_limit}", show_alert=True)
                
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="guard_control")]]
                await query.edit_message_text(
                    f"✅ تم تغيير حد التصفية الى {new_limit} طرد",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "list_admins":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                admins_data = get_guard_admins()
                admin_key = f"admins_{token[:20]}"
                admins = admins_data.get(admin_key, {})
                
                if not admins:
                    text = "※ لا يوجد مشرفين مسجلين بعد"
                else:
                    text = "※ المشرفين المسجلين:\n\n"
                    for chat_id, chat_admins in admins.items():
                        text += f"📍 {chat_id}:\n"
                        for admin_id in chat_admins:
                            text += f"  - {admin_id}\n"
                
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="guard_control")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data == "guard_broadcast":
                if user.id != owner_id:
                    await query.answer("للمالك فقط", show_alert=True)
                    return
                
                guard_user_states[user.id] = {'broadcasting': True}
                keyboard = [[InlineKeyboardButton("الغاء", callback_data="guard_control")]]
                await query.edit_message_text(
                    "ارسل الرسالة اللي عايز تذيعها للجميع",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            if data == "guard_back":
                bots_data = get_bots_data()
                bot_data = bots_data.get(token, {})
                bot_username = bot_data.get('bot_username', 'Bot')
                
                if user.id == owner_id:
                    keyboard = [
                        [InlineKeyboardButton("قسم التحكم بالبوت", callback_data="guard_control")]
                    ]
                    
                    text = f"""※ اهلا وسهلا يا مطور {first_name}

⏎ انا اعمل الان - im Just Work ✅
⏎ عدد القنوات : {channels_count}
⏎ عدد المجموعات : {groups_count}
⏎ عدد الاعضاء : {users_count}"""
                else:
                    keyboard = [
                        [InlineKeyboardButton("اضف البوت الي مجموعتك ✅", url=f"https://t.me/{bot_username}?startgroup=true")]
                    ]
                    
                    text = f"""※ اهلا وسهلا يا {first_name}

⏎ بوت حماية المجموعات والقنوات من المخربين ✅

⏎ فقط ارفع البوت بداخل قناتك او مجموعتك وسيتم تفعيل البوت تلقائيا

⏎ تاكد اعطائي صلاحيات للاستخدام السليم

⏎ المطور @{DEVELOPER_USERNAME}
⏎ الدعم @TepthonHelp"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
        
        async def guard_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            message = update.message
            if message is None:
                return
            user = message.from_user
            if user is None:
                return
            
            message_text = message.text or ""
            chat = message.chat
            
            user_state = guard_user_states.get(user.id, {})
            if user_state.get('broadcasting') and user.id == owner_id:
                guard_data = get_guard_data()
                bot_key = f"guard_{token[:20]}"
                users = guard_data.get(bot_key, {}).get('users', [])
                
                success = 0
                failed = 0
                for uid in users:
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=message_text)
                        success += 1
                    except:
                        failed += 1
                
                await message.reply_text(f"✅ تم الارسال\nنجح: {success}\nفشل: {failed}")
                guard_user_states.pop(user.id, None)
                return
            
            if chat.type in ['group', 'supergroup']:
                if message_text.startswith("رفع مشرف"):
                    chat_member = await context.bot.get_chat_member(chat.id, user.id)
                    if chat_member.status not in ['creator', 'administrator']:
                        return
                    
                    target_id = None
                    target_name = None
                    
                    if message.reply_to_message:
                        target_user = message.reply_to_message.from_user
                        if target_user:
                            target_id = target_user.id
                            target_name = target_user.first_name
                    else:
                        parts = message_text.split()
                        if len(parts) >= 3:
                            target = parts[2]
                            if target.startswith('@'):
                                target_name = target
                                try:
                                    target_chat = await context.bot.get_chat(target)
                                    target_id = target_chat.id
                                except:
                                    await message.reply_text("لم استطع العثور على هذا المستخدم")
                                    return
                            else:
                                try:
                                    target_id = int(target)
                                    target_name = str(target_id)
                                except:
                                    await message.reply_text("ارسل ايدي صحيح او معرف او رد على رسالة المستخدم")
                                    return
                    
                    if target_id is None:
                        await message.reply_text("رد على رسالة المستخدم او ارسل المعرف/الايدي")
                        return
                    
                    admins_data = get_guard_admins()
                    admin_key = f"admins_{token[:20]}"
                    if admin_key not in admins_data:
                        admins_data[admin_key] = {}
                    
                    chat_key = str(chat.id)
                    if chat_key not in admins_data[admin_key]:
                        admins_data[admin_key][chat_key] = []
                    
                    if target_id not in admins_data[admin_key][chat_key]:
                        admins_data[admin_key][chat_key].append(target_id)
                        save_guard_admins(admins_data)
                        await message.reply_text(f"✅ تم رفع {target_name} كمشرف مراقب")
                    else:
                        await message.reply_text("هذا المستخدم مشرف مراقب بالفعل")
                    return
                
                if message_text.startswith("تنزيل مشرف"):
                    chat_member = await context.bot.get_chat_member(chat.id, user.id)
                    if chat_member.status not in ['creator', 'administrator']:
                        return
                    
                    target_id = None
                    target_name = None
                    
                    if message.reply_to_message:
                        target_user = message.reply_to_message.from_user
                        if target_user:
                            target_id = target_user.id
                            target_name = target_user.first_name
                    else:
                        parts = message_text.split()
                        if len(parts) >= 3:
                            target = parts[2]
                            if target.startswith('@'):
                                target_name = target
                                try:
                                    target_chat = await context.bot.get_chat(target)
                                    target_id = target_chat.id
                                except:
                                    await message.reply_text("لم استطع العثور على هذا المستخدم")
                                    return
                            else:
                                try:
                                    target_id = int(target)
                                    target_name = str(target_id)
                                except:
                                    await message.reply_text("ارسل ايدي صحيح او معرف او رد على رسالة المستخدم")
                                    return
                    
                    if target_id is None:
                        await message.reply_text("رد على رسالة المستخدم او ارسل المعرف/الايدي")
                        return
                    
                    admins_data = get_guard_admins()
                    admin_key = f"admins_{token[:20]}"
                    chat_key = str(chat.id)
                    
                    if admin_key in admins_data and chat_key in admins_data[admin_key]:
                        if target_id in admins_data[admin_key][chat_key]:
                            admins_data[admin_key][chat_key].remove(target_id)
                            save_guard_admins(admins_data)
                            
                            kick_data = get_kick_counts()
                            kick_key = f"{token[:20]}_{chat.id}_{target_id}"
                            if kick_key in kick_data:
                                del kick_data[kick_key]
                                save_kick_counts(kick_data)
                            
                            await message.reply_text(f"✅ تم تنزيل {target_name} من المشرفين المراقبين")
                        else:
                            await message.reply_text("هذا المستخدم ليس مشرف مراقب")
                    else:
                        await message.reply_text("لا يوجد مشرفين مسجلين")
                    return
        
        async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_member_update = update.chat_member
            if chat_member_update is None:
                return
            
            chat = chat_member_update.chat
            old_status = chat_member_update.old_chat_member.status
            new_status = chat_member_update.new_chat_member.status
            kicked_by = chat_member_update.from_user
            kicked_user = chat_member_update.new_chat_member.user
            
            if new_status in ['kicked', 'left'] and old_status in ['member', 'administrator', 'creator']:
                if kicked_by and kicked_by.id != kicked_user.id:
                    admins_data = get_guard_admins()
                    admin_key = f"admins_{token[:20]}"
                    chat_key = str(chat.id)
                    
                    if admin_key in admins_data and chat_key in admins_data[admin_key]:
                        if kicked_by.id in admins_data[admin_key][chat_key]:
                            guard_data = get_guard_data()
                            bot_key = f"guard_{token[:20]}"
                            kick_limit = guard_data.get(bot_key, {}).get('kick_limit', 5)
                            
                            kick_data = get_kick_counts()
                            kick_key = f"{token[:20]}_{chat.id}_{kicked_by.id}"
                            
                            current_kicks = kick_data.get(kick_key, 0) + 1
                            kick_data[kick_key] = current_kicks
                            save_kick_counts(kick_data)
                            
                            if current_kicks >= kick_limit:
                                try:
                                    await context.bot.promote_chat_member(
                                        chat_id=chat.id,
                                        user_id=kicked_by.id,
                                        can_manage_chat=False,
                                        can_delete_messages=False,
                                        can_restrict_members=False,
                                        can_promote_members=False,
                                        can_change_info=False,
                                        can_invite_users=False,
                                        can_pin_messages=False
                                    )
                                    
                                    if kicked_by.id in admins_data[admin_key][chat_key]:
                                        admins_data[admin_key][chat_key].remove(kicked_by.id)
                                        save_guard_admins(admins_data)
                                    
                                    kick_data[kick_key] = 0
                                    save_kick_counts(kick_data)
                                    
                                    await context.bot.send_message(
                                        chat_id=chat.id,
                                        text=f"⚠️ تم تنزيل {kicked_by.first_name} من الاشراف\nالسبب: تجاوز حد التصفية ({kick_limit} طرد)"
                                    )
                                    
                                    try:
                                        await context.bot.send_message(
                                            chat_id=owner_id,
                                            text=f"⚠️ تنبيه!\n\nتم تنزيل {kicked_by.first_name} (ID: {kicked_by.id})\nمن مجموعة: {chat.title}\nالسبب: تجاوز حد التصفية ({kick_limit})"
                                        )
                                    except:
                                        pass
                                    
                                except Exception as e:
                                    logger.error(f"Error demoting admin: {e}")
                                    await context.bot.send_message(
                                        chat_id=chat.id,
                                        text=f"⚠️ {kicked_by.first_name} تجاوز حد التصفية ({current_kicks}/{kick_limit})\nلكن لا استطيع تنزيله، تأكد من صلاحياتي"
                                    )
                            else:
                                remaining = kick_limit - current_kicks
                                await context.bot.send_message(
                                    chat_id=chat.id,
                                    text=f"⚠️ تحذير: {kicked_by.first_name} قام بطرد عضو\nعدد الطرد: {current_kicks}/{kick_limit}\nمتبقي: {remaining}"
                                )
        
        async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
            my_chat_member = update.my_chat_member
            if my_chat_member is None:
                return
            
            chat = my_chat_member.chat
            new_status = my_chat_member.new_chat_member.status
            
            guard_data = get_guard_data()
            bot_key = f"guard_{token[:20]}"
            if bot_key not in guard_data:
                guard_data[bot_key] = {'kick_limit': 5, 'channels': [], 'groups': [], 'users': []}
            
            if new_status in ['administrator', 'member']:
                if chat.type == 'channel':
                    if str(chat.id) not in guard_data[bot_key].get('channels', []):
                        guard_data[bot_key]['channels'] = guard_data[bot_key].get('channels', []) + [str(chat.id)]
                elif chat.type in ['group', 'supergroup']:
                    if str(chat.id) not in guard_data[bot_key].get('groups', []):
                        guard_data[bot_key]['groups'] = guard_data[bot_key].get('groups', []) + [str(chat.id)]
                save_guard_data(guard_data)
            elif new_status in ['left', 'kicked']:
                if str(chat.id) in guard_data[bot_key].get('channels', []):
                    guard_data[bot_key]['channels'].remove(str(chat.id))
                if str(chat.id) in guard_data[bot_key].get('groups', []):
                    guard_data[bot_key]['groups'].remove(str(chat.id))
                save_guard_data(guard_data)
        
        from telegram.ext import ChatMemberHandler
        
        app.add_handler(CommandHandler('start', guard_start))
        app.add_handler(CallbackQueryHandler(guard_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guard_message))
        app.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))
        app.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
        
        running_bot_apps[token] = app
        logger.info(f"Guard Bot started successfully")
        
    except Exception as e:
        logger.error(f"Error starting Guard bot: {e}")

async def send_adhkar_to_chat(bot_token: str, chat_id: int):
    try:
        bot = Bot(token=bot_token)
        dhikr = random.choice(ADHKAR_LIST)
        await bot.send_message(chat_id=chat_id, text=dhikr)
        logger.info(f"Sent adhkar to chat {chat_id}")
    except Exception as e:
        logger.error(f"Error sending adhkar to {chat_id}: {e}")

def sync_send_adhkar(bot_token: str, chat_id: int):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(send_adhkar_to_chat(bot_token, chat_id))
        else:
            loop.run_until_complete(send_adhkar_to_chat(bot_token, chat_id))
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(send_adhkar_to_chat(bot_token, chat_id))

def register_adhkar_job(bot_token: str, chat_id: int, interval: int, end_date: datetime = None):
    job_id = f"adhkar_{bot_token[:10]}_{chat_id}"
    
    try:
        main_scheduler.remove_job(job_id)
    except JobLookupError:
        pass
    
    if end_date is None:
        main_scheduler.add_job(
            sync_send_adhkar,
            'interval',
            minutes=interval,
            id=job_id,
            args=[bot_token, chat_id]
        )
    else:
        main_scheduler.add_job(
            sync_send_adhkar,
            'interval',
            minutes=interval,
            id=job_id,
            args=[bot_token, chat_id],
            end_date=end_date
        )
    
    logger.info(f"Registered adhkar job for chat {chat_id} every {interval} minutes")
    return job_id

def schedule_adhkar(bot_token: str, chat_id: int, interval: int, duration: int = 0):
    if duration == 0:
        end_date = None
        end_date_str = None
    else:
        end_date = datetime.now() + timedelta(days=duration)
        end_date_str = end_date.isoformat()
    
    job_id = register_adhkar_job(bot_token, chat_id, interval, end_date)
    
    schedules_data = get_schedules_data()
    schedules_data[job_id] = {
        "bot_token": bot_token,
        "chat_id": chat_id,
        "interval": interval,
        "created": datetime.now().isoformat(),
        "end_date": end_date_str
    }
    save_schedules_data(schedules_data)
    
    logger.info(f"Scheduled adhkar for chat {chat_id} every {interval} minutes")

def restore_schedules():
    schedules_data = get_schedules_data()
    now = datetime.now()
    expired_jobs = []
    
    for job_id, schedule in schedules_data.items():
        end_date_str = schedule.get('end_date')
        end_date = None
        
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
            if end_date < now:
                expired_jobs.append(job_id)
                logger.info(f"Schedule {job_id} expired, removing")
                continue
        
        try:
            bot_token = schedule['bot_token']
            chat_id = schedule['chat_id']
            interval = schedule['interval']
            
            register_adhkar_job(bot_token, chat_id, interval, end_date)
            logger.info(f"Restored schedule for chat {chat_id}")
        except Exception as e:
            logger.error(f"Error restoring schedule {job_id}: {e}")
    
    if expired_jobs:
        for job_id in expired_jobs:
            del schedules_data[job_id]
        save_schedules_data(schedules_data)

async def start_adhkar_bot(token: str, owner_id: int):
    try:
        app = Application.builder().token(token).build()
        adhkar_user_states = {}
        
        async def adhkar_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            message = update.message
            if user is None or message is None:
                return
            first_name = user.first_name or "صديقي"
            
            keyboard = [
                [
                    InlineKeyboardButton("اعدادات قناتك", callback_data="channel_settings"),
                    InlineKeyboardButton("اعدادات مجموعتك", callback_data="group_settings")
                ],
                [InlineKeyboardButton("اضف البوت الى مجموعتك 🎖️", callback_data="add_info")]
            ]
            
            text = f"""※ ياهلا وسهلا يا {first_name} في بوت أذكاري 📿

⏎ بوت مخصص لنشر :
•  الأذكار والأدعية
• الأحاديث النبوية
• الأسئلة الدينية والقرانية 📿 
• آيات من القرآن الكريم 📖 

⏎ يعمل تلقائيًا داخل المجموعات والقنوات، ويُرسل المحتوى بشكل منظم علي حسب الإعدادات .

※ للإعدادات والتحكم الكامل، استخدم الأزرار بالأسفل"""
            
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        async def adhkar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            if query is None:
                return
            await query.answer()
            user = query.from_user
            if user is None:
                return
            data = query.data
            
            if data == "add_info":
                text = """※ طريقة الاضافة

1- اضف البوت للقناة او المجموعة كمشرف
2- اعطه صلاحية ارسال الرسائل
3- ارجع هنا واختر اعدادات قناتك او مجموعتك"""
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_adhkar")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data in ["channel_settings", "group_settings"]:
                setting_type = 'channel' if data == "channel_settings" else 'group'
                chat_type = "قناتك" if data == "channel_settings" else "مجموعتك"
                adhkar_user_states[user.id] = {'setting_type': setting_type}
                
                user_chats = get_user_chats(token, user.id, setting_type)
                
                keyboard = []
                if user_chats:
                    for chat in user_chats:
                        keyboard.append([InlineKeyboardButton(
                            f"📌 {chat['title']}", 
                            callback_data=f"manage_{chat['chat_id']}"
                        )])
                
                keyboard.append([InlineKeyboardButton("➕ اضافة جديدة", callback_data=f"add_new_{setting_type}")])
                keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_adhkar")])
                
                if user_chats:
                    text = f"""※ اعدادات {chat_type}

اختر من القائمة او اضف جديدة"""
                else:
                    text = f"""※ اعدادات {chat_type}

لا توجد لديك {chat_type} مضافة
اضغط على اضافة جديدة لاضافة واحدة"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data.startswith("add_new_"):
                setting_type = data.replace("add_new_", "")
                chat_type = "قناتك" if setting_type == "channel" else "مجموعتك"
                adhkar_user_states[user.id] = {'setting_type': setting_type, 'adding_new': True}
                
                text = f"""※ اضافة {chat_type}

ارسل ايدي {chat_type} او فورورد رسالة منها
للحصول على الايدي استخدم @username_to_id_bot"""
                keyboard = [[InlineKeyboardButton("رجوع", callback_data="back_adhkar")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data.startswith("manage_"):
                chat_id = int(data.replace("manage_", ""))
                try:
                    chat = await context.bot.get_chat(chat_id)
                    chat_title = chat.title or "غير معروف"
                except:
                    await query.answer("تعذر الوصول للمحادثة", show_alert=True)
                    return
                
                keyboard = [
                    [
                        InlineKeyboardButton("5 دقايق", callback_data=f"interval_{chat_id}_5"),
                        InlineKeyboardButton("ربع ساعة", callback_data=f"interval_{chat_id}_15")
                    ],
                    [
                        InlineKeyboardButton("ساعة", callback_data=f"interval_{chat_id}_60"),
                        InlineKeyboardButton("ساعتين", callback_data=f"interval_{chat_id}_120")
                    ],
                    [
                        InlineKeyboardButton("3 ساعات", callback_data=f"interval_{chat_id}_180"),
                        InlineKeyboardButton("4 ساعات", callback_data=f"interval_{chat_id}_240")
                    ],
                    [InlineKeyboardButton("رجوع", callback_data="back_adhkar")]
                ]
                
                text = f"""※ اعدادات: {chat_title}

اختر كل قد ايه تنشر الاذكار"""
                
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data == "back_adhkar":
                adhkar_user_states.pop(user.id, None)
                first_name = user.first_name or "صديقي"
                keyboard = [
                    [
                        InlineKeyboardButton("اعدادات قناتك", callback_data="channel_settings"),
                        InlineKeyboardButton("اعدادات مجموعتك", callback_data="group_settings")
                    ],
                    [InlineKeyboardButton("اضف البوت الى مجموعتك 🎖️", callback_data="add_info")]
                ]
                text = f"""※ ياهلا وسهلا يا {first_name} في بوت أذكاري 📿

⏎ بوت مخصص لنشر :
•  الأذكار والأدعية
• الأحاديث النبوية
• الأسئلة الدينية والقرانية 📿 
• آيات من القرآن الكريم 📖 

⏎ يعمل تلقائيًا داخل المجموعات والقنوات، ويُرسل المحتوى بشكل منظم علي حسب الإعدادات .

※ للإعدادات والتحكم الكامل، استخدم الأزرار بالأسفل"""
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data.startswith("interval_"):
                parts = data.split("_")
                chat_id = parts[1]
                interval = int(parts[2])
                
                duration_text = {
                    5: "5 دقايق",
                    15: "ربع ساعة",
                    60: "ساعة",
                    120: "ساعتين",
                    180: "3 ساعات",
                    240: "4 ساعات"
                }.get(interval, f"{interval} دقيقة")
                
                adhkar_user_states[user.id] = {
                    'pending_schedule': {
                        'chat_id': int(chat_id),
                        'interval': interval
                    }
                }
                
                keyboard = [
                    [
                        InlineKeyboardButton("يوم", callback_data=f"duration_{chat_id}_{interval}_1"),
                        InlineKeyboardButton("اسبوع", callback_data=f"duration_{chat_id}_{interval}_7")
                    ],
                    [InlineKeyboardButton("دائم", callback_data=f"duration_{chat_id}_{interval}_0")],
                    [InlineKeyboardButton("رجوع", callback_data="back_adhkar")]
                ]
                
                text = f"""※ اختر مدة النشر

الفترة: كل {duration_text}

اختر كم يوم تريد النشر"""
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                return
            
            if data.startswith("duration_"):
                parts = data.split("_")
                chat_id = int(parts[1])
                interval = int(parts[2])
                duration = int(parts[3])
                
                schedule_adhkar(token, chat_id, interval, duration)
                
                interval_text = {
                    5: "5 دقايق",
                    15: "ربع ساعة",
                    60: "ساعة",
                    120: "ساعتين",
                    180: "3 ساعات",
                    240: "4 ساعات"
                }.get(interval, f"{interval} دقيقة")
                
                duration_text = "دائم" if duration == 0 else (f"{duration} يوم" if duration == 1 else f"{duration} ايام")
                
                text = f"""※ تم تفعيل النشر بنجاح

الفترة: كل {interval_text}
المدة: {duration_text}

سيتم نشر الاذكار تلقائيا"""
                
                keyboard = [[InlineKeyboardButton("رجوع للقائمة", callback_data="back_adhkar")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
                adhkar_user_states.pop(user.id, None)
                return
        
        async def adhkar_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            message = update.message
            if user is None or message is None:
                return
            
            user_state = adhkar_user_states.get(user.id, {})
            if not user_state.get('setting_type'):
                return
            
            chat_id = None
            
            if message.forward_origin:
                try:
                    if hasattr(message.forward_origin, 'chat'):
                        chat_id = message.forward_origin.chat.id
                except:
                    pass
            
            if chat_id is None and message.text:
                try:
                    chat_id = int(message.text.strip())
                except:
                    await message.reply_text("ارسل ايدي صحيح او فورورد رسالة من القناة/المجموعة")
                    return
            
            if chat_id is None:
                await message.reply_text("ارسل ايدي صحيح او فورورد رسالة من القناة/المجموعة")
                return
            
            try:
                chat = await context.bot.get_chat(chat_id)
                chat_title = chat.title or "غير معروف"
            except:
                await message.reply_text("تأكد ان البوت مضاف للقناة/المجموعة كمشرف")
                return
            
            setting_type = user_state.get('setting_type')
            add_user_chat(token, user.id, chat_id, chat_title, setting_type)
            
            keyboard = [
                [
                    InlineKeyboardButton("5 دقايق", callback_data=f"interval_{chat_id}_5"),
                    InlineKeyboardButton("ربع ساعة", callback_data=f"interval_{chat_id}_15")
                ],
                [
                    InlineKeyboardButton("ساعة", callback_data=f"interval_{chat_id}_60"),
                    InlineKeyboardButton("ساعتين", callback_data=f"interval_{chat_id}_120")
                ],
                [
                    InlineKeyboardButton("3 ساعات", callback_data=f"interval_{chat_id}_180"),
                    InlineKeyboardButton("4 ساعات", callback_data=f"interval_{chat_id}_240")
                ],
                [InlineKeyboardButton("رجوع", callback_data="back_adhkar")]
            ]
            
            text = f"""※ تم التعرف على: {chat_title}

اختر كل قد ايه تنشر الاذكار"""
            
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            adhkar_user_states.pop(user.id, None)
        
        app.add_handler(CommandHandler('start', adhkar_start))
        app.add_handler(CallbackQueryHandler(adhkar_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, adhkar_message))
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        running_bot_apps[token] = app
        logger.info(f"Adhkar Bot started successfully")
        
    except Exception as e:
        logger.error(f"Error starting Adhkar bot: {e}")

async def restore_bots():
    bots_data = get_bots_data()
    for token, bot_data in bots_data.items():
        if not bot_data.get('active', True):
            continue
        try:
            bot_type = bot_data.get('type')
            owner_id = bot_data.get('owner_id')
            if bot_type == 'ai':
                asyncio.create_task(start_ai_bot(token, owner_id))
            elif bot_type == 'adhkar':
                asyncio.create_task(start_adhkar_bot(token, owner_id))
            elif bot_type == 'guard':
                asyncio.create_task(start_guard_bot(token, owner_id))
            logger.info(f"Restored bot: {bot_data.get('bot_username')}")
        except Exception as e:
            logger.error(f"Error restoring bot: {e}")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    if query is None:
        return
    
    from telegram import InlineQueryResultArticle, InputTextMessageContent
    import uuid
    
    bot_me = await context.bot.get_me()
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="انشاء بوت ذكاء اصطناعي",
            description="اضغط لارسال رابط المصنع",
            input_message_content=InputTextMessageContent(
                f"※ مصنع البوتات\n\nابدأ الان وانشئ بوتك الخاص\n@{bot_me.username}"
            )
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="انشاء بوت اذكار",
            description="اضغط لارسال رابط المصنع",
            input_message_content=InputTextMessageContent(
                f"※ مصنع البوتات\n\nابدأ الان وانشئ بوتك الخاص\n@{bot_me.username}"
            )
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="انشاء بوت منع تصفية",
            description="حماية مجموعتك من المخربين",
            input_message_content=InputTextMessageContent(
                f"※ مصنع البوتات\n\nابدأ الان وانشئ بوتك الخاص\n@{bot_me.username}"
            )
        )
    ]
    
    await query.answer(results, cache_time=300)

@flask_app.route('/')
def index():
    return "Bot is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    ensure_data_dir()
    
    if not os.path.exists(MEMBER_FILE):
        save_member_data({})
    if not os.path.exists(REMEMBER_FILE):
        save_remember_data({})
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    if not main_scheduler.running:
        main_scheduler.start()
    
    restore_schedules()
    await restore_bots()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', developer_panel))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^التحكم$'), developer_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))
    
    logger.info("Starting main bot...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Bot started successfully!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
