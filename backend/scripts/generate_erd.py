"""Generate docs/erd.svg from the SQLAlchemy metadata.

Run from the backend directory after changing any model:

    python scripts/generate_erd.py
"""
import html
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import sqlalchemy as sa  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

OUT = BACKEND / "docs" / "erd.svg"

GROUPS = {
    "identity": ("Identity & access", ["users", "otp_codes", "user_sessions"]),
    "profile": ("Profile & history", ["profiles", "medical_histories"]),
    "pregnancy": ("Pregnancy care", ["pregnancies", "daily_logs", "medical_documents",
                                     "document_files", "partner_links"]),
    "staff": ("Care team", ["staff_profiles", "care_assignments", "alerts",
                            "risk_tag_assignments", "staff_notes", "care_approvals"]),
    "paths": ("Fitness & rehab paths", ["fitness_profiles", "rehab_profiles"]),
    "audit": ("Audit", ["audit_logs"]),
}
GROUP_OF = {t: g for g, (_, ts) in GROUPS.items() for t in ts}
SECTION = {
    "users": "§1", "otp_codes": "§1", "user_sessions": "§1", "profiles": "§2",
    "medical_histories": "§3", "pregnancies": "§4", "daily_logs": "§5",
    "medical_documents": "§6", "risk_tag_assignments": "§7", "staff_notes": "§7",
    "care_approvals": "§7 §11", "audit_logs": "§8", "fitness_profiles": "§9",
    "rehab_profiles": "§10 §11", "document_files": "§6", "partner_links": "§4",
    "staff_profiles": "§7", "care_assignments": "§7", "alerts": "§5 §7",
}
TOP_ROW = ["otp_codes", "user_sessions", "staff_profiles", "profiles", "medical_histories",
           "fitness_profiles", "partner_links", "audit_logs"]
BOTTOM_ROW = ["alerts", "daily_logs", "pregnancies", "medical_documents", "rehab_profiles",
              "care_assignments", "risk_tag_assignments", "staff_notes", "care_approvals"]
# Tables drawn under their parent instead of linked to users: child -> (fk column, parent).
BELOW = {"document_files": ("document_id", "medical_documents")}
# The FK drawn as the line to users; other user FKs are shown in the rows.
OWNER_FK = {
    "user_sessions": "user_id", "profiles": "user_id", "medical_histories": "user_id",
    "fitness_profiles": "user_id", "rehab_profiles": "user_id", "pregnancies": "user_id",
    "daily_logs": "patient_id", "medical_documents": "patient_id",
    "risk_tag_assignments": "patient_id", "staff_notes": "patient_id",
    "care_approvals": "patient_id", "staff_profiles": "user_id", "partner_links": "user_id",
    "care_assignments": "patient_id", "alerts": "patient_id",
}
LOGICAL = {"otp_codes": "mobile · no FK", "audit_logs": "actor_id, patient_id · no FK"}
TIMESTAMPS = {"created_at", "updated_at"}

CHAR = 6.6        # IBM Plex Mono at 11px
HEAD_CHAR = 7.6   # IBM Plex Mono 600 at 12.5px
HEAD_H, ROW_H = 32, 20
GAP = 64
MARGIN = 40
CHANNEL = 128


def type_label(col: sa.Column) -> str:
    fks = list(col.foreign_keys)
    if fks:
        return "→ " + fks[0].column.table.name
    t = col.type
    if getattr(t, "_needs_check_constraint", False):
        base = "enum"
    elif isinstance(t, sa.Uuid):
        base = "uuid"
    elif isinstance(t, sa.Boolean):
        base = "bool"
    elif isinstance(t, sa.SmallInteger):
        base = "int2"
    elif isinstance(t, sa.BigInteger):
        base = "int8"
    elif isinstance(t, sa.Numeric):
        base = f"numeric({t.precision},{t.scale})"
    elif isinstance(t, sa.DateTime):
        base = "timestamptz"
    elif isinstance(t, sa.Date):
        base = "date"
    elif isinstance(t, sa.Text):
        base = "text"
    elif isinstance(t, sa.String):
        base = f"varchar({t.length})"
    else:
        base = t.__class__.__name__.lower()
    if col.computed is not None:
        base += " · generated"
    return base


def is_unique(table: sa.Table, col: sa.Column) -> bool:
    if col.unique:
        return True
    for c in table.constraints:
        if isinstance(c, sa.UniqueConstraint) and list(c.columns) == [col]:
            return True
    return False


