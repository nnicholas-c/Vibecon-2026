# Phase: step20 — Login screen for the demo

Version: step20-1. The user reports a login problem and wants the login screen visible in the demo: the presenter shows it, then presses "Open the demo". No tester; quick checks only.

Found by E3:
- After one "Open the demo", localStorage dp-demo-open makes AuthGate skip the login screen forever; the landing "Open the demo" also skips it (goes straight to Reset + /dispatch).
- Google sign-in from the login screen (origin=signin) REPLACES the shared business Gmail connection (finish_callback replace_one google_conn). Signing in with a personal Google account would disconnect the demo inbox emergentcouriers413@gmail.com.

## Functional requirements
- REQ-1300 [event] When "Open the demo" or "Price a job" is clicked on the landing, the system shall show the login screen (/signin) every time, even if the browser opened the demo before.
- REQ-1301 [event] When "Open the demo" is clicked on the login screen, the system shall run Reset demo data, then open /dispatch (supersedes Task 9's landing button going straight to /dispatch).
- REQ-1302 [event] When "Sign in with Google" on the login screen finishes and a business Gmail connection already exists, the system shall only start the user's session and keep the existing Gmail connection. It shall ask only for openid, email and profile in that case.
- REQ-1303 [event] When "Sign in with Google" on the login screen finishes and no Gmail connection exists, the system shall connect that account's Gmail as today.
- REQ-1304 [always] The system shall keep Settings → Email and Google as the only place that replaces the connected inbox.
- REQ-1305 [unwanted] If Google sign-in fails, then the system shall return to the login screen with "Google sign-in didn't finish. Try again or open the demo." and keep the existing Gmail connection.
- REQ-1306 [event] When the owner signs out, the system shall clear the demo flag and show the login screen.
- REQ-1307 [always] The system shall keep the login screen's look consistent with the light style: square buttons (the "Open the demo" button is currently a pill), ink primary, paper secondary.
