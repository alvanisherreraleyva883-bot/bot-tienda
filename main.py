import os, json, random, datetime
from flask import Flask
from threading import Thread, Lock
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get("TOKEN")
ADMIN_CHANNEL_ID = -1003602948532
CANAL_PAGOS_ID = -1004381290292
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
    return {"saldo_compra": 0, "saldo_venta": 0, "usdt_compra": 0, "usdt_venta": 0}
def guardar_precios(d):
    with lock_precios:
        with open(PRECIOS_FILE, "w", encoding="utf-8") as f: json.dump(d, f)
precios = cargar_precios()

STOCK_FILE = "stock.json"
lock_stock = Lock()
def cargar_stock():
    if os.path.exists(STOCK_FILE):
        try:
            with open(STOCK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"saldo": float(data.get("saldo", 0)), "usdt": float(data.get("usdt", 0))}
        except: pass
    return {"saldo": 0, "usdt": 0}
def guardar_stock(d):
    with lock_stock:
        with open(STOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
stock = cargar_stock()

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
🕒 Horario: 8:00 AM a 10:30 PM Hora Cuba 🇨🇺"""

async def cmd_cerrar(u,c):
    global tiendaCerrada
    if u.effective_user.id!= ADMIN_USER_ID: return
    tiendaCerrada = True; guardar_tienda(True)
    await u.message.reply_text("🔒 CERRADA")
async def cmd_abrir(u,c):
    global tiendaCerrada
    if u.effective_user.id!= ADMIN_USER_ID: return
    tiendaCerrada = False; guardar_tienda(False)
    await u.message.reply_text("🔓 ABIERTA")

def gen_id(): return f"{random.randint(1000, 9999)}"
TRANSFER_FILE = "transferencias.json"
LIMITE_DIARIO = 3
lock_transfer = Lock()
def cargar_transfer():
    if not os.path.exists(TRANSFER_FILE): return {"usadas": 0, "fecha": str(datetime.date.today())}
    try:
        with open(TRANSFER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("fecha")!= str(datetime.date.today()): return {"usadas": 0, "fecha": str(datetime.date.today())}
        return data
    except: return {"usadas": 0, "fecha": str(datetime.date.today())}
def guardar_transfer(data):
    with lock_transfer:
        with open(TRANSFER_FILE, "w", encoding="utf-8") as f: json.dump(data, f)

PENDIENTES = {}
PAGOS_INFO = {}
lock_pendientes = Lock()

async def cmd_stock(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return await u.message.reply_text("❌ Solo admin")
    if not c.args: return await u.message.reply_text(f"STOCK: Saldo {stock['saldo']:.0f} | USDT {stock['usdt']:.0f}")
    if c.args[0].lower()=="ver": return await u.message.reply_text(f"Saldo: {stock['saldo']:.0f} | USDT: {stock['usdt']:.0f}")
    if len(c.args)<2: return await u.message.reply_text("Uso: /stock saldo 100")
    tipo=c.args[0].lower()
    try: cantidad=float(c.args[1].replace(",","."))
    except: return await u.message.reply_text("Cantidad inválida")
    if tipo in ["saldo","cup"]: stock["saldo"]=cantidad; guardar_stock(stock); await u.message.reply_text(f"Saldo -> {cantidad:.0f}")
    elif tipo in ["usdt","crypto"]: stock["usdt"]=cantidad; guardar_stock(stock); await u.message.reply_text(f"USDT -> {cantidad:.0f}")

async def cambiar_saldo(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['saldo_compra']}")
    precios["saldo_compra"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ {precios['saldo_compra']}")
async def cambiar_venta(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['saldo_venta']}")
    precios["saldo_venta"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ {precios['saldo_venta']}")
async def cambiar_usdtc(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['usdt_compra']}")
    precios["usdt_compra"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ {precios['usdt_compra']}")
async def cambiar_usdtv(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    if not c.args: return await u.message.reply_text(f"Actual: {precios['usdt_venta']}")
    precios["usdt_venta"]=int(c.args[0]); guardar_precios(precios); await u.message.reply_text(f"✅ {precios['usdt_venta']}")
async def ver_precios(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    await u.message.reply_text(f"Compra:{precios['saldo_compra']} Venta:{precios['saldo_venta']} USDTc:{precios['usdt_compra']} USDTv:{precios['usdt_venta']} Stock S:{stock['saldo']:.0f} U:{stock['usdt']:.0f}")
async def cmd_gaste1(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    data=cargar_transfer(); data["usadas"]=min(data["usadas"]+1,LIMITE_DIARIO); data["fecha"]=str(datetime.date.today()); guardar_transfer(data)
    await u.message.reply_text(f"Anotado {data['usadas']}/{LIMITE_DIARIO}")
async def cmd_reset(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    guardar_transfer({"usadas":0,"fecha":str(datetime.date.today())}); await u.message.reply_text("Reseteado")
async def cmd_estado(u,c):
    if u.effective_user.id!= ADMIN_USER_ID: return
    data=cargar_transfer(); await u.message.reply_text(f"Usadas {data['usadas']}/{LIMITE_DIARIO} Tienda {'CERRADA' if tiendaCerrada else 'ABIERTA'} Stock {stock['saldo']:.0f}/{stock['usdt']:.0f}")

async def mostrar_menu(u,c):
    if tiendaCerrada:
        if isinstance(u,Update): await u.message.reply_text(MENSAJE_CERRADO)
        else: await u.edit_message_text(MENSAJE_CERRADO); return
    kb=[[InlineKeyboardButton("📲💳 Comprar saldo",callback_data="comprar_saldo")],[InlineKeyboardButton("💵📱 Vender saldo",callback_data="vender_saldo")],[InlineKeyboardButton("🚀🪙 Comprar USDT",callback_data="comprar_crypto")],[InlineKeyboardButton("💸🔗 Vender USDT",callback_data="vender_crypto")]]
    if isinstance(u,Update): await u.message.reply_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
    else: await u.edit_message_text("🛍️ Elige:",reply_markup=InlineKeyboardMarkup(kb))
async def tienda(u,c): await mostrar_menu(u,c)
async def soporte(u,c): await u.message.reply_text(f"Soporte {SOPORTE_USERNAME}")

async def button(update, context):
    q=update.callback_query; await q.answer(); data=q.data
    if data.startswith("confirmar_"):
        try:
            _, uid_str, pid = data.split("_",2)
            await context.bot.send_message(chat_id=int(uid_str), text=f"✅ Pedido #{pid} - ¡Pago realizado! ✅\n\nGracias por preferirnos 🙏\nUsa /tienda")
            await q.edit_message_text(f"{q.message.text}\n\n✅ CONFIRMADO Y PAGADO - #{pid}")
            try:
                info = PAGOS_INFO.get(pid, {})
                operacion = info.get("operacion", "intercambio")
                monto = info.get("monto", "0.00 CUP")
                usuario_txt = info.get("usuario", "Usuario")
                # COMPROBANTE FINAL CON ESTADO ARRIBA Y PAGADO ABAJO COMO EN LA FOTO
                texto_canal = f"📢 Solicitud completada\n\n🧾 No. pedido: {pid}\n💱 Operación: {operacion}\n💰 Monto pagado: {monto}\n👤 Usuario: {usuario_txt}\n\n📊 Estado:\n--- ✅ Pagado ---"
                await context.bot.send_message(chat_id=CANAL_PAGOS_ID, text=texto_canal)
                PAGOS_INFO.pop(pid, None)
            except Exception as e2: print(e2)
        except Exception as e: print(e)
        return
    if data.startswith("aprobar_"):
        try:
            _, uid_str, pid = data.split("_",2); uid=int(uid_str)
            with lock_pendientes: info=PENDIENTES.pop(pid,None)
            if not info: await q.edit_message_text(f"{q.message.text}\n\n⚠️ Ya procesado #{pid}"); return
            tipo=info["tipo"]; user_data=context.application.user_data.get(uid,{})
            if tipo=="compra_saldo":
                user_data["flow"]="compra_saldo_captura"; user_data["monto"]=info["monto"]; user_data["total_cup"]=info["total"]; user_data["pedido_id"]=pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\n{info['monto']:.0f} saldo = {info['total']:.0f} CUP\n💳 Tarjeta: <code>{TARJETA}</code>\nMóvil: <code>{MOVIL}</code>\n\n{ADVERTENCIA}\n\nManda CAPTURA", parse_mode="HTML")
            elif tipo=="venta_saldo":
                user_data["flow"]="venta_saldo_captura"; user_data["monto"]=info["monto"]; user_data["total_cup"]=info["total"]; user_data["pedido_id"]=pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\nVendes {info['monto']:.0f} = {info['total']:.0f} CUP\nTransfiere a <code>{MOVIL}</code>\n\n{ADVERTENCIA}\n\nManda CAPTURA", parse_mode="HTML")
            elif tipo=="compra_usdt":
                user_data["flow"]="compra_usdt_wallet"; user_data["usdt"]=info["monto"]; user_data["total_cup"]=info["total"]; user_data["pedido_id"]=pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\n{info['monto']} USDT = {info['total']:.0f} CUP\nManda WALLET BEP20")
            elif tipo=="venta_usdt":
                user_data["flow"]="venta_usdt_captura"; user_data["usdt"]=info["monto"]; user_data["total_cup"]=info["total"]; user_data["pedido_id"]=pid
                await context.bot.send_message(uid, f"✅ #{pid} APROBADO\n\nVenderás {info['monto']} USDT = {info['total']:.0f} CUP\nEnvía a <code>{WALLET_BEP20}</code>\n\n{ADVERTENCIA}\n\nManda CAPTURA", parse_mode="HTML")
            await q.edit_message_text(f"{q.message.text}\n\n✅ APROBADO - #{pid}")
        except Exception as e: print(e)
        return
    if data.startswith("rechazar_"):
        try:
            _, uid_str, pid = data.split("_",2); uid=int(uid_str)
            with lock_pendientes: PENDIENTES.pop(pid,None)
            if uid in context.application.user_data: context.application.user_data[uid].clear()
            await context.bot.send_message(uid, f"❌ Pedido #{pid} rechazado. Usa /tienda")
            await q.edit_message_text(f"{q.message.text}\n\n❌ RECHAZADO - #{pid}")
        except: pass
        return
    if data=="menu": await mostrar_menu(q,context); return
    if tiendaCerrada and data in ["comprar_saldo","vender_saldo","comprar_crypto","vender_crypto"]:
        await q.edit_message_text(MENSAJE_CERRADO); return
    pid=gen_id(); context.user_data.clear(); context.user_data["pedido_id"]=pid
    if data=="comprar_saldo":
        trans=cargar_transfer()
        if trans["usadas"]>=LIMITE_DIARIO: await q.edit_message_text(MENSAJE_AGOTADO); return
        if stock.get("saldo",0)<=0: await q.edit_message_text("💰 Saldo 0 ❌ AGOTADO"); return
        context.user_data["flow"]="compra_saldo"
        await q.edit_message_text(f"📲💳 Comprar saldo - #{pid}\n💰 Disponible: {stock['saldo']:.0f}\nPrecio 360 = {precios['saldo_compra']} CUP\n\nEscribe cuánto:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="vender_saldo":
        context.user_data["flow"]="venta_saldo"
        await q.edit_message_text(f"💵📱 Vender saldo - #{pid}\nPagamos 360 = {precios['saldo_venta']}\nCuánto vendes?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="comprar_crypto":
        if stock.get("usdt",0)<=0: await q.edit_message_text("USDT 0 ❌ AGOTADO"); return
        context.user_data["flow"]="compra_usdt_monto"
        await q.edit_message_text(f"🚀🪙 Comprar USDT - #{pid}\nDisponible: {stock['usdt']:.0f}\nPrecio {precios['usdt_compra']} CUP\n¿Cuántos?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))
    elif data=="vender_crypto":
        context.user_data["flow"]="venta_usdt_monto"
        await q.edit_message_text(f"💸🔗 Vender USDT - #{pid}\nPagamos {precios['usdt_venta']} CUP\n¿Cuántos?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Atrás",callback_data="menu")]]))

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
    def btn_aprobacion(): return InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ APROBAR #{pid}", callback_data=f"aprobar_{uid}_{pid}"), InlineKeyboardButton(f"❌ RECHAZAR", callback_data=f"rechazar_{uid}_{pid}")]])
    if flow=="compra_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_compra']
            with lock_pendientes: PENDIENTES[pid]={"uid":uid,"tipo":"compra_saldo","monto":monto,"total":total,"usuario":usuario,"username":username}
            await update.message.reply_text(f"⏳ #{pid} Solicitud {monto:.0f} = {total:.0f} CUP enviada")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 PENDIENTE #{pid}\n{header('COMPRA SALDO')}\nSaldo: {monto:.0f}\nTotal: {total:.0f}", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número Ej: 360")
    elif flow=="compra_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="compra_saldo_telefono"
            await update.message.reply_text("📸 Recibida\nEscribe tu NÚMERO")
        else: await update.message.reply_text(f"Manda foto 📸\n{ADVERTENCIA}")
    elif flow=="compra_saldo_telefono":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            monto=context.user_data.get('monto',0); total=context.user_data.get('total_cup',0)
            PAGOS_INFO[pid]={"operacion":"compra de saldo","monto":f"{total:.2f} CUP","usuario":f"{usuario} {username}"}
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nSaldo: {monto:.0f} = {total:.0f} CUP", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📱 NUMERO COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="venta_saldo":
        try:
            monto=float(txt.replace(",","."))
            total=(monto/360)*precios['saldo_venta']
            with lock_pendientes: PENDIENTES[pid]={"uid":uid,"tipo":"venta_saldo","monto":monto,"total":total,"usuario":usuario,"username":username}
            await update.message.reply_text(f"⏳ #{pid} Vender {monto:.0f} = {total:.0f} CUP")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 PENDIENTE #{pid}\n{header('VENTA SALDO')}\nSaldo: {monto:.0f}\nA pagar: {total:.0f}", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número")
    elif flow=="venta_saldo_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="venta_saldo_datos"
            await update.message.reply_text(f"📸 Recibida\nManda TARJETA y NÚMERO para {context.user_data.get('total_cup',0):.0f} CUP")
        else: await update.message.reply_text(f"Manda foto 📸\n{ADVERTENCIA}")
    elif flow=="venta_saldo_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            monto=context.user_data.get('monto',0); total=context.user_data.get('total_cup',0)
            PAGOS_INFO[pid]={"operacion":"venta de saldo","monto":f"{total:.2f} CUP","usuario":f"{usuario} {username}"}
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {monto:.0f}\nA pagar: {total:.0f}", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💳 COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="compra_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_compra']
            with lock_pendientes: PENDIENTES[pid]={"uid":uid,"tipo":"compra_usdt","monto":cant,"total":total,"usuario":usuario,"username":username}
            await update.message.reply_text(f"⏳ #{pid} {cant} USDT = {total:.0f} CUP")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 PENDIENTE #{pid}\n{header('COMPRA USDT')}\n{cant} USDT = {total:.0f}", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número")
    elif flow=="compra_usdt_wallet":
        context.user_data["wallet_cliente"]=txt; context.user_data["flow"]="compra_usdt_captura"
        await update.message.reply_text(f"Wallet guardada\n💳 Transfiere {context.user_data['total_cup']:.0f} a {TARJETA}\n{ADVERTENCIA}\nManda CAPTURA", parse_mode="HTML")
        try:
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"{header('COMPRA USDT')}\n{cant if 'cant' in locals() else context.user_data['usdt']} USDT")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET COPIABLE #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
    elif flow=="compra_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="compra_usdt_final"
            await update.message.reply_text("📸 Captura ✅\nEscribe tu NÚMERO")
        else: await update.message.reply_text(f"Manda captura 📸\n{ADVERTENCIA}")
    elif flow=="compra_usdt_final":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            total=context.user_data.get('total_cup',0); usdt=context.user_data.get('usdt',0)
            PAGOS_INFO[pid]={"operacion":"compra de USDT","monto":f"{total:.2f} CUP","usuario":f"{usuario} {username}"}
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"📲 RESUMEN FINAL #{pid}\n{usuario}\nUSDT: {usdt} = {total:.0f}\nContacto: {txt}", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"👛 WALLET + CONTACTO #{pid}:\n<code>{context.user_data['wallet_cliente']}</code>\n<code>{txt}</code>", parse_mode="HTML")
        except: pass
        context.user_data.clear()
    elif flow=="venta_usdt_monto":
        try:
            cant=float(txt.replace(",","."))
            total=cant*precios['usdt_venta']
            with lock_pendientes: PENDIENTES[pid]={"uid":uid,"tipo":"venta_usdt","monto":cant,"total":total,"usuario":usuario,"username":username}
            await update.message.reply_text(f"⏳ #{pid} Vender {cant} USDT = {total:.0f}")
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"🔔 PENDIENTE #{pid}\n{header('VENTA USDT')}\n{cant} USDT = {total:.0f}", reply_markup=btn_aprobacion())
        except: await update.message.reply_text("Solo número")
    elif flow=="venta_usdt_captura":
        if update.message.photo:
            try: await update.message.forward(ADMIN_CHANNEL_ID)
            except: pass
            context.user_data["flow"]="venta_usdt_datos"
            await update.message.reply_text(f"📸 Recibida\nManda TARJETA y NÚMERO para {context.user_data.get('total_cup',0):.0f}")
        else: await update.message.reply_text(f"Manda foto 📸\n{ADVERTENCIA}")
    elif flow=="venta_usdt_datos":
        await update.message.reply_text(MENSAJE_FINAL)
        try:
            total=context.user_data.get('total_cup',0); usdt=context.user_data.get('usdt',0)
            PAGOS_INFO[pid]={"operacion":"venta de USDT","monto":f"{total:.2f} CUP","usuario":f"{usuario} {username}"}
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💵 RESUMEN FINAL #{pid}\n{usuario}\nVende: {usdt} USDT = {total:.0f}", reply_markup=btn_confirmar())
            await context.bot.send_message(ADMIN_CHANNEL_ID, f"💳 DATOS #{pid}:\n<code>{txt}</code>", parse_mode="HTML")
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
    app.add_handler(CommandHandler("cerrar",cmd_cerrar))
    app.add_handler(CommandHandler("abrir",cmd_abrir))
    app.add_handler(CommandHandler("stock",cmd_stock))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, recibir_mensaje))
    print("🤖 Bot OK - Admin intacto + Canal solo comprobante con Estado"); app.run_polling()
if __name__=="__main__": main()
