"""Generate the Postman collection and environment in docs/postman/.

Run from the backend directory after adding or changing an endpoint:

    python scripts/generate_postman.py

tests/test_postman.py fails when a route is missing from ENDPOINTS or the JSON files are stale.

Using it: import both files into Postman and pick the "Madare Emrooz (local)" environment.
Run "Request code" then "Sign in" in "Auth (mother)" or "Auth (staff)"; the sign-in saves the
token for that folder. With SMS_BACKEND=console the code is printed in the server log.
Requests that create something (a pregnancy link, a staff member, a document…) save its id for
the requests that follow. The folders are in an order that works with "Run collection".
"""
import json
import re
import sys
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
OUT = BACKEND / "docs" / "postman"
COLLECTION = OUT / "madare-emrooz.postman_collection.json"
ENVIRONMENT = OUT / "madare-emrooz-local.postman_environment.json"

# Stable ids so regenerating gives the same file (and a clean git diff).
NAMESPACE = uuid.UUID("6f1c2d8e-3b7a-4c9e-9d2f-1a5b7c3e8f40")

# Flask path parameter -> Postman variable
PATH_VARS = {
    "patient_id": "patientId",
    "document_id": "documentId",
    "alert_id": "alertId",
    "user_id": "staffId",
    "token": "partnerToken",
    "tag": "riskTag",
    "scope": "approvalScope",
}

VARIABLES = {
    "baseUrl": "http://localhost:5000",
    "motherMobile": "09121234567",
    "staffMobile": "09120000001",
    "otpCode": "",
    "motherToken": "",
    "motherRefreshToken": "",
    "staffToken": "",
    "staffRefreshToken": "",
    "patientId": "",
    "staffId": "",
    "midwifeId": "",
    "alertId": "",
    "documentId": "",
    "partnerToken": "",
    "riskTag": "anemia",
    "approvalScope": "rehabilitation_plan",
}


def save(var: str, expr: str) -> str:
    """Test-script line that stores a value from the JSON response."""
    return f"if (pm.response.code < 300) {{ pm.collectionVariables.set('{var}', {expr}); }}"


def ep(method, path, name, *, body=None, form=None, query=None, auth="inherit", save_vars=(), doc=""):
    return {
        "method": method, "path": path, "name": name, "body": body, "form": form, "query": query,
        "auth": auth, "save": list(save_vars), "doc": doc,
    }


def sign_in(prefix: str, mobile_var: str) -> list[dict]:
    return [
        ep("POST", "/api/v1/auth/otp/request", "Request code", auth=None,
           body={"mobile": f"{{{{{mobile_var}}}}}"},
           doc="Sends a 6-digit code by SMS (202). Any format works: 0912…, +98 912…, Persian digits. "
               "Limits: 1 per minute and 5 per hour per number, 20 per hour per network (429 + Retry-After)."),
        ep("POST", "/api/v1/auth/otp/verify", "Sign in", auth=None,
           body={"mobile": f"{{{{{mobile_var}}}}}", "code": "{{otpCode}}"},
           save_vars=[save(f"{prefix}Token", "pm.response.json().access_token"),
                      save(f"{prefix}RefreshToken", "pm.response.json().refresh_token")]
           + ([save("patientId", "pm.response.json().user.id")] if prefix == "mother" else []),
           doc="Returns a 15-minute access token, a 30-day refresh token and is_new_user. "
               "A new number creates a mother's account. Put the SMS code in the otpCode variable first."),
        ep("POST", "/api/v1/auth/token/refresh", "Refresh tokens", auth=None,
           body={"refresh_token": f"{{{{{prefix}RefreshToken}}}}"},
           save_vars=[save(f"{prefix}Token", "pm.response.json().access_token"),
                      save(f"{prefix}RefreshToken", "pm.response.json().refresh_token")],
           doc="The old refresh token stops working."),
        ep("POST", "/api/v1/auth/logout", "Log out", auth=None,
           body={"refresh_token": f"{{{{{prefix}RefreshToken}}}}"}, doc="204; this device's session ends."),
        ep("GET", "/api/v1/me", "Me", doc="The signed-in account: id, mobile, role."),
    ] + ([ep("GET", "/api/v1/health", "Health", auth=None,
             doc="200 when the API can reach its database, 503 otherwise. For load balancers.")]
         if prefix == "mother" else [])


LMP_EXAMPLE = "2026-05-01"

