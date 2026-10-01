import io

from app.modules.identity.domain.enums import UserRole
from tests.modules.monitoring.test_api import listed_midwife

POSTPARTUM = {
    "subcategory": "postpartum_recovery",
    "pain_level": 4,
    "had_related_surgery": True,
    "related_surgery_name": "سزارین",
    "uses_pain_medication": False,
    "time_since_delivery": "two_to_six_months",
    "has_pelvic_warning_signs": False,
}


def test_questionnaire_rules(client, signed_in):
    _, mother = signed_in()
    saved = client.put("/api/v1/rehab-profile", json=POSTPARTUM, headers=mother)
    assert saved.status_code == 201, saved.get_json()
    body = saved.get_json()
    assert body["time_since_delivery"] == "two_to_six_months"
    assert body["is_advanced_locked"] is True and body["specialist_visit_completed"] is False

    def put(**changes):
        return client.put("/api/v1/rehab-profile", json={**POSTPARTUM, **changes}, headers=mother)

    wrong_subtype = put(injury_onset="recent")
    assert wrong_subtype.status_code == 422
    assert wrong_subtype.get_json()["error"]["details"] == {"fields": ["injury_onset"]}
    assert put(related_surgery_name=None).status_code == 422
    assert put(pain_level=11).status_code == 422
    assert put(specialist_visit_completed=True).status_code == 422  # only staff record visits

    switched = put(subcategory="injury_correction", time_since_delivery=None, has_pelvic_warning_signs=None, injury_onset="chronic")
    assert switched.status_code == 200
    assert switched.get_json()["time_since_delivery"] is None


def test_staff_record_the_visit_and_attach_imaging(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)
    client.put("/api/v1/rehab-profile", json={**POSTPARTUM, "subcategory": "orthopedic_referral",
        "time_since_delivery": None, "has_pelvic_warning_signs": None, "referral_reason": "spine_checkup"}, headers=mother)

    visit = client.post(f"/api/v1/staff/patients/{mother_id}/rehab-profile/specialist-visit", headers=doctor)
    assert visit.status_code == 200
    # Still locked: the doctor hasn't approved the plan yet.
    assert visit.get_json()["specialist_visit_completed"] is True and visit.get_json()["is_advanced_locked"] is True

    scan = client.post(
        f"/api/v1/staff/patients/{mother_id}/documents",
        data={"document_type": "imaging", "file": (io.BytesIO(b"\xff\xd8\xff" + b"x" * 50), "mri.jpg")},
        headers=midwife, content_type="multipart/form-data",
    ).get_json()
    url = f"/api/v1/staff/patients/{mother_id}/rehab-profile/imaging"
    assert client.put(url, json={"document_id": scan["id"]}, headers=doctor).status_code == 403
    linked = client.put(url, json={"document_id": scan["id"]}, headers=midwife)
    assert linked.status_code == 200 and linked.get_json()["imaging_document_id"] == scan["id"]

    # Her answers can change without losing what staff recorded.
    again = client.put("/api/v1/rehab-profile", json={**POSTPARTUM, "subcategory": "orthopedic_referral",
        "time_since_delivery": None, "has_pelvic_warning_signs": None, "referral_reason": "spine_checkup", "pain_level": 2}, headers=mother)
    assert again.get_json()["imaging_document_id"] == scan["id"]
    assert again.get_json()["specialist_visit_completed"] is True


def test_imaging_must_be_her_document(client, signed_in):
    import uuid

    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)
    client.put("/api/v1/rehab-profile", json=POSTPARTUM, headers=mother)
    url = f"/api/v1/staff/patients/{mother_id}/rehab-profile/imaging"
    assert client.put(url, json={"document_id": str(uuid.uuid4())}, headers=midwife).status_code == 404
