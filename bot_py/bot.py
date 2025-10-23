# bot.py
import json
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Configuración del log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Carga cotxes desde cotxes.json con control de errores
try:
    with open(r"D:\DAM\XML_\html\bot_py\cotxes.json", "r", encoding="utf-8") as f:
        COTXES = json.load(f)
except Exception as e:
    logger.error(f"Error al cargar cotxes.json: {e}")
    COTXES = []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Filtre de cotxes", callback_data="filtre")],
        [InlineKeyboardButton("📖 Catàleg de cotxes", callback_data="cataleg_0")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚗 Benvingut al concessionari!\nEscull una opció:", reply_markup=reply_markup
    )

import logging

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "filtre":
        await filtrar_cotxes(query)

    elif data.startswith("cataleg_"):
        try:
            index = int(data.split("_")[1])
            await mostrar_cataleg(query, index)
        except (ValueError, IndexError):
            await query.answer("⚠️ Índex invàlid.", show_alert=True)

    elif data == "start":
        await mostrar_menu_principal(query)

    elif data.startswith("reservar_"):
        if "filtrat" in data:
            try:
                index = int(data.split("_")[-1])
                await reservar_cotxe(query, context, index, mode="filtrat")
            except Exception as e:
                logging.error(f"Error al reservar cotxe filtrat: {e}")
                await query.answer("Error al reservar cotxe.", show_alert=True)
        else:
            try:
                index = int(data.split("_")[1])
                await reservar_cotxe(query, context, index, mode="cataleg")
            except Exception as e:
                logging.error(f"Error al reservar cotxe cataleg: {e}")
                await query.answer("Error al reservar cotxe.", show_alert=True)

    elif data == "filtro_marca":
        try:
            await mostrar_opciones_filtro(query, "marca")
        except Exception as e:
            logging.error(f"Error en filtro_marca: {e}")
            await query.answer("Error al mostrar opcions de filtre.", show_alert=True)

    elif data == "filtro_año":
        try:
            # Cambia "any" por la clave correcta según tu JSON. Si es 'any', está bien.
            await mostrar_opciones_filtro(query, "any")  # <-- confirma que es 'any' y no 'any' u otra cosa
        except Exception as e:
            logging.error(f"Error en filtro_año: {e}")
            await query.answer("Error al mostrar opcions de filtre.", show_alert=True)

    elif data == "filtre_next":
        await navegar_filtrat(query, context, 1)

    elif data == "filtre_prev":
        await navegar_filtrat(query, context, -1)

    elif ":" in data:
        clave, valor = data.split(":")
        await mostrar_resultados_filtrados(query, clave, valor, context)

    else:
        await query.answer("⚠️ Opció no reconeguda.", show_alert=True)


from telegram import InputMediaPhoto


