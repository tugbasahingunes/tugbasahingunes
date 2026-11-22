# App Localization: English → Turkish, with Automated QA

**Service:** software & app localization · TR ⇄ EN translation · string-file QA (JSON, ICU, Android XML, iOS .strings) · Turkish style guides

**Client problem:** "Our app's Turkish version reads like a machine translation, buttons overflow, and a broken placeholder crashed the release."

| File | What it is |
|---|---|
| [`locales/en.json`](locales/en.json) → [`locales/tr.json`](locales/tr.json) | 20 UI strings: onboarding, ICU plurals, paywall, errors, push notifications |
| [`style_guide.md`](style_guide.md) | Turkish style decisions: *sen* vs *siz*, imperatives on buttons, singular after numbers, **no suffixes on placeholders** (vowel harmony), brand-name apostrophes, İ/ı casing, length budgets |
| [`glossary.csv`](glossary.csv) | Locked terminology with notes |
| [`qa_check.py`](qa_check.py) | Automated QA; exit code 1 on errors, so it can gate CI |

## What the QA catches
Run against a deliberately broken file ([`tr_bad_example.json`](locales/tr_bad_example.json)):
```
20 keys · 5 errors · 3 warnings
  ERROR  profile.member_since: missing translation
  ERROR  workout.count: ICU plural structure broken
  ERROR  workout.count: plural suffix after a number (use singular)
  ERROR  reminder.push: suffix attached to placeholder (vowel harmony unknown)
  ERROR  paywall.trial: placeholders differ: ['days'] vs []
  warn   paywall.title: length 22 vs 14 (budget ×1.2)
  warn   error.network: check Turkish capital İ
  warn   *: mixed address forms: 6 'sen' vs 1 'siz' strings
```
The delivered `tr.json` passes with **0 errors** (one length warning, accepted after checking the button width).

**Why Turkish needs this:** `{workout}'u` can't be written correctly in advance (it may need *'u, 'ü, 'yı, 'yi…* depending on the word inserted), so I rephrase around placeholders. Turkish nouns stay singular after numbers, so ICU `one`/`other` branches are both singular. These are the bugs machine translation introduces most often.

```bash
python qa_check.py                                         # delivered file
python qa_check.py locales/en.json locales/tr_bad_example.json   # see the errors
```
