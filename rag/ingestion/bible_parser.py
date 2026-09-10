import json
import re
from pathlib import Path

import pymupdf


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

PDF_PATH = BASE_DIR / "data" / "bible" / "English_Bible.pdf"
OUTPUT_PATH = BASE_DIR / "data" / "bible" / "bible.json"


# ============================================================
# BOOKS
# ============================================================

BOOKS = [
    # --------------------------------------------------------
    # Old Testament
    # --------------------------------------------------------

    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",

    # --------------------------------------------------------
    # Deuterocanonical / Apocrypha
    # --------------------------------------------------------

    "Tobit",
    "Judith",
    "Esther (Greek)",
    "Daniel (Greek)",
    "Wisdom of Solomon",
    "Sirach",
    "Baruch",
    "1 Maccabees",
    "2 Maccabees",
    "1 Esdras",
    "Prayer of Manasses",
    "Psalm 151",
    "3 Maccabees",
    "2 Esdras",
    "4 Maccabees",

    # --------------------------------------------------------
    # New Testament
    # --------------------------------------------------------

    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
]


# Longest first.
# Important for books such as:
# "1 Corinthians"
# "2 Thessalonians"
# "Song of Solomon"
# "Esther (Greek)"
#
BOOKS_SORTED = sorted(
    BOOKS,
    key=len,
    reverse=True,
)


# ============================================================
# BOOK HEADER DETECTION
# ============================================================

