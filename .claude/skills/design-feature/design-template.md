# Design NNN — <Feature name>

**Spec:** [spec.md](spec.md)

## Data model
```python
class Thing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ...
```

## Service layer — `app/services/<module>.py`
| Function | Behaviour | Errors |
|----------|-----------|--------|
| `do_x(session, ...) -> Thing` | ... | `NotFound` if ..., `Conflict` if ... |

## API contract
### `POST /api/...`
Request:
```json
{ }
```
`201` →
```json
{ }
```
Errors: `404 {"detail": "Event not found"}`, `409 {"detail": "..."}`, `422 {"detail": "..."}`

## UI
Pages / partials touched: `app/templates/...`

```
+------------------------------+
|  wireframe                   |
+------------------------------+
```

| State | When | Visible text (assertable) |
|-------|------|---------------------------|
| ...   | ...  | "..." |

## AC mapping
| AC    | Satisfied by |
|-------|--------------|
| ACN.1 | `POST /api/...` 201 |

## Risks / notes
- ...
