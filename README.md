# Personnel Assessment

Standalone Russian-language personnel assessment application.

Implemented:

- versioned draft bank of 54 items across nine competencies;
- deterministic 0–100 scoring with reverse-keyed items;
- structural bank validation;
- cautious response-quality signals for straight-line and extremely desirable
  response patterns.

The `1.0.0-draft` bank requires expert review and pilot data before production
use. Response-quality warnings are not proof of dishonesty.

Run tests:

```powershell
python -m unittest discover -s tests -v
```
