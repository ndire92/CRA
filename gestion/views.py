from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from .utils import envoyer_whatsapp_local
from .notifications import envoyer_whatsapp_local


import datetime
import time

from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login
from .forms import RapportMatchForm, SanctionFormSet, ButFormSet, RemplacementFormSet
from .forms import (
    CompetitionForm, DesignationForm, DisponibiliteForm, EmailLoginForm, MatchForm, RapportForm,
    UserRegistrationForm, ArbitreForm, InspecteurForm
)
from .models import (
    Competition, EvenementBut, EvenementRemplacement, Match, Arbitre, Designation, Disponibilite,
    Inspecteur, Rapport, RapportMatch, SanctionDisciplinaire
)

# -------------------------  Rôles vérifiés  -------------------------
def page_accueil_view(request):
    return render(request, 'home.html')
def est_arbitre(user):
    return user.is_authenticated and user.role == 'arbitre'

def est_inspecteur(user):
    return user.is_authenticated and user.role == 'inspecteur'

def est_admin(user):
    return user.is_authenticated and user.role == 'admin'

def login_view(request):
    form = EmailLoginForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)  # ✅ corrigé ici
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            form.add_error(None, "❌ Email ou mot de passe incorrect.")
    return render(request, 'registration/login.html', {'form': form})


# -------------------------  Vues générales  -------------------------

@login_required
def dashboard_view(request):
    user = request.user

    if user.role == 'arbitre':
        designations = Designation.objects.filter(
            Q(arbitre_central__user=user) |
            Q(arbitre_assistant1__user=user) |
            Q(arbitre_assistant2__user=user) |
            Q(quatrieme_arbitre__user=user)
        ).distinct()
        return render(request, 'arbitre/dashboard.html', {'designations': designations})

    elif user.role == 'inspecteur':
        designations = Designation.objects.filter(inspecteur__user=user)
        rapports_restants = designations.exclude(rapport__isnull=False)
        return render(request, 'inspecteur/dashboard.html', {
            'designations': designations,
            'rapports_restants': rapports_restants
        })

    elif user.role == 'admin':
        nb_rapports = Rapport.objects.count()
        nb_designations_restantes = Match.objects.filter(designation__isnull=True).count()
        nb_rapports_arbitres= RapportMatch.objects.count()

        context = {
            'nb_competitions': Competition.objects.count(),
            'nb_matchs': Match.objects.count(),
            'nb_arbitres': Arbitre.objects.filter(actif=True).count(),
            'nb_inspecteurs': Inspecteur.objects.filter(actif=True).count(),
            'nb_rapports': nb_rapports,
            'nb_designations_restantes': nb_designations_restantes,
            'nb_rapports_arbitres': nb_rapports_arbitres,
            'matchs_non_assignes': Match.objects.filter(designation__isnull=True).order_by('date_match'),
        }
        return render(request, 'admin/dashboard.html', context)

    return redirect('home')

@login_required
def inscription_view(request):
    form = UserRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        messages.success(request, f"✅ Inscription réussie ! Votre identifiant est : {user.username}")
        return redirect('login')  # Ou vers une page "confirmation" personnalisée
    return render(request, 'inscription.html', {'form': form})

# -------------------------  Profils  -------------------------

@login_required
@user_passes_test(est_arbitre)
def profil_arbitre_view(request):
    arbitre, _ = Arbitre.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ArbitreForm(request.POST, instance=arbitre)
        if form.is_valid():
            form.save()  # Sauvegarder les informations mises à jour
            return redirect('dashboard')  # Rediriger après l'enregistrement
    else:
        form = ArbitreForm(instance=arbitre)

    return render(request, 'arbitre/profil.html', {'form': form})


@login_required
@user_passes_test(est_inspecteur)
def profil_inspecteur_view(request):
    inspecteur, _ = Inspecteur.objects.get_or_create(user=request.user)
    form = InspecteurForm(request.POST or None, instance=inspecteur)
    if form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'inspecteur/profil.html', {'form': form})

# -------------------------  Disponibilités  -------------------------

@login_required
def mes_disponibilites_view(request):
    dispos = Disponibilite.objects.filter(user=request.user)
    return render(request, 'disponibilite/mes_disponibilites.html', {'disponibilites': dispos})

