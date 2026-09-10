import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = Path("data/gita/bhagavad_gita_in_english_sanskrit.pdf")
OUTPUT_PATH = Path("data/gita/gita.json")

SANSKRIT_URL = (
    "https://sanskritdocuments.org/doc_giitaa/bhagvadnew.html"
)


# ============================================================
# EXPECTED VERSE COUNTS
#
# IMPORTANT:
# This matches the numbering used by YOUR PDF.
#
# Chapter 13 in this particular PDF has 34 verses.
# Some Sanskrit sources count Arjuna's initial question
# separately, resulting in 35 verses.
# We normalize that difference below.
# ============================================================

EXPECTED_VERSES = {
    1: 47,
    2: 72,
    3: 43,
    4: 42,
    5: 29,
    6: 47,
    7: 30,
    8: 28,
    9: 34,
    10: 42,
    11: 55,
    12: 20,
    13: 34,
    14: 27,
    15: 20,
    16: 24,
    17: 28,
    18: 78,
}


# ============================================================
# CHAPTER ROMAN NUMERAL MAPPING
# ============================================================

ROMAN_TO_INT = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
}


# ============================================================
# DEVANAGARI DIGITS
# ============================================================

DEVANAGARI_DIGITS = str.maketrans(
    "०१२३४५६७८९",
    "0123456789"
)


def devanagari_to_int(value):
    """
    Convert Devanagari number to Python integer.

    Example:
        १३ -> 13
    """

    return int(
        value.translate(DEVANAGARI_DIGITS)
    )


# ============================================================
# CLEAN SANSKRIT
# ============================================================

def clean_sanskrit(text):
    """
    Clean Sanskrit text while preserving Unicode Devanagari.
    """

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        lines.append(line)

    text = " ".join(lines)

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CLEAN ENGLISH
# ============================================================

def clean_english(text):
    """
    Clean English text extracted from the PDF.

    The PDF contains page headers, page numbers and other
    layout artifacts which are removed here.
    """

    cleaned_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Standalone page number
        if re.fullmatch(r"\d+", line):
            continue

        # Page header/footer
        if "Bhagavadg" in line and "[Ch." in line:
            continue

        # Text range footer
        if line.startswith("Text "):
            continue

        cleaned_lines.append(line)

    text = " ".join(cleaned_lines)

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT SANSKRIT FROM UNICODE WEB SOURCE
# ============================================================

