# Step 3a journeys

Fresh Reset, clock 10:00am. Earlier journeys stay valid. Exact seed spare minutes may change within the 30 to 70 range.

- **JRN-102** Clean loops
  - steps: Open the Fleet map, then Van 1's and Van 2's pages.
  - expected: Each route is a sensible loop. Stop numbers move steadily around it, with no back-and-forth between areas. The lines follow streets.

- **JRN-103** Demo targets still hold
  - steps: Read Van 2's and Van 4's timelines. Run requests 1, 4 and 8 in Engine test.
  - expected:
    - Van 2 has the Shattuck/51st stop at about 1:50pm, the Telegraph/Ashby stop at about 2:15pm, and about 50 spare minutes.
    - Van 4 ends near Lakeshore and Piedmont around 4pm.
    - Request 1: Van 2, under $4, $11 a visit.
    - Request 4: 4:15pm on Van 4.
    - Request 8: a later delivery that works.

- **JRN-104** Optimize route
  - steps: On a van page, press "Optimize route". Apply if it offers savings, then Undo.
  - expected: It shows "Saves X mi and Y min", or "This is already the shortest order we found". Applying lowers the miles and keeps every arrival inside its window. Undo restores the previous order.

- **JRN-105** Booking keeps quoted times
  - steps: Send request 1's Van 2 option and accept it on the Customer phone.
  - expected: Van 2 is re-optimized only if that's shorter. The new stops arrive within 15 minutes of the quoted time. The quote still shows $11 a visit.

- **JRN-106** Street routing down
  - steps: Block the routing server and open a van page that has no cached lines.
  - expected: Straight lines and the note "Street lines unavailable, showing straight lines." No error.

- **JRN-107** Fast on return
  - steps: Open Van 2, go to Fleet, then open Van 2 again.
  - expected: The second time, the street lines draw within 2 seconds.

- **JRN-108** Earlier flows still work
  - steps: Run Flow A (JRN-81), Undo (JRN-82) and Flow B (JRN-83).
  - expected: Same results as before the re-seed, apart from exact times within a few minutes.