class Box:
    def __init__(self, table: sa.Table):
        self.table = table
        self.name = table.name
        cols = [c for c in table.columns if c.name not in TIMESTAMPS]
        self.cols = sorted(cols, key=lambda c: (not c.primary_key, not c.foreign_keys))
        self.stamps = [n for n in ("created_at", "updated_at") if n in table.columns]
        self.rows = []
        for c in self.cols:
            badge = "PK" if c.primary_key else "FK" if c.foreign_keys else "UQ" if is_unique(table, c) else ""
            tl = type_label(c)
            if c.nullable and not c.primary_key:
                tl += "?"
            self.rows.append((c, badge, tl))
        name_w = max(len(c.name) for c in self.cols) * CHAR
        type_w = max(len(r[2]) for r in self.rows) * CHAR
        head_w = (len(self.name) + len(SECTION[self.name]) + 3) * HEAD_CHAR
        self.w = round(max(10 + 26 + name_w + 20 + type_w + 12, head_w + 24, 200))
        self.h = HEAD_H + ROW_H * len(self.rows) + (ROW_H if self.stamps else 0) + 6
        self.x = self.y = 0

    @property
    def cx(self):
        return self.x + self.w / 2

    def row_y(self, col_name):
        for i, (c, _, _) in enumerate(self.rows):
            if c.name == col_name:
                return self.y + HEAD_H + i * ROW_H + ROW_H / 2
        raise KeyError(col_name)

    def svg(self) -> str:
        g = GROUP_OF[self.name]
        out = [f'<g class="tbl g-{g}" id="t-{self.name}">']
        out.append(f'<rect class="box" x="{self.x}" y="{self.y}" width="{self.w}" height="{self.h}" rx="6"/>')
        out.append(
            f'<path class="head" d="M{self.x},{self.y + HEAD_H} V{self.y + 6} '
            f'a6,6 0 0 1 6,-6 H{self.x + self.w - 6} a6,6 0 0 1 6,6 V{self.y + HEAD_H} Z"/>'
        )
        out.append(f'<line class="rule" x1="{self.x}" x2="{self.x + self.w}" y1="{self.y + HEAD_H}" y2="{self.y + HEAD_H}"/>')
        out.append(f'<text class="tname" x="{self.x + 12}" y="{self.y + 21}">{self.name}</text>')
        out.append(f'<text class="tsec" x="{self.x + self.w - 12}" y="{self.y + 21}" text-anchor="end">{SECTION[self.name]}</text>')
        for i, (c, badge, tl) in enumerate(self.rows):
            by = self.y + HEAD_H + i * ROW_H + 14
            if badge:
                out.append(f'<text class="badge b-{badge.lower()}" x="{self.x + 12}" y="{by}">{badge}</text>')
            out.append(f'<text class="cname" x="{self.x + 38}" y="{by}">{c.name}</text>')
            cls = "ctype fk" if c.foreign_keys else "ctype"
            out.append(f'<text class="{cls}" x="{self.x + self.w - 12}" y="{by}" text-anchor="end">{html.escape(tl)}</text>')
        if self.stamps:
            by = self.y + HEAD_H + len(self.rows) * ROW_H + 14
            out.append(f'<text class="stamp" x="{self.x + 38}" y="{by}">+ {", ".join(self.stamps)}</text>')
        out.append("</g>")
        return "\n".join(out)


def crow_v(x, y_edge, direction, optional=True):
    """Crow's foot on a vertical line; direction=+1 means the line leaves the edge downward."""
    d = direction
    parts = [f'<path class="mark" d="M{x - 7},{y_edge} L{x},{y_edge + 12 * d} L{x + 7},{y_edge} M{x},{y_edge} V{y_edge + 12 * d}"/>']
    if optional:
        parts.append(f'<circle class="dot" cx="{x}" cy="{y_edge + 18 * d}" r="3.5"/>')
    return "".join(parts)


def one_v(x, y_edge, direction, optional=False):
    d = direction
    if optional:
        return (f'<line class="mark" x1="{x - 6}" x2="{x + 6}" y1="{y_edge + 7 * d}" y2="{y_edge + 7 * d}"/>'
                f'<circle class="dot" cx="{x}" cy="{y_edge + 15 * d}" r="3.5"/>')
    return (f'<line class="mark" x1="{x - 6}" x2="{x + 6}" y1="{y_edge + 7 * d}" y2="{y_edge + 7 * d}"/>'
            f'<line class="mark" x1="{x - 6}" x2="{x + 6}" y1="{y_edge + 12 * d}" y2="{y_edge + 12 * d}"/>')


