Most AI demos die the moment a second user shows up.

Hardcoded keys. No auth boundary. One shared database.

So when the Google Cloud Gen AI Academy — APAC (Cohort 3) Ideathon asked us to make Google AI Studio "think like a security engineer before writing a line of code," I took it literally.

I wrote the security constitution first. Then I built a Personal Gemini Journal on top of it:

🔐 Firebase Authentication — every request carries a verified ID token
🧠 Gemini — multi-turn journaling, plus structured summaries of each session
🗂️ Cloud Firestore — every path rooted at users/{uid}. Cross-user reads aren't filtered out; they're impossible to write
🔑 Secret Manager — the API key never touches code, logs, or git
☁️ Cloud Run — one container, scales to zero

The part I'm proudest of is called Reflections. Journals store your words. This one reads them back to you: recurring themes, your mood trend, and one insight you hadn't noticed.

In testing it told me: "periods of relief are brief before new pressures emerge — are you allowing full recovery?"

That's what a good friend notices.

Biggest lesson: structural isolation beats filtered isolation. When the uid comes from the verified token and every path starts at users/{uid}, there is no query a user can make that touches someone else's journal.

Full write-up (STAR format), live app, and the constitution are in the article below 👇

What's the one security control you'd never ship an AI app without?

#AccelerateAIwithCloudRun #GoogleCloud #GenAI #CloudRun #Gemini
