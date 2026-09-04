# I asked AI Studio to think like a security engineer — then built a journal that reads you back to yourself

*Built for the Google Cloud Gen AI Academy APAC Ideathon · #AccelerateAIwithCloudRun*

Most AI demos die the moment a second user shows up. Hardcoded keys, no auth
boundary, one shared database. The Ideathon challenge was refreshingly blunt
about this: configure Google AI Studio with a security "constitution" *before
writing any code*, then ship something production-grade.

So I built the **Personal Gemini Journal** — and its favorite trick is called
Reflections.

**Live app:** https://gemini-journal-716080261877.us-east1.run.app
**Code:** https://github.com/bhartiya75/gemini-journal

## What it does

You sign in, and talk through your day with Gemini — a warm, short-form
journaling companion that asks one good follow-up question at a time. When
you're done, one click on **Save entry** has Gemini distill the conversation
into a structured journal entry: a 2–3 sentence summary, a one-word mood, and
theme tags. Your raw chat is cleared; the distilled entry persists.

*(screenshot: chat + saved entries)*

## The unique feature: 🪞 Reflections

Journals store your words. Reflections reads them back to you. It analyzes
your recent entries and returns:

- the **3 most recurring themes**, each with a reason,
- a one-line **mood trend** across time,
- one specific, caring **insight** you probably hadn't noticed.

In my test data it caught something real: *"periods of relief are brief
before new pressures emerge — you may not be allowing full recovery."* That's
the kind of thing a good friend notices.

*(screenshot: Reflections card)*

## The security constitution

Phase 1 of the challenge: custom instructions in AI Studio that act as a
constitution for every build. Mine assumes hostile browsers, ID-guessing
users, public source code, and readable logs. The rules that followed:

- **Auth everywhere.** Every endpoint verifies the Firebase ID token
  server-side (issuer, audience, expiry). The uid used for storage comes
  *only* from the verified token — never from the request.
- **Structural isolation.** All Firestore paths are rooted at
  `users/{uid}/…`. Cross-user reads aren't filtered out; they're impossible
  to express. Client-side Firestore access is denied entirely — the only
  path to data is the authenticated API.
- **No secrets in code.** The Gemini API key lives in Secret Manager,
  fetched at runtime by a service account holding exactly three roles.
- **Fail closed.** Verification failure means an error, never a degraded
  anonymous mode.

The full constitution ships in the repo.

## The stack

| Piece | Role |
|---|---|
| Firebase Authentication | email/password sign-in, ID tokens |
| Gemini API | chat, structured summarization, Reflections |
| Cloud Firestore | per-user isolated entries |
| Secret Manager | runtime key retrieval |
| Cloud Run | one container, API + UI, scales to zero |

One FastAPI container. The browser holds only the public Firebase client key
and the user's own token.

## What I learned

1. **Write the constitution first.** Security directives before code changed
   what the code looked like — auth verification wasn't bolted on, it was
   the skeleton.
2. **`hidden` loses to `display:flex`.** My sign-in gate stayed painted over
   a working app because an explicit CSS display beats the HTML `hidden`
   attribute. One `[hidden]{display:none!important}` later, all was well.
3. **Structural isolation beats filtered isolation.** If the uid comes from
   the token and the path starts at `users/{uid}`, there is no query a user
   can make that touches someone else's journal.

---

*Gen AI Academy APAC Cohort 3 · built on Google Cloud*
*#AccelerateAIwithCloudRun*
