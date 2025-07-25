# Generated by Django 5.2.3 on 2025-07-21 19:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0006_rapportmatch_evenementremplacement_evenementbut_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evenementbut',
            options={'verbose_name': 'But', 'verbose_name_plural': 'Buts'},
        ),
        migrations.AlterModelOptions(
            name='evenementremplacement',
            options={'verbose_name': 'Remplacement', 'verbose_name_plural': 'Remplacements'},
        ),
        migrations.AlterModelOptions(
            name='rapportmatch',
            options={'verbose_name': 'Rapport de match', 'verbose_name_plural': 'Rapports de match'},
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='buts_domicile',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='buts_exterieur',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='jaunes_domicile',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='jaunes_exterieur',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='remplacements_domicile',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='remplacements_exterieur',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='rouges_domicile',
        ),
        migrations.RemoveField(
            model_name='rapportmatch',
            name='rouges_exterieur',
        ),
        migrations.AlterField(
            model_name='evenementbut',
            name='equipe',
            field=models.CharField(choices=[('domicile', 'Équipe domicile'), ('exterieur', 'Équipe extérieur')], max_length=20, verbose_name='Équipe'),
        ),
        migrations.AlterField(
            model_name='evenementbut',
            name='joueur_dossard',
            field=models.CharField(max_length=5, verbose_name='Dossard du buteur'),
        ),
        migrations.AlterField(
            model_name='evenementbut',
            name='minute',
            field=models.PositiveIntegerField(verbose_name='Minute du but'),
        ),
        migrations.AlterField(
            model_name='evenementbut',
            name='rapport',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buts', to='gestion.rapportmatch', verbose_name='Rapport lié'),
        ),
        migrations.AlterField(
            model_name='evenementbut',
            name='remarque',
            field=models.TextField(blank=True, null=True, verbose_name='Remarques'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='equipe',
            field=models.CharField(choices=[('domicile', 'Équipe domicile'), ('exterieur', 'Équipe extérieur')], max_length=20, verbose_name='Équipe'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='joueur_entrant',
            field=models.CharField(max_length=5, verbose_name='Dossard du joueur entrant'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='joueur_sortant',
            field=models.CharField(max_length=5, verbose_name='Dossard du joueur sortant'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='minute',
            field=models.PositiveIntegerField(verbose_name='Minute du remplacement'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='rapport',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remplacements', to='gestion.rapportmatch', verbose_name='Rapport lié'),
        ),
        migrations.AlterField(
            model_name='evenementremplacement',
            name='remarque',
            field=models.TextField(blank=True, null=True, verbose_name='Remarques'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='arbitre_central',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestion.arbitre', verbose_name='Arbitre central'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='date_rapport',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Date du rapport'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='delegue_present',
            field=models.BooleanField(default=False, verbose_name='Délégué présent'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='match',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='gestion.match', verbose_name='Match concerné'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='match_joue',
            field=models.BooleanField(default=True, verbose_name='Match joué'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='motif_non_joue',
            field=models.TextField(blank=True, null=True, verbose_name='Motif si le match n’a pas été joué'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='remarques_arbitre',
            field=models.TextField(blank=True, null=True, verbose_name='Remarques de l’arbitre'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='secouristes_present',
            field=models.BooleanField(default=False, verbose_name='Présence des secouristes'),
        ),
        migrations.AlterField(
            model_name='rapportmatch',
            name='service_ordre_present',
            field=models.BooleanField(default=False, verbose_name='Service d’ordre présent'),
        ),
        migrations.CreateModel(
            name='SanctionDisciplinaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('equipe', models.CharField(choices=[('domicile', 'Équipe domicile'), ('exterieur', 'Équipe extérieur')], max_length=20, verbose_name='Équipe concernée')),
                ('joueur_dossard', models.CharField(max_length=5, verbose_name='Dossard du joueur')),
                ('type_carton', models.CharField(choices=[('jaune', '🟨 Avertissement'), ('rouge', '🟥 Expulsion')], max_length=10, verbose_name='Type de carton')),
                ('minute', models.PositiveIntegerField(verbose_name='Minute')),
                ('remarque', models.TextField(blank=True, null=True, verbose_name='Remarques')),
                ('rapport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sanctions', to='gestion.rapportmatch', verbose_name='Rapport lié')),
            ],
            options={
                'verbose_name': 'Sanction disciplinaire',
                'verbose_name_plural': 'Sanctions disciplinaires',
            },
        ),
        migrations.DeleteModel(
            name='SanctionDisciplinaires',
        ),
    ]
