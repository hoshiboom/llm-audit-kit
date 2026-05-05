# Contributing to llm-audit-kit

Thanks for your interest! This project grows by community contributions — especially new **checklist items** based on real-world incidents.

## Quick Ways to Contribute

### 1. Add a new checklist item

The `checklist.yaml` is the heart of the project. Each item follows this shape:

```yaml
- id: L3-007                # Lx-NNN, where x is layer number
  title: Short checkable name
  question: A yes/no question asked to developers
  weight: 2                 # 1 = minor, 2 = important, 3 = critical
  rationale: Why this matters (the root cause)
  mitigation: What to do if the answer is "no"
  refs: optional links
```

Guidelines:
- **One item, one risk.** If you're tempted to write `and`, split it.
- **weight=3** is reserved for items where violation = direct exploitability
  or catastrophic damage.
- Cite a paper, CVE, or public incident if possible.
- Keep `mitigation` **concrete and verifiable** (no "be careful").

### 2. Fix / refine existing items

Got better phrasing, a stronger rationale, or updated references? PRs welcome.

### 3. Improve the audit tool

See `tools/llm-audit/audit.py`. Zero third-party deps is a **hard constraint** —
we want the tool to run anywhere with vanilla Python 3.8+.

### 4. Translate

The checklist content is bilingual-friendly. Feel free to propose
`checklist.en.yaml` / `checklist.zh.yaml` split if you want to help localize.

## Development Loop

```bash
git clone https://github.com/hoshiboom/llm-audit-kit.git
cd llm-audit-kit

# Run with the example answers to sanity-check your changes
python tools/llm-audit/audit.py \
  --answers tools/llm-audit/example-answers.json \
  --output /tmp/report.md
```

## Commit / PR Style

- Commit title: `[Lx] short summary` (e.g. `[L3] add indirect-injection spotlighting item`)
- Small, focused PRs are easier to merge. Please avoid mixing checklist edits
  with tool refactors in one PR.
- Include motivation in the PR description: *what attack / incident / paper
  prompted this item?*

## Code of Conduct

Be kind, be specific. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

## Security

Found a real vulnerability (e.g. in a system that could be scanned by this
kit)? **Do not file a public issue.** Email the maintainer via the profile
contact instead.
