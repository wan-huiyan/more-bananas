"""Banana-buddy theme for the memory report: an original yellow goggle mascot,
floating bananas, and a click-me burst. memlog.py calls theme(page, mood, word)."""

MOUTH = {"calm": "M84 150 Q100 166 116 150",
         "tight": "M86 154 L114 154",
         "over": "M86 160 Q100 146 114 160"}
SAYS = {"calm": "Hello! Lots of room.",
        "tight": "Hmm... getting squishy.",
        "over": "Beep beep! Too full!"}

BUDDY = """<div class="buddy-wrap" data-mood="{mood}">
<div class="bubble">{says}</div>
<button class="buddy" type="button" aria-label="Banana buddy. Click for a banana burst.">
<svg viewBox="0 0 200 260" aria-hidden="true">
 <ellipse class="shadow" cx="100" cy="250" rx="52" ry="7"/>
 <g class="bob">
  <g class="arm-l"><path d="M42 150 Q22 170 28 196" stroke="#f5c518" stroke-width="12" fill="none" stroke-linecap="round"/><circle cx="28" cy="198" r="9" fill="#333a45"/></g>
  <g class="arm-r"><path d="M158 150 Q182 128 178 104" stroke="#f5c518" stroke-width="12" fill="none" stroke-linecap="round"/><circle cx="178" cy="100" r="9" fill="#333a45"/></g>
  <rect x="78" y="226" width="16" height="18" rx="4" fill="#2f5d9a"/><rect x="106" y="226" width="16" height="18" rx="4" fill="#2f5d9a"/>
  <ellipse cx="84" cy="246" rx="14" ry="6" fill="#333a45"/><ellipse cx="116" cy="246" rx="14" ry="6" fill="#333a45"/>
  <rect x="42" y="30" width="116" height="206" rx="58" fill="#ffd93b"/>
  <path d="M42 176 h116 v2 a58 58 0 0 1 -116 0z" fill="#2f6fb5"/>
  <rect x="70" y="170" width="60" height="38" rx="8" fill="#2f6fb5"/>
  <path d="M70 176 L50 158 M130 176 L150 158" stroke="#2f6fb5" stroke-width="7" stroke-linecap="round"/>
  <circle cx="100" cy="190" r="7" fill="#1f4d86"/><path d="M96 190 h8" stroke="#ffd93b" stroke-width="2"/>
  <path d="M100 30 q-6 -16 -16 -20 M100 30 q2 -18 8 -24 M100 30 q10 -12 20 -12" stroke="#333a45" stroke-width="3" fill="none" stroke-linecap="round"/>
  <rect x="42" y="88" width="116" height="12" fill="#333a45"/>
  <circle cx="100" cy="94" r="34" fill="#9aa3ad" stroke="#5b6470" stroke-width="5"/>
  <circle cx="100" cy="94" r="25" fill="#fff"/>
  <g class="eye"><circle cx="100" cy="96" r="12" fill="#7a4b23"/><circle cx="100" cy="96" r="6" fill="#1b1b1b"/><circle cx="104" cy="91" r="3" fill="#fff"/></g>
  <rect class="lid" x="74" y="68" width="52" height="0" fill="#ffd93b"/>
  <path class="mouth" d="{mouth}" stroke="#5a2d0c" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path class="sweat" d="M146 70 q6 10 0 14 q-6 -4 0 -14z" fill="#8fd3ff"/>
 </g>
</svg></button></div>"""