FOLDERS = [
    ("Auth (mother)", "motherToken", "Sign-in for the mother's app.", sign_in("mother", "motherMobile")),
    ("Auth (staff)", "staffToken",
     "Staff (midwife, doctor, admin) sign in the same way. Their account must first be created by an "
     "admin (or `flask create-admin` for the first admin).",
     [e for e in sign_in("staff", "staffMobile") if e["path"] != "/api/v1/me"]
     + [ep("GET", "/api/v1/staff/me", "Staff me", doc="Name, role and listing status, for the panel header.")]),
    ("Mother · onboarding", "motherToken", "Profile and medical history. GET /profile → 404 means a new user.", [
        ep("GET", "/api/v1/profile", "Get profile", doc="`home` says which screen to open: pregnancy, "
           "trying_to_conceive, postpartum, fitness or rehabilitation."),
        ep("PUT", "/api/v1/profile", "Save profile", body={
            "first_name": "سارا", "last_name": "احمدی", "join_goal": "pregnancy",
            "reproductive_status": "pregnant", "national_code": "0012345679",
            "birth_date": "1995-06-15", "height_cm": 165.5, "initial_weight_kg": 60,
            "mother_blood_type": "O-", "spouse_blood_type": "A+",
        }, doc="201 when created, 200 when updated. join_goal: pregnancy | fitness | rehabilitation; "
               "reproductive_status (pregnancy path): trying_to_conceive | pregnant | postpartum."),
        ep("GET", "/api/v1/medical-history", "Get medical history"),
        ep("PUT", "/api/v1/medical-history", "Save medical history", body={
            "previous_children_count": 1, "miscarriage_count": 0, "has_diabetes": False,
            "has_hypertension": False, "has_thyroid_disorder": None, "spouse_has_diabetes": False,
        }, doc="Every field is optional; null means not answered."),
    ]),
    ("Mother · midwife, documents, fitness, rehab", "motherToken", "", [
        ep("GET", "/api/v1/midwives", "List midwives",
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('midwifeId', items[0].id); }"]),
        ep("GET", "/api/v1/my-midwife", "My midwife"),
        ep("PUT", "/api/v1/my-midwife", "Choose midwife", body={"midwife_id": "{{midwifeId}}"}),
        ep("GET", "/api/v1/documents", "My documents",
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('documentId', items[0].id); }"]),
        ep("GET", "/api/v1/documents/<uuid:document_id>/file", "Download my document"),
        ep("GET", "/api/v1/fitness-profile", "Get fitness profile",
           doc="dashboard_unlocked is false until staff record the specialist visit."),
        ep("PUT", "/api/v1/fitness-profile", "Save fitness profile",
           body={"goal": "weight_loss", "goal_note": "۵ کیلو تا عید"}),
        ep("GET", "/api/v1/rehab-profile", "Get rehab profile",
           doc="is_advanced_locked stays true until the visit and a doctor's approval."),
        ep("PUT", "/api/v1/rehab-profile", "Save rehab profile", body={
            "subcategory": "postpartum_recovery", "pain_level": 4, "had_related_surgery": True,
            "related_surgery_name": "سزارین", "uses_pain_medication": False,
            "time_since_delivery": "two_to_six_months", "has_pelvic_warning_signs": False,
            "has_diastasis_recti_or_stitch_pain": False,
        }, doc="Only the chosen sub-type's questions may be answered."),
    ]),
    ("Mother · pregnancy", "motherToken", "Pregnancy, bleeding reports, partner QR code.", [
        ep("POST", "/api/v1/pregnancies", "Start pregnancy", body={
            "lmp_date": LMP_EXAMPLE, "conception_type": "natural", "avg_cycle_length_days": 28,
            "care_provider_type": "midwife", "care_provider_name": "",
        }, doc="The due date is calculated from the LMP. Only one active pregnancy (409)."),
        ep("GET", "/api/v1/pregnancies/current", "Current pregnancy",
           doc="Week and due date. due_date_source is lmp or clinician."),
        ep("PATCH", "/api/v1/pregnancies/current", "Correct pregnancy details",
           body={"lmp_date": LMP_EXAMPLE},
           doc="Send only the fields to fix: lmp_date, avg_cycle_length_days, conception_type, "
               "care_provider_type, care_provider_name. A clinician-set due date is kept."),
        ep("POST", "/api/v1/daily-logs", "Report bleeding", body={"has_spotting_or_bleeding": True},
           doc="Only during a pregnancy. true raises a red alert for her midwife (or the admins)."),
        ep("GET", "/api/v1/daily-logs", "My daily logs"),
        ep("POST", "/api/v1/partner-link", "Create partner QR link",
           save_vars=[save("partnerToken", "pm.response.json().token")],
           doc="Returns url (encode it in the QR code) and token. A new link replaces the old one."),
        ep("GET", "/api/v1/partner-link", "Current partner link"),
        ep("GET", "/p/<token>", "Partner page (no sign-in, HTML)", auth=None,
           doc="What the spouse sees after scanning: Persian page with the week and Jalali due date."),
        ep("GET", "/api/v1/partner/<token>", "Partner view (no sign-in, JSON)", auth=None),
        ep("DELETE", "/api/v1/partner-link", "Turn partner link off"),
    ]),
    ("Staff · patients", "staffToken", "Doctors see every mother (Phase 1); a midwife sees the mothers who chose her.", [
        ep("GET", "/api/v1/staff/patients", "Patient list", query={"q": "", "page": "1", "per_page": "20"},
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('patientId', items[0].id); }"],
           doc="q matches a name, mobile (any form, Persian digits) or national code. Open alerts first."),
        ep("GET", "/api/v1/staff/patients/<uuid:patient_id>/summary", "Summary card"),
        ep("GET", "/api/v1/staff/patients/<uuid:patient_id>/record", "Full record", doc="Audited."),
        ep("GET", "/api/v1/staff/patients/<uuid:patient_id>/daily-logs", "Daily logs"),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/daily-logs", "Record vitals (midwife)", body={
            "systolic_bp": 120, "diastolic_bp": 80, "blood_glucose_mg_dl": 95, "weight_kg": 68.5,
            "has_headache": False, "other_complaints": "",
        }),
        ep("GET", "/api/v1/staff/patients/<uuid:patient_id>/documents", "Documents",
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('documentId', items[0].id); }"]),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/documents", "Upload document (midwife)",
           form=[("file", "file", ""), ("document_type", "text", "ultrasound"),
                 ("performed_at", "text", "2026-09-20T09:30:00+03:30"), ("fundal_height_cm", "text", "24.5"),
                 ("fetal_heart_rate_bpm", "text", "140"), ("notes", "text", "")],
           save_vars=[save("documentId", "pm.response.json().id")],
           doc="JPEG, PNG or PDF up to 10 MB. Choose the file in the form-data `file` row."),
        ep("GET", "/api/v1/staff/patients/<uuid:patient_id>/documents/<uuid:document_id>/file", "Download document"),
        ep("DELETE", "/api/v1/staff/patients/<uuid:patient_id>/documents/<uuid:document_id>",
           "Remove document (midwife)", body={"reason": "uploaded to the wrong mother"},
           doc="Deletes the file; the audit log keeps what it was and why."),
        ep("PUT", "/api/v1/staff/patients/<uuid:patient_id>/pregnancy/due-date", "Correct due date",
           body={"estimated_due_date": "2027-02-01", "reason": "ultrasound at 12 weeks"}),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/notes", "Add note",
           body={"body": "Next ultrasound in two weeks."}),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/risk-tags", "Add risk tag",
           body={"tag": "{{riskTag}}", "note": "Hb 9.8"}),
        ep("DELETE", "/api/v1/staff/patients/<uuid:patient_id>/risk-tags/<tag>", "Remove risk tag"),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/approvals", "Approve plan (doctor)",
           body={"scope": "{{approvalScope}}"}),
        ep("DELETE", "/api/v1/staff/patients/<uuid:patient_id>/approvals/<scope>", "Revoke approval (doctor)"),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/fitness-profile/specialist-visit",
           "Record fitness specialist visit"),
        ep("POST", "/api/v1/staff/patients/<uuid:patient_id>/rehab-profile/specialist-visit",
           "Record rehab specialist visit"),
        ep("PUT", "/api/v1/staff/patients/<uuid:patient_id>/rehab-profile/imaging", "Link rehab imaging (midwife)",
           body={"document_id": "{{documentId}}"}),
    ]),
    ("Staff · alerts", "staffToken", "", [
        ep("GET", "/api/v1/staff/alerts", "My alerts (midwife)",
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('alertId', items[0].id); }"]),
        ep("POST", "/api/v1/staff/alerts/<uuid:alert_id>/seen", "Mark alert seen",
           doc="Her midwife, or an admin while she has no midwife."),
    ]),
    ("Admin", "staffToken", "Sign in as an admin in Auth (staff).", [
        ep("POST", "/api/v1/admin/staff", "Create staff", body={
            "mobile": "{{staffMobile}}", "role": "midwife", "first_name": "مریم", "last_name": "رحیمی",
            "bio": "", "is_listed": True,
        }, save_vars=[save("staffId", "pm.response.json().user_id")],
           doc="role: midwife | doctor | admin. Listed midwives appear in the app for mothers to choose."),
        ep("GET", "/api/v1/admin/staff", "List staff"),
        ep("PATCH", "/api/v1/admin/staff/<uuid:user_id>", "Update staff", body={"is_listed": True, "is_active": True},
           doc="Send only what changes. Deactivating a midwife sends her mothers' alerts to the admins."),
        ep("GET", "/api/v1/admin/unassigned-alerts", "Unassigned mothers' alerts",
           save_vars=["const items = pm.response.json().items; "
                      "if (items && items.length) { pm.collectionVariables.set('alertId', items[0].id); }"]),
    ]),
    ("Mother · after the birth", "motherToken", "Last, so the requests above still see an active pregnancy.", [
        ep("POST", "/api/v1/pregnancies/current/end", "End pregnancy", body={"status": "delivered"},
           doc="delivered switches her home to postpartum; ended for other outcomes."),
    ]),
]


