        import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "8905441969:AAEusap7k6Gh09iWnky-c0zi-Wn-gkKMx1U")
ADMIN_ID = -1003602948532

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot activo"

async def mostrar_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📲💳 Comprar saldo móvil", callback_data="comprar_saldo")],
        [InlineKeyboardButton("💵📱 Vender saldo móvil", callback_data="vender_saldo")],
        [InlineKeyboardButton("🚀🪙 Comprar criptomonedas", callback_data="comprar_crypto")],
        [InlineKeyboardButton("💸🔗 Vender criptomonedas", callback_data="vender_crypto")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text("🛍️ Elige una opción:", reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text("🛍️ Elige una opción:", reply_markup=reply_markup)

async def tienda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_menu(update, context)

async def soporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📞 SOPORTE\n\n✉️ Contacta al administrador\n👤 @TuUsuarioAdmin")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "comprar_saldo":
        text = "📲💳 **Comprar saldo móvil**\n\n💵 360 por 900 CUP\n\n✍️ Escriba el monto a comprar\n\n💳 Pago único\n📌 Tarjeta CUP: 9238-1299-7507-3018\n📲 Móvil a confirmar: 55348244\n\n🤑 Después de realizar su transferencia, mande una captura de pantalla 📸"
        context.user_data["esperando_monto_compra"] = True
        context.user_data["datos_compra"] = {}
    elif query.data == "vender_saldo":
        text = "💵📱 **Vender saldo móvil**\n\n💳 360 por 750 CUP\n\n✍️ Escriba el monto a vender\n\n📲 Realice su transferencia al número: 55348244\n\n🤑 Después de realizar su transferencia, mande una captura de pantalla 📸"
        context.user_data["esperando_monto_venta"] = True
        context.user_data["datos_venta"] = {}
    elif query.data == "comprar_crypto":
        text = "🚀🪙 **Comprar criptomonedas**\n\nBTC, ETH, USDT disponibles."
    elif query.data == "vender_crypto":
        text = "💸🔗 **Vender criptomonedas**\n\nEnvía la cantidad y tu wallet."
    elif query.data == "menu":
        await mostrar_menu(query, context)
        return
    else:
        return
    keyboard = [[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def recibir_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user.first_name or update.effective_user.username or "Usuario"
    if context.user_data.get("esperando_monto_compra"):
        monto = update.message.text
        context.user_data["datos_compra"]["monto"] = monto
        await update.message.reply_text("✅ Monto registrado. Ahora mande su captura de transferencia 🤑")
        await update.message.forward(chat_id=ADMIN_ID)
        await context.bot.send_message(ADMIN_ID, f"👤 {usuario} desea **COMPRAR** {monto} de saldo.")
        context.user_data["esperando_monto_compra"] = False
        context.user_data["esperando_captura_compra"] = True
    elif context.user_data.get("esperando_monto_venta"):
        monto = update.message.text
        context.user_data["datos_venta"]["monto"] = monto
        await update.message.reply_text("✅ Monto registrado. Ahora mande su captura de transferencia 🤑")
        await update.message.forward(chat_id=ADMIN_ID)
        await context.bot.send_message(ADMIN_ID, f"👤 {usuario} desea **VENDER** {monto} de saldo.")
        context.user_data["esperando_monto_venta"] = False
        context.user_data["esperando_captura_venta"] = True
    elif context.user_data.get("esperando_captura_compra"):
        if update.message.photo:
            await update.message.reply_text("📸 Captura recibida. Ahora escriba su número de teléfono 📲")
            await update.message.forward(chat_id=ADMIN_ID)
            context.user_data["datos_compra"]["captura"] = "Recibida"
            context.user_data["esperando_captura_compra"] = False
            context.user_data["esperando_telefono_compra"] = True
        else:
            await update.message.reply_text("⚠️ Mande una captura válida en formato imagen.")
    elif context.user_data.get("esperando_captura_venta"):
        if update.message.photo:
            await update.message.reply_text("📸 Captura recibida. Ahora mande su tarjeta y número a confirmar 💳📲")
            await update.message.forward(chat_id=ADMIN_ID)
            context.user_data["datos_venta"]["captura"] = "Recibida"
            context.user_data["esperando_captura_venta"] = False
            context.user_data["esperando_datos_venta"] = True
        else:
            await update.message.reply_text("⚠️ Mande una captura válida en formato imagen.")
    elif context.user_data.get("esperando_telefono_compra"):
        telefono = update.message.text
        context.user_data["datos_compra"]["telefono"] = telefono
        await update.message.reply_text("✅ Número registrado. El administrador confirmará su compra.")
        await update.message.forward(chat_id=ADMIN_ID)
        datos = context.user_data["datos_compra"]
        resumen = f"📲 RESUMEN COMPRA\n\n👤 Usuario: {usuario}\n💵 Monto: {datos.get('monto')}\n📸 Captura: {datos.get('captura')}\n📱 Teléfono: {datos.get('telefono')}"
        await context.bot.send_message(ADMIN_ID, resumen)
        context.user_data["esperando_telefono_compra"] = False
    elif context.user_data.get("esperando_datos_venta"):
        datos_text = update.message.text
        context.user_data["datos_venta"]["datos"] = datos_text
        await update.message.reply_text("✅ Datos registrados. El administrador confirmará su pago.")
        await update.message.forward(chat_id=ADMIN_ID)
        datos_v = context.user_data["datos_venta"]
        resumen = f"💵 RESUMEN VENTA\n\n👤 Usuario: {usuario}\n💳 Monto: {datos_v.get('monto')}\n📸 Captura: {datos_v.get('captura')}\n📱 Datos: {datos_v.get('datos')}"
        await context.bot.send_message(ADMIN_ID, resumen)
        context.user_data["esperando_datos_venta"] = False

def run_flask():
    app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("soporte", soporte))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, recibir_mensaje))
    print("🤖 Bot activo y esperando comandos...")
    app.run_polling()

if __name__ == "__main__":
    main()