CSS = """
:root{--banana:#ffd93b;--denim:#2f6fb5;--violet:var(--denim)}
@media(prefers-color-scheme:light){:root:not([data-theme=dark]){--bg:#fff8dc;--fg:#1d2a44;--mute:#5f6b80;--card:rgba(255,255,255,.82);--line:rgba(47,111,181,.14)}}
@media(prefers-color-scheme:dark){:root{--bg:#0e1a2f;--card:rgba(255,217,59,.06);--line:rgba(255,217,59,.14);--violet:var(--banana)}}
body:before{background:
 radial-gradient(40% 35% at 15% 10%,color-mix(in srgb,var(--banana) 40%,transparent),transparent 70%),
 radial-gradient(35% 30% at 90% 30%,color-mix(in srgb,var(--denim) 22%,transparent),transparent 70%),
 radial-gradient(45% 40% at 55% 100%,color-mix(in srgb,var(--tone) 18%,transparent),transparent 70%)}
.hero h1,.hist h2,.c .v{font-family:Fredoka,Geist,sans-serif;letter-spacing:-.02em}
.c{border-radius:28px;border-width:2px}
.c:hover{transform:translateY(-4px) rotate(-.4deg)}
.track b,.bar b{background:linear-gradient(90deg,var(--banana),var(--denim))!important}
.hero{padding-top:40px}
.buddy-wrap{position:relative;width:190px;margin:0 auto 8px}
.buddy{all:unset;cursor:pointer;display:block;width:190px}
.buddy svg{width:100%;height:auto;overflow:visible}
.shadow{fill:color-mix(in srgb,var(--fg) 14%,transparent)}
.bubble{position:absolute;left:150px;top:6px;white-space:nowrap;padding:8px 14px;border-radius:18px 18px 18px 4px;background:var(--fg);color:var(--bg);font:600 14px Fredoka,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,.12)}
.sweat{opacity:0}
.drop{position:fixed;top:-40px;z-index:1;pointer-events:none;font-size:22px}
.pop{position:fixed;z-index:9;pointer-events:none;font-size:26px}
@media(max-width:560px){.bubble{left:auto;right:-4px;top:-34px}}
@media(prefers-reduced-motion:no-preference){
 .bob{animation:bob 2.6s ease-in-out infinite;transform-origin:100px 240px}
 .shadow{animation:shadow 2.6s ease-in-out infinite;transform-origin:100px 250px}
 .arm-r{animation:wave 1.4s ease-in-out infinite;transform-origin:158px 150px}
 .lid{animation:blink 4.5s infinite}
 .eye{animation:look 7s ease-in-out infinite}
 .bubble{animation:pop .5s cubic-bezier(.3,1.6,.5,1) both .6s}
 [data-mood=over] .sweat{animation:sweat 1.2s ease-in infinite}
 [data-mood=over] .bob{animation:panic .5s ease-in-out infinite}
 [data-mood=over] .arm-r,[data-mood=over] .arm-l{animation:flail .35s ease-in-out infinite alternate}
 [data-mood=over] .arm-l{transform-origin:42px 150px}
 .drop{animation:fall linear forwards}
 .buddy:active svg{transform:scale(.94) rotate(-3deg)}
}
@keyframes bob{50%{transform:translateY(-8px)}}
@keyframes shadow{50%{transform:scaleX(.82);opacity:.6}}
@keyframes wave{50%{transform:rotate(-22deg)}}
@keyframes flail{to{transform:rotate(18deg)}}
@keyframes panic{50%{transform:translateY(-4px) rotate(2deg)}}
@keyframes blink{0%,92%,100%{height:0}95%{height:52px}}
@keyframes look{0%,40%,100%{transform:none}50%,70%{transform:translateX(-5px)}80%,90%{transform:translateX(5px)}}
@keyframes sweat{0%{opacity:0;transform:none}20%{opacity:1}100%{opacity:0;transform:translateY(26px)}}
@keyframes pop{from{opacity:0;transform:scale(.4) translateY(10px)}}
@keyframes fall{to{transform:translateY(calc(100vh + 80px)) rotate(var(--r))}}
"""

BANANA = '<svg viewBox="0 0 24 24" width="1em" height="1em"><path d="M4 15c4 4 12 4 16-6 1-2 0-4-1-4 0 6-6 11-14 8z" fill="#ffd93b" stroke="#c99700" stroke-width="1"/><path d="M19 5l1-2" stroke="#6b4b1b" stroke-width="2" stroke-linecap="round"/></svg>'

JS = """<script>
(() => {
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const BANANA = '__BANANA__';
  // Slowly falling bananas behind everything (few, so the numbers stay readable).
  if (!calm) setInterval(() => {
    const d = document.createElement("span"); d.className = "drop"; d.innerHTML = BANANA;
    d.style.left = Math.random() * 100 + "vw"; d.style.fontSize = 14 + Math.random() * 16 + "px";
    d.style.opacity = .35 + Math.random() * .4; d.style.setProperty("--r", (Math.random() * 720 - 360) + "deg");
    d.style.animationDuration = 9 + Math.random() * 8 + "s";
    document.body.prepend(d); setTimeout(() => d.remove(), 18000);
  }, 1600);
  // Click the buddy: a banana burst and a new line.
  const lines = ["Hello!", "Banana!", "More RAM, please!", "So many tabs...", "Me want more RAM!", "Beep beep!"];
  const b = document.querySelector(".buddy"), say = document.querySelector(".bubble");
  if (b) b.addEventListener("click", e => {
    say.textContent = lines[Math.floor(Math.random() * lines.length)];
    const r = b.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 3;
    for (let i = 0; i < (calm ? 1 : 14); i++) {
      const p = document.createElement("span"); p.className = "pop"; p.innerHTML = BANANA;
      p.style.left = cx + "px"; p.style.top = cy + "px"; document.body.appendChild(p);
      const a = Math.random() * Math.PI * 2, v = 90 + Math.random() * 120;
      p.animate([{ transform: "translate(-50%,-50%) scale(.6)", opacity: 1 },
                 { transform: `translate(calc(-50% + ${Math.cos(a) * v}px), calc(-50% + ${Math.sin(a) * v + 80}px)) rotate(${a * 200}deg) scale(1)`, opacity: 0 }],
                { duration: calm ? 400 : 1100, easing: "cubic-bezier(.2,.7,.4,1)" }).onfinish = () => p.remove();
    }
  });
})();
</script>"""

