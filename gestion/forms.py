from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import (
    EvenementBut, EvenementRemplacement, RapportMatch, SanctionDisciplinaire, User, Arbitre, Inspecteur, Competition, Match,
    Designation, Rapport, Disponibilite
)
from .models import RapportMatch, SanctionDisciplinaire, EvenementBut, EvenementRemplacement
from django.forms import inlineformset_factory
from django import forms

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="zone e-mail")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        # Vérifie si l'utilisateur existe avec cet email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Aucun utilisateur trouvé avec cet e-mail.")
        except User.MultipleObjectsReturned:
            raise forms.ValidationError("Plusieurs utilisateurs ont cet email — veuillez contacter un administrateur.")

        # Authentifie avec l'email comme identifiant
        user = authenticate(username=email, password=password)
        if not user:
            raise forms.ValidationError("Email ou mot de passe invalide.")
        self.user = user
        return cleaned_data



class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email',
            'role', 'telephone', 'date_naissance', 'zone'
        ]
        widgets = {
            'date_naissance': forms.SelectDateWidget(years=range(1960, 2025)),
            'zone': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre utilisateur.")
        return email

    def generate_username(self, first_name, last_name):
        base = slugify(f"{first_name}.{last_name}")
        username = base
        count = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{count}"
            count += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.generate_username(
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name']
        )
        if commit:
            user.save()
        return user
    
    
    
# 👤 Arbitre
class ArbitreForm(forms.ModelForm):
    class Meta:
        model = Arbitre
        fields = ['niveau', 'postes_preferes', 'experience_annees', 'actif']
        widgets = {
            'postes_preferes': forms.Select()  # Utilisation d'un champ Select pour les postes
        }

# 👤 Inspecteur
class InspecteurForm(forms.ModelForm):
    class Meta:
        model = Inspecteur
        fields = ['niveau', 'experience_annees', 'actif']


# 📅 Disponibilité
class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ['date_debut', 'date_fin', 'disponible', 'commentaire']
        widgets = {
            'date_debut': forms.SelectDateWidget(),
            'date_fin': forms.SelectDateWidget(),
            'commentaire': forms.Textarea(attrs={'rows': 2})
        }

# 🏆 Compétition
class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['nom', 'date_debut', 'description', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'date_debut': forms.SelectDateWidget()
        }

# ⚽ Match
class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'competition', 'equipe_domicile', 'equipe_exterieur',
            'date_match', 'lieu', 'statut'
        ]
        widgets = {
            'date_match': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'lieu': forms.TextInput(attrs={'placeholder': 'Stade ou Complexe'}),
        }
        

class DesignationForm(forms.ModelForm):
    ZONES = [
        ("Tivaouane", "Tivaouane"),
        ("Meckhe", "Meckhe"),
        ("Mboro", "Mboro"),
        ("Pambale", "Pambale"),
    ]

    zone = forms.ChoiceField(
        choices=ZONES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select mb-2', 'id': 'zone-select'})
    )

    match = forms.ModelChoiceField(
        queryset=Match.objects.all(),
        widget=forms.HiddenInput()
    )

    def label_arbitre(self, obj):
        zone = obj.user.zone or "zone inconnue"
        return f"{obj.user.get_full_name()} • {zone}"
    
    def label_inspecteur(self, obj):
        zone = obj.user.zone or "zone inconnue"
        return f"{obj.user.get_full_name()} • {zone}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        arbitres_actifs = Arbitre.objects.select_related('user').filter(actif=True).order_by('user__zone')
        inspecteurs_actifs = Inspecteur.objects.select_related('user').filter(actif=True).order_by('user__zone')

        self.fields['arbitre_central'].queryset = arbitres_actifs
        self.fields['arbitre_assistant1'].queryset = arbitres_actifs
        self.fields['arbitre_assistant2'].queryset = arbitres_actifs
        self.fields['quatrieme_arbitre'].queryset = arbitres_actifs
        self.fields['inspecteur'].queryset = inspecteurs_actifs

        self.fields['arbitre_central'].label_from_instance = self.label_arbitre
        self.fields['arbitre_assistant1'].label_from_instance = self.label_arbitre
        self.fields['arbitre_assistant2'].label_from_instance = self.label_arbitre
        self.fields['quatrieme_arbitre'].label_from_instance = self.label_arbitre
        self.fields['inspecteur'].label_from_instance = self.label_inspecteur

        self.fields['quatrieme_arbitre'].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-select mb-2'})

    class Meta:
        model = Designation
        exclude = ['date_designation']
        
        
# 🧾 Rapport d’inspection
class RapportForm(forms.ModelForm):
    class Meta:
        model = Rapport
        exclude = ['designation', 'inspecteur', 'date_creation']
        widgets = {
            'commentaire_central': forms.Textarea(attrs={'rows': 2}),
            'commentaire_assistant1': forms.Textarea(attrs={'rows': 2}),
            'commentaire_assistant2': forms.Textarea(attrs={'rows': 2}),
            'commentaire_quatrieme': forms.Textarea(attrs={'rows': 2}),
            'commentaire_general': forms.Textarea(attrs={'rows': 3}),
            'recommandations': forms.Textarea(attrs={'rows': 2}),
            'incidents': forms.Textarea(attrs={'rows': 2}),
        }


class RapportMatchForm(forms.ModelForm):
    class Meta:
        model = RapportMatch
        fields = ['match', 'arbitre_central', 'match_joue', 'remarques_arbitre']
        widgets = {
            'match': forms.Select(attrs={'class': 'form-select'}),
            'arbitre_central': forms.Select(attrs={'class': 'form-select'}),
            'match_joue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarques_arbitre': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

SanctionFormSet = inlineformset_factory(
    RapportMatch, SanctionDisciplinaire,
    fields=['equipe', 'joueur_dossard', 'type_carton', 'minute', 'remarque'],
    widgets={
        'equipe': forms.Select(attrs={'class': 'form-select'}),
        'joueur_dossard': forms.TextInput(attrs={'class': 'form-control'}),
        'type_carton': forms.Select(attrs={'class': 'form-select'}),
        'minute': forms.NumberInput(attrs={'class': 'form-control'}),
        'remarque': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
    },
    extra=1, can_delete=True
)

ButFormSet = inlineformset_factory(
    RapportMatch, EvenementBut,
    fields=['equipe', 'joueur_dossard', 'minute', 'remarque'],
    widgets={
        'equipe': forms.Select(attrs={'class': 'form-select'}),
        'joueur_dossard': forms.TextInput(attrs={'class': 'form-control'}),
        'minute': forms.NumberInput(attrs={'class': 'form-control'}),
        'remarque': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
    },
    extra=1, can_delete=True
)

RemplacementFormSet = inlineformset_factory(
    RapportMatch, EvenementRemplacement,
    fields=['equipe', 'joueur_sortant', 'joueur_entrant', 'minute', 'remarque'],
    widgets={
        'equipe': forms.Select(attrs={'class': 'form-select'}),
        'joueur_sortant': forms.TextInput(attrs={'class': 'form-control'}),
        'joueur_entrant': forms.TextInput(attrs={'class': 'form-control'}),
        'minute': forms.NumberInput(attrs={'class': 'form-control'}),
        'remarque': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
    },
    extra=1, can_delete=True
)