@login_required
def ajouter_disponibilite_view(request):
    form = DisponibiliteForm(request.POST or None)
    if form.is_valid():
        dispo = form.save(commit=False)
        dispo.user = request.user
        dispo.save()
        return redirect('mes_disponibilites')
    return render(request, 'disponibilite/ajouter.html', {'form': form})

# -------------------------  Rapports  -------------------------

@login_required
@user_passes_test(est_inspecteur)
def remplir_rapport_view(request, designation_id):
    designation = get_object_or_404(Designation, id=designation_id, inspecteur__user=request.user)
    if hasattr(designation, 'rapport'):
        return redirect('dashboard')  # rapport déjà créé

    form = RapportForm(request.POST or None)
    if form.is_valid():
        rapport = form.save(commit=False)
        rapport.designation = designation
        rapport.inspecteur = designation.inspecteur
        rapport.save()
        return redirect('dashboard')
    return render(request, 'rapport/remplir.html', {'form': form, 'designation': designation})

# -------------------------  Désignations & matchs  -------------------------

@login_required
@user_passes_test(est_arbitre)
def mes_designations_view(request):
    desigs = Designation.objects.filter(
        Q(arbitre_central__user=request.user) |
        Q(arbitre_assistant1__user=request.user) |
        Q(arbitre_assistant2__user=request.user) |
        Q(quatrieme_arbitre__user=request.user)
    ).distinct()
    return render(request, 'arbitre/mes_designations.html', {'designations': desigs})




def est_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(est_admin)


def creer_designation_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if request.method == "POST":
        form = DesignationForm(request.POST)
        if form.is_valid():
            designation = form.save(commit=False)
            designation.match = match

            try:
                designation.full_clean()
                designation.save()
            except ValidationError as e:
                form.add_error(None, e)
                return render(request, 'designation/creer.html', {'form': form, 'match': match})

            # 📅 Infos match
            date_str = match.date_match.strftime('%A %d %B %Y à %Hh')
            lieu = match.lieu or "Non précisé"
            affiche_match = f"{match.equipe_domicile} vs {match.equipe_exterieur}"

            # 📧 Email désignés
            arbitres_users = [
                designation.arbitre_central.user,
                designation.arbitre_assistant1.user,
                designation.arbitre_assistant2.user,
                designation.inspecteur.user
            ]
            if designation.quatrieme_arbitre:
                arbitres_users.append(designation.quatrieme_arbitre.user)

            emails = [u.email for u in arbitres_users if u.email]

            contenu_email = f"""Bonjour,

Vous avez été désigné(e) pour le match suivant :

📅 Date : {date_str}
📍 Lieu : {lieu}
🏟️ Match : {affiche_match}

👥 Désignés :
- Arbitre central : {designation.arbitre_central.user.get_full_name()}
- Assistant 1 : {designation.arbitre_assistant1.user.get_full_name()}
- Assistant 2 : {designation.arbitre_assistant2.user.get_full_name()}
- 4ᵉ arbitre : {designation.quatrieme_arbitre.user.get_full_name() if designation.quatrieme_arbitre else '—'}
- Inspecteur : {designation.inspecteur.user.get_full_name()}

Merci de confirmer votre présence.

Cordialement,
Sous-CRA Tivaouane
"""

            try:
                send_mail(
                    subject=f"📋 Désignation – {affiche_match}",
                    message=contenu_email,
                    from_email="mamadou12ndir@gmail.com",
                    recipient_list=emails,
                    fail_silently=False,
                )
                noms = ', '.join([u.get_full_name() for u in arbitres_users])
                messages.success(request, f"📤 Email envoyé avec succès à {noms}")
            except Exception as e:
                messages.warning(request, f"📨 Échec d’envoi email : {e}")

            # 📲 WhatsApp désignation par rôle
            roles = [
                (designation.arbitre_central, "Arbitre central"),
                (designation.arbitre_assistant1, "Assistant 1"),
                (designation.arbitre_assistant2, "Assistant 2"),
                (designation.inspecteur, "Inspecteur"),
            ]
            if designation.quatrieme_arbitre:
                roles.append((designation.quatrieme_arbitre, "4ᵉ arbitre"))

            for arbitre, role in roles:
                if arbitre.user.telephone:
                    message_whatsapp = f"""📋 CRA Tivaouane

Bonjour {arbitre.user.get_full_name()}, vous êtes désigné comme {role} pour :

📅 {date_str}
🏟️ {affiche_match}
📍 Lieu : {lieu}

Merci de confirmer votre présence ✅"""
                    try:
                        envoyer_whatsapp_local(arbitre.user.telephone, message_whatsapp)
                        messages.success(request, f"📲 WhatsApp envoyé à {arbitre.user.get_full_name()} ({role})")
                        time.sleep(5)
                    except Exception as e:
                        messages.warning(request, f"📲 WhatsApp non envoyé à {arbitre.user.get_full_name()} : {e}")

            return redirect('dashboard')

    else:
        form = DesignationForm(initial={'match': match})

    return render(request, 'designation/creer.html', {'form': form, 'match': match})

