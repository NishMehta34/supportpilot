# Screenshot checklist (macOS)

Capture with `Shift + Command + 4` and save into `docs/screenshots/` (create the folder first). Review each screenshot for secrets and personal data before committing.

Suggested files (capture yourself; no images are fabricated in this package):
1. `docs/screenshots/login.png` — SupportPilot local login screen.
2. `docs/screenshots/threads.png` — Conversation list and placeholder chat.
3. `docs/screenshots/ticket-draft.png` — Draft awaiting explicit confirmation.
4. `docs/screenshots/ticket-confirmed.png` — Confirmed ticket.
5. `docs/screenshots/tests.png` — Terminal showing real test output.

After taking screenshots, embed only files that exist:
```markdown
![SupportPilot browser](docs/screenshots/threads.png)
```

Do not commit screenshots containing passwords, JWTs, real customer records or unrelated desktop notifications.
