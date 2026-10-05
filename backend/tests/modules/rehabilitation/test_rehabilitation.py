import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.rehabilitation.domain.enums import RehabSubcategory
from app.modules.rehabilitation.domain.policies import is_advanced_locked
from app.modules.rehabilitation.infrastructure.models import RehabProfileModel


@pytest.mark.parametrize(
    ("visit", "approval", "locked"),
    [(False, False, True), (True, False, True), (False, True, True), (True, True, False)],
)
def test_advanced_exercises_lock(visit, approval, locked):
    assert is_advanced_locked(specialist_visit_completed=visit, has_active_approval=approval) is locked


def rehab(user_id, **overrides):
    fields = dict(
        user_id=user_id,
        subcategory=RehabSubcategory.INJURY_CORRECTION,
        pain_level=4,
        had_related_surgery=False,
        uses_pain_medication=False,
    )
    fields.update(overrides)
    return RehabProfileModel(**fields)


def test_pain_level_range(session, make_user):
    session.add(rehab(make_user().id, pain_level=11))
    with pytest.raises(IntegrityError):
        session.flush()


def test_surgery_name_required(session, make_user):
    session.add(rehab(make_user().id, had_related_surgery=True))
    with pytest.raises(IntegrityError):
        session.flush()


def test_answer_reports_whether_anything_changed():
    import uuid

    from app.modules.rehabilitation.domain.entities import RehabProfile

    answers = {
        "subcategory": RehabSubcategory.YOGA_MEDITATION, "pain_level": 3,
        "had_related_surgery": False, "uses_pain_medication": False,
    }
    profile = RehabProfile.from_answers(uuid.uuid4(), answers)
    assert profile.answer(dict(answers)) is False
    assert profile.answer({**answers, "pain_level": 7}) is True
