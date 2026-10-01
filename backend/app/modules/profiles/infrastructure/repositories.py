from app.modules.profiles.domain.entities import MedicalHistory, Profile
from app.shared.infrastructure.mapping import KeyedRepository

from .models import MedicalHistoryModel, ProfileModel


class SqlAlchemyProfileRepository(KeyedRepository[Profile]):
    model = ProfileModel
    entity = Profile
    conflicts = {"uq_profiles_national_code": "This national code is already registered."}


class SqlAlchemyMedicalHistoryRepository(KeyedRepository[MedicalHistory]):
    model = MedicalHistoryModel
    entity = MedicalHistory
