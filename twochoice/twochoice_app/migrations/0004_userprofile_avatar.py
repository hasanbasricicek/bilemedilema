from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twochoice_app', '0003_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='avatar_mode',
            field=models.CharField(default='initial', max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar_preset',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar_config',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
