from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('aporte', '0001_initial')]
    operations = [migrations.AddField(
        model_name='aporte', name='simulacao_id',
        field=models.UUIDField(null=True, blank=True, unique=True, editable=False),
    )]