def postman_path(flask_path: str) -> str:
    return re.sub(r"<(?:[a-z]+:)?([a-z_]+)>", lambda m: "{{" + PATH_VARS[m.group(1)] + "}}", flask_path)


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


def request_item(folder: str, e: dict, folder_token: str | None) -> dict:
    url_path = postman_path(e["path"])
    url = {
        "raw": "{{baseUrl}}" + url_path + (
            "?" + "&".join(f"{k}={v}" for k, v in e["query"].items()) if e["query"] else ""),
        "host": ["{{baseUrl}}"],
        "path": [p for p in url_path.split("/") if p],
    }
    if e["query"]:
        url["query"] = [{"key": k, "value": v} for k, v in e["query"].items()]
    request = {"method": e["method"], "header": [], "url": url, "description": e["doc"]}
    if e["auth"] is None or folder_token is None:
        request["auth"] = {"type": "noauth"}
    if e["body"] is not None:
        request["header"].append({"key": "Content-Type", "value": "application/json"})
        request["body"] = {
            "mode": "raw",
            "raw": json.dumps(e["body"], ensure_ascii=False, indent=2),
            "options": {"raw": {"language": "json"}},
        }
    if e["form"] is not None:
        request["body"] = {
            "mode": "formdata",
            "formdata": [
                {"key": k, "type": t, **({"src": []} if t == "file" else {"value": v})}
                for k, t, v in e["form"]
            ],
        }
    item = {"id": stable_id(folder, e["method"], e["path"]), "name": e["name"], "request": request}
    if e["save"]:
        item["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": e["save"]}}]
    return item