from django.http import JsonResponse
from .models import Arbitre, Inspecteur

def arbitres_par_zone(request):
    zone = request.GET.get('zone')
    data = {
        'arbitres': [],
        'inspecteurs': []
    }

    if zone:
        arbitres = Arbitre.objects.select_related('user').filter(user__zone=zone, actif=True)
        inspecteurs = Inspecteur.objects.select_related('user').filter(user__zone=zone, actif=True)
        
        data['arbitres'] = [{"id": a.id, "text": f"{a.user.get_full_name()} • {a.user.zone}"} for a in arbitres]
        data['inspecteurs'] = [{"id": i.id, "text": f"{i.user.get_full_name()} • {i.user.zone}"} for i in inspecteurs]

    return JsonResponse(data)

@login_required
@user_passes_test(est_admin)
def creer_match_view(request):
    form = MatchForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'match/creer.html', {'form': form})

# -------------------------  Suggestion intelligente  -------------------------

@login_required
@user_passes_test(est_admin)
def suggestion_designation_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    date = match.date_match.date()

    arbitres_dispo = Arbitre.objects.filter(
        actif=True,
        user__disponibilite__date_debut__lte=date,
        user__disponibilite__date_fin__gte=date,
        user__disponibilite__disponible=True
    ).annotate(
        nb_designations=Count('central') + Count('assistant1') +
                         Count('assistant2') + Count('quatrieme')
    ).order_by('nb_designations').distinct()

    deja_ids = Designation.objects.filter(
        match__date_match__date=date
    ).values_list(
        'arbitre_central', 'arbitre_assistant1', 'arbitre_assistant2', 'quatrieme_arbitre'
    )
    deja_ids = {i for t in deja_ids for i in t if i}
    arbitres_libres = arbitres_dispo.exclude(id__in=deja_ids)

    inspecteurs_libres = Inspecteur.objects.filter(
        actif=True,
        user__disponibilite__date_debut__lte=date,
        user__disponibilite__date_fin__gte=date,
        user__disponibilite__disponible=True
    ).exclude(
        designation__match__date_match__date=date
    ).distinct()

    return render(request, 'designation/suggestions.html', {
        'match': match,
        'arbitres': arbitres_libres,
        'inspecteurs': inspecteurs_libres
    })
    

from django.contrib import messages

def inscription_view(request):
    form = UserRegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        messages.success(request, "Inscription réussie ! Connecte-toi pour continuer.")
        return redirect('login')
    return render(request, 'registration/inscription.html', {'form': form})


@login_required
@user_passes_test(est_admin)
def creer_competition_view(request):
    form = CompetitionForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Compétition créée avec succès !")
        return redirect('dashboard')
    return render(request, 'competition/creer.html', {'form': form})

@login_required
@user_passes_test(est_admin)
def liste_competitions_view(request):
    competitions = Competition.objects.order_by('-date_debut')
    return render(request, 'competition/liste.html', {'competitions': competitions})

@login_required
@user_passes_test(est_admin)
def classement_arbitres_view(request):
    arbitres = Arbitre.objects.filter(actif=True).order_by('-note_moyenne')
    return render(request, 'classement/arbitres.html', {'arbitres': arbitres})

@login_required
@user_passes_test(est_admin)
def matchs_a_designer_view(request):
    matchs = Match.objects.filter(designation__isnull=True).order_by('date_match')
    return render(request, 'designation/liste_matchs.html', {'matchs': matchs})


@login_required
@user_passes_test(est_admin)
def liste_rapports_view(request):
    rapports = Rapport.objects.select_related('designation', 'inspecteur').order_by('-designation__match__date_match')
    return render(request, 'rapport/liste.html', {'rapports': rapports})


@user_passes_test(est_inspecteur)
def mes_rapports_view(request):
    rapports = Rapport.objects.filter(inspecteur__user=request.user).order_by('-designation__match__date_match')
    return render(request, 'rapport/mes_rapports.html', {'rapports': rapports})