def favicon(mood):
    mouth = {"calm": "M12 25 Q16 28 20 25", "tight": "M12 26 L20 26", "over": "M12 27 Q16 24 20 27"}[mood]
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect x='6' y='2' width='20' height='29' rx='10' fill='%23ffd93b'/>"
            "<path d='M6 22h20v-1 0 1a10 10 0 0 1-20 0z' fill='%232f6fb5'/><rect x='6' y='11' width='20' height='3' fill='%23333a45'/>"
            "<circle cx='16' cy='12.5' r='6' fill='%23fff' stroke='%239aa3ad' stroke-width='2'/><circle cx='16' cy='13' r='2.6' fill='%237a4b23'/>"
            f"<path d='{mouth}' stroke='%235a2d0c' stroke-width='1.6' fill='none' stroke-linecap='round'/></svg>")

# The yard sizes buddies by whichever held the Mac up more: the processors or memory (report.py decides).
YARD_WORDS = {
    "cpu": ("Who is keeping the processors busy right now", "more of the processors", "processor time", "two goggles = over 10% of the processors"),
    "mem": ("Who is in your RAM right now", "more memory", "memory", "two goggles = over 1 GB"),
}
YARD = """<section class="yard-wrap rise" style="animation-delay:.2s">
<div class=yard-head><b>__HEAD__</b><span>One buddy per app and per Claude Code session. Bigger buddy, __MORE__. Click one to ask.</span></div>
<div class=yard id=yard aria-label="Animated buddies, one per app and Claude Code session, sized by __BY__"></div>
<div class=yard-key><span><i style="background:#2f6fb5"></i>an app</span><span><i style="background:#d97757"></i>a Claude Code session</span><span>__TWO__</span></div>
</section>"""