def build_collection() -> dict:
    folders = []
    for name, token_var, description, endpoints in FOLDERS:
        folder = {"name": name, "description": description,
                  "item": [request_item(name, e, token_var) for e in endpoints]}
        if token_var:
            folder["auth"] = {"type": "bearer", "bearer": [
                {"key": "token", "value": "{{" + token_var + "}}", "type": "string"}]}
        folders.append(folder)
    return {
        "info": {
            "_postman_id": stable_id("collection"),
            "name": "Madare Emrooz API",
            "description": (BACKEND / "scripts" / "generate_postman.py").read_text(encoding="utf-8")
            .split('"""')[1].strip(),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": folders,
        "variable": [{"key": k, "value": v} for k, v in VARIABLES.items() if k != "baseUrl"],
    }


def build_environment() -> dict:
    return {
        "id": stable_id("environment"),
        "name": "Madare Emrooz (local)",
        "values": [
            {"key": "baseUrl", "value": VARIABLES["baseUrl"], "type": "default", "enabled": True},
            {"key": "motherMobile", "value": VARIABLES["motherMobile"], "type": "default", "enabled": True},
            {"key": "staffMobile", "value": VARIABLES["staffMobile"], "type": "default", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
    }


def endpoints() -> list[tuple[str, str]]:
    """(method, Flask path) for every request in the collection."""
    return [(e["method"], e["path"]) for _, _, _, items in FOLDERS for e in items]


def render(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    COLLECTION.write_text(render(build_collection()), encoding="utf-8")
    ENVIRONMENT.write_text(render(build_environment()), encoding="utf-8")
    count = len(set(endpoints()))
    print(f"wrote {COLLECTION.relative_to(BACKEND)} ({count} endpoints) and {ENVIRONMENT.name}")


if __name__ == "__main__":
    sys.exit(main())
