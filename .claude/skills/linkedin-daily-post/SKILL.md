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
location.origin + '/index.html#s=' + btoa(unescape(encodeURIComponent(JSON.stringify(state))))
```

- `tab`: `general` / `basic` / `advanced` / `safety`. Omit to land on General.
- Abs/Gauge modes are **not** in `inputs` — they are top-level `p1` / `p2` (`'abs'` / `'gau'`).
- `lang: 'ja'` only on Japanese content.
- **Test on a real page load.** Changing the fragment alone does not re-run the restore; the page
  must actually load. Clear `localStorage` first so you see what a first-time visitor sees.
- Server-backed cards (ΔP, Flow Regime, PRV) still need a Calculate click; client-side cards
  (composition, steam, NPSHa, compressor, gas properties, Z-factor, pipe volume) render on open.

## Step 3 — Build the graphic

Copy `docs/linkedin/day01-mockup.html` as the pattern. It loads `index.html` in an **off-screen
iframe**, drives it with the app's own JavaScript, clones the resulting card, and freezes its
computed styles. **Never re-implement the UI** — the numbers in the image must come from the app.

Frame is 1200 × 675. Keep the footer strip carrying `engineering-converter.com`.

### Eight traps, all of which have bitten

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

Also: **`uppercase` destroys chemistry notation.** A Tailwind `uppercase` on a caption turns
`iC₄`/`nC₄`/`vol%` into `IC₄`/`NC₄`/`VOL%`. Component case is significant; don't uppercase it.

## Step 4 — Capture a real PNG

**What does not work:** the in-app Browser pane never composites frames; the Chrome MCP screenshot
does not paint CSS `transform`/`zoom` (it returns stale frames and often times out);
`save_to_disk` keeps the image in extension storage, never the filesystem; canvas export is tainted
by `foreignObject` SVG; `SetForegroundWindow` is refused from a background process, so
`CopyFromScreen` captures whatever is actually on top — **the maintainer's private windows**.

**What works:** an isolated Chrome `--app` window plus `PrintWindow`, which captures a specific
window's own pixels without needing foreground.

```powershell
# A FRESH profile dir each time — Chrome restores the previous window size from the profile
# and silently ignores --window-size.
# --disable-gpu IS REQUIRED. With GPU compositing on, PrintWindow returns a blank white surface
# (~8 KB PNG) no matter how long you wait. Software rendering makes it capture reliably.
Start-Process $chrome -ArgumentList @(
  "--user-data-dir=$env:TEMP\og_cap_$(New-Guid)", "--no-first-run", "--disable-extensions",
  "--disable-gpu", "--disable-gpu-compositing",
  "--force-device-scale-factor=1", "--window-position=0,0", "--window-size=1290,780",
  "--app=http://127.0.0.1:8000/docs/linkedin/dayNN-standalone.html")
# then PrintWindow(hWnd, hdc, 2)   # 2 = PW_RENDERFULLCONTENT
```

**Call `SetProcessDPIAware()` before `GetWindowRect`.** This display runs at 125 %. Without it,
Windows hands a DPI-unaware process virtualised coordinates and you capture a downscaled window
(1290 × 780 came back as 1032 × 624 — too small to crop 1200 × 675 out of).

**Check the output size and retry.** Even with `--disable-gpu` the first capture after window
creation can land before the first paint. A blank frame is ~8 KB; a real one is 150 KB+. Loop
until it exceeds ~60 KB rather than trusting a fixed sleep.

Crop by detecting the content origin rather than guessing the title-bar height:

```python
from PIL import Image                      # Pillow is available
dr = lambda y: sum(1 for x in range(0,W,7) if sum(px[x,y])<120)/len(range(0,W,7))
top  = next(y for y in range(H) if dr(y) > 0.85)
left = next(x for x in range(W) if dark_col(x, top+5, top+400) > 0.85)
im.crop((left, top, left+1200, top+675)).save('docs/linkedin/dayNN.png')
```

**Then open the PNG with the Read tool and actually look at it** (rule 3).

## Step 5 — Publish

Attaching the image: **only the OS clipboard works, and only two things make it land.**

> ### ATTACH THE IMAGE FIRST, INTO AN EMPTY COMPOSER.
> LinkedIn hides the media toolbar (image / document / celebrate / +) as soon as the editor
> overflows its box — and with the toolbar gone, **pasting an image does nothing at all**, silently.
> Type the body first and you cannot attach afterwards. Order is: open composer → paste image →
> *then* type the text. The attachment survives typing; the reverse does not work.
>
> If you have already typed, `ctrl+a` then `Delete` clears the editor and the toolbar comes back.

> ### THE PASTE MUST BE A REAL OS KEYSTROKE.
> A synthetic `ctrl+v` through the browser tool does **not** carry the OS clipboard — the page
> receives a paste event with nothing in it. You must `SetForegroundWindow` the Chrome window and
> `SendKeys("^v")`.
>
> **Guard it.** `SetForegroundWindow` can be refused, and focus reverts between PowerShell calls
> (each call is a new process, and running a tool refocuses the app). Activate, re-read
> `GetForegroundWindow()`, compare it to the target hWnd, and **abort if they differ** — all in a
> *single* PowerShell call. Never send a blind Ctrl+V: if focus is elsewhere it pastes the graphic
> into whatever the maintainer had open.

```powershell
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$img = [System.Drawing.Image]::FromFile("<abs path>\dayNN.png")
[System.Windows.Forms.Clipboard]::SetImage($img)   # PowerShell 5.1 is STA, required
$img.Dispose()
# ... same call: SetForegroundWindow($hwnd); verify GetForegroundWindow() -eq $hwnd; SendKeys ^v
```

Find the target window with
`Get-Process chrome | ? { $_.MainWindowTitle -like "*LinkedIn*" }` → `MainWindowHandle`.

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
5. Post. Then `…` → **Copy link to post** → paste that `lnkd.in/p/...` into the tab to resolve the
   real URL; the share id in it gives the tracker form
   `https://www.linkedin.com/feed/update/urn:li:share:<id>/`.
6. Add the pre-filled share link as the **first comment**.
7. Drafts auto-restore if the composer is closed, so a mistake is recoverable.

## Step 6 — Record

Update the tracker in `docs/POST.md` §2: status ✅ and the post URL
(`https://www.linkedin.com/feed/update/urn:li:share:.../`). Commit the PNG and the updated day
sheet, and open a PR. Re-run [Post Inspector](https://www.linkedin.com/post-inspector/) only when
`index.html` head metadata changed — LinkedIn caches previews hard.
