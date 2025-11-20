"""Internationalization support using gettext."""

import gettext
import locale
from pathlib import Path

# Global translator
_translator = None


def setup_i18n(domain: str = "massunpacker", localedir: Path | None = None) -> None:
    """
    Setup internationalization.

    Args:
        domain: Translation domain name
        localedir: Directory containing locale files (None for default)
    """
    global _translator

    if localedir is None:
        # Default locale directory relative to package
        localedir = Path(__file__).parent.parent.parent / "locales"

    # Try to get system locale
    try:
        lang, _ = locale.getdefaultlocale()
    except Exception:
        lang = "en_US"

    # Fallback to English if locale not found
    try:
        _translator = gettext.translation(
            domain, localedir=localedir, languages=[lang] if lang else None, fallback=True
        )
    except Exception:
        _translator = gettext.NullTranslations()


def _(message: str) -> str:
    """
    Translate message.

    Args:
        message: Message to translate

    Returns:
        Translated message
    """
    global _translator

    if _translator is None:
        setup_i18n()

    return _translator.gettext(message)


def _n(singular: str, plural: str, n: int) -> str:
    """
    Translate message with plural forms.

    Args:
        singular: Singular form
        plural: Plural form
        n: Number for plural selection

    Returns:
        Translated message
    """
    global _translator

    if _translator is None:
        setup_i18n()

    return _translator.ngettext(singular, plural, n)
