# Semantic Rules Reference

Rules that require agent judgment rather than mechanical detection. Use these
examples during Step 5 (CSO signal), Step 7 (content overlap), Step 8
(progressive disclosure), and Step 9 (multi-step workflow quality) of the
triage workflow.

---

## Rule 8 — Content overlap between SKILL.md and README

**Question:** Is the same information conveyed in different words across both files?

### Should flag

SKILL.md body and README contain the same substantive lines (even paraphrased):

```
# SKILL.md body
Run `skill-lint check .` to get the full picture.
Fix errors before warnings — Rule 1 blocks publishing.

# README.md (same content, slightly reworded)
Run `skill-lint check .` to get the full picture.
Fix errors before warnings — Rule 1 blocks publishing.
```

### Should not flag

Files share only incidental overlap (short lines, code snippets, headings):

```
# SKILL.md
## Triage Workflow
...

# README.md
## Usage
...
```

Overlap on lines shorter than ~20 characters, or on code blocks that must appear
in both, is expected and fine.

### Judgment call

SKILL.md should be agent-focused (triage workflow, rule table, references).
README should be human-focused (installation, starter prompts, badges).
Flag sections that duplicate *prose* between the two, not shared code examples.

---

## Rule 12 — CSO name is action-oriented

**Question:** Does the skill name read as an action (gerund preferred) rather than a noun?

### Should flag

```yaml
name: pdf-processor       # noun phrase
name: skill-creator       # noun phrase
name: code-reviewer       # noun phrase
```

### Should not flag

```yaml
name: processing-pdfs         # gerund
name: creating-skills         # gerund
name: condition-based-waiting # contains gerund segment
name: pdf                     # short well-known name — acceptable
name: commit                  # short well-known name — acceptable
name: debug                   # short well-known name — acceptable
```

### Judgment call

Apply common sense. A name like `pdf` or `commit` is universally understood as
an action in context and needs no gerund form. The goal is to prefer names that
read as "doing X" over names that read as "a thing that does X."

---

## Rule 16 — Dense or conditional sections belong in `references/`

**Question:** Would an agent look up this section reactively rather than read it upfront?

### Should flag

A step-conditional or phase heading whose body is dense enough to bulk up
the main workflow without being needed on every run:

```markdown
## Step 2 — Apply fixes

- detail line 0
- detail line 1
...
(35+ lines of specifics)
```

```markdown
## Phase 2 — Deploy

(35+ lines of deployment checklist)
```

```markdown
## After running the scan

(35+ lines of post-scan actions)
```

### Should not flag

A short step section that gives essential context upfront:

```markdown
## Step 2 — Fix Errors first

**Rule 1** (SKILL.md spec compliance) blocks publishing. Fix before anything else.
```

### Judgment call

Line count alone is not the criterion — the original Python threshold of 30 lines
was a proxy for "too much to absorb upfront." Use content density: a 35-line
section of dense checklists should move; a 35-line section of simple narrative
probably should not. Ask: "would an agent skip this on a normal run and only
read it when needed?"

---

## Rule 18 — Description is a single routing clause

**Question:** Does the `description` frontmatter function purely as a routing signal,
or has it been extended with elaboration?

### Should flag

Contains elaboration labels:

```yaml
description: Use when linting a skill. Triggers on: missing LICENSE, no CI.
description: Use when processing data. Use cases: CSV, JSON, XML.
description: Use when reviewing code. Checks: style, tests, security.
```

Multiple sentences:

```yaml
description: Use when linting a skill. It checks many things. Very useful.
description: Use when linting. It is helpful.
```

### Should not flag

Single routing clause, even with technical terms that contain punctuation:

```yaml
description: Use when validating a skill for publishing readiness.
description: Use when building X.Y.Z integrations.
description: Use when handling HTTP 4xx/5xx errors.
```

### Judgment call

Sentence-splitting on `.?!` is fragile — `X.Y.Z` and `4xx/5xx` are not sentence
boundaries. Read the description as a human would. The test is: does it say *when
to trigger the skill*, or does it start explaining *what the skill does*? The
former is correct; the latter belongs in the skill body.

---

## Rule 22 — Step completion conditions

**Question:** Does each substantive step state how the agent knows it is done
before advancing to the next step?

### Should flag

A step that only prescribes what to do with no exit condition:

~~~markdown
### Step 1 — Run the linter

```bash
skill-lint check .
```

### Step 2 — Fix errors

Review the errors and fix all reported issues.
~~~

Neither step says when it is done. An agent could skip to Step 2 after glancing
at the output, or leave Step 2 after fixing one error, without knowing the full
completion criterion.

### Should not flag

A step that names its completion condition explicitly:

~~~markdown
### Step 1 — Run the linter

```bash
skill-lint check .
```

Review the output for errors and warnings; confirm the full picture before proceeding.

### Step 2 — Fix errors

Fix all reported errors. Only proceed to Step 3 when `skill-lint check` reports no errors.
~~~

A trivially short step (single line of instruction) needs no explicit gate —
its completion is self-evident.

### Judgment call

Completion language does not need to match a fixed phrase. "Proceed only when…",
"Confirm X before continuing", "Ensure all Y are resolved", "Only after Z" — any
of these convey an exit condition. The question is whether a reasonable agent
reading the step can tell when to stop working on it.

---

## Rule 23 — Result verification step

**Question:** Does the workflow include at least one step that grounds the agent
in actual tool output, rather than relying on verbal self-report?

### Should flag

A workflow that runs a tool but never tells the agent to check what it returned:

~~~markdown
### Step 1 — Run

```bash
tool check .
```

### Step 2 — Fix

Fix the errors.

### Step 3 — Apply

Apply the suggested changes.

### Step 4 — Finish

Move on to the next task.
~~~

An agent following this workflow can claim "Step 1 completed" without ever reading
the output, because nothing in the workflow says to look at it.

### Should not flag

A workflow where at least one step explicitly grounds the agent in actual output:

~~~markdown
### Step 1 — Run

```bash
tool check .
```

Review the output for errors and warnings before deciding how to proceed.
~~~

### Judgment call

The grounding step does not need to be dedicated to result-checking — it just
needs to tell the agent to read the tool's actual output at least once. "If the
tool reported any errors, fix them now" is sufficient. The failure case is a
workflow that treats every tool invocation as a black box and never prompts the
agent to look at what was produced.
