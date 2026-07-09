from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent
TEST_FILES_DIR = BASE_DIR / "test_files"

PDF_OUTPUT_PATH = TEST_FILES_DIR / "sample_internship_form.pdf"
SIGNATURE_OUTPUT_PATH = TEST_FILES_DIR / "signature.png"


def create_sample_pdf() -> None:
    """Create a simple internship application PDF with a Signature field."""
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(PDF_OUTPUT_PATH), pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, height - 72, "Internship Application Form")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(72, height - 120, "Student name: Jane Student")
    pdf.drawString(72, height - 145, "Student email: jane.student@wseiz.edu.pl")
    pdf.drawString(72, height - 170, "Program: Computer Science")
    pdf.drawString(72, height - 195, "Semester: 4")
    pdf.drawString(72, height - 220, "Company: Example Software House")
    pdf.drawString(72, height - 245, "Internship period: 01.08.2026 - 30.09.2026")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        72,
        height - 295,
        "I request approval for the internship application described above.",
    )

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, height - 360, "Signature:")

    # Draw a line where the signature should appear.
    pdf.line(150, height - 356, 360, height - 356)

    pdf.setFont("Helvetica", 9)
    pdf.drawString(72, 72, "This is a generated test PDF for the PDF Signer API.")

    pdf.save()


def create_signature_image() -> None:
    """Create a transparent PNG signature image for testing."""
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (500, 180), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Simple fake handwritten-looking signature.
    draw.line((40, 120, 120, 70, 190, 120, 280, 60, 430, 105), width=8, fill=(20, 20, 20, 255))
    draw.line((80, 130, 420, 130), width=3, fill=(20, 20, 20, 180))

    image.save(SIGNATURE_OUTPUT_PATH)


def main() -> None:
    create_sample_pdf()
    create_signature_image()

    print("Dummy test files created successfully.")
    print(f"PDF: {PDF_OUTPUT_PATH}")
    print(f"Signature image: {SIGNATURE_OUTPUT_PATH}")


if __name__ == "__main__":
    main()