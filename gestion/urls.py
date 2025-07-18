from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # Page d'accueil et tableau de bord
    path('', views.page_accueil_view, name='home'),
    path('dashboard', views.dashboard_view, name='dashboard'),
    # Inscription utilisateur
    path('inscription/', views.inscription_view, name='inscription'),
    path('login/',auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/',auth_views.LogoutView.as_view(), name='logout'),


    # Profils
    path('profil/arbitre/', views.profil_arbitre_view, name='profil_arbitre'),
    path('profil/inspecteur/', views.profil_inspecteur_view, name='profil_inspecteur'),

    # Disponibilités
    path('disponibilites/', views.mes_disponibilites_view, name='mes_disponibilites'),
    path('disponibilites/ajouter/', views.ajouter_disponibilite_view, name='ajouter_disponibilite'),

    # Désignations (consultation pour arbitre)
    path('mes-designations/', views.mes_designations_view, name='mes_designations'),
    path('designations/en-attente/', views.matchs_a_designer_view, name='matchs_a_designer'),

    # Création de match et désignation (admin)
    path('match/nouveau/', views.creer_match_view, name='creer_match'),
    path('match/<int:match_id>/designation/', views.creer_designation_view, name='creer_designation'),
    path('match/<int:match_id>/suggestions/', views.suggestion_designation_view, name='suggestion_designation'),
    path('matchs/', views.liste_matchs_view, name='liste_matchs'),
    path('competition/nouveau/', views.creer_competition_view, name='creer_competition'),
    path('competition/', views.liste_competitions_view, name='liste_competitions'),
    path('classement/arbitres/', views.classement_arbitres_view, name='classement_arbitres'),
    # Rapport d'inspection
    path('rapport/<int:designation_id>/remplir/', views.remplir_rapport_view, name='remplir_rapport'),
    path('rapports/', views.liste_rapports_view, name='liste_rapports'),
    path('rapports/<int:rapport_id>/', views.voir_rapport_view, name='voir_rapport'),
    path('arbitres/', views.liste_arbitres_view, name='liste_arbitres'),
    path('inspecteurs/', views.liste_inspecteurs_view, name='liste_inspecteurs'),

]