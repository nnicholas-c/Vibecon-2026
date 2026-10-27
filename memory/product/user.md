# User profile

## Who
- Team of three at VibeCon SF 2026 (hackathon, Sat 10:30 to Sun noon, Logistics track).
  - Nicholas: team lead, drives Emergent, hand-checks engine math. Has studied delivery bundling (inserting one more stop into a route at the right price) and opens the pitch with that research.
  - Kevin: AI and agents (Anthropic key, web search test, red-teaming agents, making the Phones panel feel real).
  - Joey: courier interviews, research table, video, submission.
- Very structured: arrived with a full spec, phase prompts, checks, a credit budget (3,000 build credits, 1,000 cap per task) and a schedule.
- Explicitly said: skip anything Clastra-specific, and leave other projects out of the pitch.

## Purpose
- App: Drivepast. Purpose: hackathon demo with a business-style pitch. It's judged on the deployed emergent.host URL plus a recorded video. In the live final a judge reads out an address or types a request on the customer phone and taps Accept.
- Who uses it: the owner/dispatcher of a small courier (2 to 20 vans), non-technical. Drivers and customers only via texts, simulated with "Demo phones". Judges open it directly (no login).

## How they like to work
- Wants phases to roll on automatically, pausing only at the 6pm (after Phase 5) and 11:30pm (after Phase 7) checkpoints.
- Wants a full test after every phase.
- Bug reports in one message: clicked / saw / expected.
- Never restyle or rebuild finished parts unless asked.
- The demo must never depend on an outside service being up.
- Detail level: high and precise. Decision speed: fast (time-boxed weekend).

## AI approach (changed after kickoff)
- No Anthropic or outside API key. They are fine-tuning a Qwen model during the weekend on their own machine, served at an OpenAI-compatible endpoint. Backup is the Emergent universal key, then no-AI keyword parsing and templates.
- They want the app to generate synthetic training data (JSONL, train/test) and to score the model before and after fine-tuning. This is likely a pitch point.
- Asked (kickoff): which serving stack (vLLM, Ollama, llama.cpp)? Answer: not decided yet, so Phase 4 must work with any OpenAI-compatible server. Also asked for a tunnel address so level 1 can be tested.
- Decision before Phase 2: added minutes = extra driving plus stop minutes (picked the recommended option, so the demo shows "a few dollars", not 8 cents).
- Asked (during Phase 2): do Joey's interviews put a regular daily pickup near the $11 floor? (Not answered yet; ask again gently.)
- During Phase 2 they asked for the whole app to feel like phenomenonstudio.com (a design agency site). They pointed at morluto/rea (a reverse-engineering MCP tool) as a way to get there, then picked "builder studies the site directly". The design pass runs with Phase 3. They then confirmed they want "the entire feeling", and then corrected the reference: it's Phenomenon Studio's Haulix logistics dashboard Dribbble shot (dark charcoal, lime accent, dark map hero, pill stat chips), not the studio website. The reference image is saved in design_refs.
- They care about speed: they cut testing to full passes after 2, 5, 6, 7 and before deploy, with quick checks on 3, 4 and 8. They asked whether Kevin can work in parallel (support answered: yes, via a fork or job, sharing credits; I advised keeping one builder on the code).

## v2 reset (Sat, during Phase 4)
- The user sent a full v2 spec that replaces everything. There are no phases now, only an 11-step work list run without approval between steps. They want one line after each step: what's done, what was checked, credits used so far.
- The reframe is "pricing and selling", not dispatch. Dispatch becomes Fleet, with one Fleet assistant instead of per-van agents. New tagline: "Price every job from the van that already drives past."
- AI: Emergent built-in key only (they dropped the own-model-first emphasis: "Our model" stays blank). They want a fast vs strong model comparison, with and without 5 examples. Hand-written test requests are coming by Sat 6pm.
- Deadlines: deploy by Sat 8pm, final deploy by Sun 9:00am. Extras only while more than 600 credits remain.
- They are cost-aware and decisive, and prefer that I proceed without asking.

## v3 (Sat afternoon)
- Pushed back on publishing early: "focus on the app's full functionalities before polishing UI". They noticed the zig-zag routes ("pathing algorithm is non existent").
- They want real Gmail (read requests, reply in thread with Accept/Decline links), Google sign-in with their own OAuth client, and Sheets read via OAuth. Their plan update overrode their own quick answers: one shared Bayline workspace, no email/password, no separate accounts.
- They sometimes answer a question and then send a fuller plan that changes the answers. The latest full plan wins; I state the conflicts I resolved.
- They didn't understand "Deploy" (it's now called Publish in Emergent). Give click-by-click UI steps.

## AI experimenting (Sat, during step 3a routes)
- Asked for the status of OpenAI keys and said they want to experiment more with fine-tuning.
- Status I gave them: there's no personal OpenAI key in the app. GPT-5.5 runs on the Emergent built-in key, which can't fine-tune. The "Our model" slot is blank and accepts any OpenAI-compatible address, model and key. The Training data and Scoring page isn't built yet.
- I told them OpenAI's self-serve fine-tuning is winding down: it's closed to new accounts, existing accounts can start jobs until Jan 6 2027, and gpt-4.1-mini fine-tunes stop working Jan 14 2027.
- I suggested an open Qwen model fine-tuned on Together AI or Fireworks and plugged into "Our model", plus moving Training data and Scoring up.
- Their answer: probably no fine-tuning. They'll use their own external OpenAI API key, zero-shot, with a cheap fast model first, and circle back if it doesn't work. They want to save Emergent credits. They declined moving Training data and Scoring up and declined GPT-6 Luna on the built-in key. They said "chatgpt set up", which might mean a ChatGPT plan rather than API billing, so I flagged the difference.
- Action: queued a builder fix to make the "Our model" slot work with OpenAI's real API, after step 3a (overview V-5a). Done, but not yet confirmed with a real key.
- They added the Google client secret to the preview .env themselves. They asked for a "basic log in screen" plus finishing OAuth and republishing. Their builder was cancelled mid-step 4, so a fresh builder was dispatched. Interpreted login screen: "Sign in with Google" plus a one-click "Open the demo", so judges are never blocked. They'll paste the Google client ID and secret into chat. They want both the preview and live redirect URIs registered. Step 4 (Gmail) has been sent to the builder.

## Testing preference (Sun Oct 25, ~6pm PT)
- Time crunch: run the e2e tester ONLY when the user asks. Builders should also skip their own full tester runs unless asked.
- Oct 25: never rerun full suites; only targeted checks on what changed. Real-Gmail tests must use emergentcourier413@gmail.com (NOT nznicholaschen@gmail.com).
- Oct 25: MORE AUTONOMY. For feature enhancements, don't wait for the user to pick: choose sensible defaults, build the next demo-serving enhancements automatically (vision.md is the filter), chain tasks, and only ask when truly blocked (credentials, account sign-in) or when a choice contradicts the user's own spec. Report briefly after each batch.

- Oct 25: user chose to leave owner actions open (no auth checks): demo visitors can disconnect Google, change Settings and Reset. Don't re-raise.

- Oct 25: user said "stop suggesting". No next-step suggestions, idea lists or extra options; just report what was done and what the user must do.

## Open questions to learn (ask gently during builds)
- Is Drivepast meant to continue after the hackathon (real couriers from Joey's interviews) or demo only?
- What Joey's courier interviews are turning up (real pricing habits, quote turnaround). This could sharpen the demo copy.
