from datetime import timedelta

from django.utils import timezone

from core.models import Candidate, Notification
from tests.factories import candidate_factory, program_factory, user_factory


def test_candidate_can_assign_farm(db):
    user = user_factory(username="u1")
    program = program_factory()
    cand = candidate_factory(created_by=user, program=program, status=Candidate.VALIDATED)
    assert cand.can_assign_farm() is True
    cand.status = Candidate.DRAFT
    cand.save(update_fields=["status"])
    assert cand.can_assign_farm() is False


def test_notification_clear_old_notifications(db):
    user = user_factory(username="u1")
    old = Notification.add_notification(user=user, message="old")
    recent = Notification.add_notification(user=user, message="recent")

    old.created_at = timezone.now() - timedelta(days=40)
    old.save(update_fields=["created_at"])

    deleted_count, _ = Notification.clear_old_notifications(user=user, days=30)
    assert deleted_count == 1
    assert Notification.objects.filter(id=old.id).exists() is False
    assert Notification.objects.filter(id=recent.id).exists() is True

