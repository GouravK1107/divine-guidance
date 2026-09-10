import json
import re
from pathlib import Path

import pymupdf


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PDF_PATH = BASE_DIR / "data" / "quran" / "Quran_in_english.pdf"
OUTPUT_PATH = BASE_DIR / "data" / "quran" / "quran.json"


# ============================================================
# QURAN METADATA
# ============================================================

TRADITION = "quran"
BOOK = "Quran"

TRANSLATION_NAME = "Itani & AI"
TRANSLATION_ATTRIBUTION = "Translation by Itani & AI"
TRANSLATION_LICENSE = "CC BY-NC-ND"


# ============================================================
# SURAH NAMES
# ============================================================

SURAH_NAMES = [
    "Al Fatihah",
    "Al Baqarah",
    "Ali Imran",
    "An Nisa",
    "Al Maidah",
    "Al Anam",
    "Al Araf",
    "Al Anfal",
    "Al Tawbah",
    "Yunus",
    "Hud",
    "Yusuf",
    "Ar Rad",
    "Ibrahim",
    "Al Hijr",
    "An Nahl",
    "Al Isra",
    "Al Kahf",
    "Maryam",
    "Ta Ha",
    "Al Anbiya",
    "Al Hajj",
    "Al Muminun",
    "An Nur",
    "Al Furqan",
    "Al Shuara",
    "An Naml",
    "Al Qasas",
    "Al Ankabut",
    "Ar Rum",
    "Luqman",
    "As Sajdah",
    "Al Ahzab",
    "Saba",
    "Fatir",
    "Ya Seen",
    "As Saffat",
    "Saad",
    "Az Zumar",
    "Ghafir",
    "Fussilat",
    "Al Shura",
    "Az Zukhruf",
    "Ad Dukhan",
    "Al Jathiyah",
    "Al Ahqaf",
    "Muhammad",
    "Al Fath",
    "Al Hujurat",
    "Qaf",
    "Adh Dhariyat",
    "At Tur",
    "An Najm",
    "Al Qamar",
    "Ar Rahman",

    # FIXED
    "Al Waqiah",
    "Al Hadid",
    "Al Mujadalah",
    "Al Hashr",
    "Al Mumtahina",
    "As Saff",
    "Al Jumuah",
    "Al Munafiqun",
    "At Taghabun",
    "At Talaq",
    "At Tahrim",
    "Al Mulk",
    "Al Qalam",
    "Al Haqqah",
    "Al Maarij",
    "Nuh",
    "Al Jinn",
    "Al Muzzammil",
    "Al Muddathir",
    "Al Qiyamah",
    "Al Insan",
    "Al Mursalat",
    "An Naba",
    "An Naziaat",
    "Abasa",

    # FIXED
    "Al Takwir",

    "Al Infitar",
    "Al Mutaffifin",
    "Al Inshiqaq",
    "Al Buruj",

    # FIXED
    "Al Tariq",

    "Al Ala",
    "Al Ghashiyah",
    "Al Fajr",
    "Al Balad",

    # FIXED
    "Al Shams",

    "Al Layl",
    "Ad Duha",
    "Al Sharh",
    "At Tin",
    "Al Alaq",
    "Al Qadr",
    "Al Bayyinah",
    "Al Zalzalah",
    "Al Adiyat",
    "Al Qariah",

    # FIXED
    "Al Takathur",

    "Al Asr",
    "Al Humazah",
    "Al Fil",
    "Quraysh",
    "Al Maun",
    "Al Kawthar",
    "Al Kafirun",
    "An Nasr",
    "Al Masad",
    "Al Ikhlas",
    "Al Falaq",
    "An Nas",
]

# Standard verse counts for all 114 surahs.
EXPECTED_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6
]


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):
    """
    Clean PDF extraction artifacts while preserving wording.
    """

    text = text.replace("\u00ad", "")
    text = text.replace("\u0000", "")

    # Replace weird non-breaking spaces.
    text = text.replace("\u00a0", " ")

    # Remove excessive whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# PDF PARSER
# ============================================================

