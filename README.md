# Personnel Assessment

Standalone Russian-language personnel assessment application.

Implemented:

- versioned draft bank of 54 items across nine competencies;
- deterministic 0–100 scoring with reverse-keyed items;
- structural bank validation;
- cautious response-quality signals for straight-line and extremely desirable
  response patterns.
- authenticated administrator dashboard and invitation creation;
- private respondent flow with resumable answers and single-use completion;
- administrator-only reports with radar chart, interpretations and development
  recommendations;
- CSV, XLSX and PDF exports;
- SMTP-compatible e-mail delivery configured through environment variables.

The `1.0.0-draft` bank requires expert review and pilot data before production
use. Response-quality warnings are not proof of dishonesty.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Local start:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/`. In local mode invitation e-mails are printed to
the server console; configure the SMTP variables from `.env.example` for real
delivery. Production deployment must set `APP_DEBUG=0`, a strong
`APP_SECRET_KEY`, and the public hostname.