def crow_h(x_edge, y, direction):
    d = direction
    return (f'<path class="mark" d="M{x_edge},{y - 7} L{x_edge + 12 * d},{y} L{x_edge},{y + 7}"/>'
            f'<circle class="dot" cx="{x_edge + 18 * d}" cy="{y}" r="3.5"/>')


def one_h(x_edge, y, direction, optional):
    d = direction
    s = f'<line class="mark" x1="{x_edge + 7 * d}" x2="{x_edge + 7 * d}" y1="{y - 6}" y2="{y + 6}"/>'
    if optional:
        s += f'<circle class="dot" cx="{x_edge + 15 * d}" cy="{y}" r="3.5"/>'
    else:
        s += f'<line class="mark" x1="{x_edge + 12 * d}" x2="{x_edge + 12 * d}" y1="{y - 6}" y2="{y + 6}"/>'
    return s


HEADER_H = 96

STYLE = """
:root, svg {
  --canvas: #f2f5f4; --surface: #ffffff; --ink: #16201e; --muted: #5a6865; --edge: #52615e;
  --accent: #0b6b63;
  --identity: #3e5c9a; --identity-soft: #e3e9f5; --profile: #7a4e9a; --profile-soft: #eee6f4;
  --pregnancy: #a8405a; --pregnancy-soft: #f7e3e8; --staff: #2f7d5b; --staff-soft: #dff0e7;
  --paths: #9a6216; --paths-soft: #f5eadb; --audit: #5f6b6e; --audit-soft: #e6eaeb;
}
@media (prefers-color-scheme: dark) {
  :root, svg {
    --canvas: #0f1513; --surface: #18211f; --ink: #e2eae7; --muted: #97a5a1; --edge: #8fa09c;
    --accent: #4fc3b4;
    --identity: #8ea8e0; --identity-soft: #21304b; --profile: #c3a0de; --profile-soft: #33283f;
    --pregnancy: #eb8ea4; --pregnancy-soft: #43232c; --staff: #7fd0a8; --staff-soft: #1c3a2d;
    --paths: #e0ad66; --paths-soft: #3d2f1a; --audit: #a9b5b8; --audit-soft: #2a3133;
  }
}
text { font-family: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, "DejaVu Sans Mono", monospace; }
.bg { fill: var(--canvas); }
.title { font: 600 20px "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--ink); }
.subtitle { font-size: 12px; fill: var(--muted); }
.legend { font-size: 11.5px; fill: var(--ink); }
.g-identity  { --gsoft: var(--identity-soft);  --gstrong: var(--identity); }
.g-profile   { --gsoft: var(--profile-soft);   --gstrong: var(--profile); }
.g-pregnancy { --gsoft: var(--pregnancy-soft); --gstrong: var(--pregnancy); }
.g-staff     { --gsoft: var(--staff-soft);     --gstrong: var(--staff); }
.g-paths     { --gsoft: var(--paths-soft);     --gstrong: var(--paths); }
.g-audit     { --gsoft: var(--audit-soft);     --gstrong: var(--audit); }
.sw { fill: var(--gsoft); stroke: var(--gstrong); stroke-width: 1.5; }
.box { fill: var(--surface); stroke: var(--gstrong); stroke-width: 1.2; }
.head { fill: var(--gsoft); }
.rule { stroke: var(--gstrong); stroke-width: 1; opacity: .5; }
.tname { font-size: 12.5px; font-weight: 600; fill: var(--ink); }
.tsec { font-size: 11px; font-weight: 500; fill: var(--gstrong); }
.cname { font-size: 11px; fill: var(--ink); }
.ctype { font-size: 11px; fill: var(--muted); }
.ctype.fk { fill: var(--accent); font-weight: 500; }
.badge { font-size: 9px; font-weight: 600; letter-spacing: .04em; fill: var(--muted); }
.b-pk, .b-fk { fill: var(--accent); }
.stamp { font-size: 10.5px; fill: var(--muted); }
.rel { fill: none; stroke: var(--edge); stroke-width: 1.3; }
.rel.logical { stroke-dasharray: 5 4; }
.mark { fill: none; stroke: var(--edge); stroke-width: 1.3; }
.dot { fill: var(--surface); stroke: var(--edge); stroke-width: 1.3; }
.rlabel { font-size: 10.5px; fill: var(--muted); paint-order: stroke; stroke: var(--canvas); stroke-width: 4px; stroke-linejoin: round; }
"""


