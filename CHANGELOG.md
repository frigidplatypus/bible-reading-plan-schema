# Changelog

All notable changes to the Bible Reading Plan Schema will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-10

Initial stable release of the Bible Reading Plan Schema.

### Added
- Standardized YAML format for Bible reading plans
- Support for multiple schedule types:
  - `numbered`: Day 1, Day 2, etc. (numbered days)
  - `calendar`: Specific calendar dates with full ISO format (YYYY-MM-DD)
  - `calendar-generic`: Month-day dates (MMM-DD like Jan-01) not tied to specific years
  - `flexible`: Checklist plans without specific dates
  - `day-of-week`: Plans organized by day of the week
- Validation script for checking plan compliance with the schema
- Helper script for reading and displaying plan entries
- Comprehensive documentation
- Multiple example plans demonstrating each schedule type
- Support for verse ranges and chapter references
- Optional supplementary content for devotionals, prayer focus, and questions
- Support for special day types (catch-up, rest, etc.)

### Schema Features
- Structured approach to represent various Bible reading patterns
- Flexibility for different plan types (sequential, thematic, chronological)
- Metadata support for plan attribution and discoverability
- Consistent format for scripture references