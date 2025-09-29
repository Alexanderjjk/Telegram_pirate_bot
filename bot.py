import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import datetime
import os

def verificar_horario():
    ahora = datetime.datetime.now()
    hora = ahora.hour
    minuto = ahora.minute

    if (hora == 0 and minuto >= 30) or (0 < hora < 7) or (hora == 7 and minuto < 49):
        print("⏱️ Fuera de horario. Cerrando contenedor.")
        os._exit(0)  # Mata el proceso principal

verificar_horario()

# --- Token desde variable de entorno ---
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("EXCHANGE_API_KEY", "f79c32c2db3b99e4258cfd27")  # tu clave de ExchangeRate-API

# --- Base de datos SQLite ---
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        saldo INTEGER DEFAULT 0
    )
''')
conn.commit()

# --- Productos disponibles ---
productos = {
    "Curso básico IA": {"contenido": "https://ejemplo.com/curso1", "precio": 150},
    "Pack de herramientas": {"contenido": "https://ejemplo.com/tools", "precio": 200},
    "Plantilla premium": {"contenido": "https://ejemplo.com/template", "precio": 300}
}

# --- Funciones de saldo ---
def obtener_saldo(user_id):
    cursor.execute('SELECT saldo FROM usuarios WHERE id = ?', (user_id,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute('INSERT INTO usuarios (id, saldo) VALUES (?, ?)', (user_id, 100))  # $1.00 bienvenida
        conn.commit()
        return 100

def modificar_saldo(user_id, cantidad):
    saldo = obtener_saldo(user_id) + cantidad
    cursor.execute('UPDATE usuarios SET saldo = ? WHERE id = ?', (saldo, user_id))
    conn.commit()
    return saldo

# --- API de tasas ---
def obtener_tasas():
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("conversion_rates", {})
    except Exception as e:
        print(f"Error al obtener tasas: {e}")
        return {}

# --- Comandos del bot ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    obtener_saldo(user_id)
    update.message.reply_text(
        "<b>🦜 Bienvenido a ParrotedBot</b>\n\n"
        "Este bot te permite ganar y administrar saldo en <b>USD</b> por tiempo limitado.\n"
        "Has recibido <b>$1.00 USD</b> de bienvenida 🎁\n\n"
        "📌 Comandos disponibles:\n"
        "• 💰 /cuenta → Consulta tu saldo actual\n"
        "• 🛍️ /compras → Explora productos digitales\n"
        "• 🎬 /ver_anuncio → Gana saldo viendo contenido\n"
        "• 🤝 /invitar → Gana saldo por referidos\n"
        "• 💸 /retirar → Solicita extracción de saldo",
        parse_mode='HTML'
    )

def cuenta(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    saldo = obtener_saldo(user_id)
    update.message.reply_text(
        f"💰 Tu saldo actual es: <b>${saldo / 100:.2f} USD</b>\n\n"
        "Puedes usarlo para comprar productos o solicitar retiro (mínimo $25.00 USD).",
        parse_mode='HTML'
    )

def ver_anuncio(update: Update, context: CallbackContext):
    anuncio_url = "https://tuanuncio.com/landing123"
    keyboard = [[InlineKeyboardButton("✅ Ya vi el anuncio", callback_data="anuncio_visto")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"🎬 Mira este anuncio para ganar saldo:\n👉 {anuncio_url}\n\n"
        "Haz clic, espera unos segundos y luego pulsa el botón.",
        reply_markup=reply_markup
    )

def confirmar_anuncio(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    modificar_saldo(user_id, 300)  # $3.00 por anuncio
    query.answer()
    query.edit_message_text("✅ ¡Gracias! Has ganado $3.00 USD por ver el anuncio.")

def invitar(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    link = f"https://t.me/ParrotedBot?start={user_id}"
    update.message.reply_text(
        f"🔗 Comparte este enlace para invitar amigos:\n👉 {link}\n\n"
        "🎁 Ganas <b>$3.00 USD</b> por cada persona que se una.",
        parse_mode='HTML'
    )

def compras_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"{nombre} (${datos['precio'] / 100:.2f})", callback_data=nombre)]
        for nombre, datos in productos.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🛍️ Elige un producto para comprar:", reply_markup=reply_markup)

def manejar_compra(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    producto = query.data
    saldo = obtener_saldo(user_id)
    datos = productos.get(producto)

    if not datos:
        query.answer()
        query.edit_message_text("❌ Producto no válido.")
        return

    precio = datos["precio"]
    contenido = datos["contenido"]

    if saldo >= precio:
        modificar_saldo(user_id, -precio)
        query.answer()
        query.edit_message_text(f"✅ Has comprado: {producto}\nContenido:\n{contenido}")
    else:
        query.answer()
        query.edit_message_text(f"⚠️ Saldo insuficiente. Este producto cuesta ${precio / 100:.2f} USD.")

# --- Retiro ---
def retirar(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    saldo = obtener_saldo(user_id)

    if saldo < 2500:
        update.message.reply_text(
            "⚠️ Para solicitar un retiro necesitas al menos <b>$25.00 USD</b>.\n\n"
            "Esto se debe a que los costos de envío, comisiones y procesamiento hacen que montos menores no sean rentables.\n\n"
            "💡 Sigue acumulando saldo viendo anuncios o invitando amigos.",
            parse_mode='HTML'
        )
        return

    tasas = obtener_tasas()
    # Tomamos las primeras 30 monedas disponibles
    monedas = list(tasas.keys())[:30]

    keyboard = [[InlineKeyboardButton(moneda, callback_data=f"retirar_{moneda}")] for moneda in monedas]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f"✅ Puedes retirar <b>${saldo / 100:.2f} USD</b>\n\n"
        "Selecciona la moneda en la que deseas recibir tu pago:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

def mostrar_equivalente(update: Update, context: CallbackContext):
    query = update.callback_query
    moneda = query.data.split("_")[1]
    user_id = query.from_user.id
    saldo_usd = obtener_saldo(user_id) / 100

    tasas = obtener_tasas()
    tasa = tasas.get(moneda, None)

    if tasa:
        equivalente = round(saldo_usd * tasa, 2)
        query.answer()
        query.edit_message_text(
            f"💸 Equivalente en {moneda}:\n\n"
            f"<b>${saldo_usd:.2f} USD</b> ≈ <b>{equivalente} {moneda}</b>\n\n"
            "📌 Para continuar con el retiro, escribe tu método preferido (ej: Transferencia, PayPal, USDT) y tus datos de contacto.",
            parse_mode='HTML'
        )
    else:
        query.answer()
        query.edit_message_text("❌ Moneda no disponible en la API.")

# --- Main ---
def main():
    if not TOKEN:
        print("❌ Error: BOT_TOKEN no está definido.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cuenta", cuenta))
    dp.add_handler(CommandHandler("ver_anuncio", ver_anuncio))
    dp.add_handler(CommandHandler("invitar", invitar))
    dp.add_handler(CommandHandler("compras", compras_menu))
    dp.add_handler(CommandHandler("retirar", retirar))
    dp.add_handler(CallbackQueryHandler(confirmar_anuncio, pattern="anuncio_visto"))
    dp.add_handler(CallbackQueryHandler(manejar_compra))
    dp.add_handler(CallbackQueryHandler(mostrar_equivalente, pattern="retirar_"))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()