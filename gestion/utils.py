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

    pywhatkit.sendwhatmsg_instantly(
        phone_no=numero,
        message=message,
        wait_time=2,       # ← temps pour laisser WhatsApp Web se charger
        tab_close=True      # ← ferme l’onglet après envoi
    )