@login_required
def voir_rapport_view(request, rapport_id):
    rapport = get_object_or_404(Rapport, id=rapport_id)

    # Optionnel : autoriser uniquement l’admin ou l’inspecteur concerné
    if not (request.user.role == 'admin' or rapport.inspecteur.user == request.user):
        return redirect('dashboard')

    return render(request, 'rapport/detail.html', {'rapport': rapport})

@login_required
@user_passes_test(est_admin)
def liste_arbitres_view(request):
    arbitres = Arbitre.objects.select_related('user').filter(actif=True).order_by('user__last_name')
    return render(request, 'arbitre/liste.html', {'arbitres': arbitres})

@login_required
@user_passes_test(est_admin)
def liste_inspecteurs_view(request):
    inspecteurs = Inspecteur.objects.select_related('user').filter(actif=True).order_by('user__last_name')
    return render(request, 'inspecteur/liste.html', {'inspecteurs': inspecteurs})

@login_required
@user_passes_test(est_admin)
def liste_matchs_view(request):
    matchs = Match.objects.select_related('competition').order_by('-date_match')
    return render(request, 'match/liste.html', {'matchs': matchs})


@login_required
def creer_rapport_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    rapport = getattr(match, 'rapportmatch', None)

    if RapportMatch.objects.filter(match=match).exists() and not rapport:
        messages.info(request, "✅ Rapport déjà soumis.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = RapportMatchForm(request.POST, instance=rapport)
        sanction_formset = SanctionFormSet(request.POST, instance=rapport, prefix='sanction')
        but_formset = ButFormSet(request.POST, instance=rapport, prefix='but')
        remplacement_formset = RemplacementFormSet(request.POST, instance=rapport, prefix='remplacement')

        if all([form.is_valid(), sanction_formset.is_valid(), but_formset.is_valid(), remplacement_formset.is_valid()]):
            rapport = form.save(commit=False)
            rapport.match = match
            rapport.save()

            for fs in [sanction_formset, but_formset, remplacement_formset]:
                fs.instance = rapport
                fs.save()

            return redirect('rapport_succes')
    else:
        form = RapportMatchForm(instance=rapport)
        sanction_formset = SanctionFormSet(instance=rapport, prefix='sanction')
        but_formset = ButFormSet(instance=rapport, prefix='but')
        remplacement_formset = RemplacementFormSet(instance=rapport, prefix='remplacement')

    return render(request, 'rapport/rapport_ar.html', {
        'form': form,
        'sanction_formset': sanction_formset,
        'but_formset': but_formset,
        'remplacement_formset': remplacement_formset,
        'match': match,
    })
    
@login_required
def modifier_rapport_view(request, rapport_id):
    rapport = get_object_or_404(RapportMatch, id=rapport_id)

    # 🔐 Vérifie que l’arbitre connecté est bien le propriétaire
    if hasattr(request.user, 'arbitre') and rapport.arbitre_central != request.user.arbitre:
        messages.error(request, "⛔ Vous n’êtes pas autorisé à modifier ce rapport.")
        return redirect('dashboard')

    # 🔒 Vérifie si le rapport est modifiable
    if not getattr(rapport, 'modifiable', True):
        messages.error(request, "🔒 Ce rapport est verrouillé et ne peut pas être modifié.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = RapportMatchForm(request.POST, instance=rapport)
        sanction_formset = SanctionFormSet(request.POST, instance=rapport, prefix='sanction')
        but_formset = ButFormSet(request.POST, instance=rapport, prefix='but')
        remplacement_formset = RemplacementFormSet(request.POST, instance=rapport, prefix='remplacement')

        if all([form.is_valid(), sanction_formset.is_valid(), but_formset.is_valid(), remplacement_formset.is_valid()]):
            form.save()
            sanction_formset.save()
            but_formset.save()
            remplacement_formset.save()
            messages.success(request, "✏️ Rapport modifié avec succès.")
            return redirect('rapport_succes')
    else:
        form = RapportMatchForm(instance=rapport)
        sanction_formset = SanctionFormSet(instance=rapport, prefix='sanction')
        but_formset = ButFormSet(instance=rapport, prefix='but')
        remplacement_formset = RemplacementFormSet(instance=rapport, prefix='remplacement')

    return render(request, 'rapport/rapport_ar.html', {
        'form': form,
        'sanction_formset': sanction_formset,
        'but_formset': but_formset,
        'remplacement_formset': remplacement_formset,
        'match': rapport.match,
        'rapport': rapport,
        'modification': True,
    })
def rapport_succes_view(request):
    return render(request, 'rapport/succes.html')

def voir_rapport_view(request, rapport_id):
    rapport = get_object_or_404(RapportMatch, id=rapport_id)
    return render(request, 'rapport/voir_rapport.html', {'rapport': rapport})



from django.http import HttpResponse
from fpdf import FPDF

def nettoyer_texte(texte):
    """
    Remplace les caractères spéciaux Unicode par des équivalents compatibles avec FPDF (latin-1).
    """
    if not texte:
        return ""
    return (
        texte.replace("’", "'")
             .replace("–", "-")
             .replace("“", '"')
             .replace("”", '"')
             .replace("•", "-")
             .replace("…", "...")
             .replace("é", "e")
             .replace("è", "e")
             .replace("ê", "e")
             .replace("à", "a")
             .replace("ç", "c")
             .replace("ô", "o")
    )

def telecharger_rapport_view(request, rapport_id):
    rapport = get_object_or_404(RapportMatch, id=rapport_id)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, nettoyer_texte(f"Rapport du match {rapport.match}"), ln=True, align='C')

    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, nettoyer_texte(f"Arbitre central : {rapport.arbitre_central}"), ln=True)
    pdf.cell(0, 10, f"Date du rapport : {rapport.date_rapport.strftime('%d/%m/%Y %H:%M')}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Logistique :", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Service d'ordre présent : {'Oui' if rapport.service_ordre_present else 'Non'}", ln=True)
    pdf.cell(0, 8, f"Secouristes présents : {'Oui' if rapport.secouristes_present else 'Non'}", ln=True)
    pdf.cell(0, 8, f"Délégué présent : {'Oui' if rapport.delegue_present else 'Non'}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Statut du match :", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Match joué : {'Oui' if rapport.match_joue else 'Non'}", ln=True)
    if not rapport.match_joue and rapport.motif_non_joue:
        pdf.cell(0, 8, nettoyer_texte(f"Motif : {rapport.motif_non_joue}"), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Remarques de l'arbitre :", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8, nettoyer_texte(rapport.remarques_arbitre or "-"))

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Buts :", ln=True)
    pdf.set_font("Arial", '', 12)
    if rapport.buts.exists():
        for but in rapport.buts.all():
            pdf.cell(0, 8, nettoyer_texte(f"{but.minute}' - {but.equipe} - N°{but.joueur_dossard}"), ln=True)
    else:
        pdf.cell(0, 8, "Aucun but enregistré.", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Sanctions disciplinaires :", ln=True)
    pdf.set_font("Arial", '', 12)
    if rapport.sanctions.exists():
        for s in rapport.sanctions.all():
            pdf.cell(0, 8, nettoyer_texte(f"{s.minute}' - {s.equipe} - N°{s.joueur_dossard} - {s.type_carton}"), ln=True)
    else:
        pdf.cell(0, 8, "Aucune sanction enregistrée.", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Remplacements :", ln=True)
    pdf.set_font("Arial", '', 12)
    if rapport.remplacements.exists():
        for r in rapport.remplacements.all():
            pdf.cell(0, 8, nettoyer_texte(f"{r.minute}' - {r.equipe} : {r.joueur_entrant} remplace {r.joueur_sortant}"), ln=True)
    else:
        pdf.cell(0, 8, "Aucun remplacement enregistré.", ln=True)

    # Génération et retour du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_match_{rapport.id}.pdf"'

    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    response.write(pdf_bytes)
    return response

@login_required
def mes_rapports_view(request):
    if hasattr(request.user, 'arbitre'):
        # 🔐 Utilisateur est un arbitre → on affiche ses propres rapports
        rapports = RapportMatch.objects.filter(arbitre_central=request.user.arbitre).order_by('-date_rapport')
    elif request.user.role == 'admin' or request.user.is_staff:
        # 🔐 Admin → accès à tous les rapports arbitres
        rapports = RapportMatch.objects.select_related('match', 'arbitre_central').order_by('-date_rapport')
    else:
        messages.error(request, "⛔ Vous n’avez pas accès à cette liste.")
        return redirect('dashboard')

    return render(request, 'rapport/mes_rapports.html', {
        'rapports': rapports
    })

