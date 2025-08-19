import logging
from django.db.models.signals import pre_save, post_save, pre_delete
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.apps import apps
from django.db import connection
from .models import Profile, ActivityLog
from .middleware import get_request_user, get_request_ip, get_request_session_key

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Create a user profile whenever a new User is created
    """
    if created:
        Profile.objects.create(user=instance)

# -------- Generic CRUD auditing ---------
_pre_save_cache = {}
_activitylog_table_exists = None


def _activitylog_ready():
    global _activitylog_table_exists
    if _activitylog_table_exists is None:
        try:
            tables = set(connection.introspection.table_names())
            _activitylog_table_exists = ActivityLog._meta.db_table in tables
        except Exception:
            _activitylog_table_exists = False
    return _activitylog_table_exists

def _model_label(instance):
    return f"{instance._meta.app_label}.{instance.__class__.__name__}"

def _serialize_instance(instance):
    """Serialize model instance to a plain dict of editable concrete field values.
    ForeignKey fields will be stored as their raw id value.
    """
    data = {}
    for field in instance._meta.get_fields():
        if not getattr(field, 'concrete', False):
            continue
        if getattr(field, 'many_to_many', False) or getattr(field, 'one_to_many', False):
            continue  # skip relations that need separate queries
        if hasattr(field, 'attname'):
            name = field.attname.replace('_id', '') if field.is_relation else field.attname
        else:
            name = field.name
        try:
            val = getattr(instance, field.attname if hasattr(field, 'attname') else field.name)
        except Exception:
            continue
        # For bytes/files use string representation
        if hasattr(val, 'name'):
            val = val.name
        data[name] = val
    return data

@receiver(pre_save)
def log_pre_save(sender, instance, **kwargs):
    # Only track project models, skip Django internal apps
    if not hasattr(instance, '_meta'):
        return
    label = _model_label(instance)
    # Avoid logging ActivityLog itself to prevent recursion
    if label == 'core.ActivityLog':
        return
    # Only audit our app models
    if instance._meta.app_label != 'core':
        return
    if instance.pk:
        # Existing -> capture before snapshot
        try:
            existing = sender.objects.get(pk=instance.pk)
            _pre_save_cache[(label, instance.pk)] = _serialize_instance(existing)
        except sender.DoesNotExist:
            _pre_save_cache[(label, instance.pk)] = None
    else:
        _pre_save_cache[(label, None)] = None

@receiver(post_save)
def log_post_save(sender, instance, created, **kwargs):
    if not hasattr(instance, '_meta'):
        return
    label = _model_label(instance)
    if label == 'core.ActivityLog':
        return
    if instance._meta.app_label != 'core':
        return
    after = _serialize_instance(instance)
    key = (label, instance.pk if not created else None)
    before = _pre_save_cache.pop(key, None)
    action = ActivityLog.ACTION_CREATE if created else ActivityLog.ACTION_UPDATE
    if not _activitylog_ready():
        return
    try:
        ActivityLog.objects.create(
            user=get_request_user(),
            action_type=action,
            model_name=label,
            object_id=str(instance.pk),
            before_data=before,
            after_data=after,
            ip_address=get_request_ip(),
            session_key=get_request_session_key(),
        )
    except Exception:
        logger.exception('Failed to write ActivityLog for %s', label)

@receiver(pre_delete)
def log_pre_delete(sender, instance, **kwargs):
    if not hasattr(instance, '_meta'):
        return
    label = _model_label(instance)
    if label == 'core.ActivityLog':
        return
    if instance._meta.app_label != 'core':
        return
    before = _serialize_instance(instance)
    if not _activitylog_ready():
        return
    try:
        ActivityLog.objects.create(
            user=get_request_user(),
            action_type=ActivityLog.ACTION_DELETE,
            model_name=label,
            object_id=str(instance.pk),
            before_data=before,
            after_data=None,
            ip_address=get_request_ip(),
            session_key=get_request_session_key(),
        )
    except Exception:
        logger.exception('Failed to write ActivityLog (DELETE) for %s', label)

# -------- Auth auditing ---------

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action_type=ActivityLog.ACTION_LOGIN,
        model_name='auth.User',
        object_id=str(user.pk),
        before_data=None,
        after_data={'username': user.username},
        ip_address=get_request_ip(),
        session_key=get_request_session_key(),
    )

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action_type=ActivityLog.ACTION_LOGOUT,
        model_name='auth.User',
        object_id=str(getattr(user, 'pk', '')),
        before_data={'username': getattr(user, 'username', '')},
        after_data=None,
        ip_address=get_request_ip(),
        session_key=get_request_session_key(),
    )

@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username') if isinstance(credentials, dict) else ''
    ActivityLog.objects.create(
        user=None,
        action_type=ActivityLog.ACTION_FAILED_LOGIN,
        model_name='auth.User',
        object_id=None,
        before_data={'username': username},
        after_data=None,
        ip_address=get_request_ip(),
        session_key=get_request_session_key(),
    )

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """
    Save the user profile whenever a User is saved
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Create the profile if it doesn't exist
        Profile.objects.create(user=instance) 