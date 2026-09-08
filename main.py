import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = -1003602948532

async def mostrar_menu(update_or_query, context):
    keyboard = [
        [InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],
        [InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],
        [InlineKeyboardButton("🚀🪙 Comprar crypto", callback_data="comprar_crypto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text("🛍️ Elige una opción:", reply_markup=reply_markup)
    else:
        try:
            await update_or_query.edit_message_text("🛍️ Elige una opción:", reply_markup=reply_markup)
        except:
            await update_or_query.message.reply_text("🛍️ Elige una opción:", reply_markup=reply_markup)

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
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]))

async def recibir_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    estado = context.user_data.get("estado")
    user = update.effective_user
    nombre = f"@{user.username}" if user.username else user.first_name
    try: await update.message.forward(chat_id=ADMIN_ID)
    except: pass

    if estado == "esperando_monto_compra":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_compra"
        await update.message.reply_text(f"✅ Monto {update.message.text} registrado. Manda captura 📸")
        await context.bot.send_message(ADMIN_ID, f"👤 {nombre} QUIERE COMPRAR {update.message.text}")
        return
    if estado == "esperando_captura_compra" and update.message.photo:
        context.user_data["estado"] = "esperando_telefono"
        await update.message.reply_text("📸 Recibida. Ahora escribe el número a recargar 📲")
        return
    if estado == "esperando_telefono":
        resumen = f"📲 RESUMEN COMPRA\n👤 {nombre} ID:{user.id}\n💵 Monto: {context.user_data.get('monto')}\n📱 Tel: {update.message.text}"
        await context.bot.send_message(ADMIN_ID, resumen)
        await update.message.reply_text("✅ Listo. Te recargamos en breve.")
        context.user_data.clear()
        return

    if estado == "esperando_monto_venta":
        context.user_data["monto"] = update.message.text
        context.user_data["estado"] = "esperando_captura_venta"
        await update.message.reply_text("✅ Monto registrado. Manda captura 📸")
        await context.bot.send_message(ADMIN_ID, f"👤 {nombre} QUIERE VENDER {update.message.text}")
        return
    if estado == "esperando_captura_venta" and update.message.photo:
        context.user_data["estado"] = "esperando_datos"
        await update.message.reply_text("📸 Recibida. Ahora manda tu tarjeta y número")
        return
    if estado == "esperando_datos":
        resumen = f"💵 RESUMEN VENTA\n👤 {nombre} ID:{user.id}\n💳 Monto: {context.user_data.get('monto')}\n📱 Datos: {update.message.text}"
        await context.bot.send_message(ADMIN_ID, resumen)
        await update.message.reply_text("✅ Datos recibidos. Te pagamos en breve.")
        context.user_data.clear()
        return

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("start", tienda))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, recibir_mensaje))
    print("🤖 Bot activo...")
    app.run_polling()

if __name__ == "__main__":
    main()