YARD_CSS = """
.yard:before,.yard:after{content:"";position:absolute;pointer-events:none}
.yard:before{top:26px;left:-120px;width:110px;height:34px;border-radius:30px;background:color-mix(in srgb,#fff 70%,transparent);
 box-shadow:40px -14px 0 -4px color-mix(in srgb,#fff 70%,transparent),70px 2px 0 -8px color-mix(in srgb,#fff 70%,transparent)}
.yard:after{left:0;right:0;bottom:0;height:46px;background:
 repeating-linear-gradient(100deg,transparent 0 9px,color-mix(in srgb,#5aa33a 55%,transparent) 9px 11px,transparent 11px 19px);
 -webkit-mask:linear-gradient(transparent,#000 60%);mask:linear-gradient(transparent,#000 60%);transform-origin:bottom}
@media(prefers-reduced-motion:no-preference){
 .yard:before{animation:cloud 60s linear infinite}
 .yard:after{animation:sway 5s ease-in-out infinite alternate}
 .mini.busy .p-laptop .code{animation:type .5s steps(2) infinite}
 .mini.busy .hold{animation:tap .45s ease-in-out infinite alternate}
 .mini .p-gear{animation:spin 4s linear infinite}
 .mini.busy .p-tabs{animation:shuffle 1.6s ease-in-out infinite}
 .mini.busy .p-chat .d1{animation:dot 1.2s infinite} .mini.busy .p-chat .d2{animation:dot 1.2s .2s infinite} .mini.busy .p-chat .d3{animation:dot 1.2s .4s infinite}
 .mini .p-compass .needle{animation:needle 3s ease-in-out infinite}
 .mini.busy .p-shield{animation:guard 2s ease-in-out infinite}
 .mini.busy .p-wrench{animation:spin .9s ease-in-out infinite alternate}
 .mini.walk .pupil{transform:translateX(1px)}
}
@keyframes cloud{to{transform:translateX(calc(1120px + 240px))}}
@keyframes sway{to{transform:skewX(-6deg)}}
@keyframes type{50%{opacity:.25}}
@keyframes tap{to{transform:translateY(1.5px)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes shuffle{50%{transform:translate(1px,-2px) rotate(-4deg)}}
@keyframes dot{50%{transform:translateY(-2px);opacity:.4}}
@keyframes needle{30%{transform:rotate(40deg)}60%{transform:rotate(-25deg)}}
@keyframes guard{50%{transform:translateY(-3px) scale(1.06)}}

.yard-wrap{margin:8px 0 40px}
.yard-head{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;margin-bottom:10px}
.yard-head b{font:600 20px Fredoka,sans-serif} .yard-head span,.yard-key{color:var(--mute);font-size:13px}
.yard{position:relative;height:340px;border-radius:28px;border:2px dashed color-mix(in srgb,var(--denim) 30%,transparent);
 background:radial-gradient(120% 60% at 50% 115%,color-mix(in srgb,#6cc24a 35%,transparent),transparent 70%),var(--card);overflow:hidden}
.yard-key{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px} .yard-key i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.mini{position:absolute;left:0;top:0;cursor:pointer;will-change:transform}
.mini svg{display:block;width:100%;height:auto;overflow:visible}
.mini .tag{position:absolute;left:50%;top:100%;transform:translateX(-50%);margin-top:2px;white-space:nowrap;font:600 11px Fredoka,sans-serif;
 padding:1px 7px;border-radius:9px;background:color-mix(in srgb,var(--bg) 80%,transparent);color:var(--fg)}
.mini .say{position:absolute;left:50%;bottom:105%;transform:translateX(-50%);white-space:nowrap;padding:5px 10px;border-radius:12px;
 background:var(--fg);color:var(--bg);font:600 12px Fredoka,sans-serif;opacity:0;transition:opacity .2s;pointer-events:none}
.mini.talk .say{opacity:1}
@media(prefers-reduced-motion:no-preference){
 .mini.walk .leg-a{animation:step .32s ease-in-out infinite alternate}
 .mini.walk .leg-b{animation:step .32s ease-in-out infinite alternate-reverse}
 .mini.walk .body{animation:waddle .32s ease-in-out infinite alternate}
}
@keyframes step{from{transform:translateY(-3px)}to{transform:translateY(1px)}}
@keyframes waddle{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
"""

