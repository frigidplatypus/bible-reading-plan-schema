# Example Plans

Minimal, single-purpose examples — one per `schedule_type`. Each demonstrates the
smallest valid plan for that schedule type and is **not** intended for real use.

Real, published plans live in [`../plans/`](../plans/).

| File | `schedule_type` | Plan `id` |
|------|-----------------|-----------|
| `number.yaml` | `numbered` | `minimal-numbered` |
| `calendar.yaml` | `calendar` | `minimal-calendar` |
| `calendar_generic.yaml` | `calendar-generic` | `minimal-calendar-generic` |
| `flexible.yaml` | `flexible` | `minimal-flexible` |
| `day_of_week.yaml` | `day-of-week` | `minimal-day-of-week` |

All examples use Genesis chapters 1–2 as placeholder readings. Validate any of them:

```sh
python -m scripts.validate_reading_plan example_plans/number.yaml
```
