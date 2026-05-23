# Design Token Board

Scope: local Harness management Console.

Audience:

- AI platform engineers
- governance reviewers
- QA / replay engineers

Primary question:

> Can I safely preview, validate, and apply a harness project change?

Tokens:

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#f7f8fa` | page background |
| `--surface` | `#ffffff` | workbench surfaces |
| `--ink` | `#17202a` | primary text |
| `--muted` | `#667085` | supporting text |
| `--line` | `#d7dde5` | borders |
| `--accent` | `#1264a3` | primary actions |
| `--danger` | `#b42318` | destructive/cancel emphasis |
| `--radius` | `8px` | bounded controls and panes |

Interaction model:

- Left rail selects the management area.
- Primary pane owns preview/apply/cancel.
- Validation is adjacent supporting state.
- Fallback graph is deferred below the main task and keeps fixed aspect ratio.

Review council summary:

- task-first design director: primary task is visible without a hero or summary-first layout.
- interaction architect: controls map to import review state; validation remains supporting context.
- visual systems critic: restrained operational palette avoids generic decorative gradients.
- responsive and accessibility auditor: mobile stacks the rail and panes; ARIA labels exist for primary navigation and graph area.
- product language editor: visible copy is operational and avoids exposing methodology language.
