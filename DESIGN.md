# Personnel Assessment

## Product

Standalone Russian-language web application for inviting respondents to a
54-question workplace assessment and giving authenticated administrators a
private nine-competency report.

The result is a self-report of workplace tendencies, not a clinical diagnosis
or a sufficient basis for an employment decision.

## MVP

1. One authenticated administrator.
2. Expiring, single-use invitation link sent by e-mail.
3. Resumable 54-question assessment, one question per screen.
4. Six items for each of nine competencies, including reverse-keyed items.
5. Deterministic scores from 0 to 100.
6. Administrator-only results, PDF and CSV export.
7. SMTP secrets supplied only through environment variables.

## Scoring

Responses use a five-point scale. Reverse items use `6 - response`.
For every competency:

`percentage = round((sum - item_count) / (4 * item_count) * 100)`

Levels are 0–20 very low, 21–40 low, 41–60 medium, 61–80 high, and
81–100 very high. Missing responses make an attempt incomplete. Every attempt
stores its question-bank version so later revisions do not rewrite history.

## Security

- Store invitation tokens only as cryptographic hashes.
- Do not expose sequential database identifiers in public URLs.
- Consume invitations atomically and protect administrator routes with
  authentication and CSRF protection.
- Never expose scoring keys or detailed reports on respondent routes.
- Define consent, retention, and deletion policy before production use.

## Delivery order

1. Scoring engine and validated methodology.
2. Data model and administrator authentication.
3. Invitation and respondent flows.
4. Reports, exports, e-mail, and deployment hardening.

