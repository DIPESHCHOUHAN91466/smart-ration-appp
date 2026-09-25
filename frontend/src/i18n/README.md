# src/i18n — English, हिंदी, मराठी

**What:** the translation dictionary and `useTranslation()`. **Why:** every visible string in three
languages without duplicating components.
**Belongs here:** `translations.js` (app strings, 355 keys × 3), `publicStrings.js` (landing, Public Help,
chatbot — merged into the same dictionary), `useTranslation.js` (`t("key")`, language store persisted in
the browser). **Doesn't:** chatbot answers (server-side knowledge, already translated), business logic.
**Run/test:** `frontend/tests/unit/i18n.test.js` fails if a key is missing in any language or a `t()` key
used by the public pages doesn't exist.
**Connects:** components call `t("key")`; `LanguageSwitcher` changes the language everywhere, and the
chatbot sends the current language with each question.

Adding text: add the key to `en`, `hi` and `mr`, use `t("key")`, run `npm test`.
