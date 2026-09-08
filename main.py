import os, json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_CHANNEL_ID = -1003602948532
ADMIN_USER_ID = 7450751212

# TUS DATOS
TARJETA = "9238-1299-7507-3018"
MOVIL = "55348244"
WALLET_BEP20 = "0x5Ba930B965f535c202D224f4AEC5745174C2F5e9"

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

# COMANDOS ADMIN
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
    context.user_data.clear() # limpia flujos anteriores

    if q.data=="comprar_saldo":
        text=f"📲💳 **Comprar saldo**\n\n💵 360 CUP por {precios['saldo_compra']} CUP\n\n✍️ Escribe el MONTO que quieres comprar\n\n💳 Tarjeta: {TARJETA}\n📲 Móvil: {MOVIL}"
        context.user_data["flow"]="compra_saldo"
    elif q.data=="vender_saldo":
        text=f"💵📱 **Vender saldo**\n\n💳 360 CUP por {precios['saldo_venta']} CUP\n\n✍️ Escribe el MONTO que quieres vender\n\n📲 Transfiere a: {MOVIL}"
        context.user_data["flow"]="venta_saldo"
    elif q.data=="comprar_crypto":
        text=f"🚀🪙 **Comprar USDT (BEP20)**\n\n💵 Precio: {precios['usdt_compra']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT quieres comprar?\n_Ej: 10_"
        context.user_data["flow"]="compra_usdt_monto"
    elif q.data=="vender_crypto":
        text=f"💸🔗 **Vender USDT (BEP20)**\n\n💵 Precio: {precios['usdt_venta']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT quieres vender?\n_Ej: 20_"
        context.user_data["flow"]="venta_usdt_monto"
    elif q.data=="menu": await mostrar_menu(q,context); return
    else: return
    await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]), parse_mode="Markdown")

