---
name: linkedin-daily-post
description: Publish one day of the O&G Engineering Converter LinkedIn campaign — ground the numbers against the live app, build a compact pre-filled share link, generate and capture the annotated graphic as a real PNG, post it to LinkedIn with the image attached, and record the URL in docs/POST.md. Use when asked to draft, prepare, capture the image for, or publish any Day N post from the campaign in docs/POST.md.
---

# Publishing a campaign post

The plan, the per-day sheets, the verified reference values and the tracker all live in
[`docs/POST.md`](../../../docs/POST.md). **That file is the source of truth** — this skill is only
the procedure for turning a day sheet into a live post without rediscovering the traps.

## Hard rules

1. **`https://engineering-converter.com` goes in the post body of every post.** Not only the first
   comment. A reader who never opens the comments still needs to know where the tool lives.
   LinkedIn rewrites it to an `lnkd.in` short link automatically — that is fine, it resolves.
   *(Maintainer instruction, 2026-08-11. The old `unit-converter-oil-gas.vercel.app` domain is
   dead to us — never reintroduce it, in copy, in a share link, or in a graphic footer.)*
2. **Every number must be reproduced against the running app before it is written**, not copied
   from the docs. An adversarial check of the original plan found ten defects, including a wrong
   headline figure.

   Two legitimate exceptions, both with obligations attached:
   - **A figure the app computes but never displays** (Day 4's `dpFric`/`dpStatic`, Day 5's ρ and M,
     Day 6's iteration trace). Take it from the app anyway — wrap `fetch` for API-only values, use
     `win.eval` for `const` bindings, and when you must re-implement a loop, **assert your result
     equals the app's** to full precision before using it.
   - **A figure the app does not compute at all** (Day 6's Haaland and Swamee-Jain comparison).
     Allowed only when the post's argument needs it. Then: say in the post that it is not from the
     tool, and record the formula used in the day sheet so a reader can check it. Never let such a
     number sit next to app output unlabelled.
3. **Look at the rendered image before publishing.** Programmatic checks (values, sizes, arrow
   counts, colours) have all passed on an image that was visibly broken. They are not verification.
4. **Never full-screen capture.** It caught the maintainer's unrelated private windows three times.
   Capture one specific window (see step 4).
5. Publishing is irreversible-ish. Post only when asked, and report exactly what went out.

## Step 1 — Bring the app up and ground the numbers

`vercel dev` cannot run here (no node). Use the Python shim — see [[local-dev-without-vercel]] in
memory; recreate it at `<scratchpad>/devserver.py` if gone. It mounts each `api/*.py` handler on a
loopback port and serves the repo on :8000.

```bash
python devserver.py "<repo root>"    # then http://127.0.0.1:8000/index.html
```

Confirm the pinned vectors before trusting anything: ΔP 176.929 kPa · Re 2.201×10⁵ · f 0.01835 ·
Vₑ 7.689 m/s · flow regime Churn/Slug at θ=+45.0° · PRV gas 5.7047 in² → orifice P ·
JIS HHV 44.59 / WI 56.00 / SG 0.634 / MW 18.305. Run `pytest` too (242 tests).

Drive the client-side JS in a browser tab, not node. Read values from the DOM.

## Step 2 — Build the share link

**Never paste the app's Share button output** — a stock link is 4,627 characters and does not fit a
LinkedIn comment (1,250) or body (3,000).

`applyState()` → `applyInputs()` tolerates a **partial** `inputs` object, so hand-author one with
only the keys the post needs. 10–15 keys lands at ~200–400 characters.

```javascript
const state = { v: 2, tab: 'advanced', inputs: { /* only what this post shows */ } };
// '?s=' for anything you POST — LinkedIn strips the fragment when it auto-links (see below).
location.origin + '/index.html?s=' + btoa(unescape(encodeURIComponent(JSON.stringify(state))))
```

- `tab`: `general` / `basic` / `advanced` / `safety`. Omit to land on General.
- Abs/Gauge modes are **not** in `inputs` — they are top-level `p1` / `p2` (`'abs'` / `'gau'`).
- `lang: 'ja'` only on Japanese content.
- **Test on a real page load.** Changing the fragment alone does not re-run the restore; the page
  must actually load. Clear `localStorage` first so you see what a first-time visitor sees.
- ⚠️ **Use `?s=` for anything posted, not `#s=`.** LinkedIn strips everything after the `#` when
  it auto-links a URL (2026-08-16), so a fragment link renders correctly, looks clickable, and
  restores nothing. `decodeShareState()` accepts `?s=` from the query string precisely so posted
  links work — build campaign links with `'/index.html?s=' + btoa(...)`.
- **The app's own Share button must keep emitting `#s=`.** A fragment never reaches the server; a
  query string lands in access logs. Read `?s=`, never generate it — `tests/test_share_state.py`
  fails if `copyShareLink()` is flipped.
- **After publishing, read the posted anchor's `href`**, not the link you built. They are
  different URLs and only the second one is what readers click.
- Server-backed cards (ΔP, Flow Regime, PRV) still need a Calculate click; client-side cards
  (composition, steam, NPSHa, compressor, gas properties, Z-factor, pipe volume) render on open.

## Step 3 — Build the graphic

Copy `docs/linkedin/day01-mockup.html` as the pattern. It loads `index.html` in an **off-screen
iframe**, drives it with the app's own JavaScript, clones the resulting card, and freezes its
computed styles. **Never re-implement the UI** — the numbers in the image must come from the app.

Frame is 1200 × 675. Keep the footer strip carrying `engineering-converter.com`.

### Ten traps, all of which have bitten

1. **Kill CSS transitions in the iframe first**: `*{transition:none !important;animation:none !important}`.
   Transitions are driven by the compositor's frame clock, so in a non-painting context they never
   advance and `getComputedStyle` returns the **start** value forever. Symptom: the graphic shows
   Abs/Abs while the copy claims barg → psia.
2. **The staging iframe needs a real desktop viewport** (1280 × 1000, parked off-screen at
   `left:-20000px`). At 1 px wide the app renders its mobile layout and every computed width
   collapses — the card baked out 2 px wide.
3. **`setLanguage()` is async and re-renders**, resetting toggles. Set language → wait → then set
   modes and values. Language persists in `localStorage`, so force it explicitly every time or an
   earlier Japanese session silently renders an English graphic in Japanese.
4. **Tailwind's CDN JIT does not style markup injected after load.** Freeze computed styles *inside
   the iframe*, where the app's own build applies. Freezing strips `class`, so tag anything the
   annotation layer must find later — element **IDs survive**, class selectors do not.
5. **Write zero border widths explicitly.** Tailwind's preflight sets `border-style:solid` with
   `border-width:0`; dropping the `0px` as "empty" makes the browser fall back to `medium` and paint
   a 3 px box around every node.
6. **Freeze `transform` and `transform-origin`** — otherwise the frozen copy renders at scale 1.0
   while arrow coordinates were measured at the scaled size, and connectors point at nothing.
7. **`<svg>` is a replaced element**: `position:absolute; inset:0` does not stretch it. It keeps its
   intrinsic 300 × 150 and silently clips connectors. Set explicit `width`/`height` + `viewBox`.
8. **`display:none` must be written out too.** The freeze loop skips values like `none`/`normal`/
   `auto` as noise — but it also strips the `class` that hid the element. Any node the app was
   hiding (`out-liq-warn`, `comp-warn`, any `.hidden`) then *appears*. Day 2 baked two empty amber
   rectangles under the card and every programmatic check passed. Special-case `display`.
   Keep one shared `freezeStyle()` helper — the card snapshot and the standalone export both need
   the fix, and two copies of the loop will drift.

9. **Freeze the CSS Grid properties.** `grid-template-columns` and friends are NOT optional. Tailwind
   writes columns via `md:grid-cols-4`, which is a **media query** — freeze without them and the
   column definition vanishes, every cell stacks into one column, and the frozen widths/heights
   then overlap into an unreadable pile. Days 1–2 used flex cards and never hit it; Day 3's steam
   card is grid and collapsed completely. Freeze at least:
   `grid-template-columns`, `grid-template-rows`, `grid-auto-flow`, `grid-auto-columns`,
   `grid-auto-rows`, `grid-column`, `grid-row`, `row-gap`, `column-gap`, `align-self`, `justify-self`.
   `docs/linkedin/day03-mockup.html` has the complete `STYLE_PROPS` list — copy that one.

10. **`iframe.contentWindow.someHelper` is `undefined` for anything the app declares with `const`.**
    A top-level `const`/`let` binds in the global *lexical* environment and never becomes a property
    of `window` — only `var` and function declarations do. So `win.papayZ(...)` throws and
    `win.MW_AIR_GP` is `undefined`, which silently propagates as `NaN` into every derived figure
    rather than erroring anywhere useful. Day 5 shipped a table of four `NaN`s this way.
    Use `win.eval('(function(){ … })()')` instead — eval runs in the iframe's own scope, where the
    bindings are visible — and return a plain object:

    ```javascript
    var env = win.eval('(function(){'
      + 'var pPsia=toPsia(2000,"psi"), tR=toRankine(150,"F"), pz=papayZ(0.65,pPsia,tR);'
      + 'return {Z:pz.Z, tR:tR, M:0.65*MW_AIR_GP};})()');
    ```

    This matters whenever a figure the graphic needs is **not** in the DOM. Two shapes of that so
    far: an intermediate the card never displays (Day 5's ρ and M), and a value that lives only in
    an API response (Day 4's `dpFric`/`dpStatic` — there, wrap `win.fetch` instead). Either way the
    rule is the same: take it from the app, never re-derive it in the mockup.

Also: **`uppercase` destroys chemistry notation.** A Tailwind `uppercase` on a caption turns
`iC₄`/`nC₄`/`vol%` into `IC₄`/`NC₄`/`VOL%`. Component case is significant; don't uppercase it.

And: **quote what the card DISPLAYS, not the unrounded value in §4.** The Gas Property Estimator
shows `0.01666 cP` where §4 records `0.016663`. A reader who opens the app sees the former; a post
quoting the latter looks wrong. Check the display precision before writing the number down.

## Step 4 — Capture a real PNG

**Use headless Chrome.** The standalone export is self-contained and its frame is exactly
1200 × 675 at the document origin, so the viewport *is* the frame — no title-bar detection, no
crop, no DPI correction:

```bash
chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
       --window-size=1200,675 --screenshot=docs/linkedin/NAME.png <standalone url>
```

**Check the size.** A real capture is 150 KB+; a blank one is ~8 KB. Verify the dimensions too
(`PIL.Image.open(...).size` must be `(1200, 675)`).

> ⚠️ **The old `PrintWindow` recipe is DEAD as of Chrome 151** (verified 2026-08-16). An isolated
> `--app` window plus `PrintWindow(hWnd, hdc, 2)` still *returns success*, but the surface is
> blank — ~11 KB for a 1290 × 820 window — with or without `--disable-gpu`/`--disable-gpu-compositing`,
> and Chrome's render widget is now a 12 × 206 stub, so enumerating child windows does not help.
> This was confirmed against a frame that had captured fine under the old method, so it is the
> browser version and not the generator. Do not spend time re-deriving it.
>
> **Refinement (Day 7, 2026-08-17): the cause is occlusion, not Chrome 151 as such.** Adding
> `--disable-features=CalculateNativeWinOcclusion` (plus
> `--disable-backgrounding-occluded-windows`, `--disable-renderer-backgrounding`) makes
> `PrintWindow` return a full 185 KB frame again — Chrome suspends painting for a window it
> believes is covered, which the capture window always is. **Headless is still the method to
> use**; this is recorded only so the next person does not conclude the machine is broken.
> The tell for occlusion: the byte count is *identical on every retry* (11,612 here), where a
> genuine timing problem varies.

**Still true, and still the reason not to reach for a screen grab:** the in-app Browser pane never
composites frames; the Chrome MCP screenshot does not paint CSS `transform`/`zoom`; `save_to_disk`
keeps the image in extension storage, never the filesystem; canvas export is tainted by
`foreignObject` SVG; and `SetForegroundWindow` is refused from a background process, so
`CopyFromScreen` captures whatever is actually on top — **the maintainer's private windows**.
**Never full-screen capture.**

**Then open the PNG with the Read tool and actually look at it** (rule 3). Programmatic checks pass
on visibly broken images: the v3.3 frame's first capture had every value correct while the
properties panel overlapped and clipped the component grid, the 10 px citation was an unreadable
smear, and ~180 px of the frame was empty. All of that is invisible to an assertion on `data-ready`.

## Step 5 — Publish

Attaching the image: **only the OS clipboard works, and only two things make it land.**

> ### ATTACH THE IMAGE FIRST, INTO AN EMPTY COMPOSER.
> LinkedIn hides the media toolbar (image / document / celebrate / +) as soon as the editor
> overflows its box — and with the toolbar gone, **pasting an image does nothing at all**, silently.
> Type the body first and you cannot attach afterwards. Order is: open composer → paste image →
> *then* type the text. The attachment survives typing; the reverse does not work.
>
> If you have already typed, `ctrl+a` then `Delete` clears the editor and the toolbar comes back.

> ### DO NOT PRESS ESCAPE IN THE COMPOSER.
> It is not a "dismiss the hashtag suggestions" key. LinkedIn reads Escape as *close the composer*
> and raises **"Save this post as a draft?"** mid-compose. Cancel with that dialog's ✕ — **not**
> Discard — and the text and attachment both survive. Nothing needs dismissing anyway: typing a
> newline after a hashtag already commits it.

> ### THE PASTE MUST BE A REAL OS KEYSTROKE.
> A synthetic `ctrl+v` through the browser tool does **not** carry the OS clipboard — the page
> receives a paste event with nothing in it. You must `SetForegroundWindow` the Chrome window and
> `SendKeys("^v")`.
>
> **Guard it, on the window AND the tab.** `SetForegroundWindow` can be refused, and focus reverts
> between PowerShell calls (each call is a new process, and running a tool refocuses the app).
> Activate, re-read `GetForegroundWindow()`, compare it to the target hWnd, **and check the window
> title contains "LinkedIn"** — the title tracks the *active tab*, so it is the only cheap proof
> that LinkedIn is frontmost and not a background tab. Abort if either check fails. Do it all in a
> *single* PowerShell call, with the checks immediately before `SendKeys`.
>
> This is not theoretical: the browser-tool tab is often **not** the active tab (check with
> `document.visibilityState` — "hidden" means a real Ctrl+V goes to whatever tab *is* active).
> On Day 3 the guard caught the maintainer's own PR page in front and refused to paste.
> `SendKeys("^9")` jumps to the window's last tab, which is the one this session created; send it,
> then re-verify before pasting.
>
> **Check whether the maintainer is actually using the machine** before grabbing focus:
> `GetLastInputInfo` gives idle seconds. If it is ~0 they are typing right now — make one atomic,
> fully guarded attempt, and if it fails, stop and hand over rather than fighting for the browser.

> ### DO NOT CALL `ShowWindow(hwnd, 9)`.
> `SW_RESTORE` **un-maximises an already-maximised window.** On Day 5 that shrank Chrome from
> 1550×830 to 1536×442 in the middle of the sequence, which relaid out the composer, dropped the
> editor's DOM focus, and the `^v` went nowhere — the composer stayed empty with the media toolbar
> still showing, which reads exactly like the "toolbar hidden" failure and sends you hunting the
> wrong bug. `SetForegroundWindow` alone is enough to raise the window. If a window does need
> un-minimising, check `IsIconic` first and re-maximise afterwards with `ShowWindow(hwnd, 3)`.
>
> Symptom to recognise: the screenshot after the paste comes back with an odd small viewport
> (e.g. 1522×259 instead of ~1536×639). That is the resize, not a rendering hiccup.

```powershell
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$img = [System.Drawing.Image]::FromFile("<abs path>\dayNN.png")
[System.Windows.Forms.Clipboard]::SetImage($img)   # PowerShell 5.1 is STA, required
$img.Dispose()
# ... same call: SetForegroundWindow($hwnd); verify GetForegroundWindow() -eq $hwnd; SendKeys ^v
```

Find the target window with
`Get-Process chrome | ? { $_.MainWindowTitle -like "*LinkedIn*" }` → `MainWindowHandle`.

⚠️ **Close leftover capture windows first, and never fall back to "first chrome process with a
title".** A capture window carries its own `MainWindowTitle`, so the fallback can select it and
the paste lands in a throwaway window. If the `*LinkedIn*` filter finds nothing it means the
LinkedIn tab is not that window's active tab — send `^9` and re-check, do not widen the filter.

**Re-click the editor before every paste attempt.** DOM focus does not survive a window resize or
a re-raise, and the click is free.

> **The attach is not instant, and the toolbar changes as it lands** — the media icons are replaced
> by the image preview, which looks like the paste failed. **It did not.** Scroll the composer and
> confirm the preview before concluding anything. This exact misreading cost most of a session.

**The composer modal is invisible to the accessibility tree.** `read_page` and `find` return only
the feed behind it, so `ref`-based clicking does not work inside the composer — use screenshot
coordinates there. (Everywhere else, prefer refs.) The *first* click on "Start a post" from the
feed also frequently does nothing; just click it again.

Do not retry these — they are all dead ends: synthetic drag-and-drop (ignored by LinkedIn's
uploader), targeting `<input type="file">` (exists only while the media Editor is open and is hidden
from the accessibility tree, so `file_upload` cannot get a ref), injecting a `File` via
`DataTransfer` (LinkedIn's CSP blocks `connect-src` to localhost), synthetic Ctrl+V without the OS
clipboard.

Composer flow:

1. Feed → **Start a post** (ref click; repeat if the first does nothing).
2. **Paste the image into the still-empty composer** and confirm the preview appears.
3. Click into the text area and type the English body, then the Japanese section. Both languages
   go in **one post** (Day 1 set that pattern); each carries `https://engineering-converter.com`.
4. Scroll the composer to the bottom and **look at** the whole post, image included.
5. Post, then get the tracker URL — see below.
6. Add the pre-filled share link as the **first comment**, *if you want one*. Naoto ruled on
   2026-08-13 that first comments are **optional**: a day is complete once the post is scheduled
   and its URL recorded. Do not treat a missing comment as an outstanding task.
7. Drafts auto-restore if the composer is closed, so a mistake is recoverable.

### Getting the `urn:li:share:` id for the tracker

§2 records `https://www.linkedin.com/feed/update/urn:li:share:<id>/`. **The `urn:li:activity:<id>`
you can scrape off the activity feed is a DIFFERENT number** and does not match that format, so it
cannot be substituted.

**Fastest route — `…` → Embed this post → Copy code.** The clipboard then holds
`<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7493672957697806337?…">`;
regex the urn straight out of it. One dialog, no navigation.

The older route also works: `…` → **Copy link to post** → open the `lnkd.in/p/…` in the tab and read
the resolved URL, whose slug ends `…-share-<id>-…`. It costs an extra page load.

⚠️ **The `…` menu's item positions move.** It has a "Boost" row on some posts and not others, so a
fixed y-coordinate silently lands on the neighbouring item — that is how Day 5 opened *Embed this
post* while aiming for *Copy link to post*. Screenshot the open menu and click what you can see.

### Scheduling instead of posting now

LinkedIn schedules natively: the **clock icon** left of Post. Build the post exactly as above
(image first, then text), then click the clock rather than Post.

- The dialog states the timezone it is using — *"…Japan Standard Time, based on your location"*.
  Read it; do not assume. Get local now with `Get-Date` so you pick the right date.
- **Date**: triple-click the field, type `M/D/YYYY`, then click the day in the calendar that pops
  up — typing alone leaves the old day highlighted.
- **Time**: triple-click, type e.g. `8:00 AM`. The dropdown offers 15-minute steps but filters to
  what you type; click the filtered option to commit it.
- Confirm the summary line re-reads with the new date/time, then **Next** → the button changes from
  *Post* to **Schedule** → scroll the composer once more to confirm the image survived → Schedule.
- Verify in **Scheduled posts** ("Posting Thu, Aug 13 at 8:00 AM"). Reachable from the toast, or
  *View all scheduled posts* in the dialog.

> ⏳ **A scheduled post cannot carry its first comment.** There is nothing to comment on until it
> publishes. Draft the comment into the day sheet, flag it in the tracker, and post it by hand once
> the post goes live — or the pre-filled share link never ships. The post URL likewise does not
> exist until then, so §2's URL cell stays empty until after publication.

## Step 6 — Record

Update the tracker in `docs/POST.md` §2: status ✅ and the post URL
(`https://www.linkedin.com/feed/update/urn:li:share:.../`). Commit the PNG and the updated day
sheet, and open a PR. Re-run [Post Inspector](https://www.linkedin.com/post-inspector/) only when
`index.html` head metadata changed — LinkedIn caches previews hard.
