from datetime import date, datetime
from decimal import Decimal

from flask.json.provider import DefaultJSONProvider


class IsoJSONProvider(DefaultJSONProvider):
    """Serialise dates and datetimes as ISO 8601 instead of Flask's HTTP-date format,
    and decimals as numbers.

    Clients (and their Jalali conversion) expect ``2026-07-22`` and
    ``2026-07-22T10:15:00+00:00``, not ``Wed, 22 Jul 2026 00:00:00 GMT``.
    """

    @staticmethod
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, Decimal):
            # Measurements such as 165.5 cm are numbers in JSON, not strings.
            return float(o)
        return DefaultJSONProvider.default(o)
