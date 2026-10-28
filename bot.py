"""
بوت Telegram بواجهة عربية لمتابعة خطوات سكريبت إدارة الميكسات.
مهم: هذا الإصدار واجهة متابعة فقط، ولا يتصل بواجهات اتصالات الداخلية ولا ينفذ تحويلات/تغيير باقات.
لتفعيل العمليات الفعلية يلزم API رسمي ومصرح به من مزود الخدمة.
"""
import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

STEPS = [
    "تسجيل الدخول والتحقق من الحسابين",
    "تحويل الميكسات المتاحة من الأونر إلى الفرد",
    "تغيير باقة الأونر من 270 إلى 180",
    "تحويل الميكسات المتاحة من الفرد إلى الأونر",
    "تحويل ميكسات الأونر على باقة 180 إلى الفرد",
    "إعادة باقة الأونر من 180 إلى 270",
    "تحويل الميكسات المتاحة من الفرد إلى الأونر",
    "فحص رصيد الأونر ومقارنته بالهدف",
    "عرض الملخص النهائي"
]

def is_allowed(update: Update) -> bool:
    if ADMIN_ID is None:
        return True
    user = update.effective_user
    return bool(user and user.id == ADMIN_ID)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ بدء متابعة جديدة", callback_data="begin")],
        [InlineKeyboardButton("📊 حالة العملية", callback_data="status"),
         InlineKeyboardButton("📋 الخطوات", callback_data="steps")],
        [InlineKeyboardButton("⛔ إيقاف المتابعة", callback_data="stop")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        return
    context.user_data.setdefault("running", False)
    await update.message.reply_text(
        "أهلًا بك في بوت متابعة خطوات الميكسات.\n\n"
        "تنبيه: هذا الإصدار يعرض الخطوات ويتابعها يدويًا فقط؛ "
        "لا ينفذ تحويلات أو تغيير باقات تلقائيًا.\n"
        "اختر من القائمة:",
        reply_markup=main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        return
    await update.message.reply_text(
        "الأوامر المتاحة:\n/start — القائمة الرئيسية\n/status — حالة المتابعة\n/steps — عرض الخطوات\n/stop — إيقاف المتابعة",
        reply_markup=main_keyboard()
    )

async def show_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        if update.message:
            await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        return
    text = "📋 ترتيب الخطوات:\n\n" + "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(STEPS)
    )
    text += "\n\nالخطوات هنا للمتابعة فقط، وليست تنفيذًا فعليًا."
    if update.message:
        await update.message.reply_text(text, reply_markup=main_keyboard())
    else:
        await update.callback_query.message.reply_text(text, reply_markup=main_keyboard())

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        if update.message:
            await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        else:
            await update.callback_query.answer("غير مسموح", show_alert=True)
        return
    idx = context.user_data.get("step_index", 0)
    running = context.user_data.get("running", False)
    target = context.user_data.get("target", 50000)
    state = "🟢 المتابعة جارية" if running else "⚪ لا توجد متابعة جارية"
    text = f"📊 الحالة: {state}\n🎯 الهدف المختار: {target:,} ميكس\n"
    if running and idx < len(STEPS):
        text += f"الخطوة الحالية: {idx+1}. {STEPS[idx]}"
    elif idx >= len(STEPS):
        text += "اكتملت قائمة المتابعة."
    else:
        text += "اضغط بدء متابعة جديدة للبدء."
    if update.message:
        await update.message.reply_text(text, reply_markup=main_keyboard())
    else:
        await update.callback_query.message.reply_text(text, reply_markup=main_keyboard())

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        if update.message:
            await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        else:
            await update.callback_query.answer("غير مسموح", show_alert=True)
        return
    context.user_data["running"] = False
    if update.message:
        await update.message.reply_text("⛔ تم إيقاف المتابعة.", reply_markup=main_keyboard())
    else:
        await update.callback_query.answer("تم إيقاف المتابعة")
        await update.callback_query.message.reply_text("⛔ تم إيقاف المتابعة.", reply_markup=main_keyboard())

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_allowed(update):
        await query.answer("غير مسموح لك باستخدام هذا البوت.", show_alert=True)
        return

    if query.data == "begin":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("50,000 ميكس", callback_data="target:50000"),
             InlineKeyboardButton("100,000 ميكس", callback_data="target:100000")],
            [InlineKeyboardButton("رجوع", callback_data="home")]
        ])
        await query.message.reply_text("🎯 اختار الهدف المطلوب:", reply_markup=keyboard)
    elif query.data.startswith("target:"):
        target = int(query.data.split(":", 1)[1])
        context.user_data["target"] = target
        context.user_data["step_index"] = 0
        context.user_data["running"] = True
        await query.message.reply_text(
            f"✅ بدأت متابعة هدف {target:,} ميكس.\n\n"
            f"الخطوة 1: {STEPS[0]}\n\n"
            "هذه نسخة متابعة فقط. لا ترسل كلمات مرور أو بيانات حسابات في الشات.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ الخطوة التالية", callback_data="next")],
                [InlineKeyboardButton("📊 الحالة", callback_data="status"),
                 InlineKeyboardButton("⛔ إيقاف", callback_data="stop")]
            ])
        )
    elif query.data == "next":
        if not context.user_data.get("running", False):
            await query.message.reply_text("لا توجد متابعة جارية. اضغط بدء متابعة جديدة.", reply_markup=main_keyboard())
            return
        idx = context.user_data.get("step_index", 0) + 1
        context.user_data["step_index"] = idx
        if idx >= len(STEPS):
            context.user_data["running"] = False
            await query.message.reply_text("✅ انتهت قائمة المتابعة. لم يتم تنفيذ أي تحويل أو تغيير باقة تلقائيًا.", reply_markup=main_keyboard())
        else:
            await query.message.reply_text(
                f"الخطوة {idx+1}: {STEPS[idx]}\n\n"
                "بعد إتمامها يدويًا، اضغط «الخطوة التالية».",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➡️ الخطوة التالية", callback_data="next")],
                    [InlineKeyboardButton("📊 الحالة", callback_data="status"),
                     InlineKeyboardButton("⛔ إيقاف", callback_data="stop")]
                ])
            )
    elif query.data == "steps":
        await show_steps(update, context)
    elif query.data == "status":
        await status(update, context)
    elif query.data == "stop":
        await stop(update, context)
    elif query.data == "home":
        await query.message.reply_text("القائمة الرئيسية:", reply_markup=main_keyboard())

async def reject_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("غير مسموح لك باستخدام هذا البوت.")
        return
    await update.message.reply_text(
        "استخدم الأزرار أو الأوامر المتاحة. لا ترسل كلمات مرور أو توكنات هنا.",
        reply_markup=main_keyboard()
    )

def main():
    if not BOT_TOKEN:
        raise SystemExit("يرجى ضبط متغير البيئة BOT_TOKEN بالتوكن الجديد من BotFather.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("steps", show_steps))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reject_text))
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