async def mostrar_menu_principal(query):
    keyboard = [
        [InlineKeyboardButton("🔍 Filtre de cotxes", callback_data="filtre")],
        [InlineKeyboardButton("📖 Catàleg de cotxes", callback_data="cataleg_0")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_media(
        media=InputMediaPhoto(media="https://hips.hearstapps.com/hmg-prod/images/the-fast-and-the-furious-toyota-supra-subasta-1624180933.jpg?crop=1.00xw:0.892xh;0,0.0372xh&resize=1200:*", caption="🚗 Benvingut al concessionari!\nEscull una opció:"),
        reply_markup=reply_markup,
    )

async def filtrar_cotxes(query):
    keyboard = [
        [InlineKeyboardButton("Filtrar per Marca", callback_data="filtro_marca")],
        [InlineKeyboardButton("Filtrar per Any", callback_data="filtro_año")],
        [InlineKeyboardButton("🔙 Tornar", callback_data="start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_media(
        media=InputMediaPhoto(media="https://hips.hearstapps.com/hmg-prod/images/the-fast-and-the-furious-toyota-supra-subasta-1624180933.jpg?crop=1.00xw:0.892xh;0,0.0372xh&resize=1200:*", caption="🔍 Tria un tipus de filtre:"),
        reply_markup=reply_markup,
    )

async def mostrar_opciones_filtro(query, clave):
    opciones = sorted(set(str(c[clave]) for c in COTXES))
    botones = [[InlineKeyboardButton(op, callback_data=f"{clave}:{op}")] for op in opciones]
    botones.append([InlineKeyboardButton("🔙 Tornar", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(botones)
    await query.edit_message_media(
        media=InputMediaPhoto(media="https://hips.hearstapps.com/hmg-prod/images/the-fast-and-the-furious-toyota-supra-subasta-1624180933.jpg?crop=1.00xw:0.892xh;0,0.0372xh&resize=1200:*", caption=f"Selecciona una opció per {clave}:"),
        reply_markup=reply_markup,
    )



async def veure_reserves(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reserves = context.user_data.get("reservas", [])
    if not reserves:
        await update.message.reply_text("📭 No tens cap reserva.")
        return
    missatge = "📋 Les teves reserves:\n\n" + "\n".join(f"• {r}" for r in reserves)
    await update.message.reply_text(missatge)

async def reservar_cotxe(query, context, index, mode):
    if mode == "cataleg":
        if not (0 <= index < len(COTXES)):
            await query.answer("❌ Cotxe no trobat.")
            return
        cotxe = COTXES[index]
    elif mode == "filtrat":
        filtrats_info = context.user_data.get("filtrats", {})
        cotxes = filtrats_info.get("coches", [])
        if not (0 <= index < len(cotxes)):
            await query.answer("❌ Cotxe no trobat.")
            return
        cotxe = cotxes[index]
    else:
        await query.answer("❌ Mode invàlid.")
        return

    user_id = query.from_user.id
    reservas = context.user_data.get("reservas", [])

    reserva_str = f"{cotxe['marca']} {cotxe['model']} ({cotxe['any']})"

    # Evitar reservas duplicadas
    if reserva_str in reservas:
        await query.answer("ℹ️ Ja has reservat aquest cotxe.", show_alert=True)
        return

    reservas.append(reserva_str)
    context.user_data["reservas"] = reservas

    await query.answer("✅ Cotxe reservat amb èxit!", show_alert=True)


async def filtrar_cotxes(query):
    keyboard = [
        [InlineKeyboardButton("Filtrar per Marca", callback_data="filtro_marca")],
        [InlineKeyboardButton("Filtrar per Any", callback_data="filtro_año")],
        [InlineKeyboardButton("🔙 Tornar", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🔍 Tria un tipus de filtre:", reply_markup=reply_markup)

async def mostrar_cataleg(query, index):
    if 0 <= index < len(COTXES):
        cotxe = COTXES[index]
        text = f"🚗 {cotxe['marca']} {cotxe['model']} ({cotxe['any']})\n💰 Preu: {cotxe['preu']}"

        # Validar URL de imagen
        if not cotxe.get("foto", "").startswith("http"):
            await query.edit_message_text("⚠️ Imatge no disponible per aquest cotxe.")
            return

        nav_buttons = []
        if index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"cataleg_{index - 1}"))
        if index < len(COTXES) - 1:
            nav_buttons.append(InlineKeyboardButton("Següent ➡️", callback_data=f"cataleg_{index + 1}"))

        tornar_button = [InlineKeyboardButton("🔙 Tornar", callback_data="start")]
        reply_markup = InlineKeyboardMarkup([nav_buttons, tornar_button])

        reservar_button = [InlineKeyboardButton("✅ Reservar", callback_data=f"reservar_{index}")]
        reply_markup = InlineKeyboardMarkup([nav_buttons, reservar_button, tornar_button])

        await query.edit_message_media(
            media=InputMediaPhoto(media=cotxe["foto"], caption=text),
            reply_markup=reply_markup
        )
    else:
        await query.answer("❌ Cotxe no trobat.", show_alert=True)

async def mostrar_opciones_filtro(query, clave):
    opciones = sorted(set(str(c[clave]) for c in COTXES))
    botones = [[InlineKeyboardButton(op, callback_data=f"{clave}:{op}")] for op in opciones]
    botones.append([InlineKeyboardButton("🔙 Tornar", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(botones)

    await query.edit_message_text(
        f"Selecciona una opció per {clave}:", reply_markup=reply_markup
    )

async def mostrar_resultados_filtrados(query, clave, valor, context):
    filtrados = [c for c in COTXES if str(c[clave]) == valor]

    if not filtrados:
        await query.edit_message_text("❌ No s'han trobat cotxes amb aquest filtre.")
        return

    context.user_data["filtrats"] = {
        "coches": filtrados,
        "index": 0
    }

    await mostrar_cotxe_filtrat(query, filtrados, 0)

async def mostrar_cotxe_filtrat(query, cotxes_filtrats, index):
    if not cotxes_filtrats:
        await query.edit_message_text("❌ No hi ha cotxes amb aquest filtre.")
        return

    cotxe = cotxes_filtrats[index]
    text = f"🚗 {cotxe['marca']} {cotxe['model']} ({cotxe['any']})\n💰 Preu: {cotxe['preu']}"

    if not cotxe.get("foto", "").startswith("http"):
        await query.edit_message_text("⚠️ Imatge no disponible per aquest cotxe.")
        return

    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="filtre_prev"))
    if index < len(cotxes_filtrats) - 1:
        nav_buttons.append(InlineKeyboardButton("Següent ➡️", callback_data="filtre_next"))

    tornar_button = [InlineKeyboardButton("🔙 Tornar", callback_data="start")]
    reply_markup = InlineKeyboardMarkup([nav_buttons, tornar_button])

    reservar_button = [InlineKeyboardButton("✅ Reservar", callback_data=f"reservar_filtrat_{index}")]
    reply_markup = InlineKeyboardMarkup([nav_buttons, reservar_button, tornar_button])

    await query.edit_message_media(
        media=InputMediaPhoto(media=cotxe["foto"], caption=text),
        reply_markup=reply_markup
    )

async def navegar_filtrat(query, context, direccio):
    filtrats_info = context.user_data.get("filtrats")

    if not filtrats_info:
        await query.edit_message_text("⚠️ No s'han trobat filtres actius.")
        return

    cotxes = filtrats_info["coches"]
    index = filtrats_info["index"] + direccio

    if 0 <= index < len(cotxes):
        filtrats_info["index"] = index
        await mostrar_cotxe_filtrat(query, cotxes, index)
    else:
        await query.answer("🚫 No hi ha més cotxes en aquesta direcció.", show_alert=False)

# MAIN
def main():
    # Obtener el token desde variable de entorno
    TOKEN = "8480954209:AAHzTsQ0xLGnLDoP83DnukXXcRglqg0viyQ"

    if not TOKEN:
        raise ValueError("⚠️ No s'ha trobat el token del bot. Assegura't que BOT_TOKEN està configurat.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("reserves", veure_reserves))


    print("[Concessionari Bot] Iniciat...")
    app.run_polling()

if __name__ == "__main__":
    main()

