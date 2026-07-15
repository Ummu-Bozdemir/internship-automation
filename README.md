# Internship Application Agent

This project automates the processing of internship application approval emails.

The system receives internship application emails in Gmail, classifies the email intent with Groq, detects PDF attachments, signs the internship application PDF using a deployed PDF Signer API, and replies to the sender automatically.

## Final Architecture

The final architecture is:

```text
Piotr's n8n server (steve107-20107.mikrus.cloud)
→ runs the n8n workflow

Coolify
→ runs only the pdf-signer service

n8n workflow
→ calls the public PDF Signer endpoint over HTTP
```

Important:

```text
n8n is not deployed in Coolify.
Coolify is used only for the PDF Signer API.
```

## What the Workflow Does

The n8n workflow handles four main cases:

1. **Allowed sender + internship approval request + PDF attached**

   The workflow signs the PDF and replies with the signed PDF attached.

2. **Allowed sender + internship approval request + no PDF**

   The workflow replies and asks the sender to send the internship application form as a PDF attachment.

3. **Allowed sender + unrelated email**

   The workflow logs the email topic and does not send a reply.

4. **Non-allowed sender domain**

   The workflow ignores the email and does not call Groq or the PDF Signer.

## Main Components

### n8n Workflow

The workflow runs on Piotr's n8n server:

```text
https://steve107-20107.mikrus.cloud
```

Workflow name:

```text
Internship Application Agent
```

The workflow is responsible for:

```text
Gmail Trigger
→ sender/domain extraction
→ allowed domain check
→ Groq intent classification
→ PDF attachment detection
→ signature binary preparation
→ PDF Signer API call
→ Gmail reply
```

### PDF Signer API

The PDF Signer API runs on Coolify.

Public base URL:

```text
http://ummu-internship-pdf-signer.codewithpeter.com
```

Signing endpoint:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/sign
```

Documentation endpoints:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/docs
http://ummu-internship-pdf-signer.codewithpeter.com/openapi.json
```

The `/sign` endpoint expects a multipart form-data request with:

```text
pdf
signature_image
keywords
```

It returns the signed PDF as a binary file.

## Repository Structure

```text
internship-automation/
├── pdf-signer/
│   ├── Dockerfile
│   ├── main.py
│   ├── sign_pdf.py
│   ├── requirements.txt
│   └── test_files/
├── email-agent/
├── assets/
│   └── .gitkeep
├── internship-agent-workflow.json
├── docker-compose.yml
├── .env.example
├── .gitignore
├── TEST.md
└── README.md
```

## PDF Signer Service

The PDF Signer service is a FastAPI application.

It provides:

```text
GET  /health
GET  /docs
GET  /openapi.json
POST /sign
```

The `/sign` endpoint receives:

```text
pdf: uploaded PDF file
signature_image: uploaded PNG/JPG signature image
keywords: optional signature search keywords
```

If coordinates are not provided, the service searches for signature keywords in the PDF and places the signature image near the detected signature area.

## n8n Workflow Nodes

The workflow contains the following main nodes:

```text
Gmail Trigger
Extract Email Context
Allowed Domain?
Log Ignored Domain
OpenAI Intent Analysis
Normalize Intent
Approval Request?
Log Other Topic
Find PDF Attachment
Has PDF Attachment?
Reply Missing PDF
Prepare PDF Binary
Create Signature Binary
Merge PDF + Signature
Call PDF Signer
PDF Signer Success?
Reply With Signed PDF
Reply Manual Review
Add Manual Review Label
```

## AI Intent Classification

The workflow uses Groq through an OpenAI-compatible credential in n8n.

Credential type:

```text
OpenAI-compatible
```

Base URL:

```text
https://api.groq.com/openai/v1
```

Model:

```text
llama-3.1-8b-instant
```

The workflow classifies emails into:

```text
approval_request
OTHER
```

The workflow includes an additional safety filter in the `Normalize Intent` node so that emails about class schedules, timetables, courses, or exams are treated as `other` even if the model returns a wrong classification.

## Gmail Integration

The workflow uses Gmail OAuth2 credentials inside Piotr's n8n server.

Connected Gmail account:

```text
ummuzdemir@gmail.com
```

OAuth Redirect URL used in Google Cloud Console:

```text
https://steve107-20107.mikrus.cloud/rest/oauth2-credential/callback
```

The Gmail credential is used by:

```text
Gmail Trigger
Reply Missing PDF
Reply With Signed PDF
Reply Manual Review
Add Manual Review Label
```

## Allowed Domains

The workflow only processes emails from these domains:

```text
akademiata.edu.pl
wseiz.edu.pl
```

Emails from other domains are ignored.

## Signature Handling

The workflow does not rely on Piotr's n8n server file system for the signature image.

Instead, the signature image is embedded in the n8n workflow as a base64 string inside the `Create Signature Binary` Code node.

This avoids requiring a local file path such as:

```text
/home/node/.n8n-files/assets/signature.png
```

The `Create Signature Binary` node creates a binary field named:

```text
signature_image
```

The PDF attachment is prepared as:

```text
pdf
```

The `Call PDF Signer` node sends both binary fields to the PDF Signer API.

## Local Development

Local development can be done with Docker Compose.

The local setup may include:

```text
n8n
pdf-signer
local signature assets
test PDF files
```

However, the final deployed architecture is different:

```text
Local development:
n8n + pdf-signer can run locally

Final deployment:
Piotr's n8n server runs the workflow
Coolify runs only pdf-signer
```

## Environment Variables

An example environment file is provided:

```text
.env.example
```

Do not commit real secrets.

Sensitive values such as API keys, OAuth client secrets, tokens, and personal signature images must stay out of Git.

## Testing

Testing instructions are documented in:

```text
TEST.md
```

The main tested scenarios are:

```text
Approval request with PDF
Approval request without PDF
Unrelated email
Ignored sender domain
```

The final live test confirmed that the published n8n workflow automatically processes new emails without manually clicking `Execute workflow`.

## Security Notes

Do not commit:

```text
.env
Google OAuth client secrets
Gmail tokens
Groq API keys
personal signature image files
n8n credential exports
```

The `.gitignore` file excludes local secrets and personal assets.

The personal signature image should not be stored directly in the repository.

## Deployment Summary

### n8n

n8n is already hosted on Piotr's server:

```text
https://steve107-20107.mikrus.cloud
```

The workflow should be imported into this n8n instance and published there.

### PDF Signer

The PDF Signer is deployed on Coolify.

Current public endpoint:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/sign
```

The n8n `Call PDF Signer` HTTP Request node must point to this endpoint.

## Verified Final Status

The following checks were completed successfully:

```text
PDF Signer /docs endpoint works
PDF Signer /openapi.json endpoint works
Groq credential works
Gmail credential works
Approval request with PDF returns signed PDF
Approval request without PDF returns missing PDF reply
Unrelated email sends no reply
Published workflow runs automatically
```

## Notes

This project intentionally keeps the architecture simple:

```text
n8n workflow on Piotr's n8n server
PDF Signer API on Coolify
HTTP connection between them
```

No n8n deployment is required in Coolify.
