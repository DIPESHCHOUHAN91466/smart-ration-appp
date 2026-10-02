"""Values that C#, Python and JavaScript must agree on, checked from the source files themselves.

Each backend's own tests can't see the others, so a renumbered enum or a renamed QR status would pass every
suite and break production. These tests read the C# enums/constants, the Python enums and the frontend
contracts and compare them. Run from the repository root with the Python backend's virtualenv:

    backend\\SmartRation\\.venv\\Scripts\\python -m pytest tests/regression
"""

from __future__ import annotations

import re
from enum import IntEnum
from pathlib import Path

import pytest

import ai.domain as ai_domain
from app.database import enums as py_enums
from app.services.public_help_service import UPCOMING_STATUSES

ROOT = Path(__file__).resolve().parents[2]
CS_MODELS = ROOT / "backend" / "SmartRation.Api" / "Models"
FRONTEND = ROOT / "frontend" / "src"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def cs_enum(name: str) -> dict[str, int]:
    """`public enum Name { A = 1, B, C = 5 }` from any model file -> {"A": 1, "B": 2, "C": 5}."""
    for file in CS_MODELS.glob("*.cs"):
        match = re.search(rf"public enum {name}\s*\{{(?P<body>[^}}]*)\}}", read(file))
        if match:
            values, current = {}, -1
            for member in re.sub(r"//[^\n]*", "", match.group("body")).split(","):
                member = member.strip()
                if not member:
                    continue
                key, _, value = (part.strip() for part in member.partition("="))
                current = int(value) if value else current + 1
                values[key] = current
            return values
    raise AssertionError(f"C# enum {name} not found in {CS_MODELS}")


def norm(name: str) -> str:
    return name.replace("_", "").lower()


def js_strings(source: str, const: str) -> dict[str, str]:
    """`export const NAME = { KEY: "value", ... }` -> {KEY: value} (string values only)."""
    body = re.search(rf"export const {const} = \{{(?P<body>.*?)\n\}};", source, re.S).group("body")
    return dict(re.findall(r'(\w+):\s*"([^"]*)"', body))


# ---------------------------------------------------------------- enums stored as integers

PY_ENUMS = [cls for cls in vars(py_enums).values() if isinstance(cls, type) and issubclass(cls, IntEnum) and cls is not IntEnum]


# Added in the Python backend after the C# API stopped serving traffic (it is legacy and kept only for reference).
# Listed by name so nothing is added silently: whole enums the C# API never had, and members added to shared ones.
PYTHON_ONLY_ENUMS = {"GrievanceCategory", "GrievanceStatus"}
PYTHON_ONLY_MEMBERS = {"NotificationType": {"GrievanceUpdate"}}


@pytest.mark.parametrize("enum", [e for e in PY_ENUMS if e.__name__ not in PYTHON_ONLY_ENUMS], ids=lambda e: e.__name__)
def test_gateway_enums_match_the_csharp_enums(enum):
    """Both backends read and write the same integer columns: every C# value is unchanged in Python."""
    extra = PYTHON_ONLY_MEMBERS.get(enum.__name__, set())
    assert {m.name: m.value for m in enum if m.name not in extra} == cs_enum(enum.__name__)
    assert not {m.value for m in enum if m.name in extra} & set(cs_enum(enum.__name__).values())   # no reused numbers


def test_python_only_enums_are_really_python_only():
    names = {e.__name__ for e in PY_ENUMS}
    assert PYTHON_ONLY_ENUMS <= names
    for name in PYTHON_ONLY_ENUMS:
        with pytest.raises(AssertionError, match="not found"):
            cs_enum(name)


@pytest.mark.parametrize(("ai_class", "cs_name"), [
    (ai_domain.TokenStatus, "TokenStatus"),
    (ai_domain.VerificationAction, "VerificationAction"),
    (ai_domain.MovementType, "InventoryMovementType"),
])
def test_ai_service_codes_match_the_csharp_enums(ai_class, cs_name):
    cs = {norm(k): v for k, v in cs_enum(cs_name).items()}
    ai = {norm(k): v for k, v in vars(ai_class).items() if k.isupper()}
    assert ai and all(cs.get(k) == v for k, v in ai.items()), {k: (v, cs.get(k)) for k, v in ai.items()}


