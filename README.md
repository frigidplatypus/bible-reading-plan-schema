# Bible Reading Plan Format

This document describes the standardized YAML format for Bible reading plans used by the Bible Reading Plan API. This format aims to be flexible enough to represent various types of reading plans while maintaining consistency and ease of use.

**Schema Version: 1.0.0**

## Overview

Bible reading plans are represented as YAML files that define a structured approach to reading the Bible. The format accommodates various reading patterns including:

- Sequential reading plans
- Thematic reading plans
- Plans with specific calendar dates
- Plans with numbered days (day 1, day 2, etc.)
- Flexible checklist plans without specific dates
- Plans with multiple daily readings from different books
- Plans with supplementary content

## File Format Specification

### Root Structure

Each Bible reading plan file contains a single root `plan` object:

```yaml
plan:
  id: "unique-plan-id"
  name: "Plan Name"
  description: "Description of the plan"
  # Additional fields...
```

### Required Plan Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique identifier for the plan |
| `name` | String | Display name of the reading plan |
| `description` | String | Brief description of the reading plan |
| `type` | String | Type of plan: `sequential`, `thematic`, `chronological`, etc. |
| `version` | String | Version identifier for the plan (e.g., "1.0", "2023", "2023-2024") |
| `duration_days` | Integer | Total number of days in the plan (use `-1` for flexible plans) |
| `schedule_type` | String | How days are tracked: `numbered` (day 1, 2...), `calendar` (specific dates with year), `calendar-generic` (month-day only), `flexible` (checklist), or `day-of-week` (separate tracking per day of week) |
| `readings` | Array | List of reading day entries |

### Optional Plan Fields

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | Object | Additional metadata about the plan |
| `features` | Object | Special features and configuration options |

### Metadata Object

```yaml
metadata:
  author: "Author name or organization"
  tags: ["tag1", "tag2", "tag3"]
  # Other metadata fields...
```

### Reading Entry

Each entry in the `readings` array represents a single reading day or unit:

```yaml
readings:
  - day: 1  # For numbered plans
    # OR
    date: "2025-04-21"  # For calendar plans (ISO format)
    # OR
    id: "reading-1"  # For flexible checklist plans

    sections:  # Array of reading sections
      - book: "BookName"
        chapters: [1, 2, 3]  # For consecutive or specific chapters
        # OR
        chapter_verse: "5:1-11"  # For specific verse ranges

    # Optional fields
    supplementary:
      devotional: "Devotional text or prompt"
      prayer_focus: "Prayer focus for the day"
      questions: ["Question 1", "Question 2"]

    type: "regular"  # Or "catch-up", "rest", etc.
```

### Reading Section

Each reading day can have multiple sections, representing different passages to read:

```yaml
sections:
  - book: "Genesis"  # Book name
    chapters: [1, 2]  # List of chapters

  - book: "John"
    chapter_verse: "3:16-21"  # Chapter and verse range
```

### Features Object

Optional configuration for advanced features:

```yaml
features:
  allow_notes: true  # Whether the plan supports user notes
  track_partial_completion: true  # Whether partial completion can be tracked
  catch_up_strategy: "flexible"  # How to handle missed readings
```

## Scripture Reference Formats

### Chapter References

- **Full chapters**: Specify chapters as a list: `chapters: [1, 2, 3]`
- **Non-consecutive chapters**: List specific chapters: `chapters: [1, 5, 9]`

### Verse References

- **Specific verse range**: Use `chapter_verse` field with format `chapter:verse-verse`
  - Example: `chapter_verse: "3:16-21"` (chapter 3, verses 16 through 21)
- **Single verse**: Use `chapter_verse` field with format `chapter:verse`
  - Example: `chapter_verse: "3:16"` (chapter 3, verse 16)
- **Full chapter with specific verse notation**: `chapter_verse: "3"` (entire chapter 3)

## Schedule Types

### Numbered Schedule

For plans that use "Day 1", "Day 2", etc., without specific calendar dates:

```yaml
schedule_type: "numbered"
readings:
  - day: 1
    sections: [...]
  - day: 2
    sections: [...]
```

### Calendar Schedule

For plans tied to specific calendar dates:

```yaml
schedule_type: "calendar"
readings:
  - date: "2025-01-01"  # ISO format (YYYY-MM-DD)
    sections: [...]
  - date: "2025-01-02"
    sections: [...]
```

### Calendar-Generic Schedule

For plans tied to month and day but not to a specific year (can be used every year):

