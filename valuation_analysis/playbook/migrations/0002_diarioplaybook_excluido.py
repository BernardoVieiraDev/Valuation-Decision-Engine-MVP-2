from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('playbook', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='diarioplaybook', name='excluido',
            field=models.BooleanField(default=False),
        ),
    ]
