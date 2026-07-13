# Internship Application Agent

This project is an automated internship application email agent built with n8n, Gmail, Groq, and a custom PDF signer service.

The workflow listens for incoming Gmail messages, checks whether the sender domain is allowed, classifies the email intent with an OpenAI-compatible Groq model, signs internship application PDF forms, and replies to the sender with the signed PDF.

## Features

- Watches incoming Gmail messages with n8n.
- Allows only approved sender domains.
- Uses Groq through an OpenAI-compatible API connection for email intent classification.
- Detects internship application approval requests.
- Ignores unrelated academic or administrative emails.
- Detects missing PDF attachments and replies with a missing-PDF message.
- Signs internship application PDFs using a separate PDF signer service.
- Replies to the original Gmail thread with the signed PDF attached.
- Keeps private credentials, `.env` files, and signature images out of Git.

## Architecture

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ Intent Classification with Groq
→ Normalize Intent
→ Approval Request?
→ Find PDF Attachment
→ Has PDF Attachment?
→ Prepare PDF Binary
→ Read Signature Image from Disk
→ Merge PDF + Signature
→ Call PDF Signer
→ Reply With Signed PDF
```

For approval requests without a PDF attachment:

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ Intent Classification with Groq
→ Normalize Intent
→ Approval Request?
→ Find PDF Attachment
→ Has PDF Attachment?
→ Reply Missing PDF
```

For unrelated emails:

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ Intent Classification with Groq
→ Normalize Intent
→ Approval Request?
→ Log Other Topic
```

## Services

The project uses two main local services:

### n8n

n8n is responsible for:

- Gmail trigger and Gmail replies
- Workflow orchestration
- Domain filtering
- AI intent classification
- Calling the PDF signer service

Local n8n URL:

```text
http://localhost:5678
```

### PDF Signer

The PDF signer is a separate Python/FastAPI service responsible for signing PDF files.

Internal Docker URL used by n8n:

```text
http://pdf-signer:8000/sign
```

The signer expects a `POST` request with two form-data binary fields:

```text
pdf
signature_image
```

The signed PDF is returned to n8n as a binary file.

## Repository structure

```text
.
├── assets/
│   └── .gitkeep
├── email-agent/
├── pdf-signer/
│   ├── main.py
│   ├── sign_pdf.py
│   ├── requirements.txt
│   └── Dockerfile
├── .env.example
├── .gitignore
├── docker-compose.yml
├── internship-agent-workflow.json
├── TEST.md
└── README.md
```

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Ummu-Bozdemir/internship-automation.git
cd internship-automation
```

### 2. Create the local signature image

Create this file locally:

```text
assets/signature.png
```

This file is intentionally ignored by Git because it is private.

The Docker Compose setup mounts the local `assets` directory into the n8n container:

```text
/home/node/.n8n-files/assets
```

The n8n workflow reads the signature from:

```text
/home/node/.n8n-files/assets/signature.png
```

### 3. Prepare environment variables

Copy the example environment file if needed:

```bash
cp .env.example .env
```

Do not commit the real `.env` file.

The project uses Groq through an OpenAI-compatible API connection:

```text
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-8b-instant
```

### 4. Start the local services

```bash
docker compose up --build
```

n8n will be available at:

```text
http://localhost:5678
```

### 5. Configure n8n credentials

Inside n8n, configure:

- Gmail OAuth credentials
- Groq as an OpenAI-compatible chat model credential

Groq configuration:

```text
Base URL: https://api.groq.com/openai/v1
Model: llama-3.1-8b-instant
```

### 6. Import the n8n workflow

Import this workflow file into n8n:

```text
internship-agent-workflow.json
```

Then configure the required credentials on the workflow nodes.

### 7. Publish the workflow

The Gmail Trigger should be tested in published mode because manual executions may behave differently from production trigger executions.

## Allowed sender domains

The workflow currently allows emails from these domains:

```text
akademiata.edu.pl
wseiz.edu.pl
```

Emails from other domains should not continue through the approval automation.

## Testing

Manual testing instructions are documented in:

```text
TEST.md
```

The main test scenarios are:

1. Approval request with PDF attachment
2. Unrelated email
3. Approval request without PDF attachment

Expected behavior:

- Approval request with PDF attachment → signed PDF reply
- Unrelated email → no reply
- Approval request without PDF → missing PDF reply

## Security notes

The following files must not be committed:

```text
.env
assets/signature.png
credentials files
OAuth tokens
API keys
```

The repository ignores private signature files with:

```text
assets/*
!assets/.gitkeep
```

Before committing workflow exports, check that no secrets are present in the JSON file.

Example PowerShell check:

```powershell
Select-String -Path .\internship-agent-workflow.json -Pattern "gsk_|sk-|OPENAI_API_KEY|GROQ_API_KEY|GOOGLE_CLIENT_SECRET|GOOGLE_CLIENT_ID|client_secret|access_token|refresh_token|password|token|secret" -CaseSensitive:$false
```

## Current status

Completed:

- Local n8n workflow
- Groq intent classification
- PDF attachment detection
- Signature image loaded from local disk
- PDF signing through the PDF signer service
- Gmail reply with signed PDF
- Missing PDF reply
- Ignore unrelated emails
- Local manual testing
- Workflow export
- Test documentation

## Known limitations and future improvements

- The workflow uses a fixed local signature image.
- The workflow checks sender domains but does not deeply verify SPF, DKIM, or DMARC headers.
- AI-based intent classification can still make mistakes in unusual emails.
- The workflow does not validate the content of the PDF form.
- Production monitoring and alerting are not yet configured.

## Coolify deployment

Coolify access is available, but deployment steps are intentionally not included in this version yet.

Deployment documentation will be added after the local workflow, repository structure, and environment documentation are finalized.