```yaml
schedule_type: "calendar-generic"
readings:
  - date: "Jan-01"  # MMM-DD format for January 1st
    sections: [...]
  - date: "Jan-02"  # MMM-DD format for January 2nd
    sections: [...]
```

### Flexible/Checklist Schedule

For plans without specific day assignments:

```yaml
schedule_type: "flexible"
readings:
  - id: "reading-1"  # Unique identifier for the reading
    sections: [...]
  - id: "reading-2"
    sections: [...]
```

### By Day of Week Schedule

For plans that have different reading lists by day of the week.  Sunday: Poetry, Sunday: Pentatuech, Thursday: Gospels, etc.

```yaml
schedule_type: day-of-week
day_section:
    sunday: "poetry"
    monday: "pentateuch"
    tuesday: "historical"
    wednesday: "prophets"
    thursday: "gospels"
    friday: "epistles"
    saturday: "personal_choice"
readings:
    - day_of_week: "sunday"
      id: "sunday-poetry-1"
      sections:
        - book: "Psalms"
          chapters: [1, 2, 3, 4, 5]

    - day_of_week: "sunday"
      id: "sunday-poetry-2"
      sections:
        - book: "Psalms"
          chapters: [6, 7, 8, 9, 10]

    - day_of_week: "monday"
      id: "monday-pentateuch-1"
      sections:
        - book: "Genesis"
          chapters: [1, 2, 3]

    - day_of_week: "monday"
      id: "monday-pentateuch-2"
      sections:
        - book: "Genesis"
          chapters: [4, 5, 6]
```

## Special Day Types

Reading days can have special types:

```yaml
- day: 7
  type: "catch-up"  # Can be "regular", "catch-up", "rest", or custom types
  description: "Use this day to catch up on missed readings"
```

## Supplementary Content

Additional content can be included with readings:

```yaml
supplementary:
  devotional: "Text for reflection or devotional"
  prayer_focus: "Specific prayer focus"
  questions: ["Question 1?", "Question 2?"]
  # Can include other custom supplementary fields
```

## Complete Example

```yaml
plan:
  id: "nt-90"
  name: "New Testament in 90 Days"
  description: "Read through the entire New Testament in 90 days"
  type: "sequential"
  duration_days: 90
  schedule_type: "numbered"

  metadata:
    author: "Example Ministry"
    tags: ["new testament", "quarterly", "complete"]

  readings:
    - day: 1
      sections:
        - book: "Matthew"
          chapters: [1, 2, 3]

    - day: 2
      sections:
        - book: "Matthew"
          chapters: [4, 5, 6]

    # Day with multiple reading sections
    - day: 30
      sections:
        - book: "John"
          chapters: [1, 2]
        - book: "Psalms"
          chapter_verse: "23"

    # Day with verse ranges
    - day: 45
      sections:
        - book: "Romans"
          chapter_verse: "5:1-11"
        - book: "Romans"
          chapter_verse: "6:1-14"

    # Day with supplementary content
    - day: 75
      sections:
        - book: "Ephesians"
          chapters: [1, 2]
      supplementary:
        devotional: "Reflect on how Paul describes our identity in Christ"
        prayer_focus: "Give thanks for your spiritual blessings"

    # Catch-up day
    - day: 76
      type: "catch-up"
      description: "Use this day to catch up on previous readings"

  features:
    allow_notes: true
    track_partial_completion: true
    catch_up_strategy: "flexible"
```

## Validation Rules

1. Plan `id` must be unique and contain only lowercase letters, numbers, and hyphens
2. Each reading must have either `day`, `date`, or `id` based on the `schedule_type`
3. Book names must be valid Bible book names or abbreviations
4. Chapter numbers must be valid for the specified book
5. Verse ranges must be valid for the specified chapter
6. For `numbered` plans, days must start at 1 and increment continuously
7. For `calendar` plans, dates must be in ISO format (YYYY-MM-DD)
8. For `calendar-generic` plans, dates must be in MMM-DD format (e.g., "Jan-01" for January 1st)

## Best Practices

1. Keep plan IDs short but descriptive
2. Provide detailed descriptions for plans
3. Include appropriate tags to make plans discoverable
4. Use supplementary content to enhance the reading experience

## File Naming Convention

Bible reading plan files should be named using the plan's ID followed by the `.yaml` extension:

```
{plan-id}.yaml
```

Example: `nt-90.yaml`, `chronological-365.yaml`
