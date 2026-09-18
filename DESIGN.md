# Personnel Assessment

## Product

Standalone Russian-language web application for structured personnel assessment.
An authenticated HR administrator creates an individual link for a current
employee or a candidate, assigns department and position, and receives a private
detailed report after completion.

The result is decision support. It is not a clinical diagnosis, a certified IQ
score, or a sufficient basis for an employment decision.

## Current MVP

1. One authenticated HR administrator.
2. Expiring, single-use invitation with participant name, optional e-mail,
   track, department and position. Without e-mail, HR copies and sends the link manually.
3. Welcome page with purpose, instructions and explicit acknowledgement.
4. Two preassigned tracks: current employee and candidate.
5. Thirty original cognitive tasks covering numerical, logical, verbal and
   spatial reasoning. Leaders receive the advanced bank; specialists, managers
   and assistants receive the accessible bank without trick questions.
6. Fifty-four workplace-behaviour statements covering nine competencies.
7. Resumable one-question-per-screen flow.
   The participant sees a live elapsed-time counter; HR sees the final duration.
8. Private HR report with cognitive accuracy, behavioural profile,
   response-quality warnings, development practices and interview prompts.
9. PDF, XLSX and CSV export. Composure is shown as "Стрессоустойчивость".
10. HR can clear a generated link from the screen without a reload and can
    permanently delete one or multiple invitations together with their answers
    and results.

## Measurement boundaries

The cognitive pilot follows the broad domain structure used by public-domain
reasoning batteries such as ICAR, but the current questions are original and
have not yet been normed on a representative sample. The application therefore
reports raw accuracy by domain and must not label it as IQ, percentile or a
population norm. Normative interpretation requires a documented validation
study, sample characteristics, reliability analysis and versioned norms.

The behavioural module is a self-report of workplace tendencies. Personality,
motivation, cognitive ability and job knowledge remain separate modules and
must not be merged into a single opaque suitability score.

Job-specific modules will contain 20–50 questions per approved role after HR
provides job descriptions, critical tasks and scoring criteria. They must be
versioned independently and reviewed by a subject-matter expert.

## Scoring

Behaviour responses use a five-point scale. Reverse items use `6 - response`.
For every competency:

`percentage = round((sum - item_count) / (4 * item_count) * 100)`

Levels are 0–20 very low, 21–40 low, 41–60 medium, 61–80 high, and 81–100 very
high. Cognitive results are `correct / total` for each domain and overall.
Missing responses make an attempt incomplete. Every invitation stores its
question-bank version so later revisions do not rewrite history.

## Security and governance

- Store invitation tokens only as cryptographic hashes.
- Do not expose sequential database identifiers in public URLs.
- Consume invitations atomically and protect HR routes with authentication and
  CSRF protection.
- Never expose scoring keys or detailed reports on respondent routes.
- Before production use, approve legal basis/consent wording, role-based access,
  retention/deletion policy, incident process, backups and hosting jurisdiction.
- Never use one test as the sole automatic hiring, dismissal or promotion decision.

## Roadmap

1. Pilot the general modules and evaluate item difficulty, reliability,
   completion time and adverse-impact indicators.
2. Add separate personality and growth-motivation modules.
3. Build role-specific knowledge banks from validated job profiles.
4. Add configurable batteries, section navigation and HR filters.
5. Move production data to managed PostgreSQL and add role-based governance.

## Deployment

The current month-long MVP pilot is hosted on PythonAnywhere with SQLite. This is
acceptable only for controlled testing with approved pilot data. The production
target is a managed application service with PostgreSQL, HTTPS, backups,
monitoring and secrets in environment variables.
