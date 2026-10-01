from app.modules.rehabilitation.domain.entities import RehabProfile
from app.shared.infrastructure.mapping import KeyedRepository

from .models import RehabProfileModel


class SqlAlchemyRehabProfileRepository(KeyedRepository[RehabProfile]):
    model = RehabProfileModel
    entity = RehabProfile