YARD_JS = """<script>
(() => {
  const crowd = __CROWD__, mood = "__MOOD__", WORDS = __WORDS__;
  let byCpu = "__MEASURE__" === "cpu";
  const yard = document.getElementById("yard"); if (!yard || !crowd.length) return;
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const size = c => byCpu ? (c.cpu || 0) : c.gb;              // what a buddy's size stands for
  let max = Math.max(...crowd.map(size), byCpu ? 1 : .1);
  const gbTxt = gb => gb >= 1 ? gb.toFixed(1) + " GB" : Math.round(gb * 1024) + " MB";
  // Each buddy holds the thing it is (huashu: a character's action must be about the content, not just blink and bob).
  const PROP = n => /Claude desktop/.test(n) ? "chat" : /Chrome/.test(n) ? "tabs"
    : /macOS/.test(n) ? "gear" : /Slack/.test(n) ? "chat" : /Safari/.test(n) ? "compass" : /Security/.test(n) ? "shield"
    : /Tools/.test(n) ? "wrench" : /Drive/.test(n) ? "folder" : "banana";
  const PROPS = {
    laptop: '<g class="p-laptop"><rect x="14" y="62" width="32" height="20" rx="2" fill="#3b4250"/><rect x="16.5" y="64.5" width="27" height="15" rx="1" fill="#9fe3ff" class="screen"/><path d="M18 68h12M18 71h18M18 74h9" stroke="#2f6fb5" stroke-width="1.4" class="code"/><rect x="10" y="81" width="40" height="3.5" rx="1.5" fill="#5b6470"/></g>',
    tabs:   '<g class="p-tabs"><rect x="14" y="60" width="26" height="18" rx="2" fill="#fff" stroke="#c9ced6"/><rect x="18" y="64" width="26" height="18" rx="2" fill="#fff" stroke="#c9ced6"/><rect x="22" y="68" width="26" height="18" rx="2" fill="#fff" stroke="#c9ced6"/><circle cx="27" cy="73" r="2" fill="#ea4335"/><circle cx="33" cy="73" r="2" fill="#fbbc05"/><circle cx="39" cy="73" r="2" fill="#34a853"/></g>',
    gear:   '<g class="p-gear" style="transform-origin:30px 72px"><circle cx="30" cy="72" r="11" fill="#9aa3ad" stroke="#5b6470" stroke-width="2" stroke-dasharray="4 2.6"/><circle cx="30" cy="72" r="4" fill="#5b6470"/></g>',
    chat:   '<g class="p-chat"><path d="M12 62h30a4 4 0 0 1 4 4v12a4 4 0 0 1-4 4H24l-7 6v-6h-5a4 4 0 0 1-4-4V66a4 4 0 0 1 4-4z" fill="#fff" stroke="#c9ced6"/><circle cx="20" cy="72" r="2" fill="#d97757" class="d1"/><circle cx="27" cy="72" r="2" fill="#d97757" class="d2"/><circle cx="34" cy="72" r="2" fill="#d97757" class="d3"/></g>',
    compass:'<g class="p-compass"><circle cx="30" cy="72" r="11" fill="#fff" stroke="#2f6fb5" stroke-width="2.5"/><path d="M30 63l3 9-3 9-3-9z" fill="#ea4335" class="needle" style="transform-origin:30px 72px"/></g>',
    shield: '<g class="p-shield"><path d="M30 60l12 4v8c0 7-5 12-12 15-7-3-12-8-12-15v-8z" fill="#34a853" stroke="#1e7a3a" stroke-width="1.5"/><path d="M24 73l4 4 8-8" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round"/></g>',
    wrench: '<g class="p-wrench" style="transform-origin:30px 74px"><path d="M22 84l14-14m0 0a6 6 0 1 0 6-8l-4 4-3-1-1-3 4-4a6 6 0 0 0-8 6" stroke="#5b6470" stroke-width="4" fill="none" stroke-linecap="round"/></g>',
    folder: '<g class="p-folder"><path d="M14 64h11l3 3h18v17H14z" fill="#fbbc05" stroke="#c99700"/></g>',
    banana: '<g class="p-banana"><path d="M14 74c6 10 24 10 30-6 1-3-1-5-2-4-1 8-12 14-28 10z" fill="#ffd93b" stroke="#c99700"/></g>'
  };
  const svg = (c, uid) => {
    const suit = c.kind === "claude" ? "#d97757" : "#2f6fb5", suitD = c.kind === "claude" ? "#b85e40" : "#1f4d86", two = byCpu ? (c.cpu || 0) >= 10 : c.gb >= 1;
    const lens = (x, r) => `<circle cx="${x}" cy="30" r="${r}" fill="#fff" stroke="#9aa3ad" stroke-width="3"/><circle cx="${x}" cy="30" r="${r}" fill="none" stroke="#6b7480" stroke-width="1" />` +
      `<g class="pupil"><circle cx="${x}" cy="31" r="${r * .45}" fill="#7a4b23"/><circle cx="${x}" cy="31" r="${r * .22}" fill="#1b1b1b"/></g><circle cx="${x - r * .35}" cy="${30 - r * .4}" r="${r * .22}" fill="#fff" opacity=".9"/>`;
    const eyes = two ? lens(21, 8) + lens(39, 8) : lens(30, 10);
    const mouth = mood === "over" ? "M23 50 Q30 45 37 50" : mood === "tight" ? "M24 48 L36 48" : "M23 46 Q30 52 37 46";
    return `<svg viewBox="0 0 60 92"><defs><linearGradient id="y${uid}" x1="0" x2="1"><stop offset="0" stop-color="#ffe46a"/><stop offset=".55" stop-color="#ffd93b"/><stop offset="1" stop-color="#e9b912"/></linearGradient></defs>
      <ellipse cx="30" cy="89" rx="20" ry="3" fill="rgba(0,0,0,.14)"/>
      <g class="leg-a"><rect x="19" y="76" width="8" height="10" rx="3" fill="${suitD}"/><ellipse cx="22" cy="87" rx="7" ry="3.5" fill="#333a45"/><ellipse cx="20" cy="86" rx="2.5" ry="1" fill="#6b7480"/></g>
      <g class="leg-b"><rect x="33" y="76" width="8" height="10" rx="3" fill="${suitD}"/><ellipse cx="38" cy="87" rx="7" ry="3.5" fill="#333a45"/><ellipse cx="36" cy="86" rx="2.5" ry="1" fill="#6b7480"/></g>
      <g class="body" style="transform-origin:30px 80px"><rect x="6" y="6" width="48" height="76" rx="24" fill="url(#y${uid})"/>
      <ellipse cx="17" cy="20" rx="5" ry="9" fill="#fff" opacity=".28"/>
      <path d="M6 58h48v1a24 24 0 0 1-48 0z" fill="${suit}"/><path d="M8 66a24 24 0 0 0 44 0" stroke="${suitD}" stroke-width="1" stroke-dasharray="2 2" fill="none"/>
      <rect x="18" y="56" width="24" height="14" rx="4" fill="${suit}"/><rect x="21" y="59" width="18" height="8" rx="2" fill="none" stroke="${suitD}" stroke-width=".9" stroke-dasharray="1.6 1.6"/>
      <path d="M18 58L10 48M42 58L50 48" stroke="${suit}" stroke-width="4" stroke-linecap="round"/><circle cx="18.5" cy="58" r="1.8" fill="#2b2b2b"/><circle cx="41.5" cy="58" r="1.8" fill="#2b2b2b"/>
      <path d="M30 6q-3-6-8-7M30 6q2-7 6-8M30 6q5-4 9-3" stroke="#333a45" stroke-width="1.8" fill="none" stroke-linecap="round"/>
      <rect x="6" y="27" width="48" height="5" fill="#333a45"/>${eyes}
      <path d="${mouth}" stroke="#5a2d0c" stroke-width="2.6" fill="none" stroke-linecap="round"/></g>
      <g class="hold">${PROPS[c.kind === "claude" ? "laptop" : PROP(c.name)]}<path d="M8 52 Q4 64 14 70M52 52 Q56 64 46 70" stroke="#f2c418" stroke-width="5" fill="none" stroke-linecap="round"/><circle cx="14" cy="70" r="3.6" fill="#333a45"/><circle cx="46" cy="70" r="3.6" fill="#333a45"/></g></svg>`;
  };
  // Deterministic placement from the name, so buddies do not jump around on the every-minute refresh (huashu: seed every random).
  const seed = str => { let h = 2166136261; for (const ch of str) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) >>> 0) / 4294967296); };
  const W = () => yard.clientWidth, H = () => yard.clientHeight;
  const inner = (c, i) => svg(c, i) + `<span class="tag">${c.name.length > 16 ? c.name.slice(0, 15) + "…" : c.name}</span>`
    + `<span class="say">${c.name}: ${byCpu ? `${Math.round(c.cpu || 0)}% of the processors, ${gbTxt(c.gb)}` : gbTxt(c.gb)}</span>`;
  const mobs = crowd.map((c, i) => {
    const el = document.createElement("div"); el.className = "mini";
    const w = 34 + 54 * Math.sqrt(size(c) / max); el.style.width = w + "px";
    el.innerHTML = inner(c, i);
    el.title = c.name;
    yard.appendChild(el);
    const h = w * 92 / 60;
    const rnd = seed(c.name);
    const m = { el, w, h, rnd, v: 0, x: rnd() * (W() - w), y: 20 + rnd() * (H() - h - 40), tx: 0, ty: 0, wait: rnd() * 2000,
      speed: (mood === "over" ? 70 : 32) * (1.4 - .6 * Math.sqrt(size(c) / max)) };
    el.addEventListener("click", () => { el.classList.add("talk"); m.wait = 2500; setTimeout(() => el.classList.remove("talk"), 2500); });
    return m;
  });
  const place = m => m.el.style.transform = `translate(${m.x}px,${m.y}px)`;
  mobs.forEach(m => { m.tx = m.x; m.ty = m.y; place(m); });
  // Follow the page's Processors / Memory switch: resize every buddy and reword the heading.
  const apply = ms => {
    byCpu = ms === "cpu"; max = Math.max(...crowd.map(size), byCpu ? 1 : .1);
    const [hd, more, , two] = WORDS[byCpu ? "cpu" : "mem"], wrap = yard.closest(".yard-wrap");
    if (wrap) { wrap.querySelector(".yard-head b").textContent = hd; wrap.querySelector(".yard-key span:last-child").textContent = two;
      wrap.querySelector(".yard-head span").textContent = `One buddy per app and per Claude Code session. Bigger buddy, ${more}. Click one to ask.`; }
    mobs.forEach((m, i) => { const c = crowd[i], w = 34 + 54 * Math.sqrt(size(c) / max);
      m.w = w; m.h = w * 92 / 60; m.el.style.width = w + "px"; m.el.innerHTML = inner(c, i);
      m.speed = (mood === "over" ? 70 : 32) * (1.4 - .6 * Math.sqrt(size(c) / max));
      m.x = Math.min(m.x, Math.max(W() - w, 0)); m.y = Math.min(m.y, Math.max(H() - m.h - 20, 0)); place(m); });
  };
  document.querySelectorAll(".mt").forEach(b => b.addEventListener("click", () => apply(b.dataset.m)));
  try { const mm = localStorage.getItem("mm-measure"); if (mm && (mm === "cpu") !== byCpu) apply(mm); } catch (_) {}
  if (still) return;
  let last = performance.now();
  const tick = now => {
    const dt = Math.min((now - last) / 1000, .05); last = now;
    for (const m of mobs) {
      if (m.wait > 0) { m.wait -= dt * 1000; m.el.classList.remove("walk"); m.el.classList.add("busy"); continue; }
      m.el.classList.remove("busy");
      const dx = m.tx - m.x, dy = m.ty - m.y, d = Math.hypot(dx, dy);
      if (d < 2) {  // arrived: pause, then pick somewhere new in the yard
        m.wait = 400 + m.rnd() * (mood === "over" ? 600 : 3200); m.v = 0;
        m.tx = m.rnd() * (W() - m.w); m.ty = 10 + m.rnd() * (H() - m.h - 30); continue;
      }
      const want = Math.min(m.speed, d * 1.6);  // slow down on arrival
      m.v += (want - m.v) * Math.min(1, dt * 3);  // and speed up gently on departure
      const step = Math.min(d, m.v * dt);
      m.x += dx / d * step; m.y += dy / d * step;
      m.el.classList.add("walk"); m.el.querySelector("svg").style.transform = dx < 0 ? "scaleX(-1)" : "";
      m.el.style.zIndex = Math.round(m.y + m.h);
      place(m);
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
</script>"""

