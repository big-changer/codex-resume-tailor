# Resume Generator

This repository uses Codex to tailor a candidate's master resume to the job
description in `jd.txt`. Codex creates an ATS-friendly Markdown resume under
`outputs/`, then `gen-pdf.py` converts it to a selectable-text PDF.

The tailoring rules prioritize truthful, source-supported content. Unsupported
skills, metrics, employers, dates, and responsibilities must not be added just
to match a job description.

## Repository Layout

```text
.
|-- AGENTS.md       # Full Codex resume-tailoring workflow and guardrails
|-- prompt.txt      # Short per-run prompt selecting a profile and JD
|-- jd.txt          # Target job description
|-- gen-pdf.py      # Markdown-to-PDF generator
|-- profiles/       # Private candidate master resumes, grouped by candidate
`-- outputs/        # Generated tailored Markdown resumes and PDFs
```

`profiles/`, `outputs/`, and `venv/` are ignored by Git because they can contain
private candidate data, generated files, or local dependencies.

## Master Resumes

Master resumes are the source of truth for tailoring. Store them under:

```text
profiles/<candidate>/<profile>.md
```

Each profile should represent a truthful role-specific view of the same
candidate. For example, the current Jayden profiles are:

| Master resume | Best used for |
|---|---|
| `profiles/jayden/data.md` | Data engineering and analytics roles |
| `profiles/jayden/fullstack.md` | Full-stack and general software engineering roles |
| `profiles/jayden/game.md` | Game development and game engine roles |
| `profiles/jayden/mobile.md` | Mobile application roles |
| `profiles/jayden/security.md` | Security and network engineering roles |

Select the profile closest to the target role. Codex may reorder, shorten, and
reframe supported content for the JD, but it must not combine unsupported
claims from other profiles or invent missing facts.

When adding a candidate:

1. Create `profiles/<candidate>/`.
2. Add one or more role-specific Markdown master resumes.
3. Preserve exact employers, titles, dates, technologies, achievements, and
   career breaks.
4. Document known source ambiguities in `profiles/<candidate>/README.md`.

## Codex Prompt

Codex automatically reads `AGENTS.md` when working in this repository. That
file defines the complete workflow, including JD analysis, truthful title
framing, resume structure, output naming, PDF generation, and the final cover
letter response.

`prompt.txt` is the small per-run instruction. Update its `Source` value to the
chosen master resume before each run:

```text
Execute Resume Tailoring Workflow.

Source: profiles/jayden/mobile.md
JD: jd.txt
```

Then ask Codex to execute the contents of `prompt.txt`. Codex should:

1. Read the selected master resume and `jd.txt`.
2. Tailor one truthful ATS-friendly resume.
3. Save it under `outputs/<date>-<candidate>/`.
4. Run `gen-pdf.py` to create the matching PDF.
5. Respond with a cover letter and note unsupported JD keywords or missing
   source facts that limited tailoring.

Do not put tailoring preferences or factual additions in `prompt.txt`. Add
verified candidate facts to the appropriate master resume first.

## Job Description

Replace the contents of `jd.txt` with the complete target job description
before a run. Include the company name and role title when available because
Codex uses them in the generated filename. If the company is absent, the
workflow uses `unknown-company`.

## Generate A PDF Manually

The Codex workflow runs the PDF generator automatically. To regenerate a PDF
manually:

```powershell
python gen-pdf.py outputs\<date>-<candidate>\<resume>.md
```

Specify an output path or A4 page size when needed:

```powershell
python gen-pdf.py outputs\<resume>.md -o outputs\<resume>.pdf --page-size a4
```

The generator uses only the Python standard library.

## Output Rules

Generated resumes and PDFs belong in:

```text
outputs/<date>-<candidate>/<company>-<job-title>.md
outputs/<date>-<candidate>/<company>-<job-title>.pdf
```

Review every generated resume before submitting it. In particular, verify that
all technologies, metrics, tailored titles, dates, and employer names remain
supported by the selected master resume.
