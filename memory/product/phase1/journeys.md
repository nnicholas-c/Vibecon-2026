# Phase 1 journeys

Each journey starts from a fresh "Reset demo data" unless it says otherwise. Times are Pacific.

- **JRN-1** Fleet in the left rail
  - steps: Open the app on a laptop.
  - expected: The left rail shows "Bayline Courier" at the top, "Dispatch" first with a fleet icon, then Van 1 to Van 6. Each van has its color dot, name, nickname (Shattuck loop, Emeryville labs, Oakland legal, Rockridge clinics, SF Financial District, SF Mission Bay) and a status line "N stops, M spare min". N is about 20 and M is between 30 and 70. The six color dots are visibly different. Inbox (count 10), Phones and Settings sit at the bottom. The tagline "Every van gets an agent that sells its own empty minutes." and a fictional owner name are visible. Dispatch is selected.

- **JRN-2** Van 2 has the request 1 gap
  - steps: Click Van 2 and read its timeline.
  - expected: The header shows "Van 2", "Emeryville labs", driver "Dev Patel", about 20 stops and spare minutes between 40 and 60. The timeline lists stops in order with arrival time, customer name, address and window. One stop is on Shattuck Ave near 51st St arriving between 1:40pm and 2:00pm. A later stop is on Telegraph Ave near Ashby Ave arriving between 2:05pm and 2:25pm.

- **JRN-3** Van 4 ends near Lakeshore and Piedmont
  - steps: Click Van 4 and scroll to the end of the timeline.
  - expected: The last stops are near Lakeshore Ave and Piedmont Ave, with arrivals between 3:30pm and 4:30pm. The route returns by 5:00pm.

- **JRN-4** Every seeded route is feasible
  - steps: Open each van's timeline (or read route plans from the API).
  - expected: For all six vans, every planned arrival is inside that stop's window. Each route returns to its end location at or before 5:00pm. Every service time is 3 to 6 minutes and every price is $9 to $14. Vans 5 and 6 start and end at the SoMa lot, and Vans 1 to 4 at the Emeryville depot.

- **JRN-5** Stats row on a unit page
  - steps: Click Van 1, then Van 6, and read the stats row.
  - expected: Each shows cost per stop (dollars), revenue per day (dollars) and on-time rate over 4 weeks (a percentage), with no blank or "NaN" values. Revenue per day equals the sum of that van's stop prices. Van 6's on-time rate is the lowest of the six vans (interpreted).

- **JRN-6** Dispatch table matches the rail
  - steps: Click Dispatch and read the table.
  - expected: Six rows, one per van, with stops, spare minutes, revenue per day and cost per stop. Stops and spare minutes match the left rail status line and each unit page header exactly.

- **JRN-7** Echo chat saves its history
  - steps: Select Van 2, type "hello van 2", press send. Refresh the page and select Van 2 again. Then select Van 3.
  - expected: Van 2's chat shows the owner bubble "hello van 2" followed by "Echo from Van 2: hello van 2" (interpreted copy). After the refresh both bubbles are still there. Van 3's chat has no messages from Van 2 and shows its own 3 suggested prompts.

- **JRN-8** Suggested prompts send
  - steps: Select Van 2 and tap the suggested prompt "Where are your empty minutes today?". Then select Dispatch and look at its prompts.
  - expected: Van 2 shows 3 suggested prompts. Tapping one sends it as the owner's message and the echo reply follows. Dispatch shows 3 different, fleet-level prompts.

- **JRN-9** Empty message can't be sent
  - steps: Select Dispatch, leave the box empty, then type only spaces.
  - expected: The send button stays disabled both times and no message is added.

- **JRN-10** Settings defaults
  - steps: Open Settings.
  - expected: The fields show these defaults:
    - Wage $19.27 per hour, cost per mile $0.76, markup 100%.
    - Floor per recurring visit $11, floor per one-off run $35, market reference $45 to $65, weekdays per month 21.
    - San Francisco 18 mph, East Bay 22 mph, between SF and East Bay 30 mph, bridge 8 minutes, road factor 1.3.
    - Minutes per new stop 4.
    - "Auto-send quotes within my rules" is on.
    - The demo date is today's date and the demo clock is 10:00am.
    - Real texting shows "Off" with a channel and an empty team numbers list.
    - Business type is "Courier".

