import os, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_CHANNEL_ID = -1003602948532
ADMIN_USER_ID = 7450751212

app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Bot activo"

PRECIOS_FILE = "precios.json"
def cargar_precios():
    if os.path.exists(PRECIOS_FILE):
        try:
            with open(PRECIOS_FILE, "r") as f: return json.load(f)
        except: pass
    return {"saldo_compra": 900, "saldo_venta": 750, "usdt_compra": 360, "usdt_venta": 350}

def guardar_precios(d):
    with open(PRECIOS_FILE, "w") as f: json.dump(d, f)

precios = cargar_precios()

async def cambiar_saldo(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Compra saldo: {precios['saldo_compra']}\nUso: /saldo 950")
    precios["saldo_compra"] = int(context.args[0]); guardar_precios(precios)
    await update.message.reply_text(f"✅ Saldo COMPRA -> {precios['saldo_compra']} CUP")

async def cambiar_venta(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Venta saldo: {precios['saldo_venta']}\nUso: /venta 780")
    precios["saldo_venta"] = int(context.args[0]); guardar_precios(precios)
    await update.message.reply_text(f"✅ Saldo VENTA -> {precios['saldo_venta']} CUP")

async def cambiar_usdtc(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Compra USDT: {precios['usdt_compra']}\nUso: /usdtc 360")
    precios["usdt_compra"] = int(context.args[0]); guardar_precios(precios)
    await update.message.reply_text(f"✅ USDT COMPRA -> {precios['usdt_compra']} CUP")

async def cambiar_usdtv(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Venta USDT: {precios['usdt_venta']}\nUso: /usdtv 350")
    precios["usdt_venta"] = int(context.args[0]); guardar_precios(precios)
    await update.message.reply_text(f"✅ USDT VENTA -> {precios['usdt_venta']} CUP")

async def ver_precios(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    await update.message.reply_text(f"📊 PRECIOS:\n\nSaldo Compra: {precios['saldo_compra']}\nSaldo Venta: {precios['saldo_venta']}\nUSDT Compra: {precios['usdt_compra']}\nUSDT Venta: {precios['usdt_venta']}")

async def mostrar_menu(u, c):
    kb = [[InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],[InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],[InlineKeyboardButton("🚀🪙 Comprar USDT", callback_data="comprar_crypto")],[InlineKeyboardButton("💸🔗 Vender USDT", callback_data="vender_crypto")]]
    rm = InlineKeyboardMarkup(kb)
    if isinstance(u, Update): await u.message.reply_text("🛍️ Elige:", reply_markup=rm)
    else: await u.edit_message_text("🛍️ Elige:", reply_markup=rm)

async def tienda(u,c): await mostrar_menu(u,c)
async def soporte(u,c): await u.message.reply_text("📞 SOPORTE @TuUsuarioAdmin")

async def button(update, context):
    q=update.callback_query; await q.answer()
    if q.data=="comprar_saldo":
        text=f"📲💳 **Comprar saldo**\n\n💵 360 por {precios['saldo_compra']} CUP\n\n✍️ Monto a comprar\n💳 Tarjeta: 9238-1299-7507-3018\n📲 Móvil: 55348244\n🤑 Mande captura 📸"
        context.user_data["esperando_monto_compra"]=True; context.user_data["datos_compra"]={}
    elif q.data=="vender_saldo":
        text=f"💵📱 **Vender saldo**\n\n💳 360 por {precios['saldo_venta']} CUP\n\n✍️ Monto a vender\n📲 Transfiera a: 55348244\n🤑 Mande captura 📸"
        context.user_data["esperando_monto_venta"]=True; context.user_data["datos_venta"]={}
    elif q.data=="comprar_crypto":
        text=f"🚀🪙 **Comprar USDT**\n\n💵 Compra: {precios['usdt_compra']} CUP por 1 USDT\n\n✍️ Escriba cantidad"
        context.user_data["esperando_monto_compra"]=True; context.user_data["datos_compra"]={}
    elif q.data=="vender_crypto":
        text=f"💸🔗 **Vender USDT**\n\n💵 Venta: {precios['usdt_venta']} CUP por 1 USDT\n\n✍️ Escriba cantidad y wallet"
        context.user_data["esperando_monto_venta"]=True; context.user_data["datos_venta"]={}
    elif q.data=="menu": await mostrar_menu(q,context); return
    else: return
    await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]))

async def recibir_mensaje(update, context):
    usuario = update.effective_user.first_name or update.effective_user.username
    if context.user_data.get("esperando_monto_compra"):
        context.user_data["datos_compra"]["monto"]=update.message.text
        await update.message.reply_text("✅ Monto ok. Mande captura 🤑")
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} COMPRAR {update.message.text}")
        context.user_data["esperando_monto_compra"]=False; context.user_data["esperando_captura_compra"]=True
    elif context.user_data.get("esperando_monto_venta"):
        context.user_data["datos_venta"]["monto"]=update.message.text
        await update.message.reply_text("✅ Monto ok. Mande captura 🤑")
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} VENDER {update.message.text}")
        context.user_data["esperando_monto_venta"]=False; context.user_data["esperando_captura_venta"]=True
    elif context.user_data.get("esperando_captura_compra"):
        if update.message.photo:
            await update.message.reply_text("📸 Captura ok. Escriba su número 📲")
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["datos_compra"]["captura"]="Recibida"
            context.user_data["esperando_captura_compra"]=False; context.user_data["esperando_telefono_compra"]=True
        else: await update.message.reply_text("⚠️ Mande imagen.")
    elif context.user_data.get("esperando_captura_venta"):
        if update.message.photo:
            await update.message.reply_text("📸 Captura ok. Mande tarjeta y número 💳📲")
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["datos_venta"]["captura"]="Recibida"
            context.user_data["esperando_captura_venta"]=False; context.user_data["esperando_datos_venta"]=True
        else: await update.message.reply_text("⚠️ Mande imagen.")
    elif context.user_data.get("esperando_telefono_compra"):
        context.user_data["datos_compra"]["telefono"]=update.message.text
        await update.message.reply_text("✅ Registrado."); await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        d=context.user_data["datos_compra"]
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN COMPRA\n👤 {usuario}\nMonto: {d.get('monto')}\nTel: {d.get('telefono')}")
        context.user_data["esperando_telefono_compra"]=False
    elif context.user_data.get("esperando_datos_venta"):
        context.user_data["datos_venta"]["datos"]=update.message.text
        await update.message.reply_text("✅ Registrado."); await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        d=context.user_data["datos_venta"]
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN VENTA\n👤 {usuario}\nMonto: {d.get('monto')}\nDatos: {d.get('datos')}")
        context.user_data["esperando_datos_venta"]=False

def run_flask(): app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
def main():
    Thread(target=run_flask, daemon=True).start()
    app=Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("soporte", soporte))
    app.add_handler(CommandHandler("saldo", cambiar_saldo))
    app.add_handler(CommandHandler("venta", cambiar_venta))
    app.add_handler(CommandHandler("usdtc", cambiar_usdtc))
    app.add_handler(CommandHandler("usdtv", cambiar_usdtv))
    app.add_handler(CommandHandler("precios", ver_precios))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, recibir_mensaje))
    print("🤖 Bot activo..."); app.run_polling()
if __name__=="__main__": main()