def test_ai_service_ration_types_match_the_csharp_enum():
    assert {name: number for number, name in ai_domain.RATION_TYPES.items()} == cs_enum("RationType")


def test_gateway_upcoming_booking_statuses_match_the_csharp_enum():
    token_status = cs_enum("TokenStatus")
    assert all(token_status[name] == number for number, name in UPCOMING_STATUSES.items())


def test_integrity_queries_use_the_right_token_status_numbers():
    """database/queries hard-code TokenStatus numbers in SQL; they must stay in step with C#."""
    status = cs_enum("TokenStatus")
    queries = ROOT / "database" / "queries"
    assert "t.Status <> 3" in read(queries / "04_collections_with_open_tokens.sql") and status["Completed"] == 3
    assert "t.Status <> 4" in read(queries / "07_slot_count_drift.sql") and status["Cancelled"] == 4


# ---------------------------------------------------------------- QR contract (C# <-> frontend)

CS_QR = read(ROOT / "backend" / "SmartRation.Api" / "Services" / "Qr" / "QrPayloadContract.cs")
JS_QR = read(FRONTEND / "features" / "qr" / "qrContract.js")


def test_qr_envelope_constants_match():
    cs = dict(re.findall(r'public const string (Version|Project|Type) = "([^"]+)";', CS_QR))
    js = js_strings(JS_QR, "QR_CONTRACT")
    assert (js["version"], js["project"], js["type"]) == (cs["Version"], cs["Project"], cs["Type"])


def test_qr_required_fields_match_in_order():
    cs_fields = re.findall(r'"(\w+)"', re.search(r"RequiredFields\s*=\s*\[(.*?)\];", CS_QR, re.S).group(1))
    js_fields = re.findall(r'"(\w+)"', re.search(r"QR_REQUIRED_FIELDS = \[(.*?)\];", JS_QR, re.S).group(1))
    assert js_fields == cs_fields


def test_every_scan_status_the_server_can_return_is_known_and_presented_by_the_scanner():
    cs_block = re.search(r"public static class QrScanStatus\s*\{(.*?)\n\}", CS_QR, re.S).group(1)
    server = set(re.findall(r'public const string \w+ = "([A-Z_]+)";', cs_block))
    client = set(js_strings(JS_QR, "QR_STATUS").values())
    assert server and server <= client, server - client
    assert client - server == {"NETWORK_ERROR"}  # the only client-side outcome
    meta = re.search(r"export const QR_STATUS_META = \{(.*?)\n\};", JS_QR, re.S).group(1)
    assert all(re.search(rf"\b{status}:", meta) for status in client), "every status needs a presentation"


# ---------------------------------------------------------------- roles and names in the frontend

def test_every_role_has_a_home_page_and_a_frontend_type():
    roles = set(cs_enum("UserRole"))
    role_home = read(FRONTEND / "features" / "auth" / "roleHome.js")
    assert roles <= set(re.findall(r'role === "(\w+)"', role_home))
    typedef = re.search(r"@typedef \{(.*?)\} UserRole", read(FRONTEND / "types" / "api.js")).group(1)
    assert set(re.findall(r'"(\w+)"', typedef)) == roles


@pytest.mark.parametrize("name", ["TokenStatus", "RationType"])
def test_frontend_types_list_exactly_the_csharp_names(name):
    typedef = re.search(rf"@typedef \{{(.*?)\}} {name}\b", read(FRONTEND / "types" / "api.js")).group(1)
    assert set(re.findall(r'"(\w+)"', typedef)) == set(cs_enum(name))


def test_frontend_units_cover_every_ration_type():
    """utils/format.js: oil in litres, the rest in kg — a new ration type must be decided on, not defaulted."""
    assert set(cs_enum("RationType")) == {"Rice", "Wheat", "Sugar", "Pulses", "EdibleOil", "Salt"}
