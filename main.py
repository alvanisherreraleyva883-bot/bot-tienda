import os
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = -1003602948532

# Mini servidor para Render
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot tienda activo"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host='0.0.0.0', port=port)

async def mostrar_menu(update_or_query, context):
    keyboard = [
        [InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],
        [InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],
        [InlineKeyboardButton("🚀🪙 Comprar crypto", callback_data="comprar_crypto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🛍️ Elige una opción:"
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        try:
            await update_or_query.edit_message_text(text, reply_markup=reply_markup)
        except:
            await update_or_query.message.reply_text(text, reply_markup=reply_markup)

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
        text = "📲💳 COMPRAR SALDO\n\n💵 360 x 900 CUP\n\n✍️ Escribe el monto\n💳 Tarjeta: 9238-1299-7507-3018\n📲 Confirmar: 55348244"
    elif query.data == "vender_saldo":
        context.user_data["estado"] = "esperando_monto_venta"
        text = "💵📱 VENDER SALDO\n\n💳 360 x 750 CUP\n\n✍️ Escribe el monto\n📲 Transfiere a: 55348244"
    else:
        text = "🚀 Crypto disponible pronto."
    
    await query.edit_message_text(
        text=text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]])
    )

async def recibir_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = context.user_data.get("estado")
    user = update.effective_user
    nombre = f"@{user.username}" if user.username else user.first_name

    # Reenviar al admin
    try: 
        await update.message.forward(chat_id=ADMIN_ID)
    except: 
        pass

    if estado == "esperando_monto_compra":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_compra"
        await update.message.reply_text(f"✅ Monto recibido: {update.message.text}\n\n📸 Ahora manda la captura de la transferencia.")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 Nuevo cliente {nombre} quiere COMPRAR {update.message.text}")
        except: pass

    elif estado == "esperando_monto_venta":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_venta"
        await update.message.reply_text(f"✅ Monto recibido: {update.message.text}\n\n📸 Ahora manda la captura.")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 Nuevo cliente {nombre} quiere VENDER {update.message.text}")
        except: pass

    elif "captura" in str(estado):
        await update.message.reply_text("✅ Captura recibida. El admin la va a revisar. Te avisa en breve.\n\nUsa /tienda para volver al menú.")
        context.user_data["estado"] = None
    else:
        await update.message.reply_text("Usa /tienda para ver el menú 🛍️")

def main():
    # Iniciar Flask en hilo aparte
    threading.Thread(target=run_web, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("start", tienda))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, recibir_mensaje))
    
    print("Bot iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main(https 
