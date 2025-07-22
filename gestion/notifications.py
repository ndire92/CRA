import datetime
import pywhatkit

def formater_numero_senegalais(numero):
    numero = numero.strip()
    if not numero.startswith("+"):
        if numero.startswith("0"):
            numero = "+221" + numero[1:]
        elif numero.startswith("7"):
            numero = "+221" + numero
    return numero

def nettoyer_message(message):
    return ''.join(c for c in message if ord(c) < 128)

def envoyer_whatsapp_local(numero, message):
    numero = formater_numero_senegalais(numero)
    message = nettoyer_message(message)

    maintenant = datetime.datetime.now()
    heure = maintenant.hour
    minute = maintenant.minute + 2
    if minute >= 60:
        minute -= 60
        heure = (heure + 1) % 24

    pywhatkit.sendwhatmsg(numero, message, heure, minute, wait_time=15, tab_close=True)


def notifier_designation(designation):
    match = designation.match
    date_str = match.date_match.strftime('%A %d %B %Y à %Hh')
    lieu = match.lieu or "Non précisé"
    affiche_match = f"{match.equipe_domicile} vs {match.equipe_exterieur}"

    roles = [
        (designation.arbitre_central, "Arbitre central"),
        (designation.arbitre_assistant1, "Assistant 1"),
        (designation.arbitre_assistant2, "Assistant 2"),
        (designation.inspecteur, "Inspecteur"),
    ]
    if designation.quatrieme_arbitre:
        roles.append((designation.quatrieme_arbitre, "4ᵉ arbitre"))

    for arbitre, role in roles:
        if arbitre and arbitre.user.telephone:
            message = f"""📋 CRA Tivaouane

Bonjour {arbitre.user.get_full_name()}, vous êtes désigné comme {role} pour :

📅 {date_str}
🏟️ {affiche_match}
📍 Lieu : {lieu}

Merci de confirmer votre présence ✅"""

            try:
                envoyer_whatsapp_local(arbitre.user.telephone, message)
            except Exception as e:
                print(f"❌ WhatsApp non envoyé à {arbitre.user.get_full_name()} : {e}")