async def recibir_mensaje(update, context):
    usuario = update.effective_user.first_name or update.effective_user.username or "Usuario"
    uid = update.effective_user.id
    flow = context.user_data.get("flow")
    msg_text = update.message.text or ""

    if not flow:
        await update.message.reply_text("Usa /tienda para empezar")
        return

    # --- COMPRAR SALDO ---
    if flow == "compra_saldo":
        context.user_data["monto"] = msg_text
        context.user_data["flow"] = "compra_saldo_captura"
        await update.message.reply_text(f"✅ Monto: {msg_text}\n\nAhora transfiere a:\n💳 {TARJETA}\n📲 {MOVIL}\n\n📸 Manda la CAPTURA de la transferencia")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} ({uid}) - COMPRA SALDO\nMonto: {msg_text}")

    elif flow == "compra_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["flow"] = "compra_saldo_telefono"
            await update.message.reply_text("📸 Captura recibida ✅\n\n📲 Ahora escribe tu NÚMERO donde quieres el saldo")
        else:
            await update.message.reply_text("⚠️ Por favor manda la foto de la captura 📸")

    elif flow == "compra_saldo_telefono":
        context.user_data["telefono"] = msg_text
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN COMPRA SALDO\n👤 {usuario}\nMonto: {context.user_data.get('monto')}\nTel: {msg_text}")
        await update.message.reply_text("✅ Pedido registrado. Te avisaremos pronto.\n\nUsa /tienda para nuevo pedido")
        context.user_data.clear()

    # --- VENDER SALDO ---
    elif flow == "venta_saldo":
        context.user_data["monto"] = msg_text
        context.user_data["flow"] = "venta_saldo_captura"
        await update.message.reply_text(f"✅ Monto: {msg_text}\n\nTransfiere el saldo a {MOVIL} y manda la CAPTURA 📸")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} ({uid}) - VENDE SALDO\nMonto: {msg_text}")

    elif flow == "venta_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["flow"] = "venta_saldo_datos"
            await update.message.reply_text("📸 Captura ok ✅\n\n💳 Manda tu TARJETA y NÚMERO donde quieres el CUP")
        else:
            await update.message.reply_text("⚠️ Manda la foto 📸")

    elif flow == "venta_saldo_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN VENTA SALDO\n👤 {usuario}\nMonto: {context.user_data.get('monto')}\nDatos: {msg_text}")
        await update.message.reply_text("✅ Registrado. Te pagaremos pronto. /tienda")
        context.user_data.clear()

    # --- COMPRAR USDT ---
    elif flow == "compra_usdt_monto":
        try:
            cantidad = float(msg_text.replace(",","."))
            total_cup = cantidad * precios['usdt_compra']
            context.user_data["usdt"] = cantidad
            context.user_data["total_cup"] = total_cup
            context.user_data["flow"] = "compra_usdt_wallet"
            await update.message.reply_text(f"✅ Quieres {cantidad} USDT\n💰 Total a pagar: {total_cup:.0f} CUP\n\n✍️ Ahora manda tu WALLET BEP20 donde recibirás los USDT")
        except:
            await update.message.reply_text("⚠️ Escribe solo el número. Ej: 10")

    elif flow == "compra_usdt_wallet":
        context.user_data["wallet_cliente"] = msg_text
        context.user_data["flow"] = "compra_usdt_captura"
        await update.message.reply_text(f"✅ Wallet: {msg_text}\n\n💳 Transfiere {context.user_data['total_cup']:.0f} CUP a:\nTarjeta: {TARJETA}\nMóvil: {MOVIL}\n\n📸 Luego manda la CAPTURA y tu número")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} ({uid}) - COMPRA USDT\nCantidad: {context.user_data['usdt']} USDT = {context.user_data['total_cup']:.0f} CUP\nWallet cliente: {msg_text}")

    elif flow == "compra_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["flow"] = "compra_usdt_final"
            await update.message.reply_text("📸 Captura ok ✅\n\n📲 Escribe tu NÚMERO de contacto para confirmar")
        else:
            await update.message.reply_text("⚠️ Manda la captura 📸")

    elif flow == "compra_usdt_final":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN COMPRA USDT\n👤 {usuario}\nUSDT: {context.user_data['usdt']}\nTotal CUP: {context.user_data['total_cup']:.0f}\nWallet: {context.user_data['wallet_cliente']}\nContacto: {msg_text}")
        await update.message.reply_text("✅ Pedido de USDT registrado. Verificaremos y te enviaremos. /tienda")
        context.user_data.clear()

    # --- VENDER USDT ---
    elif flow == "venta_usdt_monto":
        try:
            cantidad = float(msg_text.replace(",","."))
            total_cup = cantidad * precios['usdt_venta']
            context.user_data["usdt"] = cantidad
            context.user_data["total_cup"] = total_cup
            context.user_data["flow"] = "venta_usdt_captura"
            await update.message.reply_text(f"✅ Venderás {cantidad} USDT\n💰 Recibirás: {total_cup:.0f} CUP\n\n🔗 Envía los {cantidad} USDT (BEP20) a esta wallet:\n\n`{WALLET_BEP20}`\n\n📸 Luego manda la CAPTURA del envío", parse_mode="Markdown")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"👤 {usuario} ({uid}) - VENDE USDT\nCantidad: {cantidad} USDT = {total_cup:.0f} CUP")
        except:
            await update.message.reply_text("⚠️ Escribe solo el número. Ej: 20")

    elif flow == "venta_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            context.user_data["flow"] = "venta_usdt_datos"
            await update.message.reply_text("📸 Captura ok ✅\n\n💳 Ahora manda tu TARJETA CUP y tu NÚMERO donde te pagamos los CUP")
        else:
            await update.message.reply_text("⚠️ Manda la foto de la transacción 📸")

    elif flow == "venta_usdt_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN VENTA USDT\n👤 {usuario}\nUSDT: {context.user_data['usdt']}\nRecibe: {context.user_data['total_cup']:.0f} CUP\nDatos pago: {msg_text}")
        await update.message.reply_text("✅ Venta registrada. Verificaremos tu USDT y te transferimos. /tienda")
        context.user_data.clear()

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
