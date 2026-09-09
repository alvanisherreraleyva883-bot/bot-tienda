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

MENSAJE_FINAL = "✅ Pedido registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido"

app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot activo"

PRECIOS_FILE = "precios.json"
lock_precios = Lock()

def cargar_precios():
    if os.path.exists(PRECIOS_FILE):
        try:
            with open(PRECIOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"saldo_compra": 900, "saldo_venta": 750, "usdt_compra": 360, "usdt_venta": 350}

def guardar_precios(d):
    with lock_precios:
        with open(PRECIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)

precios = cargar_precios()

def gen_id():
    return f"{random.randint(1000, 9999)}"

# COMANDOS ADMIN
async def cambiar_saldo(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args:
        return await update.message.reply_text(f"Actual compra saldo: {precios['saldo_compra']}\nUso: /saldo 950")
    try:
        precios["saldo_compra"] = int(context.args[0])
        guardar_precios(precios)
        await update.message.reply_text(f"✅ Saldo COMPRA -> {precios['saldo_compra']} CUP")
    except:
        await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_venta(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args:
        return await update.message.reply_text(f"Actual venta saldo: {precios['saldo_venta']}\nUso: /venta 780")
    try:
        precios["saldo_venta"] = int(context.args[0])
        guardar_precios(precios)
        await update.message.reply_text(f"✅ Saldo VENTA -> {precios['saldo_venta']} CUP")
    except:
        await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_usdtc(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args:
        return await update.message.reply_text(f"Actual compra USDT: {precios['usdt_compra']}\nUso: /usdtc 360")
    try:
        precios["usdt_compra"] = int(context.args[0])
        guardar_precios(precios)
        await update.message.reply_text(f"✅ USDT COMPRA -> {precios['usdt_compra']} CUP")
    except:
        await update.message.reply_text("⚠️ Usa solo números")

async def cambiar_usdtv(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    if not context.args:
        return await update.message.reply_text(f"Actual venta USDT: {precios['usdt_venta']}\nUso: /usdtv 350")
    try:
        precios["usdt_venta"] = int(context.args[0])
        guardar_precios(precios)
        await update.message.reply_text(f"✅ USDT VENTA -> {precios['usdt_venta']} CUP")
    except:
        await update.message.reply_text("⚠️ Usa solo números")

async def ver_precios(update, context):
    if update.effective_user.id!= ADMIN_USER_ID: return
    await update.message.reply_text(f"📊 PRECIOS ACTUALES:\nCompra saldo: {precios['saldo_compra']}\nVenta saldo: {precios['saldo_venta']}\nUSDT Compra: {precios['usdt_compra']}\nUSDT Venta: {precios['usdt_venta']}")

# MENU
async def mostrar_menu(u, c):
    kb = [
        [InlineKeyboardButton("📲💳 Comprar saldo", callback_data="comprar_saldo")],
        [InlineKeyboardButton("💵📱 Vender saldo", callback_data="vender_saldo")],
        [InlineKeyboardButton("🚀🪙 Comprar USDT", callback_data="comprar_crypto")],
        [InlineKeyboardButton("💸🔗 Vender USDT", callback_data="vender_crypto")]
    ]
    rm = InlineKeyboardMarkup(kb)
    if isinstance(u, Update):
        await u.message.reply_text("🛍️ Bienvenido a la Tienda\nElige una opción:", reply_markup=rm)
    else:
        await u.edit_message_text("🛍️ Bienvenido a la Tienda\nElige una opción:", reply_markup=rm)

async def tienda(u, c): await mostrar_menu(u, c)
async def soporte(u, c): await u.message.reply_text("📞 SOPORTE: @TuUsuarioAdmin")

# BOTONES
async def button(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("confirmar_"):
        try:
            _, user_id_str, pedido_id = data.split("_", 2)
            user_id = int(user_id_str)
            await context.bot.send_message(chat_id=user_id, text=f"✅ Pedido #{pedido_id} - ¡Pago realizado! ✅\n\nGracias por preferirnos 🙏\nUsa /tienda para nuevo pedido")
            await q.edit_message_text(text=q.message.text + f"\n\n✅ CONFIRMADO Y AVISADO AL CLIENTE - #{pedido_id}")
        except Exception as e:
            await q.answer(f"Error: {e}")
        return

    if data == "menu":
        await mostrar_menu(q, context)
        return

    pedido_id = gen_id()
    context.user_data.clear()
    context.user_data["pedido_id"] = pedido_id

    if data == "comprar_saldo":
        text = f"📲💳 **Comprar saldo** - `#{pedido_id}`\n\n💵 Precio: 360 = {precios['saldo_compra']} CUP\n\n✍️ Escribe cuánto saldo quieres\n_Ej: 360 o 500_"
        context.user_data["flow"] = "compra_saldo"
    elif data == "vender_saldo":
        text = f"💵📱 **Vender saldo** - `#{pedido_id}`\n\n💳 Pagamos: 360 = {precios['saldo_venta']} CUP\n\n✍️ Escribe cuánto saldo vas a vender\n_Ej: 360_"
        context.user_data["flow"] = "venta_saldo"
    elif data == "comprar_crypto":
        text = f"🚀🪙 **Comprar USDT (BEP20)** - `#{pedido_id}`\n\n💵 Precio: {precios['usdt_compra']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT quieres comprar?\n_Ej: 10_"
        context.user_data["flow"] = "compra_usdt_monto"
    elif data == "vender_crypto":
        text = f"💸🔗 **Vender USDT (BEP20)** - `#{pedido_id}`\n\n💵 Precio: {precios['usdt_venta']} CUP = 1 USDT\n\n✍️ ¿Cuántos USDT quieres vender?\n_Ej: 20_"
        context.user_data["flow"] = "venta_usdt_monto"
    else:
        return

    await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás", callback_data="menu")]]), parse_mode="Markdown")

# FLUJO DE MENSAJES
async def recibir_mensaje(update, context):
    if not update.message:
        return
    usuario = update.effective_user.first_name or "Usuario"
    username = f"@{update.effective_user.username}" if update.effective_user.username else "sin username"
    uid = update.effective_user.id
    flow = context.user_data.get("flow")
    pedido_id = context.user_data.get("pedido_id", gen_id())
    msg_text = update.message.text or ""

    if not flow:
        return await update.message.reply_text("Usa /tienda para empezar")

    def header(tipo):
        return f"🆕 #{pedido_id} - {tipo}\n👤 {usuario} {username}\n🆔 {uid}"

    def boton_confirmar():
        return InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Confirmar Pago #{pedido_id}", callback_data=f"confirmar_{uid}_{pedido_id}")]])

    # COMPRAR SALDO
    if flow == "compra_saldo":
        try:
            monto = float(msg_text.replace(",", "."))
            total = (monto / 360) * precios['saldo_compra']
            context.user_data["monto"] = monto
            context.user_data["total_cup"] = total
            context.user_data["flow"] = "compra_saldo_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nQuieres {monto:.0f} de saldo = {total:.0f} CUP\n\n💳 Transfiere {total:.0f} CUP a:\nTarjeta: `{TARJETA}`\nMóvil: {MOVIL}\n\n📸 Manda CAPTURA", parse_mode="Markdown")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA SALDO')}\nSaldo: {monto:.0f}\nTotal CUP: {total:.0f}")
        except:
            await update.message.reply_text("⚠️ Escribe solo el número. Ej: 360")

    elif flow == "compra_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} de {usuario}")
            context.user_data["flow"] = "compra_saldo_telefono"
            await update.message.reply_text("📸 Captura recibida ✅\n\n📲 Escribe tu NÚMERO donde te enviamos el saldo")
        else:
            await update.message.reply_text("⚠️ Manda foto de la captura 📸")

    elif flow == "compra_saldo_telefono":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pedido_id}\n👤 {usuario}\nSaldo: {context.user_data.get('monto',0):.0f} = {context.user_data.get('total_cup',0):.0f} CUP\nTel: {msg_text}\n\nCopiable: `{msg_text}`", parse_mode="Markdown", reply_markup=boton_confirmar())
        await update.message.reply_text(MENSAJE_FINAL)
        context.user_data.clear()

    # VENDER SALDO - CORREGIDO TARJETA Y NUMERO
    elif flow == "venta_saldo":
        try:
            monto = float(msg_text.replace(",", "."))
            total = (monto / 360) * precios['saldo_venta']
            context.user_data["monto"] = monto
            context.user_data["total_cup"] = total
            context.user_data["flow"] = "venta_saldo_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nVendes {monto:.0f} de saldo\n💰 Vas a recibir: {total:.0f} CUP\n\n📲 Transfiere el saldo a {MOVIL} y manda CAPTURA 📸")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('VENTA SALDO')}\nSaldo: {monto:.0f}\nA pagar: {total:.0f} CUP")
        except:
            await update.message.reply_text("⚠️ Escribe solo el número. Ej: 360")

    elif flow == "venta_saldo_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} de {usuario}")
            context.user_data["flow"] = "venta_saldo_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\n💳 Manda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else:
            await update.message.reply_text("⚠️ Manda foto de la captura 📸")

    elif flow == "venta_saldo_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pedido_id}\n👤 {usuario}\nVende: {context.user_data.get('monto',0):.0f}\nA pagar: {context.user_data.get('total_cup',0):.0f} CUP\nDatos: {msg_text}\n\nCopiable:\n`{msg_text}`", parse_mode="Markdown", reply_markup=boton_confirmar())
        await update.message.reply_text(MENSAJE_FINAL)
        context.user_data.clear()

    # COMPRAR USDT
    elif flow == "compra_usdt_monto":
        try:
            cant = float(msg_text.replace(",", "."))
            total = cant * precios['usdt_compra']
            context.user_data["usdt"] = cant
            context.user_data["total_cup"] = total
            context.user_data["flow"] = "compra_usdt_wallet"
            await update.message.reply_text(f"✅ #{pedido_id}\n{cant} USDT = {total:.0f} CUP\n\n✍️ Manda tu WALLET BEP20")
        except:
            await update.message.reply_text("⚠️ Solo número. Ej: 10")

    elif flow == "compra_usdt_wallet":
        context.user_data["wallet_cliente"] = msg_text
        context.user_data["flow"] = "compra_usdt_captura"
        await update.message.reply_text(f"✅ Wallet guardada\n\n💳 Transfiere {context.user_data['total_cup']:.0f} CUP a:\nTarjeta: `{TARJETA}`\nMóvil: {MOVIL}\n\n📸 Manda CAPTURA", parse_mode="Markdown")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA USDT')}\nCantidad: {context.user_data['usdt']} USDT = {context.user_data['total_cup']:.0f} CUP")
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET CLIENTE #{pedido_id} PARA COPIAR:\n\n`{msg_text}`", parse_mode="Markdown")

    elif flow == "compra_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} de {usuario}")
            context.user_data["flow"] = "compra_usdt_final"
            await update.message.reply_text("📸 Captura recibida ✅\n\n📲 Escribe tu NÚMERO de contacto")
        else:
            await update.message.reply_text("⚠️ Manda captura 📸")

    elif flow == "compra_usdt_final":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pedido_id}\n👤 {usuario}\nUSDT: {context.user_data['usdt']}\nTotal: {context.user_data['total_cup']:.0f} CUP\nContacto: {msg_text}\nWallet: {context.user_data['wallet_cliente']}\n\nWallet copiable:\n`{context.user_data['wallet_cliente']}`", parse_mode="Markdown", reply_markup=boton_confirmar())
        await update.message.reply_text(MENSAJE_FINAL)
        context.user_data.clear()

    # VENDER USDT - CORREGIDO TARJETA Y NUMERO
    elif flow == "venta_usdt_monto":
        try:
            cant = float(msg_text.replace(",", "."))
            total = cant * precios['usdt_venta']
            context.user_data["usdt"] = cant
            context.user_data["total_cup"] = total
            context.user_data["flow"] = "venta_usdt_captura"
            await update.message.reply_text(f"✅ #{pedido_id}\nVenderás {cant} USDT\n💰 Recibirás: {total:.0f} CUP")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🔗 Envía los {cant} USDT (BEP20) a esta wallet:\n\n`{WALLET_BEP20}`\n\n👆 Toca la wallet para copiarla\n\n📸 Luego manda la CAPTURA", parse_mode="Markdown")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('VENTA USDT')}\nCantidad: {cant} USDT = {total:.0f} CUP")
        except:
            await update.message.reply_text("⚠️ Solo número. Ej: 20")

    elif flow == "venta_usdt_captura":
        if update.message.photo:
            await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pedido_id} - {usuario} - VENDE {context.user_data.get('usdt')} USDT")
            context.user_data["flow"] = "venta_usdt_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\n💳 Manda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else:
            await update.message.reply_text("⚠️ Manda foto de la captura 📸")

    elif flow == "venta_usdt_datos":
        await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
        await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pedido_id}\n👤 {usuario}\nVende: {context.user_data['usdt']} USDT\nRecibe: {context.user_data['total_cup']:.0f} CUP\nDatos pago: {msg_text}\n\nCopiable:\n`{msg_text}`", parse_mode="Markdown", reply_markup=boton_confirmar())
        await update.message.reply_text(MENSAJE_FINAL)
        context.user_data.clear()

def run_flask():
    app_web.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).build()
    app.add_handler(CommandHandler("tienda", tienda))
    app.add_handler(CommandHandler("soporte", soporte))
    app.add_handler(CommandHandler("saldo", cambiar_saldo))
    app.add_handler(CommandHandler("venta", cambiar_venta))
    app.add_handler(CommandHandler("usdtc", cambiar_usdtc))
    app.add_handler(CommandHandler("usdtv", cambiar_usdtv))
    app.add_handler(CommandHandler("precios", ver_precios))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL, recibir_mensaje))
    print("🤖 Bot PRO activo con confirmación...")
    app.run_polling()

if __name__ == "__main__":
    main()
