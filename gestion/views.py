from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from .utils import envoyer_whatsapp_local
import datetime
import time
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login






from .forms import (
    CompetitionForm, DesignationForm, DisponibiliteForm, EmailLoginForm, MatchForm, RapportForm,
    UserRegistrationForm, ArbitreForm, InspecteurForm
)
from .models import (
    Competition, Match, Arbitre, Designation, Disponibilite,
    Inspecteur, Rapport
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
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            form.add_error(None, "❌ Email ou mot de passe incorrect.")
    return render(request, 'login.html', {'form': form})



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

        context = {
            'nb_competitions': Competition.objects.count(),
            'nb_matchs': Match.objects.count(),
            'nb_arbitres': Arbitre.objects.filter(actif=True).count(),
            'nb_inspecteurs': Inspecteur.objects.filter(actif=True).count(),
            'nb_rapports': nb_rapports,
            'nb_designations_restantes': nb_designations_restantes,
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
        print("POST reçu :", request.POST)
        form = DesignationForm(request.POST)
        

        if form.is_valid():
            designation = form.save(commit=False)
            designation.match = form.cleaned_data['match']  # 🔒 depuis le formulaire

            try:
                designation.full_clean()  # d'abord valider les contraintes métiers
                designation.save()        # puis enregistrer si tout passe
            except ValidationError as e:
                form.add_error(None, e)
                designation.delete()  # Nettoyage si validation échoue
                return render(request, 'designation/creer.html', {'form': form, 'match': match})

            # ✅ Infos match
            date_str = match.date_match.strftime('%A %d %B %Y à %Hh')
            lieu = match.lieu or "Non précisé"
            affiche_match = f"{match.equipe_domicile} vs {match.equipe_exterieur}"

            # 📧 Email
            emails = [
                designation.arbitre_central.user.email,
                designation.arbitre_assistant1.user.email,
                designation.arbitre_assistant2.user.email,
                designation.inspecteur.user.email,
            ]
            if designation.quatrieme_arbitre:
                emails.append(designation.quatrieme_arbitre.user.email)
            emails = [e for e in emails if e]  # Supprimer les emails vides

            email_content = f"""Bonjour,

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
                    message=email_content,
                    from_email=None,  # Peut être configuré via DEFAULT_FROM_EMAIL
                    recipient_list=emails,
                    fail_silently=False,
                )
                messages.success(request, "✅ Désignation enregistrée et email envoyé.")
            except Exception as e:
                messages.warning(request, f"📨 Email échoué : {e}")

            # 📲 WhatsApp
            roles = [
                (designation.arbitre_central, "Arbitre central"),
                (designation.arbitre_assistant1, "Assistant 1"),
                (designation.arbitre_assistant2, "Assistant 2"),
                (designation.inspecteur, "Inspecteur"),
            ]
            if designation.quatrieme_arbitre:
                roles.append((designation.quatrieme_arbitre, "4ᵉ arbitre"))

            for arbitre, role in roles:
                if arbitre.telephone:
                    message_whatsapp = f"""📋 CRA Tivaouane

Bonjour {arbitre.user.get_full_name()}, vous êtes désigné comme {role} pour :

📅 {date_str}
🏟️ {affiche_match}
📍 Lieu : {lieu}

Merci de confirmer votre présence."""
                    try:
                        envoyer_whatsapp_local(arbitre.telephone, message_whatsapp)
                        time.sleep(5)
                    except Exception as e:
                        messages.warning(request, f"WhatsApp non envoyé à {arbitre} : {e}")

            return redirect('dashboard')

    else:
        form = DesignationForm(initial={'match': match})
       

    return render(request, 'designation/creer.html', {'form': form, 'match': match})





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