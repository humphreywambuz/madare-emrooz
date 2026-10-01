"""The staff panel's views of one mother, assembled from every module.

Access is checked once and the view is written to the audit log once; the module
calls below then read by patient id without their own checks.
"""
import dataclasses
from dataclasses import asdict

from app.shared.application.context import Actor
from app.wiring import (
    auth_service,
    care_team_service,
    clinical_service,
    document_service,
    fitness_service,
    monitoring_service,
    pregnancy_service,
    profile_service,
    rehab_service,
    staff_service,
)


def _dict(value):
    return asdict(value) if value is not None and dataclasses.is_dataclass(value) else value


def _header(patient_id) -> dict:
    user = auth_service().get_user(patient_id)
    profile = profile_service().find_profile(patient_id)
    pregnancy = pregnancy_service().find_active(patient_id)
    return {
        "id": user.id,
        "mobile": user.mobile,
        "first_name": profile.first_name if profile else None,
        "last_name": profile.last_name if profile else None,
        "age": profile.age if profile else None,
        "join_goal": profile.join_goal if profile else None,
        "reproductive_status": profile.reproductive_status if profile else None,
        "gestational_week": pregnancy.gestational_week if pregnancy else None,
        "estimated_due_date": pregnancy.estimated_due_date if pregnancy else None,
        "midwife": _dict(staff_service().my_midwife(patient_id)),
    }


def summary_card(actor: Actor, patient_id) -> dict:
    """The red flags a clinician needs in under five seconds."""
    care_team = care_team_service()
    care_team.require_record_access(actor, patient_id)
    card = {
        "patient": _header(patient_id),
        "risk_tags": [asdict(t) for t in clinical_service().risk_tags(patient_id)],
    }
    care_team.record_viewed(actor, patient_id, "summary_card")
    return card


def full_record(actor: Actor, patient_id) -> dict:
    care_team = care_team_service()
    care_team.require_record_access(actor, patient_id)
    clinical = clinical_service()
    rehab = rehab_service().find(patient_id)
    documents = []
    for document in document_service().own_documents(patient_id):
        view = asdict(document)
        view.pop("storage_key")
        documents.append(view)
    logs = monitoring_service().own_logs(patient_id, limit=100)
    record = {
        "patient": _header(patient_id),
        "risk_tags": [asdict(t) for t in clinical.risk_tags(patient_id)],
        "profile": _dict(profile_service().find_profile(patient_id)),
        "medical_history": _dict(profile_service().find_medical_history(patient_id)),
        "pregnancy": _dict(pregnancy_service().find_active(patient_id)),
        "daily_logs": [{**asdict(log), "is_red_alert": log.is_red_alert} for log in logs],
        "documents": documents,
        "fitness_profile": _dict(fitness_service().find(patient_id)),
        "rehab_profile": (
            {**asdict(rehab.profile), "is_advanced_locked": rehab.is_advanced_locked} if rehab else None
        ),
        "notes": [asdict(n) for n in clinical.notes(patient_id)],
        "approvals": [asdict(a) for a in clinical.approvals(patient_id)],
    }
    care_team.record_viewed(actor, patient_id, "record")
    return record
