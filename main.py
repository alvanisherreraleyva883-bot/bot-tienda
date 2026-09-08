import os
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = -1003602948532

web = Flask(__name__)
@web.route('/')
def home():
    return "Bot tienda activo"
def run_web():
    web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def mostrar_menu(update_or_query, context):
    keyboard = [
        [InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],
        [InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],
        [InlineKeyboardButton("🚀🪙 Comprar crypto", callback_data="comprar_crypto")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text("🛍️ Elige una opción:", reply_markup=markup)
    else:
        try:
            await update_or_query.edit_message_text("🛍️ Elige una opción:", reply_markup=markup)
        except:
            await update_or_query.message.reply_text("🛍️ Elige una opción:", reply_markup=markup)

async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_menu(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu":
        await mostrar_menu(query, context)
        return
    if query.data == "comprar_saldo":
        context.user_data["estado"] = "esperando_monto_compra"
        txt = "📲💳 COMPRAR SALDO\n\n💵 360 x 900 CUP\n\n✍️ Escribe el monto\n💳 Tarjeta: 9238-1299-7507-3018\n📲 Confirmar: 55348244"
    elif query.data == "vender_saldo":
        context.user_data["estado"] = "esperando_monto_venta"
        txt = "💵📱 VENDER SALDO\n\n💳 360 x 750 CUP\n\n✍️ Escribe el monto\n📲 Transfiere a: 55348244"
    else:
        txt = "🚀 Crypto disponible pronto."
    await query.edit_message_text(text=txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]))

async def recibir_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = context.user_data.get("estado")
    user = update.effective_user
    nombre = f"@{user.username}" if user.username else user.first_name
    try:
        await update.message.forward(chat_id=ADMIN_ID)
    except:
        pass
    if estado == "esperando_monto_compra":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_compra"
        await update.message.reply_text(f"✅ Monto: {update.message.text}\n\n📸 Manda captura ahora.")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"COMPRAR {update.message.text} de {nombre}")
        except:
            pass
    elif estado == "esperando_monto_venta":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_venta"
        await update.message.reply_text(f"✅ Monto: {update.message.text}\n\n📸 Manda captura ahora.")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"VENDER {update.message.text} de {nombre}")
        except:
            pass
    elif estado and "captura" in estado:
        await update.message.reply_text("✅ Recibido. Admin revisa. Usa /tienda")
        context.user_data["estado"] = None
    else:
        await update.message.reply_text("Usa /tienda para menú")

def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("start", tienda))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, recibir_mensaje))
    app.run_polling()

if __name__ == "__main__":
    main()
