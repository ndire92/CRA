from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Arbitre, Inspecteur, Competition,
    Match, Designation, Disponibilite, Rapport, RapportMatch, SanctionDisciplinaire, EvenementBut, EvenementRemplacement

)

# ------------------------- UTILISATEUR -------------------------

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informations CRA', {
            'fields': ('role', 'telephone', 'date_naissance', 'zone')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'telephone')
        }),
    )

# ------------------------- ARBITRES -------------------------

@admin.register(Arbitre)
class ArbitreAdmin(admin.ModelAdmin):
    list_display = ('user', 'niveau', 'affiche_postes', 'note_moyenne', 'nombre_matchs', 'actif')
    list_filter = ('niveau', 'postes_preferes', 'actif')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('note_moyenne', 'nombre_matchs')

    def affiche_postes(self, obj):
        return obj.postes_preferes
    affiche_postes.short_description = "Poste préféré"

# ------------------------- INSPECTEURS -------------------------

@admin.register(Inspecteur)
class InspecteurAdmin(admin.ModelAdmin):
    list_display = ('user', 'niveau', 'experience_annees', 'actif')
    list_filter = ('niveau', 'actif')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')

# ------------------------- COMPÉTITIONS -------------------------

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_debut', 'active')
    list_filter = ('active', 'date_debut')
    search_fields = ('nom',)
    actions = ['activer', 'desactiver']

    @admin.action(description="✅ Activer les compétitions sélectionnées")
    def activer(self, request, queryset):
        queryset.update(active=True)

    @admin.action(description="❌ Désactiver les compétitions sélectionnées")
    def desactiver(self, request, queryset):
        queryset.update(active=False)

# ------------------------- MATCHS -------------------------

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('equipe_domicile', 'equipe_exterieur', 'date_match', 'competition', 'statut')
    list_filter = ('statut', 'competition', 'date_match')
    search_fields = ('equipe_domicile', 'equipe_exterieur', 'lieu')
    date_hierarchy = 'date_match'

# ------------------------- DÉSIGNATIONS -------------------------

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('match', 'arbitre_central', 'inspecteur', 'date_designation')
    list_filter = ('date_designation', 'match__competition')
    search_fields = ('match__equipe_domicile', 'match__equipe_exterieur')

# ------------------------- DISPONIBILITÉS -------------------------

@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_debut', 'date_fin', 'disponible')
    list_filter = ('disponible', 'date_debut')
    search_fields = ('user__first_name', 'user__last_name')

# ------------------------- RAPPORTS -------------------------

@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = (
        'designation', 'inspecteur', 'note_arbitre_central',
        'note_assistant1', 'note_assistant2', 'note_quatrieme', 'date_creation'
    )
    list_filter = ('date_creation', 'designation__match__competition')
    search_fields = (
        'designation__match__equipe_domicile',
        'designation__match__equipe_exterieur',
        'inspecteur__user__last_name'
    )
    readonly_fields = ('date_creation',)

    fieldsets = (
        (None, {
            'fields': ('designation', 'inspecteur', 'date_creation')
        }),
        ('Notes des arbitres', {
            'fields': (
                'note_arbitre_central', 'note_assistant1',
                'note_assistant2', 'note_quatrieme'
            )
        }),
        ('Commentaires', {
            'fields': (
                'commentaire_central', 'commentaire_assistant1',
                'commentaire_assistant2', 'commentaire_quatrieme',
                'commentaire_general', 'incidents', 'recommandations'
            )
        }),
    )
    

class SanctionDisciplinaireInline(admin.TabularInline):
    model = SanctionDisciplinaire
    extra = 1

class EvenementButInline(admin.TabularInline):
    model = EvenementBut
    extra = 1

class EvenementRemplacementInline(admin.TabularInline):
    model = EvenementRemplacement
    extra = 1

@admin.register(RapportMatch)
class RapportMatchAdmin(admin.ModelAdmin):
    list_display = ('match', 'arbitre_central', 'match_joue', 'date_rapport')
    list_filter = ('match_joue', 'date_rapport')
    search_fields = ('match__id', 'arbitre_central__nom', 'remarques_arbitre')
    inlines = [SanctionDisciplinaireInline, EvenementButInline, EvenementRemplacementInline]

@admin.register(SanctionDisciplinaire)
class SanctionDisciplinaireAdmin(admin.ModelAdmin):
    list_display = ('rapport', 'equipe', 'joueur_dossard', 'type_carton', 'minute')

@admin.register(EvenementBut)
class EvenementButAdmin(admin.ModelAdmin):
    list_display = ('rapport', 'equipe', 'joueur_dossard', 'minute')

@admin.register(EvenementRemplacement)
class EvenementRemplacementAdmin(admin.ModelAdmin):
    list_display = ('rapport', 'equipe', 'joueur_sortant', 'joueur_entrant', 'minute')
