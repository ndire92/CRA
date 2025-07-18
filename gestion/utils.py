import pywhatkit
import datetime

def envoyer_whatsapp_local(numero, message):
    """
    Ouvre WhatsApp Web à l’heure actuelle + 2 minutes pour envoyer un message.
    """
    maintenant = datetime.datetime.now()
    heure = maintenant.hour
    minute = maintenant.minute + 2

    # Gestion dépassement de 60 minutes
    if minute >= 60:
        minute -= 60
        heure = (heure + 1) % 24

    pywhatkit.sendwhatmsg(numero, message, heure, minute)