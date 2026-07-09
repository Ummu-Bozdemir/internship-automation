import argparse
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


DEFAULT_KEYWORDS = [
    "Signature:",
    "Sign here",
    "Signature",
    "İmza:",
    "Imza:",
    "Podpis:",
]


class PdfSignerError(Exception):
    """Base exception for PDF signing errors."""


class InvalidPdfError(PdfSignerError):
    """Raised when the input PDF cannot be opened."""


class InvalidSignatureImageError(PdfSignerError):
    """Raised when the signature image cannot be opened."""


class SignaturePlaceNotFoundError(PdfSignerError):
    """Raised when no signature place can be detected."""


@dataclass
class SignatureMatch:
    page_index: int
    rect: fitz.Rect
    keyword: str
    source: str


@dataclass
class SignResult:
    output_path: Path
    page: int
    x: float
    y: float
    width: float
    height: float
    match_count: int
    keyword: Optional[str]
    detection_source: str


def parse_keywords(raw_keywords: Optional[str]) -> list[str]:
    """Parse comma-separated keywords or return default keywords."""
    if not raw_keywords:
        return DEFAULT_KEYWORDS

    keywords = [item.strip() for item in raw_keywords.split(",") if item.strip()]
    return keywords or DEFAULT_KEYWORDS


def _validate_pdf_path(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise InvalidPdfError(f"PDF file does not exist: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise InvalidPdfError("Input file must be a PDF file.")


def _validate_signature_path(signature_path: Path) -> None:
    if not signature_path.exists():
        raise InvalidSignatureImageError(
            f"Signature image file does not exist: {signature_path}"
        )

    if signature_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise InvalidSignatureImageError(
            "Signature image must be a PNG, JPG, or JPEG file."
        )


def _open_signature_image(signature_path: Path) -> Image.Image:
    try:
        image = Image.open(signature_path)
        image.verify()
    except Exception as exc:
        raise InvalidSignatureImageError("Signature image is invalid or corrupted.") from exc

    return Image.open(signature_path)


def find_text_matches(
    document: fitz.Document,
    keywords: Iterable[str],
) -> list[SignatureMatch]:
    """Find signature keyword matches in a text-based PDF."""
    matches: list[SignatureMatch] = []

    for page_index in range(document.page_count):
        page = document.load_page(page_index)

        for keyword in keywords:
            rectangles = page.search_for(keyword)
            for rect in rectangles:
                matches.append(
                    SignatureMatch(
                        page_index=page_index,
                        rect=rect,
                        keyword=keyword,
                        source="text",
                    )
                )

    return matches


def find_ocr_matches(
    pdf_path: Path,
    keywords: Iterable[str],
    dpi: int = 200,
) -> list[SignatureMatch]:
    """
    Try to find signature keywords using OCR.

    This is a fallback for scanned/image-based PDFs. The returned coordinates
    are approximate, because OCR operates on rendered page images.
    """
    matches: list[SignatureMatch] = []

    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception:
        return matches

    for page_index, image in enumerate(images):
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
        )

        page_width_px, page_height_px = image.size

        for i, text in enumerate(ocr_data.get("text", [])):
            cleaned_text = text.strip()
            if not cleaned_text:
                continue

            for keyword in keywords:
                keyword_words = keyword.replace(":", "").split()
                normalized_keyword = " ".join(keyword_words).lower()
                normalized_text = cleaned_text.replace(":", "").lower()

                if normalized_keyword in normalized_text or normalized_text in normalized_keyword:
                    x_px = float(ocr_data["left"][i])
                    y_px = float(ocr_data["top"][i])
                    w_px = float(ocr_data["width"][i])
                    h_px = float(ocr_data["height"][i])

                    # Convert pixels to PDF points. PyMuPDF uses points, and
                    # rendered images use dpi pixels.
                    x_pt = x_px * 72 / dpi
                    y_pt = y_px * 72 / dpi
                    w_pt = w_px * 72 / dpi
                    h_pt = h_px * 72 / dpi

                    matches.append(
                        SignatureMatch(
                            page_index=page_index,
                            rect=fitz.Rect(
                                x_pt,
                                y_pt,
                                x_pt + w_pt,
                                y_pt + h_pt,
                            ),
                            keyword=keyword,
                            source="ocr",
                        )
                    )

        # Keep OCR fallback simple and fast. We only need the first usable page.
        if matches:
            break

    return matches


def calculate_signature_rect(
    page: fitz.Page,
    base_rect: fitz.Rect,
    width: float,
    height: float,
    manual_x: Optional[float] = None,
    manual_y: Optional[float] = None,
) -> fitz.Rect:
    """
    Calculate where the signature image should be placed.

    If manual coordinates are provided, they are used directly.
    Otherwise the signature is placed near the detected keyword.
    """
    page_rect = page.rect

    if manual_x is not None and manual_y is not None:
        x0 = manual_x
        y0 = manual_y
    else:
        # Place the signature to the right of the keyword. If there is not
        # enough horizontal space, place it below the keyword.
        x0 = base_rect.x1 + 20
        y0 = max(base_rect.y0 - 10, 0)

        if x0 + width > page_rect.width:
            x0 = base_rect.x0
            y0 = base_rect.y1 + 10

    # Auto-shrink if the signature would exceed page boundaries.
    if x0 + width > page_rect.width:
        width = max(page_rect.width - x0 - 10, 20)

    if y0 + height > page_rect.height:
        height = max(page_rect.height - y0 - 10, 20)

    return fitz.Rect(x0, y0, x0 + width, y0 + height)


def sign_pdf(
    pdf_path: str | Path,
    signature_image_path: str | Path,
    output_path: str | Path,
    keywords: Optional[str] = None,
    page: Optional[int] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
    occurrence: int = 1,
    width: float = 160,
    height: float = 60,
    enable_ocr: bool = True,
) -> SignResult:
    """
    Sign a PDF by placing a signature image near a detected signature keyword.

    Page numbers passed by users are 1-based. Internally PyMuPDF uses 0-based
    page indexes.
    """
    pdf_path = Path(pdf_path)
    signature_image_path = Path(signature_image_path)
    output_path = Path(output_path)

    _validate_pdf_path(pdf_path)
    _validate_signature_path(signature_image_path)
    _open_signature_image(signature_image_path)

    parsed_keywords = parse_keywords(keywords)

    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise InvalidPdfError("PDF file is invalid or corrupted.") from exc

    if document.page_count == 0:
        document.close()
        raise InvalidPdfError("PDF file has no pages.")

    manual_coordinates_provided = page is not None and x is not None and y is not None

    if manual_coordinates_provided:
        page_index = page - 1
        if page_index < 0 or page_index >= document.page_count:
            document.close()
            raise InvalidPdfError("Manual page number is outside the PDF page range.")

        selected_page = document.load_page(page_index)
        base_rect = fitz.Rect(x, y, x + 1, y + 1)
        selected_keyword = None
        detection_source = "manual"
        match_count = 0

    else:
        matches = find_text_matches(document, parsed_keywords)

        if not matches and enable_ocr:
            matches = find_ocr_matches(pdf_path, parsed_keywords)

        if not matches:
            document.close()
            raise SignaturePlaceNotFoundError(
                "Signature place was not found. Provide manual page, x and y coordinates."
            )

        if occurrence < 1:
            document.close()
            raise SignaturePlaceNotFoundError("Occurrence must be 1 or greater.")

        if occurrence > len(matches):
            document.close()
            raise SignaturePlaceNotFoundError(
                f"Occurrence {occurrence} was requested, but only {len(matches)} matches were found."
            )

        selected_match = matches[occurrence - 1]
        page_index = selected_match.page_index
        selected_page = document.load_page(page_index)
        base_rect = selected_match.rect
        selected_keyword = selected_match.keyword
        detection_source = selected_match.source
        match_count = len(matches)

    signature_rect = calculate_signature_rect(
        page=selected_page,
        base_rect=base_rect,
        width=width,
        height=height,
        manual_x=x if manual_coordinates_provided else None,
        manual_y=y if manual_coordinates_provided else None,
    )

    try:
        selected_page.insert_image(
            signature_rect,
            filename=str(signature_image_path),
            keep_proportion=True,
            overlay=True,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(output_path)
    finally:
        document.close()

    return SignResult(
        output_path=output_path,
        page=page_index + 1,
        x=signature_rect.x0,
        y=signature_rect.y0,
        width=signature_rect.width,
        height=signature_rect.height,
        match_count=match_count,
        keyword=selected_keyword,
        detection_source=detection_source,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sign a PDF by placing a signature image near a detected signature field."
    )
    parser.add_argument("--pdf", required=True, help="Path to the input PDF file.")
    parser.add_argument(
        "--signature",
        required=True,
        help="Path to the signature image file.",
    )
    parser.add_argument("--out", required=True, help="Path to the output signed PDF.")
    parser.add_argument(
        "--keywords",
        default=None,
        help="Comma-separated list of signature keywords.",
    )
    parser.add_argument("--page", type=int, default=None, help="Manual 1-based page number.")
    parser.add_argument("--x", type=float, default=None, help="Manual X coordinate.")
    parser.add_argument("--y", type=float, default=None, help="Manual Y coordinate.")
    parser.add_argument(
        "--occurrence",
        type=int,
        default=1,
        help="Which detected signature keyword occurrence should be used.",
    )
    parser.add_argument("--width", type=float, default=160, help="Signature width.")
    parser.add_argument("--height", type=float, default=60, help="Signature height.")

    args = parser.parse_args()

    try:
        result = sign_pdf(
            pdf_path=args.pdf,
            signature_image_path=args.signature,
            output_path=args.out,
            keywords=args.keywords,
            page=args.page,
            x=args.x,
            y=args.y,
            occurrence=args.occurrence,
            width=args.width,
            height=args.height,
        )
    except PdfSignerError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    print("PDF signed successfully.")
    print(f"Output: {result.output_path}")
    print(f"Page: {result.page}")
    print(f"Position: x={result.x:.2f}, y={result.y:.2f}")
    print(f"Size: width={result.width:.2f}, height={result.height:.2f}")
    print(f"Detection source: {result.detection_source}")
    print(f"Keyword: {result.keyword}")
    print(f"Total matches: {result.match_count}")


if __name__ == "__main__":
    main()