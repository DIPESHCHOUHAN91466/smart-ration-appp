"""What the assistant may do: a fixed list of screens to open and forms to pre-fill, each with the roles allowed.

Whatever understands the user's words (rules today, an LLM later) only *proposes* an action; it is accepted
only if it is in this list for the caller's role, and form fields are kept only if they fit the form's schema.
Nothing here reads or writes data: the phone opens the screen or form, and the user reviews and confirms.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.database.enums import GrievanceCategory, RationType, UserRole

CITIZEN = frozenset({UserRole.RuralUser})
SHOP = frozenset({UserRole.ShopOwner})
OFFICIALS = frozenset({UserRole.GovernmentOfficial, UserRole.Admin})
EVERYONE = CITIZEN | SHOP | OFFICIALS

# Screen ids the phone knows how to open (it maps them to its own routes).
SCREENS: dict[str, frozenset[UserRole]] = {
    "home": EVERYONE,
    "help": EVERYONE,
    "notifications": EVERYONE,
    "my_tokens": CITIZEN,
    "book": CITIZEN,
    "family": CITIZEN,
    "ration_card": CITIZEN,
    "eligibility": CITIZEN,
    "my_complaints": CITIZEN,
    "scan": SHOP,
    "queue": SHOP,
    "stock": SHOP,
    "shops": OFFICIALS,
    "alerts": OFFICIALS,
}

LANGUAGES = ("en", "hi", "mr")


@dataclass(frozen=True)
class FormSchema:
    """A form the assistant may pre-fill. `choices` limits a field to known values; `required` must be present
    before the user can submit (the phone asks for whatever is missing)."""
    roles: frozenset[UserRole]
    choices: dict[str, tuple[str, ...]]
    text_fields: dict[str, int]          # field -> max length
    required: tuple[str, ...]

    def draft(self, proposed: dict[str, str]) -> tuple[dict[str, str], list[str]]:
        """Keep only fields that fit the schema; list the required ones still missing."""
        fields: dict[str, str] = {}
        for name, value in proposed.items():
            if not isinstance(value, str) or not value.strip():
                continue
            value = value.strip()
            if name in self.choices and value in self.choices[name]:
                fields[name] = value
            elif name in self.text_fields:
                fields[name] = value[: self.text_fields[name]]
        return fields, [name for name in self.required if name not in fields]


FORMS: dict[str, FormSchema] = {
    # Matches POST /api/grievances (see grievance_service): the citizen's name, mobile and shop come from their
    # account, so the form never asks for them again.
    "grievance": FormSchema(
        roles=CITIZEN,
        choices={"category": tuple(c.name for c in GrievanceCategory), "rationType": tuple(r.name for r in RationType)},
        text_fields={"description": 1000},
        required=("category", "description"),
    ),
}


def screen_allowed(screen: str | None, role: UserRole) -> bool:
    return screen in SCREENS and role in SCREENS[screen]


def form_allowed(form: str | None, role: UserRole) -> bool:
    return form in FORMS and role in FORMS[form].roles
