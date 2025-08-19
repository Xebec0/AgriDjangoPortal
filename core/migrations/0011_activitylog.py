from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_profile_country_of_birth_profile_date_of_birth_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete'), ('LOGIN', 'Login'), ('LOGOUT', 'Logout'), ('FAILED_LOGIN', 'Failed Login'), ('SYSTEM', 'System')], max_length=20)),
                ('model_name', models.CharField(db_index=True, max_length=100)),
                ('object_id', models.CharField(blank=True, max_length=64, null=True)),
                ('before_data', models.JSONField(blank=True, null=True)),
                ('after_data', models.JSONField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('session_key', models.CharField(blank=True, max_length=40, null=True)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='activitylog',
            index=models.Index(fields=['user'], name='core_activ_user_id_2a2fba_idx'),
        ),
        migrations.AddIndex(
            model_name='activitylog',
            index=models.Index(fields=['action_type'], name='core_activ_action__8a6671_idx'),
        ),
        migrations.AddIndex(
            model_name='activitylog',
            index=models.Index(fields=['timestamp'], name='core_activ_timesta_7642d5_idx'),
        ),
    ]
