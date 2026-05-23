# CLI

```bash
harnessable init ./project --name "Project"
harnessable validate ./project
harnessable rules --project ./project list
harnessable rules --project ./project add ./rule.yaml --preview
harnessable rules --project ./project apply <preview-id>
harnessable capabilities --project ./project list
harnessable fallback --project ./project validate
harnessable eval --project ./project run ./evals
harnessable replay --project ./project run <run-id>
harnessable trace --project ./project show <run-id>
harnessable console ./project
```

The CLI is local-first and does not start a hosted service.
