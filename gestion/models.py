from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

# --------------------- UTILISATEURS ---------------------

class User(AbstractUser):
    ROLE_CHOICES = [
        ('arbitre', 'Arbitre'),
        ('inspecteur', 'Inspecteur'),
        ('admin', 'Administrateur'),
    ]
    username = models.CharField(max_length=150, unique=True)  # gardé pour compatibilité
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # requis pour Django


    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=15, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.TextField(blank=True)


# --------------------- ARBITRES ---------------------

class Arbitre(models.Model):
    NIVEAU_CHOICES = [
        ('regional', 'Régional'),
        ('national', 'National'),
        ('elite', 'Elite'),
    ]
    
    POSTE_CHOICES = [
        ('central', 'Arbitre Central'),
        ('assistant', 'Arbitre Assistant'),
        ('quatrieme', 'Quatrième Arbitre'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    postes_preferes = models.CharField(
        max_length=50, 
        choices=POSTE_CHOICES, 
        blank=True,
        null=True
    )  # Ici, on garde un seul poste préféré au lieu de plusieurs
    experience_annees = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)
    note_moyenne = models.FloatField(default=0)
    nombre_matchs = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.niveau}"

# --------------------- INSPECTEURS ---------------------

class Inspecteur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    niveau = models.CharField(max_length=20, choices=Arbitre.NIVEAU_CHOICES)
    experience_annees = models.IntegerField(default=0)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Inspecteur {self.niveau}"

# --------------------- COMPÉTITION ---------------------

class Competition(models.Model):
    nom = models.CharField(max_length=200)
    date_debut = models.DateField()
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

# --------------------- MATCH ---------------------

class Match(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    equipe_domicile = models.CharField(max_length=100)
    equipe_exterieur = models.CharField(max_length=100)
    date_match = models.DateTimeField()
    lieu = models.CharField(max_length=200)
    statut = models.CharField(max_length=20, choices=[
        ('programme', 'Programmé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('reporte', 'Reporté'),
    ], default='programme')

    def __str__(self):
        return f"{self.equipe_domicile} vs {self.equipe_exterieur} - {self.date_match.strftime('%d/%m/%Y')}"

# --------------------- DÉSIGNATION ---------------------



class Designation(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='designation', verbose_name="Match")
    arbitre_central = models.ForeignKey(Arbitre, on_delete=models.CASCADE, related_name='central')
    arbitre_assistant1 = models.ForeignKey(Arbitre, on_delete=models.CASCADE, related_name='assistant1')
    arbitre_assistant2 = models.ForeignKey(Arbitre, on_delete=models.CASCADE, related_name='assistant2')
    quatrieme_arbitre = models.ForeignKey(Arbitre, on_delete=models.CASCADE, related_name='quatrieme', null=True, blank=True)
    inspecteur = models.ForeignKey(Inspecteur, on_delete=models.CASCADE)
    date_designation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Désignation - {self.match}" if self.match_id else "Désignation (incomplète)"

    def clean(self):
        errors = {}

        # ✅ Vérification que le match est bien défini
        if not self.match_id:
            errors['match'] = "Un match valide et daté est requis."
            raise ValidationError(errors)

        # ✅ Ici on est sûr que self.match existe
        date_jour = self.match.date_match.date()
        arbitres = [self.arbitre_central, self.arbitre_assistant1, self.arbitre_assistant2]
        if self.quatrieme_arbitre:
            arbitres.append(self.quatrieme_arbitre)

        # Vérifie si un arbitre est déjà désigné sur un autre match le même jour
        for arbitre in arbitres:
            conflits = Designation.objects.filter(
                match__date_match__date=date_jour
            ).filter(
                Q(arbitre_central=arbitre) |
                Q(arbitre_assistant1=arbitre) |
                Q(arbitre_assistant2=arbitre) |
                Q(quatrieme_arbitre=arbitre)
            ).exclude(pk=self.pk)

            if conflits.exists():
                errors.setdefault('__all__', []).append(
                    f"{arbitre} est déjà désigné pour un autre match le {date_jour}.")

        # Vérifie si un inspecteur est déjà désigné ce jour-là
        if Designation.objects.filter(
            match__date_match__date=date_jour,
            inspecteur=self.inspecteur
        ).exclude(pk=self.pk).exists():
            errors['inspecteur'] = f"{self.inspecteur} est déjà inspecteur sur un autre match ce jour-là."

        if errors:
            raise ValidationError(errors)

# --------------------- DISPONIBILITÉ ---------------------

class Disponibilite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_fin = models.DateField()
    disponible = models.BooleanField(default=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'date_debut', 'date_fin']

    def __str__(self):
        statut = "Disponible" if self.disponible else "Indisponible"
        return f"{self.user.get_full_name()} - {statut} ({self.date_debut} à {self.date_fin})"

# --------------------- RAPPORT ---------------------

class Rapport(models.Model):
    designation = models.OneToOneField(Designation, on_delete=models.CASCADE)
    inspecteur = models.ForeignKey(Inspecteur, on_delete=models.CASCADE)

    note_arbitre_central = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    note_assistant1 = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    note_assistant2 = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    note_quatrieme = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(20)], null=True, blank=True)

    commentaire_central = models.TextField()
    commentaire_assistant1 = models.TextField()
    commentaire_assistant2 = models.TextField()
    commentaire_quatrieme = models.TextField(blank=True)

    commentaire_general = models.TextField()
    incidents = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_notes()

    def _update_notes(self):
        notes_map = {
            self.designation.arbitre_central: self.note_arbitre_central,
            self.designation.arbitre_assistant1: self.note_assistant1,
            self.designation.arbitre_assistant2: self.note_assistant2
        }
        if self.designation.quatrieme_arbitre and self.note_quatrieme is not None:
            notes_map[self.designation.quatrieme_arbitre] = self.note_quatrieme

        for arbitre, note in notes_map.items():
            rapports = Rapport.objects.filter(
                models.Q(designation__arbitre_central=arbitre) |
                models.Q(designation__arbitre_assistant1=arbitre) |
                models.Q(designation__arbitre_assistant2=arbitre) |
                models.Q(designation__quatrieme_arbitre=arbitre)
            )
            total_notes = []
            for r in rapports:
                if r.designation.arbitre_central == arbitre:
                    total_notes.append(r.note_arbitre_central)
                elif r.designation.arbitre_assistant1 == arbitre:
                    total_notes.append(r.note_assistant1)
                elif r.designation.arbitre_assistant2 == arbitre:
                    total_notes.append(r.note_assistant2)
                elif r.designation.quatrieme_arbitre == arbitre and r.note_quatrieme is not None:
                    total_notes.append(r.note_quatrieme)
            if total_notes:
                arbitre.note_moyenne = sum(total_notes) / len(total_notes)
                arbitre.nombre_matchs = len(total_notes)
                arbitre.save()

    def __str__(self):
        return f"Rapport - {self.designation.match}"
    
    

class Cours(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    lieu = models.CharField(max_length=200, blank=True)
    formateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cours_formes')
    participants = models.ManyToManyField(User, blank=True, related_name='cours_participes')

    def __str__(self):
        return self.titre

    

    