def detect_book_header(line):
    """
    Detect running PDF headers such as:

        Genesis 5:18
        1 Corinthians 1:1
        Esther (Greek) 8:14
        Philemon 1
        Jude 1
        Psalm 151 1
    """

    line = line.strip()

    for book in BOOKS_SORTED:

        prefix = book + " "

        if not line.startswith(prefix):
            continue

        remainder = line[len(prefix):].strip()

        match = re.fullmatch(
            r"(\d+)(?::(\d+))?",
            remainder
        )

        if not match:
            continue

        chapter = int(match.group(1))

        if match.group(2):
            header_verse = int(match.group(2))
        else:
            header_verse = 1

        return book, chapter, header_verse

    return None


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Normalize whitespace while preserving the actual Bible text.
    """

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# VERSE LINE DETECTION
# ============================================================

def detect_verse_start(line, expected_verse):
    """
    Detect a verse at the START of a line.

    Handles both:

        16 Cain left Yahweh's presence...

    and:

        16Cain left Yahweh's presence...

    The important safety mechanism is that the detected verse
    MUST equal the expected next verse.

    This prevents ordinary numbers inside Bible text from being
    interpreted as verse numbers.
    """

    line = line.strip()

    if not line:
        return None

    # --------------------------------------------------------
    # Number at beginning of line.
    #
    # Examples:
    #
    # 1 In the beginning...
    # 16Cain left...
    # 17 Cain knew...
    #
    # --------------------------------------------------------

    match = re.match(
        r"^(\d{1,3})(?:\s*)(.*)$",
        line
    )

    if not match:
        return None

    verse_number = int(
        match.group(1)
    )

    verse_text = match.group(2).strip()

    if verse_number != expected_verse:
        return None

    if not verse_text:
        return None

    return verse_number, verse_text


# ============================================================
# MAIN PARSER
# ============================================================

def parse_bible():

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"\nBible PDF not found:\n"
            f"{PDF_PATH}\n\n"
            f"Make sure English_Bible.pdf is inside:\n"
            f"data/bible/\n"
        )

    print(f"PDF: {PDF_PATH}")
    print()

    pdf = pymupdf.open(
        PDF_PATH
    )

    records = []

    current_book = None
    current_chapter = None
    current_verse = None
    current_text = []

    books_seen = []

    # ========================================================
    # SAVE CURRENT VERSE
    # ========================================================

    def save_current():

        nonlocal current_verse
        nonlocal current_text

        if (
            current_book is None
            or current_chapter is None
            or current_verse is None
        ):
            return

        text = clean_text(
            " ".join(current_text)
        )

        if not text:
            return

        records.append(
            {
                "tradition": "bible",

                "book": current_book,

                "chapter": current_chapter,

                "verse": current_verse,

                "text": text,

                "source": (
                    f"{current_book} "
                    f"{current_chapter}:"
                    f"{current_verse}"
                ),

                "translation": "World English Bible",
            }
        )

        current_verse = None
        current_text = []

    # ========================================================
    # PROCESS PDF PAGES
    # ========================================================

    for page_number, page in enumerate(
        pdf,
        start=1
    ):

        raw_text = page.get_text(
            "text"
        )

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        if len(lines) < 3:
            continue

        # ====================================================
        # RUNNING PAGE HEADER
        # ====================================================

        header = detect_book_header(
            lines[0]
        )

        if header:

            book, chapter, header_verse = header

            # ------------------------------------------------
            # BOOK CHANGE
            # ------------------------------------------------

            if current_book != book:

                save_current()

                current_book = book
                current_chapter = None
                current_verse = None
                current_text = []

                if book not in books_seen:

                    books_seen.append(
                        book
                    )

                    print(
                        f"✓ {len(books_seen):02d}. "
                        f"{book}"
                    )

            # ------------------------------------------------
            # CHAPTER CHANGE
            # ------------------------------------------------
            #
            # IMPORTANT:
            #
            # The page header can already show the next
            # chapter while the actual content still begins
            # with the previous chapter.
            #
            # Therefore:
            #
            # SAVE previous verse FIRST
            # THEN change chapter.
            #
            # ------------------------------------------------

            elif current_chapter != chapter:

                save_current()

            current_chapter = chapter

        # ====================================================
        # REMOVE RUNNING HEADERS
        # ====================================================

        # lines[0] = left running header
        # lines[1] = printed page number
        # lines[2] = right running header

        content_lines = lines[3:]

        # ====================================================
        # PROCESS CONTENT
        # ====================================================

        for line in content_lines:

            # ------------------------------------------------
            # FOOTNOTES
            # ------------------------------------------------

            if re.match(
                r"^[†‡§*]",
                line
            ):
                continue

            # ------------------------------------------------
            # CHAPTER MARKER
            # ------------------------------------------------
            #
            # In this PDF a standalone number represents
            # a chapter transition:
            #
            # 6
            #
            # followed by:
            #
            # 1 In the beginning...
            #
            # ------------------------------------------------

            if re.fullmatch(
                r"\d{1,3}",
                line
            ):

                chapter_number = int(line)

                # Only switch chapters when it is actually
                # different from the current chapter.

                if (
                    current_chapter != chapter_number
                    and current_verse is not None
                ):

                    save_current()

                current_chapter = chapter_number

                continue

            # ------------------------------------------------
            # DETERMINE EXPECTED VERSE
            # ------------------------------------------------

            if current_verse is None:

                expected_verse = 1

            else:

                expected_verse = (
                    current_verse + 1
                )

            # ------------------------------------------------
            # VERSE DETECTION
            # ------------------------------------------------

            verse_result = detect_verse_start(
                line,
                expected_verse
            )

            if verse_result:

                verse_number, verse_text = (
                    verse_result
                )

                # Save previous verse first.

                save_current()

                # Start new verse.

                current_verse = verse_number

                current_text = [
                    verse_text
                ]

                continue

            # ------------------------------------------------
            # WRAPPED CONTINUATION
            # ------------------------------------------------

            if current_verse is not None:

                current_text.append(
                    line
                )

    # ========================================================
    # SAVE FINAL VERSE
    # ========================================================

    save_current()

    pdf.close()

    return records, books_seen


# ============================================================
# VALIDATION
# ============================================================

def validate(
    records,
    books_seen
):

    errors = []

    # ========================================================
    # BOOK COUNT
    # ========================================================

    if len(books_seen) != len(BOOKS):

        errors.append(
            f"Expected {len(BOOKS)} books, "
            f"found {len(books_seen)}."
        )

    # ========================================================
    # MISSING BOOKS
    # ========================================================

    missing_books = [
        book
        for book in BOOKS
        if book not in books_seen
    ]

    if missing_books:

        errors.append(
            f"Missing books: {missing_books}"
        )

    # ========================================================
    # EXTRA / UNKNOWN BOOKS
    # ========================================================

    unknown_books = [
        book
        for book in books_seen
        if book not in BOOKS
    ]

    if unknown_books:

        errors.append(
            f"Unknown books: {unknown_books}"
        )

    # ========================================================
    # GROUP BY BOOK + CHAPTER
    # ========================================================

    grouped = {}

    for record in records:

        key = (
            record["book"],
            record["chapter"]
        )

        grouped.setdefault(
            key,
            []
        ).append(
            record["verse"]
        )

    # ========================================================
    # VALIDATE CHAPTERS + VERSES
    # ========================================================

    for book in BOOKS:

        book_chapters = sorted(
            {
                chapter
                for (
                    record_book,
                    chapter
                ) in grouped.keys()
                if record_book == book
            }
        )

        if not book_chapters:
            continue

        # ----------------------------------------------------
        # Chapters should start at 1 and be continuous.
        # ----------------------------------------------------

        expected_chapters = list(
            range(
                1,
                max(book_chapters) + 1
            )
        )

        if book_chapters != expected_chapters:

            errors.append(
                f"Chapter sequence error in "
                f"{book}: found {book_chapters}"
            )

        # ----------------------------------------------------
        # Verse validation
        # ----------------------------------------------------

        for chapter in book_chapters:

            verses = grouped[
                (book, chapter)
            ]

            # Remove duplicates while preserving order.

            unique_verses = list(
                dict.fromkeys(
                    verses
                )
            )

            if not unique_verses:

                errors.append(
                    f"No verses found in "
                    f"{book} {chapter}"
                )

                continue

            # Chapter must start with verse 1.

            if unique_verses[0] != 1:

                errors.append(
                    f"Verse sequence error in "
                    f"{book} {chapter}: "
                    f"starts with "
                    f"{unique_verses[:10]}"
                )

                continue

            # Must be continuous.

            expected = list(
                range(
                    1,
                    max(unique_verses) + 1
                )
            )

            if unique_verses != expected:

                errors.append(
                    f"Verse sequence error in "
                    f"{book} {chapter}: "
                    f"found "
                    f"{unique_verses[:20]}"
                )

    # ========================================================
    # EMPTY TEXT
    # ========================================================

    empty_text = [
        record["source"]
        for record in records
        if not record["text"].strip()
    ]

    if empty_text:

        errors.append(
            f"Empty verse text found: "
            f"{empty_text[:10]}"
        )

    # ========================================================
    # REQUIRED FIELDS
    # ========================================================

    required_fields = {
        "tradition",
        "book",
        "chapter",
        "verse",
        "text",
        "source",
        "translation",
    }

    for index, record in enumerate(records):

        missing = [
            field
            for field in required_fields
            if field not in record
        ]

        if missing:

            errors.append(
                f"Record {index} missing fields: "
                f"{missing}"
            )

    # ========================================================
    # DUPLICATE SOURCE REFERENCES
    # ========================================================

    sources = [
        record["source"]
        for record in records
    ]

    duplicate_sources = sorted(
        {
            source
            for source in sources
            if sources.count(source) > 1
        }
    )

    if duplicate_sources:

        errors.append(
            f"Duplicate verse references: "
            f"{duplicate_sources[:10]}"
        )

    # ========================================================
    # CHECK RECORD ORDER
    # ========================================================

    for i in range(
        1,
        len(records)
    ):

        previous = records[i - 1]
        current = records[i]

        # Different book: okay.
        if previous["book"] != current["book"]:
            continue

        # Same book, different chapter.
        if previous["chapter"] != current["chapter"]:

            if current["chapter"] < previous["chapter"]:

                errors.append(
                    f"Book order error near "
                    f"{current['source']}"
                )

            continue

        # Same book + chapter.
        if current["verse"] != previous["verse"] + 1:

            errors.append(
                f"Record order error near "
                f"{current['source']}"
            )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    if errors:

        print()
        print("=" * 60)
        print("VALIDATION FAILED")
        print("=" * 60)
        print()

        for error in errors:

            print(
                "✗",
                error
            )

        raise SystemExit(1)

    print()
    print("=" * 60)
    print("VALIDATION PASSED")
    print("=" * 60)

    print(
        f"✓ Books: {len(books_seen)}"
    )

    print(
        f"✓ Verses: {len(records)}"
    )

    print(
        "✓ Every chapter has sequential verses"
    )

    print(
        "✓ No empty verse text"
    )

    print(
        "✓ No duplicate verse references"
    )

    print(
        "✓ Required fields present"
    )

    print(
        "✓ Record order is valid"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("WORLD ENGLISH BIBLE → JSON")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    records, books_seen = parse_bible()

    # --------------------------------------------------------
    # Validate BEFORE saving
    # --------------------------------------------------------

    validate(
        records,
        books_seen
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        f"✓ Saved: {OUTPUT_PATH}"
    )

    print(
        f"✓ Total records: "
        f"{len(records)}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()