# Testing Guide

This document describes the manual test scenarios for the Internship Application Agent.

## Prerequisites

Before testing, make sure that:

- Docker Compose is running.
- The n8n workflow is imported and published.
- Gmail credentials are configured in n8n.
- The Groq OpenAI-compatible credential is configured in n8n.
- The local signature image exists at:

```text
assets/signature.png
```

- The signature image is mounted into the n8n container at:

```text
/home/node/.n8n-files/assets/signature.png
```

- The PDF Signer service is available from n8n at:

```text
http://pdf-signer:8000/sign
```

- Test emails are sent from an allowed sender domain.

Allowed domains:

```text
akademiata.edu.pl
wseiz.edu.pl
```

## Notes

The workflow should be tested in published mode. Do not rely only on the manual **Execute workflow** button, because the Gmail Trigger behaves differently in manual and published executions.

After sending each test email, wait for the Gmail Trigger polling interval and then check the n8n **Executions** tab.

---

## Scenario 1: Approval request with PDF attachment

### Purpose

Verify that the workflow detects an internship approval request, finds the attached PDF, signs it, and replies with the signed PDF.

### Test email

Send an email from an allowed domain.

Subject:

```text
Internship application approval request
```

Body:

```text
Hello,

Please process my internship application.

Program: Computer Science
Semester: 4
Company: Example Software House
Internship period: 01.08.2026 - 30.09.2026

I attached the internship application PDF form for approval.

Best regards,
Jane Student
```

Attachment:

```text
sample_internship_form.pdf
```

### Expected n8n path

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
→ Read/Write Files from Disk
→ Merge PDF + Signature
→ Call PDF Signer
→ PDF Signer Success?
→ Reply With Signed PDF
```

### Expected result

- Workflow execution succeeds.
- A reply email is sent.
- The reply contains a signed PDF attachment.
- The signed PDF contains the signature image.

---

## Scenario 2: Unrelated email

### Purpose

Verify that unrelated academic emails are ignored and do not receive an automatic reply.

### Test email

Send an email from an allowed domain.

Subject:

```text
Question about the class schedule
```

Body:

```text
Hello,

Could you please provide information about this semester's class schedule and weekly timetable?

Thank you.
```

No attachment is required.

### Expected n8n path

```text
Gmail Trigger
→ Extract Email Context
→ Allowed Domain?
→ OpenAI Intent Analysis
→ Normalize Intent
→ Approval Request?
→ Log Other Topic
```

### Expected result

- Workflow execution succeeds.
- Intent is normalized as:

```text
other
```

- No Gmail reply is sent.

---

## Scenario 3: Approval request without PDF attachment

### Purpose

Verify that an approval request without a PDF is still recognized as an approval request, but receives a missing PDF reply.

### Test email

Send an email from an allowed domain.

Subject:

```text
Internship application approval request
```

Body:

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

No attachment.

### Expected n8n path

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

### Expected result

- Workflow execution succeeds.
- Intent is normalized as:

```text
approval_request
```

- A reply email is sent.
- The reply asks the sender to send the internship application form as a PDF attachment.
- No signed PDF is sent.

---

## Expected production behavior

The workflow should only reply automatically when:

- The sender domain is allowed.
- The email is about internship application approval.
- The workflow either signs the attached PDF or asks for the missing PDF.

The workflow should not reply to unrelated emails.