- **JRN-11** Connection status and demo controls
  - steps: Open Settings and look at connection status and demo controls.
  - expected:
    - There are four status rows ("Our model", "Backup AI (Emergent universal key)", "OpenStreetMap data", "Real texting"), each labeled green "connected" or grey "using fallback".
    - "Our model" reads "Not set up yet". There is no row for web search, and no mention of Anthropic or an Anthropic key anywhere.
    - "Reset demo data" is enabled.
    - "Refresh from OpenStreetMap", "Send request 1 from the customer phone" and "Customer taps Accept" are disabled with "Available in a later step" (interpreted).

- **JRN-12** Settings save and survive a refresh
  - steps: In Settings, change wage to 20, the demo clock to 2:00pm, and add a team number. Save. Refresh the page and reopen Settings.
  - expected: "Saved" appears. After the refresh, wage shows $20.00, the clock shows 2:00pm and the team number is listed. Cost per stop on the Dispatch table is higher than before for every van. Spare minutes are unchanged.

- **JRN-13** Speed change recomputes routes
  - steps: Note Van 2's spare minutes. In Settings change the East Bay speed from 22 to 15 mph and save. Return to Van 2.
  - expected: Van 2's spare minutes are lower than before, and later arrival times on its timeline have moved later. The rail, header and Dispatch table all show the same new spare minutes.

- **JRN-14** Bad Settings input is refused
  - steps: In Settings, clear the wage field and type -5 in cost per mile. Press save.
  - expected: An inline message appears next to each bad field. Nothing is saved: after a refresh the old values are still there.

- **JRN-15** Reset demo restores everything
  - steps: Change wage to 25, add a team number, send a chat message to Van 1, and change the East Bay speed. Open Settings, press "Reset demo data" and confirm "Reset all demo data? This can't be undone.".
  - expected:
    - "Demo data reset" appears within 10 seconds.
    - Settings show the defaults from JRN-10, except the team number, which is still listed.
    - Van 1's chat is empty.
    - Van 2's timeline again matches JRN-2.
    - Inbox shows 10.
    - The demo date is today and the clock is 10:00am.

- **JRN-16** Reset can be cancelled
  - steps: Press "Reset demo data", then cancel the confirmation.
  - expected: Nothing changes. Settings and chat history are as before.

- **JRN-17** Inbox and Phones placeholders
  - steps: Click Inbox, then Phones.
  - expected: Inbox shows a friendly placeholder that mentions 10 requests and "The inbox opens in a later step". Phones shows "Demo phones arrive in a later step". Neither shows an error or JSON (interpreted).

- **JRN-18** Business switcher
  - steps: Open the business switcher at the top of the left rail.
  - expected: It lists "Bayline Courier" only, and selecting it keeps the current view.

- **JRN-19** Phone layout
  - steps: Open the app at 390x844. Use the "List", "Chat" and "Page" tabs. Pick Van 2 from List, then open Chat and Page.
  - expected: Three tabs labeled List, Chat and Page. List shows the rail content. After picking Van 2, Chat shows Van 2's chat and Page shows Van 2's header, timeline and stats. No horizontal scrolling or clipped text on any tab.

- **JRN-20** Seed contents via API
  - steps: Read the API (contract at /api/openapi.json).
  - expected:
    - /api/openapi.json returns 200.
    - There are about 120 stops (about 20 per van).
    - The directory has the 11 businesses from spec section 5 with coordinates and hours.
    - There are about 40 fallback prospects, each within 300 meters of a seeded stop.
    - There are 10 requests, all with status "new", with the spec texts and sources.
    - Run history has 20 weekdays per stop.
    - Most arrivals are between 5 minutes early and 10 minutes late.
    - Every phone number contains 555.

- **JRN-21** Learned service minutes
  - steps: Through the API, compare a stop's planned service minutes with its run-history average and the route plan's departure minus arrival for that stop.
  - expected: The route plan uses the run-history average (within rounding), not the planned value, where they differ.

- **JRN-22** Persistence across restart
  - steps: Send a chat message and change a setting. Restart the backend (or wait and reload later). Reload the app.
  - expected: The chat message and setting are still there, and the seed was not re-created (no duplicate vans or stops).

- **JRN-23** Friendly offline message
  - steps: With the backend unreachable, load or use the app.
  - expected: A friendly "Can't reach Drivepast right now. Try again in a moment." message shows. No raw error text, stack trace or JSON appears anywhere.
