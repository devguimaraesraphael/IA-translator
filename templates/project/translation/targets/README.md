# Target-language layout

Create one directory per BCP 47 language tag. Never mix locales in one directory.

```text
targets/
└── <language-tag>/
    ├── README.md
    ├── glossary.md
    ├── editorial-conventions.md
    ├── manuscript/
    │   └── <same filename as source>.md
    ├── decisions/
    │   └── <same filename as source>.md
    └── verification/
        └── <same filename as source>.md
```

`manuscript/` holds publication-ready literary text only. Copy the working glossary and
editorial conventions from `../context/` into this directory, resolve target-specific choices
there, and keep chapter decisions and verification logs outside the manuscript.

## Target metadata

- Language tag: TO DECIDE
- Language name: TO DECIDE
- Locale and spelling standard: TO DECIDE
- Translation status: preparation
- Last verified source revision: TO DECIDE
