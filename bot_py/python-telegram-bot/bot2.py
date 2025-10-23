import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

with open(r"D:\DAM\XML_\html\bot_py\cotxes.json", "r", encoding="utf-8") as f:
    COTXES = json.load(f)

RESERVES_FILE = "reserves.json"

def carregar_reserves():
    try:
        with open(RESERVES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def guardar_reserves(reserves):
    with open(RESERVES_FILE, "w", encoding="utf-8") as f:
        json.dump(reserves, f, ensure_ascii=False, indent=4)

ASK_NAME, ASK_PHONE, ASK_EMAIL, ASK_HORARI = range(4)
pending_reservations = {}

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🏎️ *Benvingut al Concessionari de Luxe!*\n\n"
        "Descobreix la nostra col·lecció exclusiva de vehicles d'alta gamma.\n"
        "Què vols fer?\n"
    )

    keyboard = [
        [InlineKeyboardButton("📖 Veure Catàleg Complet", callback_data="cataleg_0")],
        [InlineKeyboardButton("🔍 Filtrar per Marca", callback_data="filtre")],
        [InlineKeyboardButton("📋 Les Meves Reserves", callback_data="meves_reserves")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# --- BOTONS PRINCIPALS ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "filtre":
        await mostrar_menu_filtre(query)
    elif data.startswith("cataleg_"):
        index = int(data.split("_")[1])
        await mostrar_cataleg(query, index)
    elif data == "meves_reserves":
        await mostrar_reserves(query)
    elif data == "menu_principal":
        await tornar_menu_principal(query)

# --- MENU PRINCIPAL (tornar) ---
async def tornar_menu_principal(query):
    welcome_text = (
        "🏎️ *Benvingut al Concessionari de Luxe!*\n\n"
        "Descobreix la nostra col·lecció exclusiva de vehicles d'alta gamma.\n"
        "Què vols fer?\n"
    )

    keyboard = [
        [InlineKeyboardButton("📖 Veure Catàleg Complet", callback_data="cataleg_0")],
        [InlineKeyboardButton("🔍 Filtrar per Marca", callback_data="filtre")],
        [InlineKeyboardButton("📋 Les Meves Reserves", callback_data="meves_reserves")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.delete()
    except:
        pass

    await query.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- MOSTRAR RESERVES ---
async def mostrar_reserves(query):
    user_id = query.from_user.id
    reserves = carregar_reserves()

    user_reserves = [r for r in reserves if r["client"]["user_id"] == user_id]

    if not user_reserves:
        text = "❌ *No tens cap reserva*\n\nComença a explorar el nostre catàleg!"
    else:
        text = f"📋 *Les Teves Reserves* ({len(user_reserves)})\n\n"
        for i, r in enumerate(user_reserves, 1):
            text += (
                f"*{i}. {r.get('marca', 'N/A')} {r.get('model', 'N/A')}*\n"
                f"   💰 {r.get('preu', 'N/A')}\n"
                f"   🕐 {r.get('horari', 'Pendent')}\n\n"
            )

    keyboard = [[InlineKeyboardButton("🔙 Tornar al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.delete()
    except:
        pass

    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- FILTRE PER MARCA ---
async def mostrar_menu_filtre(query):
    # Implementa la función que muestre el menú de filtro
    keyboard = [
        [InlineKeyboardButton("Marca 1", callback_data="marca:Marca1")],
        [InlineKeyboardButton("Marca 2", callback_data="marca:Marca2")],
        [InlineKeyboardButton("🔙 Tornar al Menú", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("Selecciona una marca per filtrar:", reply_markup=reply_markup)

# --- CATÀLEG AMB NAVEGACIÓ MILLORADA ---
async def mostrar_cataleg(query, index):
    cotxe = COTXES[index]

    text = (
        f"🏎️ *{cotxe['marca']} {cotxe['model']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Any: *{cotxe['any']}*\n"
        f"💰 Preu: *{cotxe['preu']}*\n"
        f"📊 Vehicle {index + 1} de {len(COTXES)}\n"
    )

    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"cataleg_{index-1}"))
    nav_buttons.append(InlineKeyboardButton(f"• {index + 1}/{len(COTXES)} •", callback_data="noop"))
    if index < len(COTXES) - 1:
        nav_buttons.append(InlineKeyboardButton("Següent ➡️", callback_data=f"cataleg_{index+1}"))

    keyboard = [
        nav_buttons,
        [InlineKeyboardButton("✅ RESERVAR AQUEST COTXE", callback_data=f"reservar_{index}")],
        [InlineKeyboardButton("🔙 Tornar al Menú", callback_data="menu_principal")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.message.delete()
    except:
        pass

    await query.message.reply_photo(
        photo=cotxe["foto"],
        caption=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- RESERVAR: inici ---
async def iniciar_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data.split("_")[1])
    pending_reservations[user_id] = index

    cotxe = COTXES[index]

    text = (
        f"📝 *Formulari de Reserva*\n\n"
        f"Estàs reservant:\n"
        f"🚗 *{cotxe['marca']} {cotxe['model']}* ({cotxe['any']})\n"
        f"💰 {cotxe['preu']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Si us plau, escriu el teu *nom complet*:"
    )

    await query.message.reply_text(text, parse_mode="Markdown")
    return ASK_NAME

# --- Pas 1: Nom ---
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nom = update.message.text.strip()

    if len(nom) < 3:
        await update.message.reply_text("❌ El nom ha de tenir almenys 3 caràcters. Torna-ho a intentar:")
        return ASK_NAME

    context.user_data["nom"] = nom
    await update.message.reply_text(
        "✅ Nom registrat!\n\n📞 Ara escriu el teu *número de telèfon*:",
        parse_mode="Markdown"
    )
    return ASK_PHONE

# --- Pas 2: Telèfon ---
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telefon = update.message.text.strip()

    if len(telefon) < 9:
        await update.message.reply_text("❌ El telèfon ha de tenir almenys 9 dígits. Torna-ho a intentar:")
        return ASK_PHONE

    context.user_data["telefon"] = telefon
    await update.message.reply_text(
        "✅ Telèfon registrat!\n\n📧 Ara escriu el teu *email*:",
        parse_mode="Markdown"
    )
    return ASK_EMAIL

# --- Pas 3: Email ---
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()

    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Email invàlid. Torna-ho a intentar:")
        return ASK_EMAIL

    context.user_data["email"] = email

    keyboard = [
        [InlineKeyboardButton("🌅 Matí (9:00 - 13:00)", callback_data="horari_mati")],
        [InlineKeyboardButton("🌞 Tarda (14:00 - 18:00)", callback_data="horari_tarda")],
        [InlineKeyboardButton("🌆 Vespre (18:00 - 20:00)", callback_data="horari_vespre")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ Email registrat!\n\n🕐 *Selecciona l'horari* preferit per visitar el concessionari:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return ASK_HORARI

# --- Pas 4: Horari i guardar ---
async def ask_horari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Processant reserva...")

    user_id = query.from_user.id

    horari_map = {
        "horari_mati": "Matí (9:00 - 13:00)",
        "horari_tarda": "Tarda (14:00 - 18:00)",
        "horari_vespre": "Vespre (18:00 - 20:00)"
    }
    context.user_data["horari"] = horari_map.get(query.data, "No especificat")

    index = pending_reservations.get(user_id)
    if index is None:
        await query.message.reply_text("❌ Error: No s'ha trobat la reserva.")
        return ConversationHandler.END

    cotxe = COTXES[index]

    reserves = carregar_reserves()
    reserva = {
        "cotxe_id": cotxe.get("cotxe_id", index),
        "marca": cotxe["marca"],
        "model": cotxe["model"],
        "any": cotxe["any"],
        "preu": cotxe["preu"],
        "client": {
            "user_id": user_id,
            "nom": context.user_data["nom"],
            "telefon": context.user_data["telefon"],
            "email": context.user_data["email"],
        },
        "horari": context.user_data["horari"]
    }
    reserves.append(reserva)
    guardar_reserves(reserves)

    del pending_reservations[user_id]

    confirmation = (
        "✅ *RESERVA CONFIRMADA!*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🚗 *{cotxe['marca']} {cotxe['model']}*\n"
        f"📅 Any: {cotxe['any']}\n"
        f"💰 Preu: {cotxe['preu']}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Client:* {context.user_data['nom']}\n"
        f"📞 *Telèfon:* {context.user_data['telefon']}\n"
        f"📧 *Email:* {context.user_data['email']}\n"
        f"🕐 *Horari:* {context.user_data['horari']}\n\n"
        "Ens veiem al concessionari! 🎉"
    )

    keyboard = [[InlineKeyboardButton("🔙 Tornar al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(confirmation, parse_mode="Markdown", reply_markup=reply_markup)

    return ConversationHandler.END

# --- Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in pending_reservations:
        del pending_reservations[user_id]

    keyboard = [[InlineKeyboardButton("🔙 Tornar al Menú", callback_data="menu_principal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "❌ Reserva cancel·lada.\n\nTorna quan vulguis!",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# --- MAIN ---
def main():
    TOKEN = "8480954209:AAHzTsQ0xLGnLDoP83DnukXXcRglqg0viyQ"
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(iniciar_reserva, pattern="^reservar_")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_HORARI: [CallbackQueryHandler(ask_horari, pattern="^horari_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button))

    print("🚗 [Bot Concessionari] Iniciat correctament!")
    app.run_polling()

if __name__ == "__main__":
    main()

