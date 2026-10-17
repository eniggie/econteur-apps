// ECONTEUR hub — progressive enhancement only: every page works without JS.
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = matchMedia("(pointer: fine)").matches;

  // Reveal on scroll
  const items = document.querySelectorAll(".reveal");
  if (reduce || !("IntersectionObserver" in window)) items.forEach((el) => el.classList.add("in"));
  else {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach((el, i) => { el.style.transitionDelay = `${Math.min(i % 6, 5) * 60}ms`; io.observe(el); });
  }

  // Card tilt + glare (mouse/trackpad only, never on touch, never with reduced motion)
  if (fine && !reduce) {
    document.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("pointermove", (ev) => {
        const r = card.getBoundingClientRect();
        const x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height;
        card.style.setProperty("--mx", `${x * 100}%`);
        card.style.setProperty("--my", `${y * 100}%`);
        card.style.transform = `perspective(900px) rotateX(${(0.5 - y) * 5}deg) rotateY(${(x - 0.5) * 6}deg) translateY(-3px)`;
      });
      card.addEventListener("pointerleave", () => { card.style.transform = ""; });
    });
  }

  // Category filter (home page)
  const chips = document.querySelectorAll(".chip[data-filter]");
  const cards = document.querySelectorAll(".grid .card[data-cat]");
  chips.forEach((chip) => chip.addEventListener("click", () => {
    const f = chip.dataset.filter;
    chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
    let shown = 0;
    cards.forEach((card) => {
      const on = f === "all" || card.dataset.cat.split(" ").includes(f);
      card.hidden = !on; if (on) shown++;
    });
    const live = document.getElementById("filter-status");
    if (live) live.textContent = `${shown} product${shown === 1 ? "" : "s"} shown`;
  }));

  // Count-up for real numbers only (data-count holds the true value)
  const counts = document.querySelectorAll("[data-count]");
  const run = (el) => {
    const to = Number(el.dataset.count); if (!Number.isFinite(to)) return;
    if (reduce) { el.textContent = el.dataset.count + (el.dataset.suffix || ""); return; }
    const start = performance.now(), dur = 1100;
    const step = (t) => {
      const p = Math.min(1, (t - start) / dur), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
      el.textContent = v + (el.dataset.suffix || "");
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if ("IntersectionObserver" in window) {
    const co = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { run(e.target); co.unobserve(e.target); } }), { threshold: 0.6 });
    counts.forEach((el) => co.observe(el));
  } else counts.forEach(run);
})();
