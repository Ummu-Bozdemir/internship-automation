# Testing Guide — Internship Application Agent

This document describes how to test the Internship Application Agent in the final deployment architecture.

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

n8n is not deployed in Coolify. Coolify is used only for the PDF Signer API.

## Services

### n8n

The workflow runs on Piotr's n8n server:

```text
https://steve107-20107.mikrus.cloud
```

The workflow name is:

```text
Internship Application Agent
```

### PDF Signer

The PDF Signer API runs on Coolify.

Public base URL:

```text
http://ummu-internship-pdf-signer.codewithpeter.com
```

Main signing endpoint:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/sign
```

Health/API documentation endpoints:

```text
http://ummu-internship-pdf-signer.codewithpeter.com/docs
http://ummu-internship-pdf-signer.codewithpeter.com/openapi.json
```

## Required n8n Credentials

The workflow requires two credentials configured directly inside Piotr's n8n server.

### Gmail OAuth2 API

Used by:

```text
Gmail Trigger
Reply Missing PDF
Reply With Signed PDF
Reply Manual Review
Add Manual Review Label
```

OAuth Redirect URL used in Google Cloud Console:

```text
https://steve107-20107.mikrus.cloud/rest/oauth2-credential/callback
```

The Gmail account connected to the workflow is:

```text
ummuzdemir@gmail.com
```

### Groq OpenAI-Compatible Credential

Used by:

```text
OpenAI Intent Analysis
```

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

## Allowed Sender Domains

The workflow processes emails only from these domains:

```text
akademiata.edu.pl
wseiz.edu.pl
```

Emails from other domains should be ignored.

## Test Preparation

Before testing:

1. Make sure the PDF Signer is running in Coolify.
2. Make sure the n8n workflow is published.
3. Do not click `Execute workflow` for production/live tests.
4. Send test emails to:

```text
ummuzdemir@gmail.com
```

5. Send test emails from an allowed sender domain:

```text
@akademiata.edu.pl
```

or

```text
@wseiz.edu.pl
```

## Test 1 — Approval Request With PDF

### Purpose

Verify that the workflow detects an approval request with a PDF attachment, signs the PDF using the PDF Signer service, and replies with the signed PDF.

### Sender

Allowed school email account:

```text
@akademiata.edu.pl
```

or

```text
@wseiz.edu.pl
```

### Recipient

```text
ummuzdemir@gmail.com
```

### Subject

```text
Internship application approval request - PDF attached
```

### Body

```text
Hello,

Please process and sign my internship application form.

Program: Computer Science
Semester: 4
Company: Example Software House
Internship period: 01.08.2026 - 30.09.2026

The internship application PDF is attached.

Best regards,
Jane Student
```

### Attachment

Attach a PDF file, for example:

```text
sample_internship_form.pdf
```

### Expected n8n Execution Path

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ OpenAI Intent Analysis
→ Normalize Intent
→ Approval Request?
→ Find PDF Attachment
→ Has PDF Attachment?
→ Prepare PDF Binary
→ Create Signature Binary
→ Merge PDF + Signature
→ Call PDF Signer
→ PDF Signer Success?
→ Reply With Signed PDF
```

### Expected Result

The sender receives a reply with a signed PDF attached.

Expected reply text:

```text
Hello,

Your internship application form has been approved and signed automatically.

Please find the signed PDF attached.

Best regards,
Internship Coordinator
```

The attached PDF should contain the signature image placed in the signature area.

## Test 2 — Approval Request Without PDF

### Purpose

Verify that the workflow detects an approval request without a PDF attachment and asks the sender to send the PDF.

### Sender

Allowed school email account:

```text
@akademiata.edu.pl
```

or

```text
@wseiz.edu.pl
```

### Recipient

```text
ummuzdemir@gmail.com
```

### Subject

```text
Internship application approval request
```

### Body

```text
Hello,

Please process my internship application.

Program: Computer Science
Semester: 4
Company: Example Software House
Internship period: 01.08.2026 - 30.09.2026

I am sending this request for approval, but I forgot to attach the PDF form.

Best regards,
Jane Student
```

### Attachment

Do not attach any file.

### Expected n8n Execution Path

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ OpenAI Intent Analysis
→ Normalize Intent
→ Approval Request?
→ Find PDF Attachment
→ Has PDF Attachment?
→ Reply Missing PDF
```

### Expected Result

The sender receives a reply asking for the missing PDF attachment.

Expected reply text:

```text
Hello,

Thank you for your message. I can see that you are requesting approval of an internship application form, but I could not find a PDF attachment.

Please send the internship application form as a PDF attachment, and I will process it.

Best regards,
Internship Coordinator
```

## Test 3 — Unrelated Email

### Purpose

Verify that the workflow does not reply to emails that are not internship application approval requests.

### Sender

Allowed school email account:

```text
@akademiata.edu.pl
```

or

```text
@wseiz.edu.pl
```

### Recipient

```text
ummuzdemir@gmail.com
```

### Subject

```text
Ders programı hakkında soru
```

### Body

```text
Hello,

I would like to ask about the class schedule for this semester.

Could you please let me know where I can find the timetable?

Best regards,
Jane Student
```

### Attachment

Do not attach any file.

### Expected n8n Execution Path

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ OpenAI Intent Analysis
→ Normalize Intent
→ Approval Request?
→ Log Other Topic
```

### Expected Result

No reply should be sent.

The workflow should finish successfully.

## Test 4 — Ignored Domain

### Purpose

Verify that the workflow ignores emails from domains that are not allowed.

### Sender

A non-school email address, for example:

```text
@gmail.com
```

### Recipient

```text
ummuzdemir@gmail.com
```

### Subject

```text
Internship application approval request
```

### Body

```text
Hello,

Please process my internship application form.

Best regards,
Jane Student
```

### Expected n8n Execution Path

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ Log Ignored Domain
```

### Expected Result

No reply should be sent.

The workflow should not call Groq.

The workflow should not call PDF Signer.

## Notes

For live tests after the workflow is published, do not click:

```text
Execute workflow
```

The published Gmail Trigger should automatically pick up new emails.

Use the n8n `Executions` tab to verify which nodes ran.
