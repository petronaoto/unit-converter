# -*- coding: utf-8 -*-
"""Build the v3.4 documentation-restructure graphic.

The two jump-link strips are lifted VERBATIM (label + Tailwind classes) from
index.html at two commits — pre-v3.4 (ae3f3dc^) and current main — so the pills
are the app's own markup styled by the app's own Tailwind build. The only thing
this file adds is the annotation layer: a colour bar under each pill showing
which TAB that section documents. That is the whole argument.
"""
import io, json, os, re, subprocess

SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'v34-docs-standalone.html')

# section anchor -> owning tab. Derived from the section headings in index.html
# at the matching commit, not guessed.
TAB = {
 'howto-releases':'notes',
}
COLOR = {
 'app'  : ('#64748b','App-wide'),
 'gen'  : ('#3b82f6','General'),
 'basic': ('#22c55e','Basic Eng'),
 'adv'  : ('#f59e0b','Advanced'),
 'gt'   : ('#a855f7','GT Fuel'),
 'safe' : ('#ef4444','Safety'),
 'rep'  : ('#0ea5e9','Report'),
 'notes': ('#78716c','Release notes'),
}
# label -> tab (labels are stable across the two versions)
BYLABEL = {
 'Header':'app','Mobile':'app','Copy':'app',
 'General':'gen','Custom':'gen',
 'Basic Eng':'basic','Gas Props':'basic','Steam':'basic','NPSHa':'basic','Compressor':'basic',
 'Composition':'adv','LNG Refs':'adv','Conditions':'adv','Properties':'adv','Flow':'adv',
 'LNG Cargo':'adv','ΔP':'adv','Fittings':'adv','Flow Regime':'adv',
 'GT Fuel':'gt','PRV':'safe','Report':'rep',
}
def tab_of(anchor, label):
    if anchor.startswith('howto-new') or anchor == 'howto-releases': return 'notes'
    key = re.sub(r'^[★\s\d]+','',label).strip()
    return BYLABEL[key]

d = json.load(io.open(os.path.join(SP,'strips.json'), encoding='utf-8'))

def pills(rows):
    out=[]
    for anchor, cls, label in rows:
        t = tab_of(anchor, label)
        c = COLOR[t][0]
        out.append('<span class="pillwrap"><a class="%s">%s</a>'
                   '<span class="bar" style="background:%s"></span></span>' % (cls, label, c))
    return '\n'.join(out)

def runs(rows):
    """contiguous same-tab runs — the number the image is really about"""
    seq=[tab_of(a,l) for a,_,l in rows]
    n=1
    for i in range(1,len(seq)):
        if seq[i]!=seq[i-1]: n+=1
    return n

legend = ''.join('<span class="lg"><i style="background:%s"></i>%s</span>'%(c,n)
                 for c,n in [COLOR[k] for k in ['app','gen','basic','adv','gt','safe','rep','notes']])

