import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from sign_pdf import (
    InvalidPdfError,
    InvalidSignatureImageError,
    PdfSignerError,
    SignaturePlaceNotFoundError,
    sign_pdf,
)


app = FastAPI(
    title="PDF Signer API",
    description="API for placing a signature image into a PDF document.",
    version="1.0.0",
)


def cleanup_temp_directory(temp_dir: Path) -> None:
    """Remove temporary files after the response has been sent."""
    shutil.rmtree(temp_dir, ignore_errors=True)


def validate_uploaded_file(upload: UploadFile, allowed_extensions: set[str]) -> None:
    """Validate uploaded file extension."""
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_FILE_TYPE",
                "message": f"Invalid file type for {filename}. Allowed extensions: {sorted(allowed_extensions)}",
            },
        )


async def save_upload_file(upload: UploadFile, destination: Path) -> None:
    """Save a FastAPI UploadFile to disk."""
    with destination.open("wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Healthcheck endpoint used by deployment platforms."""
    return {"status": "ok"}


@app.post("/sign")
async def sign_endpoint(
    pdf: UploadFile = File(...),
    signature_image: UploadFile = File(...),
    keywords: Optional[str] = Form(default=None),
    x: Optional[float] = Form(default=None),
    y: Optional[float] = Form(default=None),
    page: Optional[int] = Form(default=None),
    occurrence: int = Form(default=1),
    width: float = Form(default=160),
    height: float = Form(default=60),
) -> FileResponse:
    """
    Sign a PDF and return the signed PDF as a binary response.

    Manual coordinates can be provided with page, x and y.
    If they are not provided, the service searches for signature keywords.
    """
    validate_uploaded_file(pdf, {".pdf"})
    validate_uploaded_file(signature_image, {".png", ".jpg", ".jpeg"})

    manual_values = [page is not None, x is not None, y is not None]
    if any(manual_values) and not all(manual_values):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_MANUAL_COORDINATES",
                "message": "Manual signing requires page, x and y together.",
            },
        )

    if occurrence < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_OCCURRENCE",
                "message": "Occurrence must be 1 or greater.",
            },
        )

    if width <= 0 or height <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SIGNATURE_SIZE",
                "message": "Signature width and height must be positive numbers.",
            },
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="pdf-signer-"))

    input_pdf_path = temp_dir / "input.pdf"
    signature_path = temp_dir / f"signature{Path(signature_image.filename or '.png').suffix}"
    output_pdf_path = temp_dir / "signed.pdf"

    await save_upload_file(pdf, input_pdf_path)
    await save_upload_file(signature_image, signature_path)

    try:
        result = sign_pdf(
            pdf_path=input_pdf_path,
            signature_image_path=signature_path,
            output_path=output_pdf_path,
            keywords=keywords,
            page=page,
            x=x,
            y=y,
            occurrence=occurrence,
            width=width,
            height=height,
        )
    except SignaturePlaceNotFoundError as exc:
        cleanup_temp_directory(temp_dir)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "SIGNATURE_PLACE_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc
    except InvalidPdfError as exc:
        cleanup_temp_directory(temp_dir)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_PDF",
                "message": str(exc),
            },
        ) from exc
    except InvalidSignatureImageError as exc:
        cleanup_temp_directory(temp_dir)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SIGNATURE_IMAGE",
                "message": str(exc),
            },
        ) from exc
    except PdfSignerError as exc:
        cleanup_temp_directory(temp_dir)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PDF_SIGNER_ERROR",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        cleanup_temp_directory(temp_dir)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "UNEXPECTED_ERROR",
                "message": "An unexpected error occurred while signing the PDF.",
            },
        ) from exc

    headers = {
        "X-Signature-Page": str(result.page),
        "X-Signature-X": f"{result.x:.2f}",
        "X-Signature-Y": f"{result.y:.2f}",
        "X-Signature-Width": f"{result.width:.2f}",
        "X-Signature-Height": f"{result.height:.2f}",
        "X-Match-Count": str(result.match_count),
        "X-Detection-Source": result.detection_source,
    }

    if result.keyword:
        headers["X-Matched-Keyword"] = result.keyword

    return FileResponse(
        path=output_pdf_path,
        media_type="application/pdf",
        filename="signed.pdf",
        headers=headers,
        background=BackgroundTask(cleanup_temp_directory, temp_dir),
    )