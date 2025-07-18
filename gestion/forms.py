from django import forms
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import (
    User, Arbitre, Inspecteur, Competition, Match,
    Designation, Rapport, Disponibilite
)

from django import forms

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail")
    password = forms.CharField(widget=forms.PasswordInput)


    
    
    
    
class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email',
            'role', 'telephone', 'date_naissance', 'adresse'
        ]
        widgets = {
            'date_naissance': forms.SelectDateWidget(years=range(1960, 2025)),
            'adresse': forms.Textarea(attrs={'rows': 2}),
        }

    def generate_username(self, first_name, last_name):
        from django.utils.text import slugify
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
            self.cleaned_data['first_name'], self.cleaned_data['last_name']
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
        
from django import forms
from .models import Designation, Arbitre, Inspecteur

class DesignationForm(forms.ModelForm):
    match = forms.ModelChoiceField(
        queryset=Match.objects.all(),
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        arbitres_actifs = Arbitre.objects.filter(actif=True)
        inspecteurs_actifs = Inspecteur.objects.filter(actif=True)

        self.fields['arbitre_central'].queryset = arbitres_actifs
        self.fields['arbitre_assistant1'].queryset = arbitres_actifs
        self.fields['arbitre_assistant2'].queryset = arbitres_actifs
        self.fields['quatrieme_arbitre'].queryset = arbitres_actifs
        self.fields['inspecteur'].queryset = inspecteurs_actifs

        self.fields['quatrieme_arbitre'].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-select mb-2',
            })

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