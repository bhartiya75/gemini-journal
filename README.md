# 📔 Personal Gemini Journal

A production-grade, security-first journaling companion built for the
**Google Cloud Gen AI Academy APAC — Ideathon Challenge**.

Sign in, talk through your day with Gemini, save the conversation as a
summarized journal entry — and let **Reflections** surface the patterns you
didn't notice: recurring themes, your mood trend, and one caring insight.

**Live app:** https://gemini-journal-716080261877.us-central1.run.app

## How the required services are used

| Requirement | Implementation |
|---|---|
| **Firebase Authentication** | Email/password sign-in via the Firebase Web SDK; every API call carries the ID token, verified server-side (issuer, audience, expiry) |
| **Gemini API** | Multi-turn journaling chat, entry summarization (structured JSON), and the Reflections insight engine |
| **Cloud Firestore** | Every read/write is rooted at `users/{uid}/…` from the *verified* token — cross-user access is structurally impossible; client-side Firestore access is denied entirely ([firestore.rules](firestore.rules)) |
| **Secret Manager** | The Gemini API key is fetched at runtime by a least-privilege service account — never hardcoded, logged, or committed |
| **Cloud Run** | Single container serves the API + static UI; scales to zero |

## Unique feature — 🪞 Reflections

Most journal apps store your words. Reflections *reads them back to you*:
it analyzes your recent entries (summaries, moods, themes) and returns

- the **3 most recurring themes**, each with a reason,
- a one-line **mood trend** over time,
- one specific, caring **insight** you may not have noticed.

It unlocks after two saved entries and updates as you write.

## Security posture

Built under an AI Studio "constitution" of security custom instructions
written **before any code** — see [constitution.md](constitution.md).
Highlights: token-verified everything, uid only from the verified token,
deny-all client Firestore rules, Secret Manager for keys, least-privilege
IAM (`datastore.user`, `secretmanager.secretAccessor`, `aiplatform.user`),
bounded inputs, fail-closed errors, no payloads in logs.

## Architecture

```
Browser (Firebase Web SDK: sign-in, ID token)
   │  Bearer <ID token>
   ▼
Cloud Run (FastAPI, journal-sa)
   ├─ verify_firebase_token ──► reject if invalid
   ├─ /api/chat        ──► Gemini (key from Secret Manager) + history
   ├─ /api/save        ──► Gemini JSON summary ──► Firestore users/{uid}/entries
   ├─ /api/entries     ──► Firestore users/{uid}/entries
   └─ /api/reflections ──► Gemini over recent entries ──► themes/trend/insight
```

## Run it yourself

```bash
gcloud services enable run.googleapis.com identitytoolkit.googleapis.com \
  firestore.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com

# one-time: Firestore DB, email/password auth, secret, runtime SA (see constitution.md)
printf '%s' "$GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

gcloud run deploy gemini-journal --source=. --region=us-central1 \
  --allow-unauthenticated --service-account journal-sa@PROJECT.iam.gserviceaccount.com \
  --set-env-vars GOOGLE_CLOUD_PROJECT=PROJECT
```

---
Built for #AccelerateAIwithCloudRun · Gen AI Academy APAC Cohort 3
