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
        puntos INTEGER DEFAULT 0
    )
''')
conn.commit()

# --- Opciones con contenido y costo ---
opciones = {
    "Opción 1": {"contenido": "https://ejemplo.com/recurso1", "costo": 1},
    "Opción 2": {"contenido": "https://ejemplo.com/recurso2", "costo": 2},
    "Opción 3": {"contenido": "https://ejemplo.com/recurso3", "costo": 3}
}

# --- Funciones de puntos ---
def obtener_puntos(user_id):
    cursor.execute('SELECT puntos FROM usuarios WHERE id = ?', (user_id,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    else:
        cursor.execute('INSERT INTO usuarios (id, puntos) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        return 0

def modificar_puntos(user_id, cantidad):
    puntos = obtener_puntos(user_id) + cantidad
    cursor.execute('UPDATE usuarios SET puntos = ? WHERE id = ?', (puntos, user_id))
    conn.commit()
    return puntos

# --- Comandos ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    obtener_puntos(user_id)
    update.message.reply_text(
        "🦜 ¡Bienvenido a ParrotedBot!\n\nUsa /opciones para ver el menú.\nUsa /ver_anuncio o /compartido para ganar puntos.\nUsa /puntos para ver tu saldo."
    )

def puntos(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    puntos = obtener_puntos(user_id)
    update.message.reply_text(f"📊 Tienes {puntos} puntos.")

def compartido(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    modificar_puntos(user_id, 3)
    update.message.reply_text("🤝 ¡Gracias por compartir! Has ganado 3 puntos.")

def ver_anuncio(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    anuncio_url = "https://tuanuncio.com/landing123"
    keyboard = [[InlineKeyboardButton("✅ Ya vi el anuncio", callback_data="anuncio_visto")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"🎬 Mira este anuncio para ganar puntos:\n{anuncio_url}\n\nHaz clic, espera unos segundos y luego pulsa el botón.",
        reply_markup=reply_markup
    )

def confirmar_anuncio(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    modificar_puntos(user_id, 3)
    query.answer()
    query.edit_message_text("✅ ¡Gracias! Has ganado 3 puntos por ver el anuncio.")

def opciones_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(f"{nombre} ({datos['costo']} pts)", callback_data=nombre)]
        for nombre, datos in opciones.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📦 Selecciona una opción:", reply_markup=reply_markup)

def manejar_opcion(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    opcion = query.data
    puntos = obtener_puntos(user_id)
    datos = opciones.get(opcion)

    if not datos:
        query.answer()
        query.edit_message_text("❌ Opción no válida.")
        return

    costo = datos["costo"]
    contenido = datos["contenido"]

    if puntos >= costo:
        modificar_puntos(user_id, -costo)
        query.answer()
        query.edit_message_text(f"✅ Has elegido: {opcion}\nCosto: {costo} puntos\nContenido:\n{contenido}")
    else:
        query.answer()
        query.edit_message_text(f"⚠️ No tienes suficientes puntos. Esta opción cuesta {costo} puntos.")

# --- Main ---
def main():
    if not TOKEN:
        print("❌ Error: BOT_TOKEN no está definido en las variables de entorno.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("puntos", puntos))
    dp.add_handler(CommandHandler("compartido", compartido))
    dp.add_handler(CommandHandler("ver_anuncio", ver_anuncio))
    dp.add_handler(CommandHandler("opciones", opciones_menu))
    dp.add_handler(CallbackQueryHandler(manejar_opcion))
    dp.add_handler(CallbackQueryHandler(confirmar_anuncio, pattern="anuncio_visto"))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()