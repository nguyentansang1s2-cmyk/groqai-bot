import os
import json
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8621404114:AAHBjHjUYhm2u61a0iu-sGHbpddUo0UlU7w')
ADMIN_ID  = int(os.environ.get('ADMIN_ID', '7870316880'))
CODES_FILE = 'codes.json'

# ── Load/Save codes ───────────────────────────────────────────────────────────
def load_codes():
    if not os.path.exists(CODES_FILE):
        return {'available': [], 'sent': {}}
    with open(CODES_FILE, 'r') as f:
        return json.load(f)

def save_codes(data):
    with open(CODES_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Helper ────────────────────────────────────────────────────────────────────
def is_admin(user_id):
    return user_id == ADMIN_ID

# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        data = load_codes()
        await update.message.reply_text(
            f"👋 Xin chào Admin!\n\n"
            f"📦 Kho VIP codes: {len(data['available'])} codes còn lại\n"
            f"📤 Đã gửi: {len(data['sent'])} codes\n\n"
            f"📖 Lệnh:\n"
            f"/addcodes - Thêm codes vào kho\n"
            f"/send @username hoặc chat_id - Gửi code cho người mua\n"
            f"/stock - Xem số codes còn lại\n"
            f"/sent - Xem lịch sử gửi code\n"
            f"/revoke @username - Thu hồi code (nếu thẻ giả)"
        )
    else:
        await update.message.reply_text(
            "👋 Xin chào! Tôi là bot GroqAI VIP.\n\n"
            "Sau khi mua VIP thành công, admin sẽ gửi code cho bạn qua bot này.\n\n"
            "🔗 Mua VIP tại: https://your-site.netlify.app/mua-vip"
        )

# ── /addcodes - Admin thêm codes vào kho ─────────────────────────────────────
async def addcodes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "📋 Gửi danh sách VIP codes cho tôi!\n\n"
        "Mỗi code 1 dòng, ví dụ:\n"
        "GROQ-XXXX-XXXX-XXXX\n"
        "GROQ-YYYY-YYYY-YYYY\n\n"
        "Gửi ngay bên dưới 👇"
    )
    ctx.user_data['waiting_codes'] = True

# ── /send - Admin gửi code cho người mua ─────────────────────────────────────
async def send_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not ctx.args:
        await update.message.reply_text(
            "❌ Cú pháp: /send @username hoặc /send chat_id\n\n"
            "Ví dụ:\n"
            "/send @nguyen_sang\n"
            "/send 123456789"
        )
        return

    target = ctx.args[0].replace('@', '')
    data = load_codes()

    if not data['available']:
        await update.message.reply_text("❌ Hết codes rồi! Dùng /addcodes để thêm.")
        return

    # Lấy 1 code ngẫu nhiên
    code = random.choice(data['available'])
    data['available'].remove(code)
    data['sent'][target] = {
        'code': code,
        'time': __import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    save_codes(data)

    # Gửi code cho người mua
    vip_msg = (
        f"🎉 <b>Chúc mừng! VIP Code của bạn:</b>\n\n"
        f"⭐ <code>{code}</code>\n\n"
        f"📖 <b>Cách kích hoạt:</b>\n"
        f"1. Vào web GroqAI\n"
        f"2. Màn hình welcome → nhập code vào ô <b>CODE VIP</b>\n"
        f"3. Lấy Gemini key miễn phí tại:\n"
        f"   👉 aistudio.google.com/apikey\n"
        f"4. Nhập cả 2 → <b>Chat không giới hạn!</b> ♾️\n\n"
        f"❓ Hỗ trợ: @Groq_vip_bot"
    )

    try:
        # Thử gửi qua username hoặc chat_id
        target_id = int(target) if target.isdigit() else f"@{target}"
        await ctx.bot.send_message(
            chat_id=target_id,
            text=vip_msg,
            parse_mode='HTML'
        )
        await update.message.reply_text(
            f"✅ Đã gửi code <code>{code}</code> cho {ctx.args[0]}!\n"
            f"📦 Còn lại: {len(data['available'])} codes",
            parse_mode='HTML'
        )
    except Exception as e:
        # Nếu không gửi được → gửi lại cho admin để forward thủ công
        await update.message.reply_text(
            f"⚠️ Không gửi trực tiếp được!\n\n"
            f"Code cho {ctx.args[0]}:\n"
            f"<code>{code}</code>\n\n"
            f"Hãy forward tin nhắn này cho họ thủ công.\n"
            f"Lỗi: {str(e)}",
            parse_mode='HTML'
        )

# ── /stock - Xem số codes còn ─────────────────────────────────────────────────
async def stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    data = load_codes()
    await update.message.reply_text(
        f"📦 Kho VIP Codes:\n\n"
        f"✅ Còn lại: {len(data['available'])} codes\n"
        f"📤 Đã gửi: {len(data['sent'])} codes\n\n"
        f"Thêm codes: /addcodes"
    )

# ── /sent - Xem lịch sử ───────────────────────────────────────────────────────
async def sent_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    data = load_codes()
    if not data['sent']:
        await update.message.reply_text("Chưa gửi code nào.")
        return
    lines = ["📋 Lịch sử gửi code:\n"]
    for user, info in list(data['sent'].items())[-20:]:
        lines.append(f"• @{user}: {info['code']} ({info['time']})")
    await update.message.reply_text('\n'.join(lines))

# ── /revoke - Thu hồi code ────────────────────────────────────────────────────
async def revoke(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not ctx.args:
        await update.message.reply_text("Cú pháp: /revoke @username")
        return
    target = ctx.args[0].replace('@', '')
    data = load_codes()
    if target in data['sent']:
        code = data['sent'][target]['code']
        data['available'].append(code)
        del data['sent'][target]
        save_codes(data)
        await update.message.reply_text(f"✅ Đã thu hồi code {code} từ @{target}.\nCode được trả lại kho.")
    else:
        await update.message.reply_text(f"❌ Không tìm thấy @{target} trong lịch sử.")

# ── Nhận text - xử lý khi admin gửi danh sách codes ─────────────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not ctx.user_data.get('waiting_codes'): return

    text = update.message.text.strip()
    new_codes = [c.strip() for c in text.split('\n') if c.strip().startswith('GROQ-')]

    if not new_codes:
        await update.message.reply_text("❌ Không tìm thấy code hợp lệ!\nCode phải bắt đầu bằng GROQ-")
        return

    data = load_codes()
    # Tránh trùng lặp
    added = 0
    for c in new_codes:
        if c not in data['available'] and c not in [v['code'] for v in data['sent'].values()]:
            data['available'].append(c)
            added += 1

    save_codes(data)
    ctx.user_data['waiting_codes'] = False
    await update.message.reply_text(
        f"✅ Đã thêm {added} codes vào kho!\n"
        f"📦 Tổng còn lại: {len(data['available'])} codes"
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('addcodes', addcodes))
    app.add_handler(CommandHandler('send', send_code))
    app.add_handler(CommandHandler('stock', stock))
    app.add_handler(CommandHandler('sent', sent_history))
    app.add_handler(CommandHandler('revoke', revoke))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot đang chạy...")
    app.run_polling()

if __name__ == '__main__':
    main()