def legend(width: float) -> str:
    y = 70
    parts = [
        f'<text class="title" x="{MARGIN}" y="38">Madare Emrooz · Phase 1 (MVP) data model</text>',
        f'<text class="subtitle" x="{MARGIN}" y="58">Generated from backend/app/modules by scripts/generate_erd.py.'
        " § = section of the spec · ? = nullable · → = foreign key</text>",
    ]
    x = MARGIN
    for g, (label, _) in GROUPS.items():
        parts.append(f'<g class="g-{g}"><rect class="sw" x="{x}" y="{y + 4}" width="12" height="12" rx="2"/>'
                     f'<text class="legend" x="{x + 18}" y="{y + 14}">{html.escape(label)}</text></g>')
        x += 18 + len(label) * 7 + 24
    x += 16
    notation = [
        ("exactly one", f'<line class="mark" x1="{{a}}" x2="{{b}}" y1="{y + 10}" y2="{y + 10}"/>'
                        f'<line class="mark" x1="{{t1}}" x2="{{t1}}" y1="{y + 4}" y2="{y + 16}"/>'
                        f'<line class="mark" x1="{{t2}}" x2="{{t2}}" y1="{y + 4}" y2="{y + 16}"/>'),
        ("zero or one", f'<line class="mark" x1="{{a}}" x2="{{b}}" y1="{y + 10}" y2="{y + 10}"/>'
                        f'<line class="mark" x1="{{t2}}" x2="{{t2}}" y1="{y + 4}" y2="{y + 16}"/>'
                        f'<circle class="dot" cx="{{t0}}" cy="{y + 10}" r="3.5"/>'),
        ("zero or many", f'<line class="mark" x1="{{a}}" x2="{{b}}" y1="{y + 10}" y2="{y + 10}"/>'
                         f'<path class="mark" d="M{{b}},{y + 3} L{{t1}},{y + 10} L{{b}},{y + 17}"/>'
                         f'<circle class="dot" cx="{{t0}}" cy="{y + 10}" r="3.5"/>'),
        ("no FK", f'<line class="rel logical" x1="{{a}}" x2="{{b}}" y1="{y + 10}" y2="{y + 10}"/>'),
    ]
    for label, shape in notation:
        a, b = x, x + 36
        parts.append(shape.format(a=a, b=b, t0=a + 20, t1=a + 26, t2=a + 31))
        parts.append(f'<text class="legend" x="{b + 8}" y="{y + 14}">{label}</text>')
        x = b + 8 + len(label) * 7 + 24
    return "\n".join(parts)