def theme(page, mood, crowd=(), measure="mem"):
    import json
    head, more, by, two = YARD_WORDS["cpu" if measure == "cpu" else "mem"]
    page = page.replace("</style>", YARD_CSS + "</style>", 1)
    page = page.replace("<!--YARD-->", YARD.replace("__HEAD__", head).replace("__MORE__", more).replace("__BY__", by).replace("__TWO__", two), 1)
    page = page.replace("</body>", YARD_JS.replace("__CROWD__", json.dumps(list(crowd)).replace("</", "<\\/")).replace("__MOOD__", mood)
                        .replace("__MEASURE__", measure).replace("__WORDS__", json.dumps(YARD_WORDS)) + "</body>", 1)
    return _theme(page, mood)

MAGIC_CSS = r"""
/* sparkle-that-page: banana palette tokens, selection, scrollbar, wand cursor, climbing buddy */
:root{--stp-c1:#ffd93b;--stp-c2:#2f6fb5;--stp-c3:#d97757;--stp-c4:#9fe3ff;--stp-c5:#fff3b0;--stp-ink:#1d2a44}
::selection{background:var(--stp-c1);color:var(--stp-ink)}
html{scrollbar-color:var(--stp-c1) transparent}
::-webkit-scrollbar{width:12px}::-webkit-scrollbar-thumb{background:var(--stp-c1);border-radius:9px;border:3px solid var(--bg)}
@media(pointer:fine){html{cursor:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'%3E%3Cpath d='M4 30L22 10' stroke='%23c99700' stroke-width='3' stroke-linecap='round'/%3E%3Cpath d='M18 12c3 5 9 5 11-2 0-2-1-3-2-2-1 4-5 6-9 4z' fill='%23ffd93b' stroke='%23c99700'/%3E%3Cpath d='M26 3l1 2.5 2.5 1-2.5 1L26 10l-1-2.5-2.5-1 2.5-1z' fill='%23fff3b0'/%3E%3C/svg%3E") 4 28,auto}
 .buddy,.mini,button,a{cursor:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'%3E%3Cpath d='M4 30L22 10' stroke='%23c99700' stroke-width='3' stroke-linecap='round'/%3E%3Cpath d='M18 12c3 5 9 5 11-2 0-2-1-3-2-2-1 4-5 6-9 4z' fill='%23ffd93b' stroke='%23c99700'/%3E%3Cpath d='M26 1l1.6 4 4 1.6-4 1.6L26 12l-1.6-4-4-1.6 4-1.6z' fill='%23d97757'/%3E%3C/svg%3E") 4 28,pointer}}
.stp-trail{position:fixed;left:0;top:0;z-index:2147483600;pointer-events:none;font-size:14px;will-change:transform,opacity}
.climb{position:fixed;right:10px;top:90px;bottom:24px;width:26px;z-index:2147483601;pointer-events:none}
.climb:before{content:"";position:absolute;left:12px;top:0;bottom:0;width:2px;border-radius:2px;background:repeating-linear-gradient(var(--line) 0 6px,transparent 6px 10px)}
.climb .who{position:absolute;left:0;top:0;width:26px;transition:transform .25s cubic-bezier(.2,.8,.2,1)}
.climb .who svg{width:100%;height:auto}
@media(max-width:720px){.climb{display:none}}
@media(prefers-reduced-motion:no-preference){
 .climb .who svg{animation:climbbob 1.2s ease-in-out infinite alternate}
 html.accent .hero h1{animation:siren .9s cubic-bezier(.3,1.6,.5,1) 1}
}
@keyframes climbbob{to{transform:translateY(-3px) rotate(4deg)}}
@keyframes siren{20%{transform:scale(1.04) rotate(-1deg)}40%{transform:scale(1.02) rotate(1deg)}}
"""

