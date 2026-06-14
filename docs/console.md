# Console

The local Console is a static management surface served by `harnessable console`.

Current views:

- operator action queue
- selected run detail
- decision timeline
- approval evidence form
- replay diff
- artifact registry
- audit export action
- fallback graph placeholder
- trace/project status strip

Design constraints:

- default light mode
- no card farm
- primary task visible on first viewport
- graph container preserves aspect ratio through CSS `aspect-ratio`
- responsive layout for narrow viewports
- list-first operator workflow instead of card dashboard
