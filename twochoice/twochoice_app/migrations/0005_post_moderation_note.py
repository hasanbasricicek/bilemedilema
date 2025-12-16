from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twochoice_app', '0004_userprofile_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='moderation_note',
            field=models.TextField(blank=True, default=''),
        ),
    ]
