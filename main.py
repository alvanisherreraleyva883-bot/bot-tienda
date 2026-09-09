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
def gen_id(): return f"{random.randint(1000, 9999)}"

async def cambiar_saldo(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['saldo_compra']}\nUso: /saldo 950")
    precios["saldo_compra"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ Compra -> {precios['saldo_compra']}")
async def cambiar_venta(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['saldo_venta']}\nUso: /venta 780")
    precios["saldo_venta"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ Venta -> {precios['saldo_venta']}")
async def cambiar_usdtc(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['usdt_compra']}\nUso: /usdtc 360")
    precios["usdt_compra"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ USDT Compra -> {precios['usdt_compra']}")
async def cambiar_usdtv(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['usdt_venta']}\nUso: /usdtv 350")
    precios["usdt_venta"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ USDT Venta -> {precios['usdt_venta']}")
async def ver_precios(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    await u.message.reply_text(f"PRECIOS:\nCompra saldo: {precios['saldo_compra']}\nVenta saldo: {precios['saldo_venta']}\nUSDT Compra: {precios['usdt_compra']}\nUSDT Venta: {precios['usdt_venta']}")

async def mostrar_menu(u,c):
    kb=[[InlineKeyboardButton("📲💳 Comprar saldo",callback_data="comprar_saldo")],[InlineKeyboardButton("💵📱 Vender saldo",callback_data="vender_saldo")],[InlineKeyboardButton("🚀🪙 Comprar USDT",callback_data="comprar_crypto")],[InlineKeyboardButton("💸🔗 Vender USDT",callback_data="vender_crypto")]]
    if isinstance(u,Update): await u.message.reply_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
    else: await u.edit_message_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
async def tienda(u,c): await mostrar_menu(u,c)
async def soporte(u,c): await u.message.reply_text("📞 @TuAdmin")

async def button(update, context):
    q=update.callback_query; await q.answer()
    data=q.data
    if data.startswith("confirmar_"):
        try:
            _, uid_str, pid = data.split("_",2)
            await context.bot.send_message(chat_id=int(uid_str), text=f"✅ Pedido #{pid} - ¡Pago realizado! ✅\n\nGracias por preferirnos 🙏")
            await q.edit_message_text(f"{q.message.text}\n\n✅ CONFIRMADO - #{pid}")
        except Exception as e:
            print(f"Error confirmar: {e}")
        return
    if data=="menu": await mostrar_menu(q,context); return
    pid=gen_id()
    context.user_data.clear()
    context.user_data["pedido_id"]=pid
    if data=="comprar_saldo":
        context.user_data["flow"]="compra_saldo"
        await q.edit_message_text(f"📲💳 Comprar saldo - #{pid}\n\n💵 360 = {precios['saldo_compra']} CUP\n\nEscribe cuánto quieres:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="vender_saldo":
        context.user_data["flow"]="venta_saldo"
        await q.edit_message_text(f"💵📱 Vender saldo - #{pid}\n\nPagamos: 360 = {precios['saldo_venta']} CUP\n\nEscribe cuánto vendes:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="comprar_crypto":
        context.user_data["flow"]="compra_usdt_monto"
        await q.edit_message_text(f"🚀🪙 Comprar USDT - #{pid}\n\nPrecio: {precios['usdt_compra']} CUP = 1 USDT\n\n¿Cuántos USDT?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="vender_crypto":
        context.user_data["flow"]="venta_usdt_monto"
        await q.edit_message_text(f"💸🔗 Vender USDT - #{pid}\n\nPagamos: {precios['usdt_venta']} CUP = 1 USDT\n\n¿Cuántos vendes?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))

async def recibir_mensaje(update, context):
    if not update.message: return
    usuario=update.effective_user.first_name or "Usuario"
    username=f"@{update.effective_user.username}" if update.effective_user.username else ""
    uid=update.effective_user.id
    flow=context.user_data.get("flow")
    pid=context.user_data.get("pedido_id", gen_id())
    txt=update.message.text or ""
    if not flow:
        return await update.message.reply_text("Usa /tienda")

    def header(t): return f"🆕 #{pid} - {t}\n👤 {usuario} {username}\n🆔 {uid}"
    def btn_confirmar():
        return InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Confirmar Pago #{pid}", callback_data=f"confirmar_{uid}_{pid}")]])

    # COMPRAR SALDO
    if flow=="compra_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_compra']
            context.user_data["monto"]=monto; context.user_data["total_cup"]=total; context.user_data["flow"]="compra_saldo_captura"
            await update.message.reply_text(f"✅ #{pid}\nQuieres {monto:.0f} saldo = {total:.0f} CUP\n\nTransfiere {total:.0f} CUP a:\nTarjeta: {TARJETA}\nMovil: {MOVIL}\n\nManda CAPTURA")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA SALDO')}\nSaldo: {monto:.0f}\nTotal: {total:.0f} CUP")
        except: await update.message.reply_text("Solo número. Ej: 360")
    elif flow=="compra_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            except: pass
            try: await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pid} de {usuario}")
            except: pass
            context.user_data["flow"]="compra_saldo_telefono"
            await update.message.reply_text("📸 Captura recibida ✅\n\nEscribe tu NÚMERO donde te enviamos el saldo")
        else: await update.message.reply_text("Manda foto 📸")
    elif flow=="compra_saldo_telefono":
        # Primero avisamos al cliente SIEMPRE, aunque falle el grupo
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nSaldo: {context.user_data.get('monto',0):.0f} = {context.user_data.get('total_cup',0):.0f} CUP\nTel: {txt}\nCopiable: {txt}", reply_markup=btn_confirmar())
        except Exception as e: print(f"Error grupo: {e}")
        context.user_data.clear()

    # VENDER SALDO
    elif flow=="venta_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_venta']
            context.user_data["monto"]=monto; context.user_data["total_cup"]=total; context.user_data["flow"]="venta_saldo_captura"
            await update.message.reply_text(f"✅ #{pid}\nVendes {monto:.0f} saldo\nRecibes: {total:.0f} CUP\n\nTransfiere saldo a {MOVIL} y manda CAPTURA")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('VENTA SALDO')}\nSaldo: {monto:.0f}\nA pagar: {total:.0f} CUP")
        except: await update.message.reply_text("Solo número. Ej: 360")
    elif flow=="venta_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            except: pass
            try: await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pid} de {usuario}")
            except: pass
            context.user_data["flow"]="venta_saldo_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\nManda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text("Manda foto 📸")
    elif flow=="venta_saldo_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {context.user_data.get('monto',0):.0f}\nPagar: {context.user_data.get('total_cup',0):.0f} CUP\nDatos: {txt}\nCopiable: {txt}", reply_markup=btn_confirmar())
        except Exception as e: print(f"Error grupo: {e}")
        context.user_data.clear()

    # COMPRAR USDT
    elif flow=="compra_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_compra']
            context.user_data["usdt"]=cant; context.user_data["total_cup"]=total; context.user_data["flow"]="compra_usdt_wallet"
            await update.message.reply_text(f"✅ #{pid}\n{cant} USDT = {total:.0f} CUP\n\nManda tu WALLET BEP20")
        except: await update.message.reply_text("Solo número. Ej: 10")
    elif flow=="compra_usdt_wallet":
        context.user_data["wallet_cliente"]=txt; context.user_data["flow"]="compra_usdt_captura"
        await update.message.reply_text(f"✅ Wallet guardada\n\nTransfiere {context.user_data['total_cup']:.0f} CUP a:\nTarjeta: {TARJETA}\nMovil: {MOVIL}\n\nManda CAPTURA")
        try: await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA USDT')}\nCantidad: {context.user_data['usdt']} USDT\nWallet: {txt}")
        except: pass
    elif flow=="compra_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            except: pass
            try: await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pid} - {usuario}")
            except: pass
            context.user_data["flow"]="compra_usdt_final"
            await update.message.reply_text("📸 Captura ✅\n\nEscribe tu NÚMERO de contacto")
        else: await update.message.reply_text("Manda captura 📸")
    elif flow=="compra_usdt_final":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nUSDT: {context.user_data['usdt']}\nTotal: {context.user_data['total_cup']:.0f} CUP\nContacto: {txt}\nWallet: {context.user_data['wallet_cliente']}", reply_markup=btn_confirmar())
        except Exception as e: print(f"Error grupo: {e}")
        context.user_data.clear()

    # VENDER USDT
    elif flow=="venta_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_venta']
            context.user_data["usdt"]=cant; context.user_data["total_cup"]=total; context.user_data["flow"]="venta_usdt_captura"
            await update.message.reply_text(f"✅ #{pid}\nVenderás {cant} USDT\nRecibirás: {total:.0f} CUP\n\nEnvía los {cant} USDT a:\n{WALLET_BEP20}\n\nLuego manda CAPTURA")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('VENTA USDT')}\nCantidad: {cant} USDT = {total:.0f} CUP")
        except: await update.message.reply_text("Solo número. Ej: 20")
    elif flow=="venta_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(chat_id=ADMIN_CHANNEL_ID)
            except: pass
            try: await context.bot.send_message(ADMIN_CHANNEL_ID, f"📸 CAPTURA #{pid} - VENDE {context.user_data.get('usdt')} USDT")
            except: pass
            context.user_data["flow"]="venta_usdt_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\nManda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text("Manda foto 📸")
    elif flow=="venta_usdt_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {context.user_data['usdt']} USDT\nRecibe: {context.user_data['total_cup']:.0f} CUP\nDatos: {txt}\nCopiable: {txt}", reply_markup=btn_confirmar())
        except Exception as e: print(f"Error grupo: {e}")
        context.user_data.clear()

def run_flask(): app_web.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
def main():
    Thread(target=run_flask,daemon=True).start()
    app=Application.builder().token(TOKEN).read_timeout(60).write_timeout(60).connect_timeout(60).build()
    app.add_handler(CommandHandler("tienda",tienda))
    app.add_handler(CommandHandler("soporte",soporte))
    app.add_handler(CommandHandler("saldo",cambiar_saldo))
    app.add_handler(CommandHandler("venta",cambiar_venta))
    app.add_handler(CommandHandler("usdtc",cambiar_usdtc))
    app.add_handler(CommandHandler("usdtv",cambiar_usdtv))
    app.add_handler(CommandHandler("precios",ver_precios))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL,recibir_mensaje))
    print("🤖 Bot PRO FIX activo..."); app.run_polling()
if __name__=="__main__": main()
