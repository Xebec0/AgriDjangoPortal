"""
Cache invalidation signals for automatic cache management
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AgricultureProgram, Candidate, Registration
from .cache_utils import invalidate_program_cache, invalidate_candidate_cache


@receiver(post_save, sender=AgricultureProgram)
@receiver(post_delete, sender=AgricultureProgram)
def invalidate_program_cache_on_change(sender, **kwargs):
    """Invalidate program cache when programs are modified"""
    invalidate_program_cache()


@receiver(post_save, sender=Candidate)
@receiver(post_delete, sender=Candidate)
def invalidate_candidate_cache_on_change(sender, **kwargs):
    """Invalidate candidate cache when candidates are modified"""
    invalidate_candidate_cache()


@receiver(post_save, sender=Registration)
@receiver(post_delete, sender=Registration)
def invalidate_related_cache_on_registration_change(sender, **kwargs):
    """Invalidate caches when registrations change"""
    # Registration changes affect both program and candidate data
    invalidate_program_cache()
    invalidate_candidate_cache()
