import os, json, random
from flask import Flask
from threading import Thread, Lock
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_CHANNEL_ID = -1003602948532
ADMIN_USER_ID = 7450751212

TARJETA = "9238-1299-7507-3018"
MOVIL = "55348244"
WALLET_BEP20 = "0x5Ba930B965f535c202D224f4AEC5745174C2F5e9"

app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Bot activo"

PRECIOS_FILE = "precios.json"
lock_precios = Lock()

def cargar_precios():
    if os.path.exists(PRECIOS_FILE):
        try:
            with open(PRECIOS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"saldo_compra": 900, "saldo_venta": 750, "usdt_compra": 360, "usdt_venta": 350}

def guardar_precios(d):
    with lock_precios:
        with open(PRECIOS_FILE, "w", encoding="utf-8") as f: json.dump(d, f)

precios = cargar_precios()

def gen_id():
    return f"PEDIDO-{random.randint(1000, 9999)}"

async def cambiar_saldo(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Compra saldo: {precios['saldo_compra']}\nUso: /saldo 950")
    try:
        precios["saldo_compra"] = int(context.args[0]); guardar_precios(precios)
        await update.message.reply_text(f"✅ Saldo COMPRA -> {precios['saldo_compra']} CUP")
    except: await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_venta(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Venta saldo: {precios['saldo_venta']}\nUso: /venta 780")
    try:
        precios["saldo_venta"] = int(context.args[0]); guardar_precios(precios)
        await update.message.reply_text(f"✅ Saldo VENTA -> {precios['saldo_venta']} CUP")
    except: await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_usdtc(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Compra USDT: {precios['usdt_compra']}\nUso: /usdtc 360")
    try:
        precios["usdt_compra"] = int(context.args[0]); guardar_precios(precios)
        await update.message.reply_text(f"✅ USDT COMPRA -> {precios['usdt_compra']} CUP")
    except: await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_usdtv(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args: return await update.message.reply_text(f"Venta USDT: {precios['usdt_venta']}\nUso: /usdtv 350")
    try:
        precios["usdt_venta"] = int(context.args[0]); guardar_precios(precios)
        await update.message.reply_text(f"✅ USDT VENTA -> {precios['usdt_venta']} CUP")
    except: await update.message.reply_text("⚠️ Usa solo números")

async def ver_precios(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    await update.message.reply_text(f"📊 PRECIOS:\nSaldo Compra: {precios['saldo_compra']}\nSaldo Venta: {precios['saldo_venta']}\nUSDT Compra: {precios['usdt_compra']}\nUSDT Venta: {precios['usdt_venta']}")

async def mostrar_menu(u, c):
    kb = [[InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],[InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],[InlineKeyboardButton("🚀🪙 Comprar USDT", callback_data="comprar_crypto")],[InlineKeyboardButton("💸🔗 Vender USDT", callback_data="vender_crypto")]]
    rm = InlineKeyboardMarkup(kb)
    if isinstance(u, Update): await u.message.reply_text("🛍️ Elige:", reply_markup=rm)
    else: await u.edit_message_text("🛍️ Elige:", reply_markup=rm)

async def tienda(u,c): await mostrar_menu(u,c)
async def soporte(u,c): await u.message.reply_text("📞 SOPORTE @TuUsuarioAdmin")

async def button(update, context):
    q=update.callback_query; await q.answer()
    if q.data.startswith("pagado_"):
        try:
            await q.edit_message_text(q.message.text + "\n\n✅ PAGADO ✓")
        except: pass
        return
    if q.data == "menu":
        await mostrar_menu(q, context); return

    pedido_id = gen_id()
    context.user_data.clear()
    context.user_data["pedido_id"] = pedido_id

    if q.data=="comprar_saldo":
        text=f"📲💳 **Comprar saldo** - `#{pedido_id}`\n\n💵 Precio: 360 = {precios['saldo_compra']} CUP\n\n✍️ Escribe cuanto saldo quieres\n_Ej: 360 o 500_"
        context.user_data["flow"]="compra_saldo"
    elif q.data=="vender_saldo":
        text=f"💵📱 **Vender saldo** - `#{pedido_id}`\n\n💳 Pagamos: 360 = {precios['saldo_venta']} CUP\n\n✍️ Escribe cuanto vas a vender"
        context.user_data["flow"]="venta_saldo"
    elif q.data=="comprar_crypto":
        text=f"🚀🪙 **Comprar USDT** - `#{pedido_id}`\n\n💵 Precio: {precios['usdt_compra']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT quieres?"
        context.user_data["flow"]="compra_usdt_monto"
    elif q.data=="vender_crypto":
        text=f"💸🔗 **Vender USDT** - `#{pedido_id}`\n\n💵 Pagamos: {precios['usdt_venta']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT vendes?"
        context.user_data["flow"]="venta_usdt_monto"
    else: return
    await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]), parse_mode="Markdown")

async def recibir_mensaje(update, context):
    if not update.message: return
    usuario = update.effective_user.first_name or "Usuario"
    username = f"@{update.effective_user.username}" if update.effective_user.username else "sin username"
    uid = update.effective_user.id
    flow = context.user_data.get("flow")
    pedido_id = context.user_data.get("pedido_id", "SIN-ID")
    msg_text = update.message.text or ""
    if not flow: return await update.message.reply_text("Usa /tienda para empezar")

    def admin_header(tipo):
        return f"🆕 #{pedido_id} - {tipo}\n👤 {usuario} {username}\n🆔 {uid}"

    if flow == "compra_saldo":
        try:
            monto = float(msg_text.replace(",","."))
            total = (monto / 360) * precios['saldo_compra']
            context.user_data["monto"] = monto; context.user_data["total_cup"] = total
            context.user_data["flow"] = "compra_saldo_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nQuieres {monto:.0f} saldo = {total:.0f} CUP\n\n💳 Transfiere {total:.0f} CUP a:\n`{TARJETA}`\n📲 {MOVIL}\n\n📸 Manda CAPTURA", parse_mode="Markdown")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{admin_header('COMPRA SALDO')}\nSaldo: {monto:.0f}\nTotal: {total:.0f} CUP", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Marcar {pedido_id} Pagado", callback_data=f"pagado_{pedido_id}")]]))
        except: await update.message.reply_text("⚠️ Solo número. Ej: 360")
    elif flow == "compra_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} de {usuario}")
            context.user_data["flow"] = "compra_saldo_telefono"
            await update.message.reply_text("📸 Captura recibida ✅\n\n📲 Escribe tu NÚMERO")
        else: await update.message.reply_text("⚠️ Manda foto de la captura 📸")
    elif flow == "compra_saldo_telefono":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN #{pedido_id}\n👤 {usuario}\nSaldo: {context.user_data.get('monto',0):.0f} = {context.user_data.get('total_cup',0):.0f} CUP\nTel: {msg_text}\n\n`{msg_text}`", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Pedido #{pedido_id} registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido")
        context.user_data.clear()
    elif flow == "venta_saldo":
        try:
            monto = float(msg_text.replace(",","."))
            total = (monto / 360) * precios['saldo_venta']
            context.user_data["monto"] = monto; context.user_data["total_cup"] = total
            context.user_data["flow"] = "venta_saldo_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nVendes {monto:.0f} saldo\n💰 Recibes: {total:.0f} CUP\n\n📲 Transfiere saldo a {MOVIL} y manda CAPTURA")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{admin_header('VENTA SALDO')}\nSaldo: {monto:.0f}\nA pagar: {total:.0f} CUP")
        except: await update.message.reply_text("⚠️ Solo número. Ej: 360")
    elif flow == "venta_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} de {usuario}")
            context.user_data["flow"] = "venta_saldo_datos"
            await update.message.reply_text(f"📸 Ok ✅\n\n💳 Manda TARJETA y NÚMERO donde te pagamos {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text("⚠️ Manda foto 📸")
    elif flow == "venta_saldo_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN #{pedido_id}\n👤 {usuario}\nVende: {context.user_data.get('monto',0):.0f}\nPagar: {context.user_data.get('total_cup',0):.0f} CUP\nDatos: {msg_text}\n\nCopiable:\n`{msg_text}`", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Pedido #{pedido_id} registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido")
        context.user_data.clear()
    elif flow == "compra_usdt_monto":
        try:
            cant = float(msg_text.replace(",","."))
            total = cant * precios['usdt_compra']
            context.user_data["usdt"] = cant; context.user_data["total_cup"] = total
            context.user_data["flow"] = "compra_usdt_wallet"
            await update.message.reply_text(f"✅ #{pedido_id}\n{cant} USDT = {total:.0f} CUP\n\n✍️ Manda tu WALLET BEP20")
        except: await update.message.reply_text("⚠️ Solo número. Ej: 10")
    elif flow == "compra_usdt_wallet":
        context.user_data["wallet_cliente"] = msg_text
        context.user_data["flow"] = "compra_usdt_captura"
        await update.message.reply_text(f"✅ Wallet guardada\n\n💳 Transfiere {context.user_data['total_cup']:.0f} CUP a:\n`{TARJETA}`\n📲 {MOVIL}\n\n📸 Manda CAPTURA", parse_mode="Markdown")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"{admin_header('COMPRA USDT')}\nCantidad: {context.user_data['usdt']} USDT = {context.user_data['total_cup']:.0f} CUP")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET CLIENTE #{pedido_id} PARA COPIAR:\n\n`{msg_text}`", parse_mode="Markdown")
    elif flow == "compra_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} - {usuario}")
            context.user_data["flow"] = "compra_usdt_final"
            await update.message.reply_text("📸 Captura ✅\n\n📲 Escribe tu NÚMERO de contacto")
        else: await update.message.reply_text("⚠️ Manda captura 📸")
    elif flow == "compra_usdt_final":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN #{pedido_id}\n👤 {usuario}\nUSDT: {context.user_data['usdt']}\nTotal: {context.user_data['total_cup']:.0f} CUP\nContacto: {msg_text}\nWallet: {context.user_data['wallet_cliente']}\n\nWallet copiable:\n`{context.user_data['wallet_cliente']}`", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Pedido #{pedido_id} registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido")
        context.user_data.clear()
    elif flow == "venta_usdt_monto":
        try:
            cant = float(msg_text.replace(",","."))
            total = cant * precios['usdt_venta']
            context.user_data["usdt"] = cant; context.user_data["total_cup"] = total
            context.user_data["flow"] = "venta_usdt_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nVenderás {cant} USDT\n💰 Recibirás: {total:.0f} CUP")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🔗 Envía los {cant} USDT (BEP20) a:\n\n`{WALLET_BEP20}`\n\n👆 Toca para copiar\n\n📸 Luego manda CAPTURA", parse_mode="Markdown")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{admin_header('VENTA USDT')}\nCantidad: {cant} USDT = {total:.0f} CUP")
        except: await update.message.reply_text("⚠️ Solo número. Ej: 20")
    elif flow == "venta_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} - {usuario} - VENDE {context.user_data.get('usdt')} USDT")
            context.user_data["flow"] = "venta_usdt_datos"
            await update.message.reply_text(f"📸 Ok ✅\n\n💳 Manda TARJETA y NÚMERO donde te pagamos {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text("⚠️ Manda foto 📸")
    elif flow == "venta_usdt_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN #{pedido_id}\n👤 {usuario}\nVende: {context.user_data['usdt']} USDT\nRecibe: {context.user_data['total_cup']:.0f} CUP\nDatos: {msg_text}\n\nCopiable:\n`{msg_text}`", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Pedido #{pedido_id} registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido")
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
