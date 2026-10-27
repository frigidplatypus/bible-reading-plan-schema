#!/usr/bin/env python3

import json
import yaml
import argparse
import os
import re
from datetime import datetime
import sys

# --- Constants ---
SCHEMA_VERSION = "1.0.0"
BIBLE_DATA_DEFAULT_FILENAME = 'books-of-the-bible.yaml'
REQUIRED_PLAN_FIELDS = ['id', 'name', 'description', 'type', 'version', 'duration_days', 'schedule_type', 'readings']
ALLOWED_SCHEDULE_TYPES = ['numbered', 'calendar', 'calendar-generic', 'flexible', 'day-of-week']
ALLOWED_WEEK_DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
PLAN_ID_PATTERN = re.compile(r'^[a-z0-9-]+$')
# Regex for chapter/verse parsing (more robust)
# Matches: 1 | 1:1 | 1:1-10
CV_PATTERN = re.compile(r'^(\d+)(?::(\d+)(?:-(\d+))?)?$')

# Global dictionary to store processed bible data for efficient lookup
processed_bible_data_global = None

# --- Helper Functions ---

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def load_plan_file(filepath):
    """Loads a YAML or JSON plan/data file with error handling."""
    if not os.path.exists(filepath):
        raise ValidationError(f"File not found: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath.lower().endswith('.json'):
                return json.load(f)
            return yaml.safe_load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Error parsing JSON file {filepath}: {e}")
    except yaml.YAMLError as e:
        raise ValidationError(f"Error parsing YAML file {filepath}: {e}")
    except Exception as e:
        raise ValidationError(f"Error reading file {filepath}: {e}")

def convert_calendar_generic_to_date(generic_date, year):
    """
    Converts a calendar-generic date (MMM-DD) to a datetime.date object for a specific year.
    
    Args:
        generic_date (str): A string in MMM-DD format (e.g., "Jan-01")
        year (int): The year to use for the date
        
    Returns:
        datetime.date: The calendar date for the specified year
        
    Raises:
        ValueError: If the generic_date format is invalid
    """
    if not validate_mmdd_date(generic_date):
        raise ValueError(f"Invalid calendar-generic date format: {generic_date}. Expected format like 'Jan-01'.")
        
    month_abbr = generic_date[:3]
    day_str = generic_date[4:]
    
    # Convert month abbreviation to month number
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    month = month_map[month_abbr]
    day = int(day_str)
    
    return datetime(year, month, day).date()

def preprocess_bible_data(raw_bible_data):
    """
    Processes the raw Bible data into a lookup dictionary for validation.
    Keys are lowercase book names/abbreviations.
    Values are {'canonical': CanonicalName, 'chapters': {chapter_num: verse_count}}.
    """
    processed = {}
    if not isinstance(raw_bible_data, dict):
         raise ValidationError("Bible data YAML must be a dictionary (e.g., containing 'old_testament', 'new_testament').")

    for testament, books in raw_bible_data.items():
        if not isinstance(books, dict):
             raise ValidationError(f"Expected dictionary of books under '{testament}', but found {type(books).__name__}.")
        for book_name, book_data in books.items():
            if not isinstance(book_data, dict) or 'chapters' not in book_data:
                 raise ValidationError(f"Invalid data structure for book '{book_name}'. Missing 'chapters' dictionary.")

            chapters_dict = book_data.get('chapters', {})
            if not isinstance(chapters_dict, dict):
                 raise ValidationError(f"Expected 'chapters' to be a dictionary for book '{book_name}', but found {type(chapters_dict).__name__}.")

            # Ensure chapter keys are integers and verse counts are integers
            validated_chapters = {}
            for ch, v_count in chapters_dict.items():
                try:
                    ch_int = int(ch)
                    v_count_int = int(v_count)
                    if ch_int <= 0 or v_count_int < 0: # Verse count can be 0 theoretically, but not negative. Chapter > 0.
                         raise ValueError("Chapter/Verse counts must be positive.")
                    validated_chapters[ch_int] = v_count_int
                except (ValueError, TypeError):
                     raise ValidationError(f"Invalid chapter ({ch}) or verse count ({v_count}) for book '{book_name}'. Must be integers.")

            book_info = {'canonical': book_name, 'chapters': validated_chapters}

            # Add canonical name (lowercase)
            if book_name.lower() in processed:
                 raise ValidationError(f"Duplicate definition found for book name: {book_name.lower()}")
            processed[book_name.lower()] = book_info

            # Add abbreviations (lowercase)
            abbreviations = book_data.get('abbreviations', [])
            if isinstance(abbreviations, list):
                for abbr in abbreviations:
                    if isinstance(abbr, str):
                        if abbr.lower() in processed and processed[abbr.lower()]['canonical'] != book_name:
                            # Handle potential conflicts if abbreviations are reused across books (unlikely but possible)
                             raise ValidationError(f"Abbreviation '{abbr.lower()}' is ambiguous or redefined. Used for '{processed[abbr.lower()]['canonical']}' and '{book_name}'.")
                        processed[abbr.lower()] = book_info
                    else:
                         raise ValidationError(f"Found non-string abbreviation '{abbr}' for book '{book_name}'.")
            else:
                 raise ValidationError(f"Expected 'abbreviations' to be a list for book '{book_name}', but found {type(abbreviations).__name__}.")

    return processed

def find_book_data(book_ref):
    """Looks up book data using the preprocessed global dictionary."""
    global processed_bible_data_global
    if processed_bible_data_global is None:
        # This should not happen if preprocess_bible_data was called correctly
        raise RuntimeError("Bible data not preprocessed.")

    if not isinstance(book_ref, str) or not book_ref:
        return None, None, ["Book reference must be a non-empty string."]

    lookup_key = book_ref.lower()
    if lookup_key in processed_bible_data_global:
        data = processed_bible_data_global[lookup_key]
        return data['canonical'], data['chapters'], []
    else:
        # Simple suggestion based on direct key match (case-insensitive)
        possible_matches = [k for k in processed_bible_data_global if k.startswith(lookup_key)]
        suggestions = []
        if possible_matches:
            # Get unique canonical names from matches
            suggested_names = sorted(list(set(processed_bible_data_global[m]['canonical'] for m in possible_matches)))
            suggestions.append(f"Book '{book_ref}' not found. Did you mean one of: {', '.join(suggested_names)}?")
        else:
            suggestions.append(f"Book '{book_ref}' not found in the provided Bible data.")
        return None, None, suggestions

def validate_iso_date(date_str):
    """Validates YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False

def validate_mmdd_date(date_str):
    """Validates MMM-DD format for calendar-generic plans (e.g., Jan-01, Feb-28)."""
    try:
        # Check format: three letters for month abbreviation, hyphen, then two digits for day
        if not isinstance(date_str, str) or len(date_str) != 6:
            return False
            
        # Check if the format is like "Jan-01"
        month_abbr = date_str[:3]
        if date_str[3] != '-':
            return False
            
        day_str = date_str[4:]
        if not day_str.isdigit() or len(day_str) != 2:
            return False
            
        # Check if month abbreviation is valid
        valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if month_abbr not in valid_months:
            return False
            
        # Check if day is valid (between 01-31)
        day = int(day_str)
        if day < 1 or day > 31:
            return False
            
        # Additional validation for months with fewer days
        thirty_day_months = ['Apr', 'Jun', 'Sep', 'Nov']
        if month_abbr in thirty_day_months and day > 30:
            return False
            
        if month_abbr == 'Feb' and day > 29:
            return False
            
        return True
    except (ValueError, TypeError):
        return False

# --- Main Validation Logic ---

def validate_plan(plan_file_path, bible_data_path):
    """Validates the reading plan YAML or JSON file."""
    global processed_bible_data_global
    errors = []

    # 1. Load Bible Data and Preprocess
    try:
        raw_bible_data = load_plan_file(bible_data_path)
        processed_bible_data_global = preprocess_bible_data(raw_bible_data)
    except ValidationError as e:
        errors.append(f"Critical error loading Bible data ({bible_data_path}): {e}")
        return errors # Cannot proceed without valid Bible data

    # 2. Load Plan Data
    try:
        plan_yaml = load_plan_file(plan_file_path)
    except ValidationError as e:
        errors.append(f"Critical error loading plan file ({plan_file_path}): {e}")
        return errors # Cannot proceed without plan data

    # 3. Validate Root Structure
    if not isinstance(plan_yaml, dict) or 'plan' not in plan_yaml:
        errors.append("Plan file must contain a root 'plan' object.")
        return errors # Cannot validate further if root is missing/invalid

    plan_data = plan_yaml['plan']
    if not isinstance(plan_data, dict):
        errors.append("The 'plan' key must contain a dictionary (object).")
        return errors

    # 4. Validate Required Top-Level Fields
    for field in REQUIRED_PLAN_FIELDS:
        if field not in plan_data:
            errors.append(f"Root plan object missing required field: '{field}'.")

    # Stop if core fields are missing, as they affect subsequent checks
    if any(f"'{field}'" in err for err in errors for field in ['schedule_type', 'readings']):
         return errors

    # 5. Validate Specific Top-Level Field Formats/Values
    plan_id = plan_data.get('id')
    if plan_id and (not isinstance(plan_id, str) or not PLAN_ID_PATTERN.match(plan_id)):
        errors.append(f"Plan 'id' ('{plan_id}') is invalid. Must contain only lowercase letters, numbers, and hyphens.")

    if 'name' in plan_data and not isinstance(plan_data['name'], str):
        errors.append("Plan 'name' must be a string.")
    if 'description' in plan_data and not isinstance(plan_data['description'], str):
        errors.append("Plan 'description' must be a string.")
    if 'type' in plan_data and not isinstance(plan_data['type'], str):
        errors.append("Plan 'type' must be a string.")
    if 'version' in plan_data and not isinstance(plan_data['version'], str):
        errors.append("Plan 'version' must be a string.")

    duration_days = plan_data.get('duration_days')
    if 'duration_days' in plan_data:
        if not isinstance(duration_days, int):
            errors.append(f"Plan 'duration_days' must be an integer (e.g., 90, 365, or -1 for flexible), but found {type(duration_days).__name__}.")
        elif duration_days < -1 or duration_days == 0:
             errors.append(f"Plan 'duration_days' must be a positive integer or -1. Found: {duration_days}.")

    schedule_type = plan_data.get('schedule_type')
    if schedule_type not in ALLOWED_SCHEDULE_TYPES:
        errors.append(f"Plan 'schedule_type' ('{schedule_type}') is invalid. Allowed types: {', '.join(ALLOWED_SCHEDULE_TYPES)}.")

    readings = plan_data.get('readings')
    if not isinstance(readings, list):
        errors.append("Plan 'readings' field must be a list (array).")
        return errors # Cannot validate individual readings

    # 6. Validate Readings
    expected_day = 1
    processed_dates = set()
    reading_identifiers = set() # For flexible IDs
    highest_day_found = 0

    for i, reading in enumerate(readings):
        reading_context = f"reading entry {i+1}" # Default context

        if not isinstance(reading, dict):
            errors.append(f"Error in {reading_context}: Entry must be a dictionary (object).")
            continue # Skip to next reading

        has_identifier = False
        # Validate identifier based on schedule_type
        if schedule_type == 'numbered':
            day_num = reading.get('day')
            if day_num is None:
                errors.append(f"Error in {reading_context}: Missing 'day' field for 'numbered' schedule type.")
            elif not isinstance(day_num, int) or day_num <= 0:
                errors.append(f"Error in {reading_context}: 'day' field ('{day_num}') must be a positive integer.")
            else:
                reading_context = f"reading for Day {day_num}"
                has_identifier = True
                highest_day_found = max(highest_day_found, day_num)
                if day_num != expected_day:
                    errors.append(f"Error in {reading_context}: Day number out of sequence. Expected day {expected_day}, but found {day_num}.")
                expected_day += 1 # Increment expected day *after* check

        elif schedule_type == 'calendar':
            date_str = reading.get('date')
            if date_str is None:
                errors.append(f"Error in {reading_context}: Missing 'date' field for 'calendar' schedule type.")
            elif not isinstance(date_str, str) or not validate_iso_date(date_str):
                errors.append(f"Error in {reading_context}: 'date' field ('{date_str}') must be a string in YYYY-MM-DD format.")
            else:
                reading_context = f"reading for Date {date_str}"
                has_identifier = True
                processed_dates.add(date_str)

        elif schedule_type == 'calendar-generic':
            date_str = reading.get('date')
            if date_str is None:
                errors.append(f"Error in {reading_context}: Missing 'date' field for 'calendar-generic' schedule type.")
            elif not isinstance(date_str, str) or not validate_mmdd_date(date_str):
                errors.append(f"Error in {reading_context}: 'date' field ('{date_str}') must be a string in MM-DD format.")
            else:
                reading_context = f"reading for Date {date_str}"
                has_identifier = True
                processed_dates.add(date_str)

        elif schedule_type == 'flexible':
            item_id = reading.get('id')
            if item_id is None:
                 errors.append(f"Error in {reading_context}: Missing 'id' field for 'flexible' schedule type.")
            elif not isinstance(item_id, str) or not item_id:
                 errors.append(f"Error in {reading_context}: 'id' field must be a non-empty string.")
            else:
                 reading_context = f"reading with ID '{item_id}'"
                 has_identifier = True
                 if item_id in reading_identifiers:
                     errors.append(f"Error in {reading_context}: Duplicate reading 'id' found. IDs must be unique for 'flexible' plans.")
                 reading_identifiers.add(item_id)

        elif schedule_type == 'day-of-week':
            dow = reading.get('day_of_week')
            item_id = reading.get('id') # ID is also needed for day-of-week tracking

            if dow is None:
                errors.append(f"Error in {reading_context}: Missing 'day_of_week' field for 'day-of-week' schedule type.")
            elif not isinstance(dow, str) or dow.lower() not in ALLOWED_WEEK_DAYS:
                errors.append(f"Error in {reading_context}: Invalid 'day_of_week' ('{dow}'). Must be one of: {', '.join(ALLOWED_WEEK_DAYS)} (case-insensitive).")
            else:
                 # Require ID as well for this schedule type for unique identification
                 if item_id is None:
                     errors.append(f"Error in {reading_context} (DayOfWeek: {dow}): Missing 'id' field. Required for 'day-of-week' schedule type for uniqueness.")
                 elif not isinstance(item_id, str) or not item_id:
                     errors.append(f"Error in {reading_context} (DayOfWeek: {dow}): 'id' field must be a non-empty string.")
                 else:
                    reading_context = f"reading for {dow.capitalize()} with ID '{item_id}'"
                    has_identifier = True
                    id_key = (dow.lower(), item_id) # Combine day and id for uniqueness check
                    if id_key in reading_identifiers:
                        errors.append(f"Error in {reading_context}: Duplicate reading 'id' found for this day of week. IDs must be unique per day for 'day-of-week' plans.")
                    reading_identifiers.add(id_key)

        if not has_identifier and schedule_type in ALLOWED_SCHEDULE_TYPES:
             # If we got here, an identifier was expected but invalid/missing
             errors.append(f"Error in {reading_context}: Invalid or missing identifier for schedule type '{schedule_type}'.")
             continue # Cannot reliably check sections without a valid context

        # Validate reading type (optional field)
        reading_type = reading.get('type', 'regular') # Default to regular
        if not isinstance(reading_type, str):
             errors.append(f"Error in {reading_context}: Optional 'type' field must be a string, but found {type(reading_type).__name__}.")

        # Validate sections (only if type is not 'rest' or 'catch-up' without specific readings)
        # Allow 'catch-up' or 'rest' days to optionally omit 'sections'
        sections = reading.get('sections')
        if sections is None:
            if reading_type not in ['rest', 'catch-up']:
                 errors.append(f"Error in {reading_context}: Missing required 'sections' field for reading type '{reading_type}'.")
            # If type is rest/catch-up, sections are optional. Skip section validation.
            continue

        if not isinstance(sections, list):
            errors.append(f"Error in {reading_context}: 'sections' field must be a list (array).")
            continue # Skip section validation for this reading

        if not sections and reading_type not in ['rest', 'catch-up']:
             errors.append(f"Error in {reading_context}: 'sections' list cannot be empty for reading type '{reading_type}'.")

        section_info = []  # (canonical_book, chapters_list_or_None) per section, for redundancy check
        for j, section in enumerate(sections):
            section_context = f"{reading_context}, section {j+1}"

            if not isinstance(section, dict):
                errors.append(f"Error in {section_context}: Section must be a dictionary (object).")
                continue

            book_ref = section.get('book')
            if not book_ref:
                errors.append(f"Error in {section_context}: Missing required 'book' field.")
                continue # Cannot validate chapters/verses without a book

            canonical_book, chapter_data, book_errors = find_book_data(book_ref)
            if book_errors:
                for book_err in book_errors:
                    errors.append(f"Error in {section_context} (Book: '{book_ref}'): {book_err}")
                continue # Cannot proceed with this section if book is invalid

            section_context = f"{reading_context}, section {j+1} (Book: {canonical_book})"

            has_chapters = 'chapters' in section
            has_chapter_verse = 'chapter_verse' in section

            if not (has_chapters ^ has_chapter_verse): # XOR check
                errors.append(f"Error in {section_context}: Must specify *either* 'chapters' (list) *or* 'chapter_verse' (string), but not both or neither.")
                continue

            if has_chapters:
                chapters_list = section['chapters']
                if not isinstance(chapters_list, list) or not chapters_list:
                    errors.append(f"Error in {section_context}: 'chapters' must be a non-empty list of chapter numbers.")
                else:
                    for chapter_num in chapters_list:
                        if not isinstance(chapter_num, int):
                            errors.append(f"Error in {section_context}: Chapter number '{chapter_num}' must be an integer.")
                        elif chapter_num not in chapter_data:
                             errors.append(f"Error in {section_context}: Invalid chapter number {chapter_num}. {canonical_book} does not have chapter {chapter_num}.")

            if has_chapter_verse:
                cv_string = section['chapter_verse']
                if not isinstance(cv_string, str):
                     errors.append(f"Error in {section_context}: 'chapter_verse' must be a string.")
                     continue

                match = CV_PATTERN.match(cv_string.strip())
                if not match:
                    errors.append(f"Error in {section_context}: Invalid 'chapter_verse' format ('{cv_string}'). Expected format like '1', '1:1', or '1:1-10'.")
                    continue

                try:
                    # Extract parts - groups are 1-indexed, None if not present
                    ch_str, v_start_str, v_end_str = match.groups()
                    chapter_num = int(ch_str)

                    if chapter_num not in chapter_data:
                        errors.append(f"Error in {section_context}: Invalid chapter number {chapter_num} in '{cv_string}'. {canonical_book} does not have chapter {chapter_num}.")
                        continue

                    max_verses = chapter_data[chapter_num]

                    if v_start_str: # Format is C:V or C:V-V
                        v_start = int(v_start_str)
                        if not (1 <= v_start <= max_verses):
                            errors.append(f"Error in {section_context}: Start verse {v_start} in '{cv_string}' is out of range for {canonical_book} chapter {chapter_num} (max verses: {max_verses}).")
                            continue # Stop checking end verse if start is invalid

                        if v_end_str: # Format is C:V-V
                            v_end = int(v_end_str)
                            if not (v_start <= v_end <= max_verses):
                                 errors.append(f"Error in {section_context}: End verse {v_end} in '{cv_string}' is out of range or invalid for {canonical_book} chapter {chapter_num} (start: {v_start}, max: {max_verses}).")

                    # If only chapter ('C') was specified, no verse validation needed beyond chapter existence check above

                except ValueError:
                     # Should not happen with regex, but belt-and-suspenders
                     errors.append(f"Error in {section_context}: Could not parse chapter/verse numbers in '{cv_string}'.")

            # Record this section for the redundant-split check below.
            # chapters_list is the full-chapter list, or None for partial/invalid sections.
            if has_chapters:
                section_info.append((canonical_book, chapters_list if isinstance(chapters_list, list) else None))
            else:
                section_info.append((canonical_book, None))

        # Reject redundant splits: two adjacent sections for the same book whose
        # full-chapter lists are contiguous should be a single section.
        for k in range(len(section_info) - 1):
            book_a, chs_a = section_info[k]
            book_b, chs_b = section_info[k + 1]
            if book_a == book_b and chs_a and chs_b:
                if all(isinstance(c, int) for c in chs_a + chs_b) and chs_b[0] == chs_a[-1] + 1:
                    errors.append(
                        f"Error in {reading_context}: Redundant sections for '{book_a}' "
                        f"(chapters {chs_a[-1]} and {chs_b[0]} are contiguous). "
                        f"Combine them into a single section."
                    )

        # Validate supplementary content (optional)
        supplementary = reading.get('supplementary')
        if supplementary is not None:
            if not isinstance(supplementary, dict):
                 errors.append(f"Error in {reading_context}: Optional 'supplementary' field must be a dictionary (object).")
            else:
                # Basic type checks for known supplementary fields
                if 'devotional' in supplementary and not isinstance(supplementary['devotional'], str):
                     errors.append(f"Error in {reading_context}: Supplementary 'devotional' must be a string.")
                if 'prayer_focus' in supplementary and not isinstance(supplementary['prayer_focus'], str):
                     errors.append(f"Error in {reading_context}: Supplementary 'prayer_focus' must be a string.")
                if 'questions' in supplementary:
                    if not isinstance(supplementary['questions'], list) or \
                       not all(isinstance(q, str) for q in supplementary['questions']):
                        errors.append(f"Error in {reading_context}: Supplementary 'questions' must be a list of strings.")

    # 7. Post-Iteration Checks
    if schedule_type == 'numbered' and duration_days is not None and duration_days != -1:
        # expected_day is now 1 greater than the last valid day found
        last_day_found = expected_day - 1
        # Use highest_day_found in case there were sequencing errors reported earlier
        actual_days = highest_day_found
        if actual_days != duration_days:
             errors.append(f"Plan metadata mismatch: 'duration_days' is {duration_days}, but the highest day number found in readings is {actual_days}.")

    # Add check for calendar duration? Maybe less critical.
    # if schedule_type == 'calendar' and duration_days is not None and duration_days != -1:
    #     if len(processed_dates) != duration_days:
    #         errors.append(f"Plan metadata mismatch: 'duration_days' is {duration_days}, but found {len(processed_dates)} unique dates in readings.")

    # Validate optional features field
    features = plan_data.get('features')
    if features is not None and not isinstance(features, dict):
        errors.append("Optional 'features' field must be a dictionary (object).")

    # Validate optional metadata field
    metadata = plan_data.get('metadata')
    if metadata is not None and not isinstance(metadata, dict):
         errors.append("Optional 'metadata' field must be a dictionary (object).")
    elif isinstance(metadata, dict):
        if 'author' in metadata and not isinstance(metadata['author'], str):
             errors.append("Metadata 'author' field must be a string.")
        if 'tags' in metadata:
            if not isinstance(metadata['tags'], list) or \
               not all(isinstance(t, str) for t in metadata['tags']):
                 errors.append("Metadata 'tags' field must be a list of strings.")

    return errors

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Validate a Bible Reading Plan YAML or JSON file against the specified format.")
    parser.add_argument("plan_file", help="Path to the Bible Reading Plan YAML or JSON file to validate.")
    parser.add_argument("--bible-data",
                        default=BIBLE_DATA_DEFAULT_FILENAME,
                        help=f"Path to the Bible book data YAML or JSON file (default: {BIBLE_DATA_DEFAULT_FILENAME} in the current directory).")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    try:
        validation_errors = validate_plan(args.plan_file, args.bible_data)

        if not validation_errors:
            print("-------------------------")
            print(" Validation Successful! ")
            print("-------------------------")
            print(f"Plan file '{args.plan_file}' conforms to the specification.")
            sys.exit(0)
        else:
            print("-----------------------")
            print(" Validation Failed. ")
            print("-----------------------")
            print(f"Found {len(validation_errors)} error(s) in plan file '{args.plan_file}':\n")
            for i, error in enumerate(validation_errors, 1):
                print(f"{i}. {error}")
            print("\nPlease review the errors above and correct the plan file.")
            sys.exit(1)

    except Exception as e:
        # Catch unexpected errors during validation process itself
        print(f"\n--- An Unexpected Error Occurred During Validation ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print("Validation could not be completed.", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
