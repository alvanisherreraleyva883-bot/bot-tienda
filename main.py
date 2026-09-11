import os, json, random, datetime
from flask import Flask
from threading import Thread, Lock
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
TOKEN = os.environ.get("TOKEN")
ADMIN_CHANNEL_ID = -1003602948532
ADMIN_USER_ID = 7450751212
TARJETA = "9238-1299-7507-3018"
MOVIL = "55348244"
WALLET_BEP20 = "0x5Ba930B965f535c202D224f4AEC5745174C2F5e9"
SOPORTE_USERNAME = "@AlvanisPivqvaplay"
MENSAJE_FINAL = "✅ Pedido registrado. Le pagaremos en breve. Gracias por preferirnos 🙏\n\nUsa /tienda para nuevo pedido"
ADVERTENCIA = "⚠️ ATENCIÓN:\nLa captura debe verse con TOTAL CLARIDAD (monto, fecha, referencia).\n\n🚫 Cualquier intento de engaño, captura falsa, editada o estafa = BANEO PERMANENTE y serás reportado en todos los grupos y canales."
MENSAJE_AGOTADO = "⚠️ Saldo ETECSA agotado por hoy límite 3\nPor favor vuelve mañana para realizar tu pedido. Te esperamos 🙏"
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

# --- INICIO NUEVO: SISTEMA DE TIENDA ABIERTA/CERRADA ---
TIENDA_FILE = "tienda.json"
lock_tienda = Lock()
def cargar_tienda():
    if os.path.exists(TIENDA_FILE):
        try:
            with open(TIENDA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cerrada", False)
        except: pass
    return False

def guardar_tienda(cerrada):
    with lock_tienda:
        with open(TIENDA_FILE, "w", encoding="utf-8") as f:
            json.dump({"cerrada": cerrada}, f)

tiendaCerrada = cargar_tienda()

MENSAJE_CERRADO = """🌙 ¡CubanStore está CERRADO ahora mismo! 🔒

🕒 Horario de trabajo:
De 8:00 AM a 10:30 PM
Hora de Cuba 🇨🇺"""

async def cmd_cerrar(u,c):
    global tiendaCerrada
    if u.effective_user.id!= ADMIN_USER_ID: return
    tiendaCerrada = True
    guardar_tienda(True)
    await u.message.reply_text("🔒 CubanStore CERRADA correctamente\n\nAhora cuando toquen cualquier botón les saldrá el cartel de cerrado.")

async def cmd_abrir(u,c):
    global tiendaCerrada
    if u.effective_user.id!= ADMIN_USER_ID: return
    tiendaCerrada = False
    guardar_tienda(False)
    await u.message.reply_text("🔓 CubanStore ABIERTA correctamente")

# --- FIN NUEVO ---

def gen_id(): return f"{random.randint(1000, 9999)}"
TRANSFER_FILE = "transferencias.json"
LIMITE_DIARIO = 3
lock_transfer = Lock()
def cargar_transfer():
    if not os.path.exists(TRANSFER_FILE):
        return {"usadas": 0, "fecha": str(datetime.date.today())}
    try:
        with open(TRANSFER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("fecha")!= str(datetime.date.today()):
            return {"usadas": 0, "fecha": str(datetime.date.today())}
        return data
    except:
        return {"usadas": 0, "fecha": str(datetime.date.today())}
def guardar_transfer(data):
    with lock_transfer:
        with open(TRANSFER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
PENDIENTES = {}
lock_pendientes = Lock()
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
async def cmd_gaste1(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    data = cargar_transfer()
    data["usadas"] = min(data["usadas"] + 1, LIMITE_DIARIO)
    data["fecha"] = str(datetime.date.today())
    guardar_transfer(data)
    await u.message.reply_text(f"✅ Anotado. Hoy: {data['usadas']}/{LIMITE_DIARIO} usadas. Te quedan {LIMITE_DIARIO - data['usadas']}")
async def cmd_reset(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    data = {"usadas": 0, "fecha": str(datetime.date.today())}
    guardar_transfer(data)
    await u.message.reply_text(f"♻️ Contador reseteado a 0/{LIMITE_DIARIO}. Saldo desbloqueado.")
async def cmd_estado(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    data = cargar_transfer()
    await u.message.reply_text(f"📊 ESTADO HOY {data['fecha']}:\nUsadas: {data['usadas']}/{LIMITE_DIARIO}\nQuedan: {LIMITE_DIARIO - data['usadas']}\n\n🏪 Tienda: {'🔒 CERRADA' if tiendaCerrada else '🔓 ABIERTA'}")
async def mostrar_menu(u,c):
    # BLOQUEO TAMBIEN EN /tienda
    if tiendaCerrada:
        if isinstance(u,Update):
            await u.message.reply_text(MENSAJE_CERRADO)
        else:
            await u.edit_message_text(MENSAJE_CERRADO)
        return
    kb=[[InlineKeyboardButton("📲💳 Comprar saldo",callback_data="comprar_saldo")],[InlineKeyboardButton("💵📱 Vender saldo",callback_data="vender_saldo")],[InlineKeyboardButton("🚀🪙 Comprar USDT",callback_data="comprar_crypto")],[InlineKeyboardButton("💸🔗 Vender USDT",callback_data="vender_crypto")]]
    if isinstance(u,Update): await u.message.reply_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
    else: await u.edit_message_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
async def tienda(u,c): await mostrar_menu(u,c)
async def soporte(u,c):
    await u.message.reply_text(f"📞 SOPORTE OFICIAL\n\n👤 Dueño: {SOPORTE_USERNAME}\n\nSi tienes dudas escríbeme directo al privado 🙏", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Hablar con Soporte", url="https://t.me/AlvanisPivqvaplay")]]))
async def button(update, context):
    q=update.callback_query; await q.answer()
    data=q.data
    if data.startswith("confirmar_"):
        try:
            _, uid_str, pid = data.split("_",2)
            await context.bot.send_message(chat_id=int(uid_str), text=f"✅ Pedido #{pid} - ¡Pago realizado! ✅\n\nGracias por preferirnos 🙏\nUsa /tienda para nuevo pedido")
            await q.edit_message_text(f"{q.message.text}\n\n✅ CONFIRMADO Y PAGADO - #{pid}")
        except Exception as e: print(e)
        return
    if data.startswith("aprobar_"):
        try:
            _, uid_str, pid = data.split("_",2)
            uid = int(uid_str)
            with lock_pendientes:
                info = PENDIENTES.pop(pid, None)
            if not info:
                await q.edit_message_text(f"{q.message.text}\n\n⚠️ Ya fue procesado #{pid}")
                return
            tipo = info["tipo"]
            user_data = context.application.user_data.get(uid, {})
            if tipo == "compra_saldo":
                user_data["flow"] = "compra_saldo_captura"
                user_data["monto"] = info["monto"]
                user_data["total_cup"] = info["total"]
                user_data["pedido_id"] = pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\nQuieres {info['monto']:.0f} saldo = {info['total']:.0f} CUP\n\nTransfiere {info['total']:.0f} CUP a:\nTarjeta: {TARJETA}\nMovil: {MOVIL}\n\n{ADVERTENCIA}\n\nAhora manda la CAPTURA 📸")
            elif tipo == "venta_saldo":
                user_data["flow"] = "venta_saldo_captura"
                user_data["monto"] = info["monto"]
                user_data["total_cup"] = info["total"]
                user_data["pedido_id"] = pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\nVendes {info['monto']:.0f} saldo\nRecibes: {info['total']:.0f} CUP\n\nTransfiere saldo a {MOVIL}\n\n{ADVERTENCIA}\n\nManda CAPTURA 📸")
            elif tipo == "compra_usdt":
                user_data["flow"] = "compra_usdt_wallet"
                user_data["usdt"] = info["monto"]
                user_data["total_cup"] = info["total"]
                user_data["pedido_id"] = pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\n{info['monto']} USDT = {info['total']:.0f} CUP\n\nManda tu WALLET BEP20")
            elif tipo == "venta_usdt":
                user_data["flow"] = "venta_usdt_captura"
                user_data["usdt"] = info["monto"]
                user_data["total_cup"] = info["total"]
                user_data["pedido_id"] = pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\nVenderás {info['monto']} USDT\nRecibirás: {info['total']:.0f} CUP\n\nEnvía los {info['monto']} USDT a:\n<code>{WALLET_BEP20}</code>\n\n{ADVERTENCIA}\n\nLuego manda CAPTURA 📸", parse_mode="HTML")
            context.application.user_data[uid] = user_data
            await q.edit_message_text(f"{q.message.text}\n\n✅ APROBADO POR TI - #{pid}")
        except Exception as e: print(f"Error aprobar: {e}")
        return
    if data.startswith("rechazar_"):
        try:
            _, uid_str, pid = data.split("_",2)
            uid = int(uid_str)
            with lock_pendientes:
                PENDIENTES.pop(pid, None)
            if uid in context.application.user_data:
                context.application.user_data[uid].clear()
            await context.bot.send_message(uid, f"❌ Pedido #{pid} rechazado.\n\nNo se pudo realizar la operación en este momento, intenta más tarde.\nUsa /tienda")
            await q.edit_message_text(f"{q.message.text}\n\n❌ RECHAZADO POR TI - #{pid}")
        except Exception as e: print(f"Error rechazar: {e}")
        return
    if data=="menu": await mostrar_menu(q,context); return

    # --- BLOQUEO DE TIENDA CERRADA PARA LOS 4 BOTONES ---
    if tiendaCerrada and data in ["comprar_saldo", "vender_saldo", "comprar_crypto", "vender_crypto"]:
        await q.edit_message_text(MENSAJE_CERRADO, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver",callback_data="menu")]]))
        return
    # --- FIN BLOQUEO ---

    pid=gen_id()
    context.user_data.clear()
    context.user_data["pedido_id"]=pid
    if data=="comprar_saldo":
        trans = cargar_transfer()
        if trans["usadas"] >= LIMITE_DIARIO:
            await q.edit_message_text(MENSAJE_AGOTADO, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver",callback_data="menu")]]))
            return
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
    if txt.startswith("/"): return
    if not flow: return await update.message.reply_text("Usa /tienda")
    def header(t): return f"🆕 #{pid} - {t}\n👤 {usuario} {username}\n🆔 {uid}"
    def btn_confirmar(): return InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Confirmar Pago #{pid}", callback_data=f"confirmar_{uid}_{pid}")]])
    def btn_aprobacion():
        return InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ APROBAR #{pid}", callback_data=f"aprobar_{uid}_{pid}"), InlineKeyboardButton(f"❌ RECHAZAR", callback_data=f"rechazar_{uid}_{pid}")]])
    if flow=="compra_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_compra']
            with lock_pendientes:
                PENDIENTES[pid] = {"uid": uid, "tipo": "compra_saldo", "monto": monto, "total": total, "usuario": usuario, "username": username}
            await update.message.reply_text(f"⏳ #{pid}\nSolicitud de {monto:.0f} saldo = {total:.0f} CUP enviada a revisión.\nTe avisamos cuando sea aprobada.")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 SOLICITUD PENDIENTE #{pid}\n{header('COMPRA SALDO')}\nSaldo: {monto:.0f}\nTotal: {total:.0f} CUP\n\n¿Aprobar?", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número. Ej: 360")
    elif flow=="compra_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="compra_saldo_telefono"
            await update.message.reply_text("📸 Captura recibida ✅\n\nEscribe tu NÚMERO donde te enviamos el saldo")
        else: await update.message.reply_text(f"Manda foto con claridad 📸\n\n{ADVERTENCIA}")
    elif flow=="compra_saldo_telefono":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nSaldo: {context.user_data.get('monto',0):.0f} = {context.user_data.get('total_cup',0):.0f} CUP", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📱 NUMERO COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="venta_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_venta']
            with lock_pendientes:
                PENDIENTES[pid] = {"uid": uid, "tipo": "venta_saldo", "monto": monto, "total": total, "usuario": usuario, "username": username}
            await update.message.reply_text(f"⏳ #{pid}\nSolicitud de vender {monto:.0f} saldo = {total:.0f} CUP enviada a revisión.")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 SOLICITUD PENDIENTE #{pid}\n{header('VENTA SALDO')}\nSaldo: {monto:.0f}\nA pagar: {total:.0f} CUP\n\n¿Aprobar?", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número. Ej: 360")
    elif flow=="venta_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="venta_saldo_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\nManda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text(f"Manda foto con claridad 📸\n\n{ADVERTENCIA}")
    elif flow=="venta_saldo_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {context.user_data.get('monto',0):.0f}\nA pagar: {context.user_data.get('total_cup',0):.0f} CUP", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💳 TARJETA Y NUMERO COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="compra_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_compra']
            with lock_pendientes:
                PENDIENTES[pid] = {"uid": uid, "tipo": "compra_usdt", "monto": cant, "total": total, "usuario": usuario, "username": username}
            await update.message.reply_text(f"⏳ #{pid}\nSolicitud de {cant} USDT = {total:.0f} CUP enviada a revisión.")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 SOLICITUD PENDIENTE #{pid}\n{header('COMPRA USDT')}\nCantidad: {cant} USDT = {total:.0f} CUP\n\n¿Aprobar?", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número. Ej: 10")
    elif flow=="compra_usdt_wallet":
        context.user_data["wallet_cliente"]=txt; context.user_data["flow"]="compra_usdt_captura"
        await update.message.reply_text(f"✅ Wallet guardada\n\nTransfiere {context.user_data['total_cup']:.0f} CUP a:\nTarjeta: {TARJETA}\nMovil: {MOVIL}\n\n{ADVERTENCIA}\n\nManda CAPTURA 📸")
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA USDT')}\nCantidad: {context.user_data['usdt']} USDT = {context.user_data['total_cup']:.0f} CUP")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
    elif flow=="compra_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="compra_usdt_final"
            await update.message.reply_text("📸 Captura ✅\n\nEscribe tu NÚMERO de contacto")
        else: await update.message.reply_text(f"Manda captura con claridad 📸\n\n{ADVERTENCIA}")
    elif flow=="compra_usdt_final":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nUSDT: {context.user_data['usdt']}\nTotal: {context.user_data['total_cup']:.0f} CUP\nContacto: {txt}", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET + CONTACTO COPIABLE #{pid}:\nWallet: <code>{context.user_data['wallet_cliente']}</code>\nNumero: <code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="venta_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_venta']
            with lock_pendientes:
                PENDIENTES[pid] = {"uid": uid, "tipo": "venta_usdt", "monto": cant, "total": total, "usuario": usuario, "username": username}
            await update.message.reply_text(f"⏳ #{pid}\nSolicitud de vender {cant} USDT = {total:.0f} CUP enviada a revisión.")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 SOLICITUD PENDIENTE #{pid}\n{header('VENTA USDT')}\nCantidad: {cant} USDT = {total:.0f} CUP\n\n¿Aprobar?", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número. Ej: 20")
    elif flow=="venta_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="venta_usdt_datos"
            await update.message.reply_text(f"📸 Captura recibida ✅\n\nManda tu TARJETA CUP y tu NÚMERO a confirmar para pagarte los {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text(f"Manda captura con claridad 📸\n\n{ADVERTENCIA}")
    elif flow=="venta_usdt_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {context.user_data['usdt']} USDT\nRecibe: {context.user_data['total_cup']:.0f} CUP", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💳 DATOS COPIABLES #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
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
    app.add_handler(CommandHandler("gaste1",cmd_gaste1))
    app.add_handler(CommandHandler("reset",cmd_reset))
    app.add_handler(CommandHandler("estado",cmd_estado))
    # NUEVOS COMANDOS DE CIERRE
    app.add_handler(CommandHandler("cerrar",cmd_cerrar))
    app.add_handler(CommandHandler("abrir",cmd_abrir))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, recibir_mensaje))
    print("🤖 Bot FINAL FIX FOTO OK"); app.run_polling()
if __name__=="__main__": main()
