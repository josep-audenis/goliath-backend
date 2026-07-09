# Prompts

## Agent Prompts

### Wiki Update Check
```text
Did this change reveal durable knowledge that future agents cannot recover from code or Graphifyy?
If yes, update the smallest relevant docs/llm-wiki page.
If no, leave wiki unchanged.
```

### Decision Capture
```text
Record this as an ADR only if it has durable architectural impact.
Include decision, context, alternatives, why this choice, consequences, date, and status.
```

## Rules
- Store reusable prompts only.
- Do not store task-specific chat transcripts.
- Keep prompts short and direct.

## Related
- [decisions.md](decisions.md)