HTML = '''<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdn.tailwindcss.com"></script>
<style>

 *{transition:none!important;animation:none!important;box-sizing:border-box}
 html,body{margin:0;padding:0;background:#020617}
 #frame{width:1200px;height:675px;position:relative;overflow:hidden;
   background:radial-gradient(1100px 460px at 18%% -12%%,#0c1424 0%%,#020617 62%%);
   font-family:ui-sans-serif,system-ui,'Segoe UI',sans-serif;color:#e2e8f0}
 .pad{position:absolute;inset:0 0 42px 0;padding:0 44px;display:flex;flex-direction:column;justify-content:center}
 h1{font-size:39px;line-height:1.12;font-weight:800;margin:0;letter-spacing:-.015em;color:#f8fafc}
 h1 em{font-style:normal;color:#f59e0b}
 .sub{margin:13px 0 0;font-size:17.5px;color:#94a3b8;line-height:1.4}
 .panel{margin-top:19px;border:1px solid #1e293b;border-radius:15px;background:#0b111f;padding:16px 20px 19px}
 .panel.after{border-color:#14532d;background:#0a1410}
 .cap{display:flex;align-items:center;gap:12px;margin-bottom:15px}
 .tag{font:700 11px/1 ui-monospace,monospace;letter-spacing:.15em;text-transform:uppercase;
   padding:6px 10px;border-radius:6px}
 .tag.b{background:rgba(239,68,68,.14);color:#f87171;border:1px solid rgba(239,68,68,.35)}
 .tag.a{background:rgba(34,197,94,.14);color:#4ade80;border:1px solid rgba(34,197,94,.38)}
 .capt{font-size:14.5px;color:#94a3b8}
 .capt b{color:#f1f5f9;font-weight:700}
 .strip{display:flex;flex-wrap:wrap;gap:9px 7px}
 .pillwrap{position:relative;display:inline-flex;flex-direction:column;align-items:stretch}
 .pillwrap a{font:400 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap;
   padding:7px 9px;border-radius:6px 6px 0 0;background:#1e293b;border:1px solid #334155;
   border-bottom:none;color:#e2e8f0}
 .bar{height:8px;border-radius:0 0 4px 4px}
 .lgrow{display:flex;flex-wrap:wrap;gap:18px;margin-top:19px;justify-content:center}
 .lg{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:#94a3b8}
 .lg i{width:20px;height:6px;border-radius:3px;display:inline-block}
 .payoff{margin-top:19px;display:flex;flex-direction:column;align-items:flex-start;gap:5px;padding:16px 20px;
   border:1px solid #1e293b;border-left:4px solid #f59e0b;border-radius:10px;background:#0b111f}
 .payoff .big{font:800 17px/1.3 ui-sans-serif,system-ui;color:#f8fafc;white-space:nowrap}
 .payoff .txt{font-size:14px;color:#94a3b8;line-height:1.45}
 .payoff .txt b{color:#cbd5e1;font-weight:600}
 .foot{position:absolute;left:0;right:0;bottom:0;height:42px;display:flex;align-items:center;
   justify-content:space-between;padding:0 44px;background:#020617;border-top:1px solid #1e293b}
 .foot .u{font:600 13px ui-monospace,monospace;color:#f59e0b}
 .foot .m{font-size:11.5px;color:#64748b}
</style></head><body><div id="frame"><div class="pad">
 <h1>My manual was sorted by <em>release date</em>.</h1>
 <p class="sub">The same jump-link strip, before and after. Each bar is the tab that section documents.</p>

 <div class="panel">
  <div class="cap"><span class="tag b">Before</span>
   <span class="capt">ordered by release &nbsp;·&nbsp; <b>%(rb)d colour runs</b> &nbsp;·&nbsp; the Basic Eng calculators sit in 4, 13, 16, 17, 18</span></div>
  <div class="strip">%(pb)s</div>
 </div>

 <div class="panel after">
  <div class="cap"><span class="tag a">After</span>
   <span class="capt">ordered by the tab bar &nbsp;·&nbsp; <b>%(ra)d colour runs</b> &nbsp;·&nbsp; one contiguous block per tab &mdash; the fewest possible</span></div>
  <div class="strip">%(pa)s</div>
  <div class="lgrow">%(lg)s</div>
 </div>

 <div class="payoff">
  <span class="big">Then I wrote the rule down.</span>
  <span class="txt">Insert a section at its position, never append &mdash; and a release adds an appendix entry, not a banner at the top.<br><b>Four releases have shipped since. Every one of them landed in the right place.</b></span>
 </div>
</div>
<div class="foot"><span class="u">engineering-converter.com</span>
 <span class="m">How To Use &mdash; jump-link strip &middot; pre-v3.4 vs live</span></div>
</div></body></html>''' % {
 'pb': pills(d['before']), 'pa': pills(d['after']),
 'rb': runs(d['before']), 'ra': runs(d['after']), 'lg': legend}

io.open(OUT,'w',encoding='utf-8',newline='\n').write(HTML)
print('runs before =', runs(d['before']), ' runs after =', runs(d['after']))
print('written', OUT)
