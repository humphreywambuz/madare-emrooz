from app.modules.identity.domain.enums import UserRole
from tests.modules.monitoring.test_api import listed_midwife


def test_dashboard_opens_after_the_specialist_visit(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)

    assert client.get("/api/v1/fitness-profile", headers=mother).status_code == 404
    saved = client.put("/api/v1/fitness-profile", json={"goal": "weight_loss", "goal_note": "۵ کیلو تا عید"}, headers=mother)
    assert saved.status_code == 201
    assert saved.get_json()["dashboard_unlocked"] is False

    url = f"/api/v1/staff/patients/{mother_id}/fitness-profile/specialist-visit"
    assert client.post(url, headers=other_midwife).status_code == 403
    visited = client.post(url, headers=doctor)
    assert visited.status_code == 200 and visited.get_json()["dashboard_unlocked"] is True

    # Changing the goal keeps the visit.
    updated = client.put("/api/v1/fitness-profile", json={"goal": "muscle_gain"}, headers=mother)
    assert updated.status_code == 200
    body = updated.get_json()
    assert body == {**body, "goal": "muscle_gain", "goal_note": None, "dashboard_unlocked": True}


def test_fitness_validation(client, signed_in):
    _, mother = signed_in()
    assert client.put("/api/v1/fitness-profile", json={"goal": "flying"}, headers=mother).status_code == 422
    assert client.put("/api/v1/fitness-profile", json={"goal": "other", "specialist_visit_completed": True}, headers=mother).status_code == 422
