/* scroll-scenes.js — scroll-scrubbed image-sequence scenes. No dependencies, no build step.
 *
 * Markup (one per scene; any number of scenes per page):
 *   <section class="scene" style="--len:400vh"
 *            data-frames="assets/scene-1/f_%04d.webp" data-count="96"
 *            data-frames-hd="assets/scene-1-hd/f_%04d.webp" data-count-hd="96"         (optional, large screens)
 *            data-frames-mobile="assets/scene-1-m/f_%04d.webp" data-count-mobile="48"   (optional)
 *            data-poster="assets/scene-1/poster.jpg">
 *     <div class="scene__stage">
 *       <canvas class="scene__canvas" aria-hidden="true"></canvas>
 *       <div class="scene__scrim" aria-hidden="true"></div>
 *       <div class="band" data-in="0.00" data-out="0.32">...</div>
 *       <div class="band" data-in="0.36" data-out="1.00" data-static>...</div>
 *     </div>
 *   </section>
 *
 * Parallax: any element with data-speed="0.15" drifts against the scroll (negative = opposite way).
 * State hooks for CSS: .scene.is-static, .scene.is-ready, --load (0..1), band --k (0..1), band opacity.
 */
(() => {
  'use strict';

  const MOBILE_Q = '(max-width: 720px), (orientation: portrait) and (pointer: coarse)';
  const HD_MIN_PX = 1400;             // canvas backing width above this loads data-frames-hd when present
  const REDUCED_Q = '(prefers-reduced-motion: reduce)';
  const LOAD_MARGIN = '150% 0px';     // start fetching a scene 1.5 viewports before it arrives
  const CONCURRENCY = 6;
  const SMOOTH = 0.14;                // lerp per 60fps frame; tune by feel
  const MAX_DPR = 2;

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const smoothstep = (p, e0, e1) => {
    const t = clamp((p - e0) / (e1 - e0), 0, 1);
    return t * t * (3 - 2 * t);
  };
  const frameUrl = (tpl, i) =>
    tpl.replace(/%0(\d)d/, (_, w) => String(i).padStart(Number(w), '0')).replace('%d', String(i));

  const mqMobile = matchMedia(MOBILE_Q);
  const mqReduced = matchMedia(REDUCED_Q);

  // Progressive load order: every 8th frame first, then 4th, 2nd, rest.
  // Scrubbing works almost immediately at low temporal resolution and sharpens as frames land.
  function loadOrder(count) {
    const seen = new Uint8Array(count);
    const order = [];
    for (const step of [8, 4, 2, 1]) {
      for (let i = 0; i < count; i += step) if (!seen[i]) { seen[i] = 1; order.push(i); }
    }
    if (!seen[count - 1]) order.push(count - 1);
    return order;
  }

  class Scene {
    constructor(el) {
      this.el = el;
      this.stage = el.querySelector('.scene__stage');
      this.canvas = el.querySelector('.scene__canvas');
      this.ctx = this.canvas.getContext('2d', { alpha: false });
      this.bands = [...el.querySelectorAll('.band')].map(b => ({
        el: b,
        a: Number(b.dataset.in ?? 0),
        b: Number(b.dataset.out ?? 1),
        ramp: b.dataset.ramp ? Number(b.dataset.ramp) : null,
        op: -1, k: -1
      }));
      this.fx = Number(el.dataset.focusX ?? 0.5);   // cover-crop focal point
      this.fy = Number(el.dataset.focusY ?? 0.5);
      this.mode = null;         // 'desktop' | 'mobile' | 'static'
      this.frames = [];
      this.count = 0;
      this.loaded = 0;
      this.target = 0;
      this.shown = 0;
      this.drawn = -1;
      this.nearScreen = false;
      this.loadToken = 0;
      this.w = 0; this.h = 0;
    }

    progress() {
      const r = this.el.getBoundingClientRect();
      const range = r.height - innerHeight;
      return range > 0 ? clamp(-r.top / range, 0, 1) : (r.top <= 0 ? 1 : 0);
    }

    setMode(mode) {
      if (mode === this.mode) return;
      this.mode = mode;
      this.loadToken++;                           // cancels any in-flight load from the old mode
      this.frames = [];
      this.loaded = 0;
      this.drawn = -1;
      this.el.classList.toggle('is-static', mode === 'static');
      this.el.classList.remove('is-ready');
      this.el.style.setProperty('--load', '0');
      this.bands.forEach(b => { b.op = -1; b.k = -1; });

      if (mode === 'static') {
        if (this.el.dataset.poster) this.stage.style.backgroundImage = `url("${this.el.dataset.poster}")`;
        this.showStaticBands();
        return;
      }
      this.bands.forEach(b => b.el.removeAttribute('hidden'));
      const d = this.el.dataset;
      const tier = mode === 'mobile' && d.framesMobile ? 'Mobile' : mode === 'hd' && d.framesHd ? 'Hd' : '';
      this.tpl = tier ? d['frames' + tier] : d.frames;
      this.count = Number(tier ? d['count' + tier] : d.count);
      this.frames = new Array(this.count).fill(null);
      this.resize();
      if (this.nearScreen) this.load();
    }

    showStaticBands() {
      // Static visitors see one composed moment: the band marked data-static, else the last band.
      const pick = this.bands.find(b => b.el.hasAttribute('data-static')) || this.bands[this.bands.length - 1];
      this.bands.forEach(b => {
        const on = b === pick;
        b.el.style.opacity = on ? '1' : '0';
        b.el.style.setProperty('--k', on ? '1' : '0');
        b.el.toggleAttribute('hidden', !on);
      });
    }

    load() {
      if (this.mode === 'static' || this.loading === this.loadToken) return;
      const token = this.loading = this.loadToken;
      const queue = loadOrder(this.count);
      let failed = 0;
      const poster = this.el.dataset.poster;
      if (poster) this.stage.style.backgroundImage = `url("${poster}")`;   // paints before frame 1 lands

      const next = () => {
        if (token !== this.loadToken || !queue.length) return;
        const i = queue.shift();
        const img = new Image();
        img.decoding = 'async';
        img.src = frameUrl(this.tpl, i + 1);                 // ffmpeg numbers frames from 1
        img.decode().then(() => {
          if (token !== this.loadToken) return;
          this.frames[i] = img;
          this.loaded++;
          this.el.style.setProperty('--load', (this.loaded / this.count).toFixed(3));
          if (i === 0 || this.loaded === 1) { this.el.classList.add('is-ready'); this.drawn = -1; wake(); }
          // A frame closer to the wanted one just landed (e.g. after a jump into a loading scene):
          // redraw even though the lerp has already converged and the loop is resting.
          else if (this.nearScreen && this.drawn !== -1) {
            const want = Math.round(this.shown * (this.count - 1));
            if (Math.abs(i - want) < Math.abs(this.drawn - want)) { this.drawn = -1; wake(); }
          }
        }).catch(() => {
          if (token !== this.loadToken) return;
          this.el.classList.add('has-missing-frames');
          if (++failed >= 8 && this.loaded === 0) queue.length = 0;   // wrong path or no frames: stop, the poster carries the scene
        }).finally(next);
      };
      for (let n = 0; n < CONCURRENCY; n++) next();
    }

    resize() {
      const dpr = Math.min(MAX_DPR, devicePixelRatio || 1);
      const w = Math.round(this.stage.clientWidth * dpr);
      const h = Math.round(this.stage.clientHeight * dpr);
      if (w === this.w && h === this.h) return;
      this.w = this.canvas.width = w;
      this.h = this.canvas.height = h;
      this.drawn = -1;
    }

    // Nearest loaded frame to i, searching outward. Returns -1 when nothing is loaded yet.
    nearest(i) {
      if (this.frames[i]) return i;
      for (let d = 1; d < this.count; d++) {
        if (i - d >= 0 && this.frames[i - d]) return i - d;
        if (i + d < this.count && this.frames[i + d]) return i + d;
      }
      return -1;
    }

    draw(i) {
      const f = this.nearest(i);
      if (f < 0 || f === this.drawn) return;
      this.drawn = f;
      const img = this.frames[f];
      this.ctx.imageSmoothingQuality = 'high';   // resizing the canvas resets context state, so set it per draw
      const s = Math.max(this.w / img.naturalWidth, this.h / img.naturalHeight);   // cover
      const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
      this.ctx.drawImage(img, (this.w - dw) * this.fx, (this.h - dh) * this.fy, dw, dh);
    }

    bandsAt(p) {
      for (const band of this.bands) {
        const { a, b } = band;
        const f = Math.min(0.02, (b - a) / 3);
        const first = a <= 0, last = b >= 1;
        const op = (first ? 1 : smoothstep(p, a, a + f)) * (last ? 1 : 1 - smoothstep(p, b - f, b));
        const ramp = band.ramp || Math.min(0.025, (b - a) * 0.35);
        const k = first ? Math.max(clamp((p - a) / ramp, 0, 1), loadK) : clamp((p - a) / ramp, 0, 1);
        const opR = Math.round(op * 1000) / 1000;
        if (opR !== band.op) { band.op = opR; band.el.style.opacity = String(opR); }
        if (Math.abs(k - band.k) > 0.008 || (k === 1 && band.k !== 1) || (k === 0 && band.k !== 0)) {
          band.k = k;
          band.el.style.setProperty('--k', k.toFixed(3));
        }
      }
    }

    // Returns true while still easing toward the target.
    tick(dtScale) {
      if (this.mode === 'static') return false;
      this.shown += (this.target - this.shown) * (1 - Math.pow(1 - SMOOTH, dtScale));
      const moving = Math.abs(this.target - this.shown) > 0.0004;
      if (!moving) this.shown = this.target;
      this.draw(Math.round(this.shown * (this.count - 1)));
      this.bandsAt(this.shown);
      return moving;
    }
  }

  // ---- page-wide wiring ------------------------------------------------------------------
  const scenes = [...document.querySelectorAll('.scene')].map(el => new Scene(el));
  const parallax = [...document.querySelectorAll('[data-speed]')].map(el => ({ el, s: Number(el.dataset.speed), y: NaN }));
  let loadK = 0;                    // band one's one-time load assembly, so the page opens with words settled
  let rafId = null, last = 0;

  function modeNow() {
    if (mqReduced.matches) return 'static';
    if (mqMobile.matches) return 'mobile';
    return innerWidth * Math.min(MAX_DPR, devicePixelRatio || 1) > HD_MIN_PX ? 'hd' : 'desktop';
  }
  function applyModes() {
    const m = modeNow();
    scenes.forEach(s => {
      const hasMobile = !!s.el.dataset.framesMobile;
      s.setMode(m === 'mobile' && !hasMobile && s.el.dataset.mobile === 'static' ? 'static' : m);
    });
    parallax.forEach(p => { p.y = NaN; if (m === 'static') p.el.style.transform = ''; });
    onScroll();
  }

  function onScroll() {
    for (const s of scenes) s.target = s.progress();
    wake();
  }

  function wake() { if (rafId === null) { last = 0; rafId = requestAnimationFrame(frame); } }

  function frame(now) {
    const dt = Math.min(100, now - (last || now));
    last = now;
    const dtScale = dt / 16.667 || 1;
    let busy = false;
    if (loadK < 1) { loadK = Math.min(1, loadK + dt / 900); busy = true; }
    for (const s of scenes) if (s.nearScreen && s.tick(dtScale)) busy = true;    if (!mqReduced.matches) {
      for (const p of parallax) {
        const r = p.el.getBoundingClientRect();
        const off = (r.top - (p.y || 0) + r.height / 2) - innerHeight / 2;   // untransformed position, so the drift never feeds back
        if (Math.abs(off) > innerHeight * 1.5) continue;                    // far off-screen: leave it alone
        const y = Math.round(off * p.s * 10) / 10;
        if (y !== p.y) { p.y = y; p.el.style.transform = `translate3d(0, ${y}px, 0)`; }
      }
    }
    rafId = busy ? requestAnimationFrame(frame) : null;
  }

  const io = new IntersectionObserver(entries => {
    for (const e of entries) {
      const s = scenes.find(x => x.el === e.target);
      s.nearScreen = e.isIntersecting;
      if (e.isIntersecting) { s.load(); s.target = s.progress(); s.shown = s.target; s.drawn = -1; }
    }
    wake();
  }, { rootMargin: LOAD_MARGIN });
  scenes.forEach(s => io.observe(s.el));

  const ro = new ResizeObserver(() => {
    const m = modeNow();
    if (scenes.some(s => s.mode !== 'static' && s.mode !== m)) applyModes();   // e.g. window maximised past the HD threshold
    scenes.forEach(s => s.mode !== 'static' && s.resize());
    onScroll();
  });
  scenes.forEach(s => ro.observe(s.stage));

  addEventListener('scroll', onScroll, { passive: true });
  mqMobile.addEventListener('change', applyModes);
  mqReduced.addEventListener('change', applyModes);
  document.addEventListener('visibilitychange', () => document.body.classList.toggle('paused', document.hidden));

  applyModes();
  window.ScrollScenes = { scenes, refresh: applyModes };   // exposed for self-tests and tuning
})();
