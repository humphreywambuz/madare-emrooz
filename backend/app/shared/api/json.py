from datetime import date, datetime

from flask.json.provider import DefaultJSONProvider


class IsoJSONProvider(DefaultJSONProvider):
    """Serialise dates and datetimes as ISO 8601 instead of Flask's HTTP-date format.

    Clients (and their Jalali conversion) expect ``2026-07-22`` and
    ``2026-07-22T10:15:00+00:00``, not ``Wed, 22 Jul 2026 00:00:00 GMT``.
    """

    @staticmethod
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)
