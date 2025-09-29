import os
import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# --- Token desde variable de entorno ---
TOKEN = os.getenv("BOT_TOKEN")

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
        cursor.execute('INSERT INTO usuarios (id, saldo) VALUES (?, ?)', (user_id, 100))  # $1.00 de bienvenida
        conn.commit()
        return 100

def modificar_saldo(user_id, cantidad):
    saldo = obtener_saldo(user_id) + cantidad
    cursor.execute('UPDATE usuarios SET saldo = ? WHERE id = ?', (saldo, user_id))
    conn.commit()
    return saldo

# --- Comandos del bot ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    obtener_saldo(user_id)
    update.message.reply_text(
        "<b>🦜 Bienvenido a ParrotedBot</b>\n\n"
        "Has recibido $1.00 USD de bienvenida.\n\n"
        "Comandos disponibles:\n"
        "• /cuenta → Ver tu saldo actual\n"
        "• /compras → Ver productos disponibles\n"
        "• /ver_anuncio → Ganar saldo viendo un anuncio\n"
        "• /invitar → Compartir el bot y ganar saldo",
        parse_mode='HTML'
    )

def cuenta(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    saldo = obtener_saldo(user_id)
    update.message.reply_text(f"💰 Tu saldo actual es: ${saldo / 100:.2f} USD", parse_mode='HTML')

def ver_anuncio(update: Update, context: CallbackContext):
    anuncio_url = "https://tuanuncio.com/landing123"
    keyboard = [[InlineKeyboardButton("✅ Ya vi el anuncio", callback_data="anuncio_visto")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"🎬 Mira este anuncio para ganar saldo:\n{anuncio_url}\n\nHaz clic, espera unos segundos y luego pulsa el botón.",
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
        f"🔗 Comparte este enlace para invitar amigos:\n{link}\n\n"
        "🎁 Ganas $3.00 USD por cada persona que se una.",
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
    dp.add_handler(CallbackQueryHandler(confirmar_anuncio, pattern="anuncio_visto"))
    dp.add_handler(CallbackQueryHandler(manejar_compra))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()