def parse_pdf():

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"\nPDF not found:\n{PDF_PATH}\n\n"
            "Make sure Quran_in_english.pdf is inside:\n"
            "data/quran/"
        )

    print(f"PDF: {PDF_PATH}")

    doc = pymupdf.open(PDF_PATH)

    records = []

    current_surah = None
    current_ayah = None
    current_text = []

    def save_current_ayah():

        nonlocal current_ayah
        nonlocal current_text

        if current_surah is None:
            return

        if current_ayah is None:
            return

        text = clean_text(" ".join(current_text))

        if not text:
            return

        records.append({
            "tradition": TRADITION,
            "book": BOOK,
            "chapter": current_surah["number"],
            "chapter_name": current_surah["name"],
            "verse": current_ayah,
            "text": text,
            "source": (
                f"Quran "
                f"{current_surah['number']}:"
                f"{current_ayah}"
            ),
            "translation": TRANSLATION_NAME,
            "translation_attribution": TRANSLATION_ATTRIBUTION,
            "translation_license": TRANSLATION_LICENSE,
        })

        current_ayah = None
        current_text = []

    # ========================================================
    # Detect surah headers robustly
    # ========================================================

    def detect_surah_header(lines, index):

        # --------------------------------------------
        # Pattern 1:
        #
        # The Opening
        # 1
        # Al Fatihah
        # --------------------------------------------

        if index + 2 < len(lines):

            number_line = lines[index + 1].strip()
            name_line = lines[index + 2].strip()

            if (
                re.fullmatch(r"\d{1,3}", number_line)
                and 1 <= int(number_line) <= 114
            ):

                number = int(number_line)

                expected_name = SURAH_NAMES[number - 1]

                if (
                    name_line.lower()
                    == expected_name.lower()
                ):
                    return number

        # --------------------------------------------
        # Pattern 2:
        #
        # Sometimes extraction/layout can change.
        # Search for a known surah name followed
        # somewhere nearby by its number.
        # --------------------------------------------

        if index + 1 < len(lines):

            current = lines[index].strip()

            for number, expected_name in enumerate(
                SURAH_NAMES,
                start=1
            ):

                if current.lower() != expected_name.lower():
                    continue

                # Check nearby lines for the number.
                for j in range(
                    index + 1,
                    min(index + 5, len(lines))
                ):

                    candidate = lines[j].strip()

                    if candidate == str(number):
                        return number

        # --------------------------------------------
        # Pattern 3:
        #
        # Some pages have:
        #
        # The Compassionate 55
        # Ar Rahman
        #
        # Number and English title are on the same line.
        # --------------------------------------------

        if index + 1 < len(lines):

            current = lines[index].strip()
            next_line = lines[index + 1].strip()

            for number, expected_name in enumerate(
                SURAH_NAMES,
                start=1
            ):

                if next_line.lower() != expected_name.lower():
                    continue

                # Example:
                # "The Compassionate 55"
                if re.search(
                    rf"\b{number}\b$",
                    current
                ):
                    return number
                
        return None

    # ========================================================
    # Process pages
    # ========================================================

    for page_number in range(11, len(doc)):

        page = doc[page_number]

        raw_text = page.get_text("text")

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        i = 0

        while i < len(lines):

            line = lines[i]

            # =================================================
            # SURAH HEADER DETECTION
            # =================================================

            detected_surah = detect_surah_header(
                lines,
                i
            )

            if detected_surah is not None:

                # Avoid detecting the same surah repeatedly
                # inside its own page content.
                if (
                    current_surah is None
                    or detected_surah
                    != current_surah["number"]
                ):

                    save_current_ayah()

                    current_surah = {
                        "number": detected_surah,
                        "name": SURAH_NAMES[
                            detected_surah - 1
                        ],
                    }

                    current_ayah = None
                    current_text = []

                    print(
                        f"✓ Surah {detected_surah}: "
                        f"{current_surah['name']}"
                    )

                # -----------------------------------------
                # Skip the complete standard header.
                # -----------------------------------------

                if (
                    i + 2 < len(lines)
                    and re.fullmatch(
                        r"\d{1,3}",
                        lines[i + 1]
                    )
                    and lines[i + 1]
                    == str(detected_surah)
                ):

                    i += 3
                    continue

                i += 1
                continue

            # =================================================
            # Repeated subtitle:
            #
            # The Opening • Al Fatihah
            # =================================================

            if current_surah and "•" in line:

                parts = [
                    part.strip().lower()
                    for part in line.split("•")
                ]

                if len(parts) == 2:

                    if (
                        parts[1]
                        == current_surah["name"].lower()
                    ):
                        i += 1
                        continue

            # =================================================
            # Ignore Bismillah
            # =================================================

            if line.lower().startswith(
                "in the name of god, the gracious"
            ):

                i += 1
                continue

            # =================================================
            # AYAH
            # =================================================

            ayah_match = re.match(
                r"^(\d{1,3})\.\s*(.*)$",
                line
            )

            if (
                ayah_match
                and current_surah is not None
            ):

                save_current_ayah()

                current_ayah = int(
                    ayah_match.group(1)
                )

                first_text = (
                    ayah_match.group(2).strip()
                )

                current_text = [first_text]

                i += 1
                continue

            # =================================================
            # AYAH CONTINUATION
            # =================================================

            if current_ayah is not None:

                current_text.append(line)

            i += 1

    # Save final ayah
    save_current_ayah()

    doc.close()

    return records

