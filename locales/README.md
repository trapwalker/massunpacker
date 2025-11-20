# Localization Files

This directory contains translation files for massunpacker.

## Structure

```
locales/
├── en/
│   └── LC_MESSAGES/
│       ├── massunpacker.po   # English translations (source)
│       └── massunpacker.mo   # Compiled (generated)
└── ru/
    └── LC_MESSAGES/
        ├── massunpacker.po   # Russian translations
        └── massunpacker.mo   # Compiled (generated)
```

## Adding translations

### Extract translatable strings

```bash
# Generate .pot template from source code
xgettext --language=Python --keyword=_ --keyword=_n:1,2 \
    --output=locales/massunpacker.pot \
    --from-code=UTF-8 \
    src/massunpacker/*.py
```

### Create new language

```bash
# Create .po file for new language
msginit --input=locales/massunpacker.pot \
    --locale=ru_RU.UTF-8 \
    --output=locales/ru/LC_MESSAGES/massunpacker.po
```

### Update existing translations

```bash
# Update .po files with new strings
msgmerge --update locales/ru/LC_MESSAGES/massunpacker.po \
    locales/massunpacker.pot
```

### Compile translations

```bash
# Compile .po to .mo
msgfmt locales/ru/LC_MESSAGES/massunpacker.po \
    --output-file=locales/ru/LC_MESSAGES/massunpacker.mo
```

## Supported languages

- English (en) - Default
- Russian (ru) - Prepared for translation

## Note

Currently, the application uses English messages directly in the code.
Translation files (.po/.mo) are prepared but not yet generated.

To enable translations:
1. Extract messages using `xgettext`
2. Translate strings in .po files
3. Compile using `msgfmt`
