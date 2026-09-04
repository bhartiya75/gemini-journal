# From Academy to Ideathon: Building a Secure Personal Gemini Journal on Google Cloud

I had the privilege of participating in the **Google Cloud Gen AI Academy —
APAC Edition (Cohort 3)**, a challenge-based program run by Google Cloud with
Hack2skill. After completing the Academy phase — the Cloud Run track,
codelabs, and quizzes — I took on its capstone: the **Ideathon Challenge**.

Here is that journey, in STAR form.

## ⭐ Situation

The Ideathon brief was refreshingly honest about a real industry problem:
most AI-generated apps look great in a demo and fall apart in production —
hardcoded API keys, no authentication boundaries, one shared database with
zero isolation between users.

The challenge: configure **Google AI Studio to think like a security
engineer before writing a single line of code**, then use it to ship a real,
production-grade application — the *Personal Gemini Journal*.

## 🎯 Task

Build an authenticated journaling web app where users sign in, brainstorm or
journal with Gemini, and have conversations automatically summarized and
saved — meeting four non-negotiable requirements:

1. **User authentication** via Firebase
2. **Multi-turn AI interaction** with the Gemini API
3. **User-isolated data storage** in Cloud Firestore — zero cross-user leakage
4. **Secure key management** via Google Cloud Secret Manager — never hardcoded

…deployed on **Cloud Run**, plus at least **one original feature** beyond the
base spec.

## 🔨 Action

**Phase 1 — the constitution.** Before any code, I wrote security custom
instructions for AI Studio: assume hostile browsers, ID-guessing users,
public source code, and readable logs. Every build that followed was bound
by it (it ships in the repo as `constitution.md`).

**Phase 2 — the build.** A single FastAPI container on Cloud Run serving
both the API and the UI:

- **Auth everywhere.** Every endpoint verifies the Firebase ID token
  server-side (issuer, audience, expiry). The uid used for storage comes
  *only* from the verified token — never from the request body.
- **Structural isolation.** Every Firestore path is rooted at
  `users/{uid}/…`. Cross-user reads aren't filtered out — they're
  impossible to express. Client-side Firestore access is denied entirely.
- **No secrets in code.** The Gemini API key is fetched at runtime from
  Secret Manager by a least-privilege service account (exactly three roles).
- **Fail closed.** Verification failure returns an error — never a degraded
  anonymous mode.

The journaling flow: chat with Gemini through your day; one click on **Save
entry** has Gemini distill the conversation into a structured entry —
summary, one-word mood, theme tags — persisted to your own Firestore subtree.

**Phase 3 — the original feature: 🪞 Reflections.** Journals store your
words; Reflections reads them back to you. Gemini analyzes your recent
entries and returns the **3 most recurring themes** (with reasons), a
**mood trend** across time, and **one caring insight** you probably hadn't
noticed. In testing it caught something real: *"periods of relief are brief
before new pressures emerge — you may not be allowing full recovery."*
That's what a good friend notices.

## 🏁 Result

A working, production-grade app — live on Cloud Run, scaling to zero:

- **Live app:** https://gemini-journal-716080261877.us-east1.run.app
- **Code + constitution:** https://github.com/bhartiya75/gemini-journal

*(screenshot: sign-in and chat)*

*(screenshot: the Reflections card)*

All four core requirements verified end-to-end: unauthenticated requests are
rejected (401), multi-turn context carries across the conversation, every
entry lands in the caller's own isolated subtree, and the key never appears
in code, logs, or git history.

**What stayed with me:**

1. **Write the constitution first.** Security directives before code changed
   the shape of the code — verification wasn't bolted on, it was the skeleton.
2. **Structural isolation beats filtered isolation.** When the uid comes from
   the verified token and every path starts at `users/{uid}`, there is no
   query a user can write that touches someone else's journal.
3. **Ship the boring controls.** Secret Manager, least-privilege IAM,
   fail-closed errors — none of it is glamorous, and all of it is the
   difference between a demo and a product.

Grateful to **Google Cloud** and **Hack2skill** for a program that insisted
on production discipline, not just prompts.

*#AccelerateAIwithCloudRun #GoogleCloud #GenAI #CloudRun #Gemini #Firebase*