def build() -> None:
    app = create_app()
    with app.app_context():
        tables = {t.name: t for t in db.metadata.sorted_tables}
    boxes = {n: Box(t) for n, t in tables.items()}
    missing = set(boxes) ^ set(TOP_ROW + BOTTOM_ROW + list(BELOW) + ["users"])
    if missing:
        sys.exit(f"Place these tables in TOP_ROW/BOTTOM_ROW (or remove them): {sorted(missing)}")

    users = boxes["users"]
    users.w = max(users.w, 340)
    top = [boxes[n] for n in TOP_ROW]
    bot = [boxes[n] for n in BOTTOM_ROW]

    def row_w(row):
        return sum(b.w for b in row) + GAP * (len(row) - 1)

    width = max(row_w(top), row_w(bot)) + 2 * MARGIN
    y_top_base = HEADER_H + MARGIN + max(b.h for b in top)
    x = (width - row_w(top)) / 2
    for b in top:
        b.x, b.y = round(x), y_top_base - b.h
        x += b.w + GAP
    users.x, users.y = round((width - users.w) / 2), y_top_base + CHANNEL
    y_bot = users.y + users.h + CHANNEL
    x = (width - row_w(bot)) / 2
    for b in bot:
        b.x, b.y = round(x), y_bot
        x += b.w + GAP
    for child, (_, parent) in BELOW.items():
        c, p = boxes[child], boxes[parent]
        c.x, c.y = round(p.cx - c.w / 2), p.y + p.h + CHANNEL // 2
    height = max(b.y + b.h for b in boxes.values()) + MARGIN

    lines = []

    def route(row, edge_y, users_edge_y, sign):
        """Hub-and-spoke routing to users; sign=+1 when the row sits above users.

        Lines of outer tables use the track closest to users, so no two lines cross.
        """
        n = len(row)
        span = users.w - 60
        attach = [users.x + 30 + (span * i / (n - 1) if n > 1 else span / 2) for i in range(n)]
        order = sorted(range(n), key=lambda i: row[i].cx)
        attach_of = {idx: attach[k] for k, idx in enumerate(order)}
        left = sorted([i for i in range(n) if row[i].cx < attach_of[i] - 1], key=lambda i: row[i].cx)
        right = sorted([i for i in range(n) if row[i].cx > attach_of[i] + 1], key=lambda i: -row[i].cx)
        level = {}
        for grp in (left, right):
            for j, i in enumerate(grp):
                level[i] = len(grp) - 1 - j
        levels = max(len(left), len(right), 1)
        step = min(14, 60 / max(levels - 1, 1))
        for i, b in enumerate(row):
            cx, ax = round(b.cx), round(attach_of[i])
            child_edge = edge_y(b)
            if i in level:
                ty = child_edge + sign * (46 + level[i] * step)
                d = f"M{cx},{child_edge} V{ty} H{ax} V{users_edge_y}"
            else:
                d = f"M{cx},{child_edge} V{users_edge_y}"
            logical = b.name in LOGICAL
            lines.append(f'<path class="rel{" logical" if logical else ""}" d="{d}"/>')
            label_y = child_edge + sign * 30 + (4 if sign > 0 else 0)
            if logical:
                lines.append(f'<text class="rlabel" x="{cx + 8}" y="{label_y}">{LOGICAL[b.name]}</text>')
                continue
            fk_col = b.table.columns[OWNER_FK[b.name]]
            if fk_col.primary_key:
                lines.append(one_v(cx, child_edge, sign, optional=True))
            else:
                lines.append(crow_v(cx, child_edge, sign))
            lines.append(one_v(ax, users_edge_y, -sign))
            lines.append(f'<text class="rlabel" x="{cx + 12}" y="{label_y}">{fk_col.name}</text>')

    route(top, lambda b: b.y + b.h, users.y, +1)
    route(bot, lambda b: b.y, users.y + users.h, -1)

    def neighbour(child, col, parent):
        c, p = boxes[child], boxes[parent]
        cy, py = round(c.row_y(col)), round(p.row_y("id"))
        optional = c.table.columns[col].nullable
        if c.x < p.x:
            cx_edge, px_edge, d = c.x + c.w, p.x, 1
        else:
            cx_edge, px_edge, d = c.x, p.x + p.w, -1
        mid = round((cx_edge + px_edge) / 2)
        lines.append(f'<path class="rel" d="M{cx_edge},{cy} H{mid} V{py} H{px_edge}"/>')
        lines.append(crow_h(cx_edge, cy, d))
        lines.append(one_h(px_edge, py, -d, optional))

    neighbour("daily_logs", "pregnancy_id", "pregnancies")
    neighbour("medical_documents", "pregnancy_id", "pregnancies")
    neighbour("rehab_profiles", "imaging_document_id", "medical_documents")
    neighbour("alerts", "daily_log_id", "daily_logs")

    for child, (col, parent) in BELOW.items():
        c, p = boxes[child], boxes[parent]
        x = round(p.cx)
        lines.append(f'<path class="rel" d="M{x},{p.y + p.h} V{c.y}"/>')
        lines.append(one_v(x, c.y, -1, optional=True))  # zero or one file per document
        lines.append(one_v(x, p.y + p.h, +1))
        lines.append(f'<text class="rlabel" x="{x + 12}" y="{c.y - 22}">{col}</text>')

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        'aria-label="Entity-relationship diagram of the Phase 1 tables. Every table references users; '
        "daily_logs and medical_documents also reference pregnancies, rehab_profiles and "
        "document_files reference medical_documents, and alerts reference daily_logs.\">",
        f"<style>{STYLE}</style>",
        f'<rect class="bg" width="{width}" height="{height}"/>',
        legend(width),
        *lines,
        *(b.svg() for b in boxes.values()),
        "</svg>",
    ]
    OUT.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(BACKEND)} ({width:.0f}x{height:.0f}, {len(tables)} tables)")


if __name__ == "__main__":
    build()
