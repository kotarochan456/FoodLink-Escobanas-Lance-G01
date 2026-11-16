from django.db import migrations, models

def require_legacy_choice(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.using(schema_editor.connection.alias).filter(role='MEMBER').update(role=None)

def restore_member_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.using(schema_editor.connection.alias).filter(
        models.Q(role__isnull=True) | models.Q(role__in=['DONOR', 'RECIPIENT'])
    ).update(role='MEMBER')

class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]
    operations = [
        migrations.RemoveConstraint(model_name='user', name='valid_role'),
        migrations.AlterField(model_name='user', name='role', field=models.CharField(
            max_length=10, choices=[('ADMIN', 'Admin'), ('DONOR', 'Donor'), ('RECIPIENT', 'Recipient')],
            null=True, blank=True, default=None)),
        migrations.RunPython(require_legacy_choice, restore_member_roles),
        migrations.AddConstraint(model_name='user', constraint=models.CheckConstraint(
            condition=models.Q(role__in=['ADMIN', 'DONOR', 'RECIPIENT']) | models.Q(role__isnull=True),
            name='valid_role')),
    ]