# ============================================================
# VALIDATION
# ============================================================

def validate(records):

    if not records:
        raise ValueError(
            "No Quran records were extracted."
        )

    print("\nValidating structure...")

    # --------------------------------------------------------
    # Check all 114 surahs exist.
    # --------------------------------------------------------

    chapters = sorted(
        set(record["chapter"] for record in records)
    )

    expected_chapters = list(range(1, 115))

    if chapters != expected_chapters:

        raise ValueError(
            f"Expected chapters 1-114.\n"
            f"Found: {chapters}"
        )

    # --------------------------------------------------------
    # Group records by surah.
    # --------------------------------------------------------

    grouped = {}

    for record in records:

        grouped.setdefault(
            record["chapter"],
            []
        ).append(record)

    # --------------------------------------------------------
    # Validate every surah's verse numbering.
    # --------------------------------------------------------

    for chapter in range(1, 115):

        verses = sorted(
            grouped[chapter],
            key=lambda x: x["verse"]
        )

        actual_numbers = [
            verse["verse"]
            for verse in verses
        ]

        expected_numbers = list(
            range(
                1,
                EXPECTED_COUNTS[chapter - 1] + 1
            )
        )

        if actual_numbers != expected_numbers:

            raise ValueError(
                f"\nVerse validation failed for Surah "
                f"{chapter} ({SURAH_NAMES[chapter - 1]})\n"
                f"Expected: 1-{EXPECTED_COUNTS[chapter - 1]}\n"
                f"Found: {actual_numbers}"
            )

    # --------------------------------------------------------
    # Check empty text.
    # --------------------------------------------------------

    empty_records = [
        record["source"]
        for record in records
        if not record["text"].strip()
    ]

    if empty_records:

        raise ValueError(
            f"Empty text found in: "
            f"{empty_records[:10]}"
        )

    # --------------------------------------------------------
    # Total ayah count.
    # --------------------------------------------------------

    expected_total = sum(EXPECTED_COUNTS)

    if len(records) != expected_total:

        raise ValueError(
            f"\nTotal ayah count mismatch.\n"
            f"Expected: {expected_total}\n"
            f"Extracted: {len(records)}"
        )

    print("✓ 114 surahs detected")
    print(f"✓ {len(records)} ayahs validated")
    print("✓ Verse numbering is sequential")
    print("✓ No empty ayahs")


# ============================================================
# SAVE JSON
# ============================================================

def save_json(records):

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
            records,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\n✓ JSON saved:\n{OUTPUT_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("QURAN PDF PARSER")
    print("=" * 60)

    print("\nExtracting Quran text...")

    records = parse_pdf()

    print(
        f"\nExtracted records: {len(records)}"
    )

    validate(records)

    save_json(records)

    # --------------------------------------------------------
    # Show samples.
    # --------------------------------------------------------

    print("\nSample records:")

    for record in records[:3]:

        print(
            f"\n{record['source']}"
        )

        print(
            record["text"]
        )

    print("\nLast record:")

    print(
        f"{records[-1]['source']}"
    )

    print(
        records[-1]["text"]
    )

    print("\n" + "=" * 60)
    print("QURAN PARSING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()