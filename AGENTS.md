# Resume Tailoring Workflow Prompt

Use this prompt to run the complete resume-tailoring workflow in one pass while preserving the full reasoning structure from the staged prompts.

Inputs:
- Candidate source file, usually `jayden/fullstack.md`
- Target job description: `jd.txt`

Primary task:
Create one truthful, ATS-friendly tailored resume in Markdown. Work through each step below in order, using the intermediate sections to control quality before writing the final resume.

## Step 01 - Input Prep

Read the candidate source and JD. If company/career-break notes are provided, merge them into the evidence base without changing facts.

Identify:
- Candidate's real titles by company.
- Company names and dates.
- Real technologies used at each company.
- Real responsibilities and achievements.
- Career gaps or breaks that must be preserved.
- Any missing facts required to avoid guessing.

Internal output:
```markdown
## Input Readiness
- Resume source: input/data.md
- JD source: jd.txt

Rules:
- Do not rewrite the original source file.
- Do not infer employment dates.
- Preserve original company names exactly unless the user asks for a public-facing variant.
- Do not ask the user for tailoring preferences; infer the tailoring strategy from the JD.

## Step 02 - JD Analysis

Analyze JD, and extract skill set, and role responsibilities to prepare resume updating.

## Step 03 - Company Title And Description Tailor

For each company entry, produce:
1. A tailored display title that fits the target JD.
2. A company/role description that highlights the most relevant true scope.
3. descriptions should be ATS familiar by including numberical information.
4. A rewritten key skills line ordered by JD relevance.

Internal output:
```markdown
## Tailored Company Framing

### [Company Name]
- Dates: [unchanged]
- Tailored display title: [JD-aligned but honest]
- Company/role description: [5 ~ 8 sentences]
- Key Skills: [JD-relevant real technologies first, less relevant technologies later]
```

Allowed title changes:
- Use a title that reflects the real scope more clearly for this JD.
- Emphasize function, seniority, domain, or stack if supported by the work.
- Example: "Software Engineer" -> "Full-Stack Software Engineer" if full-stack work is proven.
- Example: "Lead Software Engineer" -> "Lead Software Engineer, Platform & Architecture" if platform/architecture work is proven.
- Example: "Software Developer" -> "Web Application Developer" if web application work is proven.

Not allowed:
- Do not invent promotions or seniority.
- Do not change company names or dates.
- Do not claim a direct title that was not true if it changes seniority materially.
- Do not add technologies to a company unless the candidate truly used them there.
- Do not hide career breaks by changing dates.

Style:
- Match the JD vocabulary naturally.
- Keep descriptions concise and resume-ready.
- Prefer employer-readable titles over keyword stuffing.

## Step 04 - Final Resume Draft

Write a tailored resume that matches the JD while remaining truthful.

Required sections:
1. Name and contact.
2. Targeted professional summary.
3. Technical skills grouped by category.
4. Professional experience.
5. Education.

Experience requirements:
- Use the tailored display titles from Step 03.
- Keep company names and dates unchanged.
- Rewrite bullets to emphasize the JD's highest-priority responsibilities.
- Keep achievements measurable only where the source material supports the metric.
- Put JD-relevant technologies first in each "Key Skills" line.
- Avoid repeating the same opening verb, phrase, achievement, or responsibility across adjacent bullets.
- Do not repeat the same keyword in every bullet; distribute supported keywords across summary, skills, and experience.
- Limit each experience entry to the strongest JD-relevant bullets instead of listing every possible responsibility.
- Each bullet should make one clear point: action, scope, technology/context, and result where supported.
- Use clean, professional English with correct spelling, grammar, tense, capitalization, and punctuation.
- Prefer concise wording over inflated phrasing such as "deep expertise in" unless the source clearly supports it.

Visual emphasis requirements:
- Use Markdown bold (`**important phrase**`) for selected high-value words and phrases so the final resume is eye-catching when rendered to PDF.
- Bold only short phrases, not full sentences or entire bullets.
- Prioritize bolding supported JD-match keywords, core technologies, role scope, measurable outcomes, business impact, and leadership signals.
- Good examples: `**C#**`, `**.NET Core**`, `**REST APIs**`, `**reduced deployment time by 15%**`, `**mentored 3-4 engineers**`, `**order processing latency**`.
- In the summary, bold 2-4 of the strongest matching phrases.
- In Technical Skills, bold only the most JD-critical skills in each category.
- In experience bullets, bold 1-2 important phrases per bullet at most, and skip bolding when a bullet is already clear.
- Do not bold company names, dates, every technology, or repeated phrases.
- Do not use italics, all caps, emojis, icons, colors, HTML, or decorative symbols for emphasis.
- Avoid bolding the same keyword repeatedly across the resume; bold it where it matters most.

Final resume format:
```markdown
# [Candidate Name]
[Targeted Title]

[contact details]

## Summary
[3-5 lines targeted to JD]

## Technical Skills
- Languages:
- Backend:
- Frontend:
- Cloud & DevOps:
- Databases:
- Other:

## Professional Experience

### [Company Name]
**[Tailored Display Title]**  
[Dates]

[Company/role description]

- [tailored bullet]
- [tailored bullet]

Key Skills: [ordered stack]

## Education
[education]
```

## File Naming

Save the final resume as:

```text
outputs/{date}-{candidate-name}/{company-name}-{job-title}.md
```

Filename formatting:
- Use lowercase.
- Replace spaces and punctuation with hyphens.
- Collapse repeated hyphens.
- Remove leading/trailing hyphens.
- If the JD does not name the company, use `unknown-company`.
- Example: `output/unknown-company-midweight-back-end-developer-edgars-berzins.md`

## Final Output To User

After completing the workflow, respond with:
- The final resume file created.
- Major unsupported JD keywords intentionally omitted.
- Any missing source facts that limited tailoring.

Do not write separate intermediate workflow files unless the user explicitly asks for them.

## Core Rules

- Do not overwrite `input/resume.txt`, `input/source-template.md`, or `input/jd.txt`.
- Do not fabricate skills, employers, dates, responsibilities, metrics, certifications, tools, CMS platforms, cloud platforms, or direct experience.
- If a JD keyword is unsupported by the source, omit it from the resume rather than forcing it in.
- Use transferable wording only when the source clearly supports closely related experience.
- Keep company names and dates unchanged.
- Preserve career breaks or gaps; do not hide them by changing dates.
- Prefer ATS-friendly Markdown with standard headings and no tables in the final resume body.

## Finally, run gen-pdf.py file to generate PDF file

## give me cover letter as your response.