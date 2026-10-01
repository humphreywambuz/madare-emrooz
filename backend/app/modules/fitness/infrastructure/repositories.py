from app.modules.fitness.domain.entities import FitnessProfile
from app.shared.infrastructure.mapping import KeyedRepository

from .models import FitnessProfileModel


class SqlAlchemyFitnessProfileRepository(KeyedRepository[FitnessProfile]):
    model = FitnessProfileModel
    entity = FitnessProfile
