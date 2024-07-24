LANGUAGES = {
    'english': 'English',
    'farsi': 'Farsi'
}

TRANSLATIONS = {
    'english': {
        'Welcome to the bot!': 'Welcome to the bot!',
        'You are not authorized to use this bot.': 'You are not authorized to use this bot.',
        'Please provide the Instagram post URL:': 'Please provide the Instagram post URL:',
        'Please provide the comments, each comment on a new line:': 'Please provide the comments, each comment on a new line:',
        'Not enough accounts for the number of comments. Please provide more accounts.': 'Not enough accounts for the number of comments. Please provide more accounts.',
        'Order added successfully.': 'Order added successfully.',
        'You are not authorized to add orders.': 'You are not authorized to add orders.',
        'Please provide the username of the new admin:': 'Please provide the username of the new admin:',
        'Admin added successfully.': 'Admin added successfully.',
        'This user is already an admin.': 'This user is already an admin.',
        'Action canceled.': 'Action canceled.'
    },
    'farsi': {
        'Welcome to the bot!': 'به ربات خوش آمدید!',
        'You are not authorized to use this bot.': 'شما مجاز به استفاده از این ربات نیستید.',
        'Please provide the Instagram post URL:': 'لطفاً آدرس پست اینستاگرام را وارد کنید:',
        'Please provide the comments, each comment on a new line:': 'لطفاً نظرات را وارد کنید، هر نظر در یک خط جداگانه:',
        'Not enough accounts for the number of comments. Please provide more accounts.': 'حساب‌های کافی برای تعداد نظرات وجود ندارد. لطفاً حساب‌های بیشتری وارد کنید.',
        'Order added successfully.': 'سفارش با موفقیت اضافه شد.',
        'You are not authorized to add orders.': 'شما مجاز به اضافه کردن سفارشات نیستید.',
        'Please provide the username of the new admin:': 'لطفاً نام کاربری مدیر جدید را وارد کنید:',
        'Admin added successfully.': 'مدیر با موفقیت اضافه شد.',
        'This user is already an admin.': 'این کاربر از قبل مدیر است.',
        'Action canceled.': 'عملیات لغو شد.'
    }
}

def get_translation(text, language):
    return TRANSLATIONS.get(language, {}).get(text, text)