MAGIC_JS = r"""<script>
(() => {
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches, fine = matchMedia("(pointer: fine)").matches;
  const cols = ["--stp-c1", "--stp-c2", "--stp-c3", "--stp-c4"].map(v => getComputedStyle(document.documentElement).getPropertyValue(v).trim());
  // Sparse sparkle trail: one glint every 24px of travel (sparkle-that-page default density).
  if (fine && !calm) {
    let lx = 0, ly = 0, live = 0;
    addEventListener("pointermove", e => {
      if (Math.hypot(e.clientX - lx, e.clientY - ly) < 24 || live > 40) return;
      lx = e.clientX; ly = e.clientY; live++;
      const s = document.createElement("span"); s.className = "stp-trail"; s.textContent = Math.random() < .3 ? "✦" : "✧";
      s.style.color = cols[Math.floor(Math.random() * cols.length)];
      document.body.appendChild(s);
      const dx = (Math.random() - .5) * 30, dy = 20 + Math.random() * 20;
      s.animate([{ transform: `translate(${lx}px,${ly}px) scale(1)`, opacity: 1 }, { transform: `translate(${lx + dx}px,${ly + dy}px) scale(.2) rotate(90deg)`, opacity: 0 }],
                { duration: 800, easing: "cubic-bezier(.2,.7,.4,1)" }).onfinish = () => { s.remove(); live--; };
    }, { passive: true });
  }
  // A tiny buddy climbs the rail as you scroll (scroll-depth indicator, "mascot" variant).
  const rail = document.createElement("div"); rail.className = "climb"; rail.setAttribute("aria-hidden", "true");
  rail.innerHTML = '<div class="who"><svg viewBox="0 0 60 92"><rect x="6" y="6" width="48" height="76" rx="24" fill="#ffd93b"/><path d="M6 58h48v1a24 24 0 0 1-48 0z" fill="#2f6fb5"/><rect x="6" y="27" width="48" height="5" fill="#333a45"/><circle cx="30" cy="30" r="10" fill="#fff" stroke="#9aa3ad" stroke-width="3"/><circle cx="30" cy="27" r="4.5" fill="#7a4b23"/><path d="M23 46 Q30 52 37 46" stroke="#5a2d0c" stroke-width="2.6" fill="none" stroke-linecap="round"/></svg></div>';
  document.body.appendChild(rail);
  const who = rail.firstChild; let ticking = false;
  const place = () => { ticking = false; const f = scrollY / Math.max(1, document.documentElement.scrollHeight - innerHeight);
    who.style.transform = `translateY(${(1 - f) * (rail.clientHeight - 40)}px)`; };
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(place); } }, { passive: true }); place();
  // Tab peekaboo: a gentle note while the tab is hidden, restored on return.
  const title = document.title;
  document.addEventListener("visibilitychange", () => { document.title = document.hidden ? "Hello? Come back!" : title; });
  // One accent, only when it matters (huashu: fast moves are for the key moment): the headline shakes once if the Mac is swapping hard.
  if (document.querySelector(".buddy-wrap[data-mood=over]") && !document.documentElement.classList.contains("again")) document.documentElement.classList.add("accent");
})();
</script>"""

def _theme(page, mood):
    page = page.replace("</style>", MAGIC_CSS + "</style>", 1).replace("</body>", MAGIC_JS + "</body>", 1)
    import re
    page = page.replace("family=Geist:", "family=Fredoka:wght@500;600;700&family=Geist:", 1)
    page = page.replace("</style>", CSS + "</style>", 1)
    page = re.sub(r"<link rel=icon href='[^']*'>", lambda m: f"<link rel=icon href=\"data:image/svg+xml,{favicon(mood)}\">", page, 1)
    page = page.replace("<section class=hero>", "<section class=hero>" + BUDDY.format(mood=mood, says=SAYS[mood], mouth=MOUTH[mood]), 1)
    return page.replace("</body>", JS.replace("__BANANA__", BANANA) + "</body>", 1)
