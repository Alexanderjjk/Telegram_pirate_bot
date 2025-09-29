import os
import sqlite3
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
        saldo INTEGER DEFAULT 0  -- almacenado en centavos
    )
''')
conn.commit()

# --- Productos con contenido y precio en USD ---
productos = {
    "Curso básico IA": {"contenido": "https://ejemplo.com/curso1", "precio": 150},  # $1.50
    "Pack de herramientas": {"contenido": "https://ejemplo.com/tools", "precio": 200},  # $2.00
    "Plantilla premium": {"contenido": "https://ejemplo.com/template", "precio": 300}  # $3.00
}

# --- Funciones de saldo ---
def obtener_saldo(user_id):
    cursor.execute('SELECT saldo FROM usuarios WHERE id = ?', (user_id,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute('INSERT INTO usuarios (id, saldo) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        return 0

def modificar_saldo(user_id, cantidad_centavos):
    saldo = obtener_saldo(user_id) + cantidad_centavos
    cursor.execute('UPDATE usuarios SET saldo = ? WHERE id = ?', (saldo, user_id))
    conn.commit()
    return saldo

# --- Comandos ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    obtener_saldo(user_id)
    update.message.reply_text(
        "🦜 ¡Bienvenido a ParrotedBot!\n\nUsa /compras para ver productos.\nUsa /ver_anuncio o /compartido para ganar saldo.\nUsa /cuenta para ver tu balance."
    )

def cuenta(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    saldo = obtener_saldo(user_id)
    update.message.reply_text(f"💰 Tu saldo actual es: ${saldo / 100:.2f} USD")

def compartido(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    modificar_saldo(user_id, 3)  # $0.03
    update.message.reply_text("🤝 ¡Gracias por compartir! Has ganado $0.03 USD.")

def ver_anuncio(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
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
    modificar_saldo(user_id, 3)  # $0.03
    query.answer()
    query.edit_message_text("✅ ¡Gracias! Has ganado $0.03 USD por ver el anuncio.")

def compras_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"{nombre} (${datos['precio'] / 100:.2f})", callback_data=nombre)]
        for nombre, datos in productos.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🛒 Elige un producto para comprar:", reply_markup=reply_markup)

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
        query.edit_message_text(f"✅ Has comprado: {producto}\nPrecio: ${precio / 100:.2f}\nContenido:\n{contenido}")
    else:
        query.answer()
        query.edit_message_text(f"⚠️ No tienes suficiente saldo. Este producto cuesta ${precio / 100:.2f} USD.")

# --- Main ---
def main():
    if not TOKEN:
        print("❌ Error: BOT_TOKEN no está definido en las variables de entorno.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cuenta", cuenta))
    dp.add_handler(CommandHandler("compartido", compartido))
    dp.add_handler(CommandHandler("ver_anuncio", ver_anuncio))
    dp.add_handler(CommandHandler("compras", compras_menu))
    dp.add_handler(CallbackQueryHandler(manejar_compra))
    dp.add_handler(CallbackQueryHandler(confirmar_anuncio, pattern="anuncio_visto"))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()