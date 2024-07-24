import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, Order, OrderStatus, read_data
from add_order import add_order
from telegram_bot_translation import get_translation, LANGUAGES  # Custom translation module to handle translations

# Telegram bot token
TOKEN = '7447231078:AAFOZU4vSUdMvinjFqQekzglFkVyFEdv_ys'

# States for ConversationHandler
LANGUAGE, ADMIN_ACTIONS, ADD_ORDER_URL, ADD_ORDER_COMMENTS, ADD_ADMIN, ADD_USER_USERNAME, ADD_USER_PASSWORD, SHOWING_LIST = range(8)

# Load admin data
if os.path.exists('admins.json'):
    with open('admins.json', 'r') as f:
        admins = json.load(f)
else:
    admins = {'main_admin': ['main_admin_username'], 'order_admin': []}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data['username'] = user.username
    context.user_data['is_main_admin'] = user.username in admins['main_admin']
    context.user_data['is_order_admin'] = user.username in admins['order_admin']
    print(user.username)
    if not context.user_data['is_main_admin'] and not context.user_data['is_order_admin']:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='english')],
        [InlineKeyboardButton("🇮🇷 Farsi", callback_data='farsi')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 Please select your language:", reply_markup=reply_markup)
    
    return LANGUAGE

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    language = query.data
    context.user_data['language'] = language

    await show_admin_actions(update, context)

    return ADMIN_ACTIONS

async def show_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    keyboard = []

    if user_data['is_main_admin']:
        keyboard.extend([
            [InlineKeyboardButton("➕ " + get_translation("Add Order", user_data['language']), callback_data='add_order')],
            [InlineKeyboardButton("👤 " + get_translation("Add Admin", user_data['language']), callback_data='add_admin')],
            [InlineKeyboardButton("👥 " + get_translation("Add User", user_data['language']), callback_data='add_user')],
            [InlineKeyboardButton("📋 " + get_translation("List Admins", user_data['language']), callback_data='list_admins')],
            [InlineKeyboardButton("📋 " + get_translation("List Orders", user_data['language']), callback_data='list_orders')],
            [InlineKeyboardButton("📋 " + get_translation("List Accounts", user_data['language']), callback_data='list_accounts')],
        ])
    elif user_data['is_order_admin']:
        keyboard.append([InlineKeyboardButton("➕ " + get_translation("Add Order", user_data['language']), callback_data='add_order')])
    
    keyboard.append([InlineKeyboardButton("❌ " + get_translation("Cancel", user_data['language']), callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(get_translation("📋 What would you like to do?", user_data['language']), reply_markup=reply_markup)
    else:
        await update.message.reply_text(get_translation("📋 What would you like to do?", user_data['language']), reply_markup=reply_markup)

async def admin_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'add_order':
        await add_order_url(update, context)
        return ADD_ORDER_URL
    elif action == 'add_admin':
        await add_admin(update, context)
        return ADD_ADMIN
    elif action == 'add_user':
        await add_user_username(update, context)
        return ADD_USER_USERNAME
    elif action == 'list_admins':
        await list_admins(update, context)
        return SHOWING_LIST
    elif action == 'list_orders':
        await list_orders(update, context)
        return SHOWING_LIST
    elif action == 'list_accounts':
        await list_accounts(update, context)
        return SHOWING_LIST
    elif action == 'cancel':
        await cancel(update, context)
        return ConversationHandler.END

async def add_order_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    if not (user_data['is_main_admin'] or user_data['is_order_admin']):
        await update.callback_query.edit_message_text(get_translation("🚫 You are not authorized to add orders.", user_data['language']))
        return ConversationHandler.END
    
    await update.callback_query.edit_message_text(
        get_translation("🔗 Please provide the Instagram post URL:", user_data['language']),
    )
    return ADD_ORDER_URL

async def add_order_comments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    user_data['post_url'] = update.message.text
    
    await update.message.reply_text(
        get_translation("💬 Please provide the comments, each comment on a new line:", user_data['language']),
    )
    return ADD_ORDER_COMMENTS

async def save_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    comments = update.message.text.split('\n')
    
    data_file = 'accounts.json'
    db_url = 'sqlite:///orders.db'
    engine = create_engine(db_url)
    SessionFactory = sessionmaker(bind=engine)
    
    data = read_data(data_file)
    account_usernames = [account['username'] for account in data['accounts']]
    
    num_accounts = len(account_usernames)
    num_comments = len(comments)
    
    if num_comments < num_accounts:
        comments *= (num_accounts // num_comments) + 1
        comments = comments[:num_accounts]
    elif num_comments > num_accounts:
        comments = comments[:num_accounts]

    add_order(user_data['post_url'], comments, account_usernames, SessionFactory)
    await update.message.reply_text(get_translation("✅ Order added successfully.", user_data['language']))
    await show_admin_actions(update, context)
    return ADMIN_ACTIONS

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    if not user_data['is_main_admin']:
        await update.callback_query.edit_message_text(get_translation("🚫 You are not authorized to add admins.", user_data['language']))
        return ConversationHandler.END
    
    await update.callback_query.edit_message_text(
        get_translation("👤 Please provide the username of the new admin:", user_data['language']),
    )
    return ADD_ADMIN

async def save_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    new_admin = update.message.text
    
    if 'order_admin' not in admins:
        admins['order_admin'] = []
    
    if new_admin not in admins['order_admin']:
        admins['order_admin'].append(new_admin)
        with open('admins.json', 'w') as f:
            json.dump(admins, f)
        await update.message.reply_text(get_translation("✅ Admin added successfully.", user_data['language']))
    else:
        await update.message.reply_text(get_translation("⚠️ This user is already an admin.", user_data['language']))
    
    await show_admin_actions(update, context)
    return ADMIN_ACTIONS

async def add_user_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    if not user_data['is_main_admin']:
        await update.callback_query.edit_message_text(get_translation("🚫 You are not authorized to add users.", user_data['language']))
        return ConversationHandler.END

    await update.callback_query.edit_message_text(
        get_translation("👥 Please provide the username of the new account:", user_data['language']),
    )
    return ADD_USER_USERNAME

async def add_user_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    user_data['new_username'] = update.message.text

    await update.message.reply_text(
        get_translation("🔑 Please provide the password of the new account:", user_data['language']),
    )
    return ADD_USER_PASSWORD

async def save_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    new_password = update.message.text
    new_username = user_data['new_username']

    # Read the existing accounts
    data_file = 'accounts.json'
    data = read_data(data_file)
    if not data:
        data = {'accounts': []}
    
    # Add the new account
    data['accounts'].append({
        'username': new_username,
        'password': new_password
    })

    # Save back to accounts.json
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await update.message.reply_text(get_translation("✅ User added successfully.", user_data['language']))
    await show_admin_actions(update, context)
    return ADMIN_ACTIONS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    if update.callback_query:
        await update.callback_query.edit_message_text(get_translation("❌ Action canceled.", user_data['language']))
    else:
        await update.message.reply_text(get_translation("❌ Action canceled.", user_data['language']))
    return ConversationHandler.END

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    admin_list = '\n'.join(admins['main_admin'] + admins['order_admin'])
    await split_and_send_message(update.callback_query, get_translation(f"👥 Admins List:\n{admin_list}", user_data['language']), context)
    return SHOWING_LIST

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    db_url = 'sqlite:///orders.db'
    engine = create_engine(db_url)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    orders = session.query(Order).all()
    order_list = '\n'.join([f"{order.id}: {order.post_url} - {order.status.name}" for order in orders])
    session.close()

    await split_and_send_message(update.callback_query, get_translation(f"📋 Orders List:\n{order_list}", user_data['language']), context)
    return SHOWING_LIST

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    data_file = 'accounts.json'
    data = read_data(data_file)
    account_list = '\n'.join([account['username'] for account in data['accounts']])

    await split_and_send_message(update.callback_query, get_translation(f"👤 Accounts List:\n{account_list}", user_data['language']), context)
    return SHOWING_LIST

async def split_and_send_message(callback_query, text, context):
    # Split the text into chunks of maximum 4096 characters
    max_length = 4096
    text_parts = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    for i, part in enumerate(text_parts):
        if i == 0:
            await callback_query.edit_message_text(part, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='back')]]))
        else:
            message = await callback_query.message.reply_text(part)
            context.user_data['last_message_id'] = message.message_id

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await show_admin_actions(update, context)
    return ADMIN_ACTIONS

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language_selection)],
            ADMIN_ACTIONS: [CallbackQueryHandler(admin_action_selection)],
            ADD_ORDER_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_order_comments)],
            ADD_ORDER_COMMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_order)],
            ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_admin)],
            ADD_USER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user_password)],
            ADD_USER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_user)],
            SHOWING_LIST: [CallbackQueryHandler(go_back, pattern='back')]
        },
        fallbacks=[CallbackQueryHandler(cancel), CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
