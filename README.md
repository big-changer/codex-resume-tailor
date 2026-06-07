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
|-- profiles/       # Private master resumes, grouped by profile owner
`-- outputs/        # Generated tailored Markdown resumes and PDFs
```

`profiles/`, `outputs/`, and `venv/` are ignored by Git because they can contain
private candidate data, generated files, or local dependencies.

## Master Resumes

Master resumes are the source of truth for tailoring. Store them under a
user-defined profile directory:

```text
profiles/<profile-owner>/<resume-focus>.md
```

`<profile-owner>` can be a name, alias, username, or other identifier. The
workflow does not require a specific candidate name.

Each master resume should represent a truthful role-specific view of its
profile owner. A general profile directory might look like:

```text
profiles/
`-- example-user/
    |-- data-engineering.md
    |-- full-stack.md
    |-- mobile.md
    `-- README.md
```

Select the profile closest to the target role. Codex may reorder, shorten, and
reframe supported content for the JD, but it must not combine unsupported
claims from other profiles or invent missing facts.

When adding a profile owner:

1. Create `profiles/<profile-owner>/`.
2. Add one or more role-specific Markdown master resumes.
3. Preserve exact employers, titles, dates, technologies, achievements, and
   career breaks.
4. Document known source ambiguities in
   `profiles/<profile-owner>/README.md`.

## Codex Prompt

Codex automatically reads `AGENTS.md` when working in this repository. That
file defines the complete workflow, including JD analysis, truthful title
framing, resume structure, output naming, PDF generation, and the final cover
letter response.

`prompt.txt` is the small per-run instruction. Update its `Source` value to the
chosen master resume before each run:

```text
Execute Resume Tailoring Workflow.

Source: profiles/example-user/full-stack.md
JD: jd.txt
```

Then ask Codex to execute the contents of `prompt.txt`. Codex should:

1. Read the selected master resume and `jd.txt`.
2. Tailor one truthful ATS-friendly resume.
3. Save it under `outputs/<date>-<profile-owner>/`.
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
python gen-pdf.py outputs\<date>-<profile-owner>\<resume>.md
```

Specify an output path or A4 page size when needed:

```powershell
python gen-pdf.py outputs\<resume>.md -o outputs\<resume>.pdf --page-size a4
```

The generator uses only the Python standard library.

## Output Rules

Generated resumes and PDFs belong in:

```text
outputs/<date>-<profile-owner>/<company>-<job-title>.md
outputs/<date>-<profile-owner>/<company>-<job-title>.pdf
```

Review every generated resume before submitting it. In particular, verify that
all technologies, metrics, tailored titles, dates, and employer names remain
supported by the selected master resume.
