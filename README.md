# Internship Application Agent

This project automates the processing of internship application approval emails.

The workflow receives emails from Gmail, checks whether the sender domain is allowed, analyzes the email intent, signs valid internship application PDFs, and replies automatically with the signed PDF.

## Tools and Technologies Used

- **n8n**: Runs the automation workflow.
- **Gmail / Google OAuth**: Receives internship application emails and sends automated replies.
- **Groq API**: Classifies email intent using an OpenAI-compatible credential.
- **Coolify**: Hosts the PDF Signer service.
- **FastAPI**: Provides the PDF Signer API.
- **Python**: Implements the PDF signing logic.
- **Docker**: Containerizes the PDF Signer service.
- **GitHub**: Stores the source code, documentation, and exported n8n workflow.
- **Swagger / OpenAPI Docs**: Documents and verifies the PDF Signer API endpoints.

## Final Architecture

```text
Gmail
  ↓
Provided n8n server
  ↓
Coolify PDF Signer service
  ↓
Gmail reply with signed PDF
```

The n8n workflow runs on the provided n8n server.

Coolify is used only for the PDF Signer service.

## Workflow Overview

The workflow performs these main steps:

1. Receives a new email through Gmail.
2. Extracts the email subject, body, sender, and attachments.
3. Checks whether the sender domain is allowed.
4. Uses Groq to classify the email intent.
5. Continues only for internship application approval requests.
6. Checks whether a PDF attachment exists.
7. Sends the PDF and signature image to the PDF Signer API.
8. Replies to the original email with the signed PDF.

If the PDF is missing, the workflow replies asking for the PDF form.

If the email is unrelated or the sender domain is not allowed, the workflow does not continue with PDF signing.

## PDF Signer Service

The PDF Signer service is deployed on Coolify.

Public API documentation:

```text
https://ummu-internship-pdf-signer.codewithpeter.com/docs#/
```

Signing endpoint used by n8n:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/sign
```

The `/sign` endpoint accepts:

- `pdf`
- `signature_image`
- optional keyword or coordinate parameters

It returns the signed PDF as a binary file.

## Deployment Notes

The final deployment uses:

- The provided n8n server for the workflow.
- Coolify only for the PDF Signer service.
- Dockerfile-based deployment for the PDF Signer.
- Gmail and Groq credentials configured directly inside n8n.

The `docker-compose.yml` file is simplified and only contains the PDF Signer service for local development.

## Testing Summary

The following scenarios were tested:

- Valid internship approval request with PDF: signed PDF reply sent.
- Valid internship approval request without PDF: missing PDF reply sent.
- Unrelated email: no reply sent.
- Non-allowed sender domain: workflow stopped and no reply sent.

The main end-to-end test confirms that the workflow receives an internship approval email, signs the attached PDF, and replies with the signed file.

## Repository Contents

```text
README.md
TEST.md
.env.example
docker-compose.yml
internship-agent-workflow.json
pdf-signer/
```

## Security Notes

Real API keys, OAuth secrets, access tokens, and personal signature files should not be committed to the repository.

Credentials are configured inside n8n or deployment settings.