def extract_sanskrit():

    print("Downloading Sanskrit source...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://sanskritdocuments.org/",
    }

    response = requests.get(
        SANSKRIT_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text("\n")

    # --------------------------------------------------------
    # SanskritDocuments uses verse markers like:
    #
    # ॥ १-१॥
    # ॥ १-२॥
    #
    # Capture verse text preceding the marker.
    # --------------------------------------------------------

    pattern = re.compile(
        r"(?P<verse_text>.*?)"
        r"[॥]\s*"
        r"(?P<chapter>[०-९]+)"
        r"\s*-\s*"
        r"(?P<verse>[०-९]+)"
        r"\s*[॥]",
        re.DOTALL
    )

    raw_records = {}

    for match in pattern.finditer(text):

        chapter = devanagari_to_int(
            match.group("chapter")
        )

        verse = devanagari_to_int(
            match.group("verse")
        )

        if chapter not in EXPECTED_VERSES:
            continue

        verse_text = clean_sanskrit(
            match.group("verse_text")
        )

        if not verse_text:
            continue

        # ----------------------------------------------------
        # Keep only Devanagari/punctuation content.
        # ----------------------------------------------------

        devanagari_parts = re.findall(
            r"[\u0900-\u097F।॥,.!?;:\-\s]+",
            verse_text
        )

        verse_text = " ".join(
            part.strip()
            for part in devanagari_parts
            if part.strip()
        )

        if not verse_text:
            continue

        raw_records[
            (chapter, verse)
        ] = verse_text

    # --------------------------------------------------------
    # CHAPTER 13 NORMALIZATION
    #
    # Some editions count Arjuna's opening question as
    # Chapter 13 Verse 1.
    #
    # Our PDF does NOT use that numbering.
    #
    # Therefore:
    #
    # Source 13:1 -> ignored
    # Source 13:2 -> PDF 13:1
    # Source 13:3 -> PDF 13:2
    # ...
    # Source 13:35 -> PDF 13:34
    # --------------------------------------------------------

    normalized_records = {}

    for (chapter, verse), verse_text in raw_records.items():

        if chapter == 13:

            # Ignore source's separate opening question
            if verse == 1:
                continue

            normalized_verse = verse - 1

            if normalized_verse < 1:
                continue

            if normalized_verse > EXPECTED_VERSES[13]:
                continue

            normalized_records[
                (13, normalized_verse)
            ] = verse_text

        else:

            if verse > EXPECTED_VERSES[chapter]:
                continue

            normalized_records[
                (chapter, verse)
            ] = verse_text

    print(
        f"Sanskrit verses extracted: "
        f"{len(normalized_records)}"
    )

    return normalized_records


# ============================================================
# FIND CHAPTER START PAGES IN PDF
# ============================================================

def find_chapter_pages(reader):

    chapter_starts = []

    for page_index in range(
        20,
        len(reader.pages)
    ):

        text = (
            reader.pages[page_index]
            .extract_text()
            or ""
        )

        match = re.search(
            r"Chapter\s+([IVXLC]+)",
            text
        )

        if not match:
            continue

        roman = match.group(1)

        chapter_number = ROMAN_TO_INT.get(
            roman
        )

        if chapter_number is None:
            continue

        expected_next = (
            len(chapter_starts) + 1
        )

        if chapter_number == expected_next:

            chapter_starts.append(
                (
                    chapter_number,
                    page_index
                )
            )

        if len(chapter_starts) == 18:
            break

    return chapter_starts


# ============================================================
# NORMALIZE TRANSLATION REFERENCE
# ============================================================

def normalize_reference(reference):
    """
    Normalize translation references extracted from the PDF.

    Examples:

        4ó6   -> 4-6
        40ó44 -> 40-44
        51ó53 -> 51-53
        4 2   -> 42
    """

    reference = reference.strip()

    # PDF extraction converts the dash in references
    # into the character "ó".
    reference = reference.replace("ó", "-")
    reference = reference.replace("Ó", "-")

    # Also handle other possible dash characters.
    reference = reference.replace("–", "-")
    reference = reference.replace("—", "-")

    # Remove spaces around dash.
    reference = re.sub(
        r"\s*-\s*",
        "-",
        reference
    )

    # PDF sometimes extracts 42 as "4 2".
    reference = re.sub(
        r"(?<=\d)\s+(?=\d)",
        "",
        reference
    )

    return reference.strip()

# ============================================================
# GET VERSES FROM TRANSLATION REFERENCE
# ============================================================

def parse_reference_numbers(reference):
    """
    Convert translation reference into verse numbers.

    Examples:

        "42"
            -> [42]

        "4-6"
            -> [4, 5, 6]

        "26 & first half of 27"
            -> [26, 27]

        "Second half of 27 and first half of 28"
            -> [27, 28]
    """

    reference = normalize_reference(
        reference
    )

    # First detect explicit ranges.
    range_match = re.search(
        r"(\d+)\s*-\s*(\d+)",
        reference
    )

    if range_match:

        start = int(
            range_match.group(1)
        )

        end = int(
            range_match.group(2)
        )

        if start <= end:
            return list(
                range(start, end + 1)
            )

    # Otherwise collect all numbers.
    numbers = [
        int(number)
        for number in re.findall(
            r"\d+",
            reference
        )
    ]

    # Remove duplicates while preserving order.
    result = []

    for number in numbers:

        if number not in result:
            result.append(number)

    return result


# ============================================================
# EXTRACT ENGLISH TRANSLATIONS
# ============================================================

def extract_english(reader):

    chapter_pages = find_chapter_pages(reader)

    print("\nChapter pages:")

    for chapter, page in chapter_pages:

        print(
            f"Chapter {chapter}: "
            f"PDF page {page + 1}"
        )

    english = {}

    for index, (
        chapter,
        start_page
    ) in enumerate(chapter_pages):

        # ----------------------------------------------------
        # Determine chapter ending page
        # ----------------------------------------------------

        if index + 1 < len(chapter_pages):

            end_page = (
                chapter_pages[index + 1][1]
            )

        else:

            end_page = len(reader.pages)

        # ----------------------------------------------------
        # Extract complete chapter text
        # ----------------------------------------------------

        chapter_text = "\n".join(
            reader.pages[i].extract_text()
            or ""
            for i in range(
                start_page,
                end_page
            )
        )

        # ----------------------------------------------------
        # PDF Sanskrit verse markers
        #
        # Example:
        #
        # H 1H
        # H 2H
        # H 3H
        # ----------------------------------------------------

        verse_markers = list(
            re.finditer(
                r"H\s*(\d{1,3})\s*H",
                chapter_text
            )
        )

        # ----------------------------------------------------
        # Normal translation references
        #
        # Examples:
        #
        # (1)
        # (4ó6)
        # (40ó44)
        # (51ó53)
        # (4 2)
        # ----------------------------------------------------

        translation_markers = list(
            re.finditer(
                r"\(([^()]*(?:\d)[^()]*)\)",
                chapter_text
            )
        )

        # ====================================================
        # NORMAL TRANSLATION REFERENCES
        # ====================================================

        for marker in translation_markers:

            raw_reference = (
                marker.group(1).strip()
            )

            reference = normalize_reference(
                raw_reference
            )

            target_verses = (
                parse_reference_numbers(
                    reference
                )
            )

            if not target_verses:
                continue

            # Keep only valid verses for this chapter.
            target_verses = [
                verse
                for verse in target_verses
                if (
                    1 <= verse
                    <= EXPECTED_VERSES[chapter]
                )
            ]

            if not target_verses:
                continue

            # ------------------------------------------------
            # Find last Sanskrit marker before translation.
            # ------------------------------------------------

            previous_sanskrit = None

            for verse_marker in verse_markers:

                if (
                    verse_marker.end()
                    <= marker.start()
                ):

                    previous_sanskrit = (
                        verse_marker
                    )

                else:

                    break

            if previous_sanskrit is None:
                continue

            # ------------------------------------------------
            # Translation text lies between Sanskrit marker
            # and translation reference.
            # ------------------------------------------------

            translation_text = chapter_text[
                previous_sanskrit.end():
                marker.start()
            ]

            translation_text = clean_english(
                translation_text
            )

            if not translation_text:
                continue

            # ------------------------------------------------
            # Store against every verse in grouped reference.
            #
            # Example:
            #
            # (4-6)
            #
            # gets assigned to:
            #
            # 4
            # 5
            # 6
            # ------------------------------------------------

            for verse in target_verses:

                key = (
                    chapter,
                    verse
                )

                if key not in english:

                    english[key] = {
                        "text": translation_text,
                        "reference": reference,
                    }

        # ====================================================
        # SPECIAL RECOVERY
        #
        # Handles cases where "(" is missing.
        #
        # Example:
        #
        # deeply pondering over it, now do as you like. 63)
        #
        # ====================================================

        for i, verse_marker in enumerate(
            verse_markers
        ):

            pdf_verse = int(
                verse_marker.group(1)
            )

            if (
                pdf_verse < 1
                or pdf_verse
                > EXPECTED_VERSES[chapter]
            ):
                continue

            start = verse_marker.end()

            if i + 1 < len(verse_markers):

                end = (
                    verse_markers[i + 1].start()
                )

            else:

                end = len(chapter_text)

            segment = chapter_text[
                start:end
            ]

            segment = clean_english(
                segment
            )

            if not segment:
                continue

            # ------------------------------------------------
            # Look for a missing-opening-parenthesis reference.
            #
            # IMPORTANT:
            # Do NOT require it to be at the absolute end,
            # because PDF footer text can follow it.
            # ------------------------------------------------

            matches = list(
                re.finditer(
                    r"(\d{1,3})\)",
                    segment
                )
            )

            if not matches:
                continue

            # Use the last reference in the segment.
            match = matches[-1]

            reference = match.group(1)

            target_verses = (
                parse_reference_numbers(
                    reference
                )
            )

            if not target_verses:
                continue

            # For this recovery path, the reference should
            # correspond to the current PDF verse.
            if pdf_verse not in target_verses:
                continue

            translation_text = (
                segment[:match.start()]
            )

            translation_text = clean_english(
                translation_text
            )

            if not translation_text:
                continue

            key = (
                chapter,
                pdf_verse
            )

            if key not in english:

                english[key] = {
                    "text": translation_text,
                    "reference": reference,
                }

    print(
        f"\nEnglish translation mappings: "
        f"{len(english)}"
    )

    return english

# ============================================================
# BUILD FINAL DATASET
# ============================================================

def build_dataset(
    sanskrit,
    english
):

    dataset = []

    print("\nBuilding final dataset...")

    for chapter in range(1, 19):

        expected = EXPECTED_VERSES[
            chapter
        ]

        chapter_count = 0

        for verse in range(
            1,
            expected + 1
        ):

            key = (
                chapter,
                verse
            )

            # ------------------------------------------------
            # Sanskrit
            # ------------------------------------------------

            sanskrit_text = (
                sanskrit.get(key)
            )

            if not sanskrit_text:

                print(
                    f"WARNING: Missing Sanskrit "
                    f"{chapter}:{verse}"
                )

                continue

            # ------------------------------------------------
            # English
            # ------------------------------------------------

            english_data = (
                english.get(key)
            )

            if not english_data:

                print(
                    f"WARNING: Missing English "
                    f"{chapter}:{verse}"
                )

                english_text = ""
                translation_reference = ""

            else:

                english_text = (
                    english_data["text"]
                )

                translation_reference = (
                    english_data["reference"]
                )

            # ------------------------------------------------
            # Final record
            # ------------------------------------------------

            record = {
                "tradition": "gita",
                "book": "Bhagavad Gita",
                "chapter": chapter,
                "verse": str(verse),
                "sanskrit": sanskrit_text,
                "english": english_text,
                "source": (
                    f"Bhagavad Gita "
                    f"{chapter}:{verse}"
                ),
                "translation_reference": (
                    translation_reference
                ),
            }

            dataset.append(record)

            chapter_count += 1

        print(
            f"Chapter {chapter}: "
            f"{chapter_count}/{expected} verses"
        )

    return dataset


# ============================================================
# VALIDATE DATASET
# ============================================================

def validate(dataset):

    print("\n==============================")
    print("VALIDATION")
    print("==============================")

    total = len(dataset)

    print(
        f"Total records: {total}"
    )

    # --------------------------------------------------------
    # Total validation
    # --------------------------------------------------------

    if total == 700:

        print(
            "✓ Total verses = 700"
        )

    else:

        print(
            "✗ Expected 700 verses!"
        )

    # --------------------------------------------------------
    # Chapter validation
    # --------------------------------------------------------

    all_chapters_correct = True

    for chapter in range(1, 19):

        count = sum(
            1
            for item in dataset
            if item["chapter"] == chapter
        )

        expected = EXPECTED_VERSES[
            chapter
        ]

        if count == expected:

            print(
                f"✓ Chapter {chapter}: "
                f"{count}/{expected}"
            )

        else:

            print(
                f"✗ Chapter {chapter}: "
                f"{count}/{expected}"
            )

            all_chapters_correct = False

    # --------------------------------------------------------
    # Empty Sanskrit / English validation
    # --------------------------------------------------------

    empty_sanskrit = [
        item["source"]
        for item in dataset
        if not item["sanskrit"].strip()
    ]

    empty_english = [
        item["source"]
        for item in dataset
        if not item["english"].strip()
    ]

    print()

    if not empty_sanskrit:

        print(
            "✓ Sanskrit present for all records"
        )

    else:

        print(
            f"✗ Missing Sanskrit: "
            f"{len(empty_sanskrit)}"
        )

        for source in empty_sanskrit:
            print(
                f"  - {source}"
            )

    if not empty_english:

        print(
            "✓ English present for all records"
        )

    else:

        print(
            f"✗ Missing English: "
            f"{len(empty_english)}"
        )

        for source in empty_english:
            print(
                f"  - {source}"
            )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    if (
        total == 700
        and all_chapters_correct
        and not empty_sanskrit
        and not empty_english
    ):

        print(
            "\n✓ DATASET VALIDATION PASSED"
        )

        return True

    print(
        "\n✗ DATASET VALIDATION FAILED"
    )

    return False


# ============================================================
# SAVE JSON
# ============================================================

def save_json(dataset):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dataset,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("==============================")
    print("BHAGAVAD GITA DATASET BUILDER")
    print("==============================")

    # --------------------------------------------------------
    # Check PDF
    # --------------------------------------------------------

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"PDF not found: {PDF_PATH}"
        )

    # --------------------------------------------------------
    # Read PDF
    # --------------------------------------------------------

    reader = PdfReader(
        str(PDF_PATH)
    )

    print(
        f"PDF pages: {len(reader.pages)}"
    )

    # --------------------------------------------------------
    # 1. Sanskrit
    # --------------------------------------------------------

    sanskrit = extract_sanskrit()

    # --------------------------------------------------------
    # 2. English
    # --------------------------------------------------------

    english = extract_english(
        reader
    )

    # --------------------------------------------------------
    # 3. Build dataset
    # --------------------------------------------------------

    dataset = build_dataset(
        sanskrit,
        english
    )

    # --------------------------------------------------------
    # 4. Validate
    # --------------------------------------------------------

    validation_passed = validate(
        dataset
    )

    # --------------------------------------------------------
    # 5. Save
    #
    # Save only after validation.
    # --------------------------------------------------------

    if validation_passed:

        save_json(dataset)

    else:

        print(
            "\nJSON was NOT saved because "
            "validation failed."
        )

        print(
            "Fix the warnings before continuing."
        )

        return

    # --------------------------------------------------------
    # Show first record
    # --------------------------------------------------------

    if dataset:

        print(
            "\n=============================="
        )

        print(
            "FIRST RECORD"
        )

        print(
            "=============================="
        )

        print(
            json.dumps(
                dataset[0],
                ensure_ascii=False,
                indent=2
            )
        )

    # --------------------------------------------------------
    # Show last record
    # --------------------------------------------------------

    if dataset:

        print(
            "\n=============================="
        )

        print(
            "LAST RECORD"
        )

        print(
            "=============================="
        )

        print(
            json.dumps(
                dataset[-1],
                ensure_ascii=False,
                indent=2
            )
        )

    print(
        "\n=============================="
    )

    print(
        "DONE"
    )

    print(
        "=============================="
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()