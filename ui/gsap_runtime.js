/**
 * MJZ AI Pro — GSAP runtime (runs inside st.components iframe, targets parent DOM)
 * Uses: gsap.to/from, timeline, matchMedia (ScrollTrigger not required for chat UI)
 */
(function () {
  const P = window.parent;
  const D = P.document;
  const GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.12.7/dist/gsap.min.js";

  function loadGsap(cb) {
    if (P.gsap) {
      cb(P.gsap);
      return;
    }
    const existing = D.getElementById("mjz-gsap-script");
    if (existing) {
      existing.addEventListener("load", () => cb(P.gsap));
      return;
    }
    const s = D.createElement("script");
    s.id = "mjz-gsap-script";
    s.src = GSAP_URL;
    s.async = true;
    s.onload = () => cb(P.gsap);
    D.head.appendChild(s);
  }

  function mark(el, key) {
    if (!el || el.getAttribute("data-mjz-" + key)) return false;
    el.setAttribute("data-mjz-" + key, "1");
    return true;
  }

  function animateHero(gsap) {
    const header = D.querySelector(".ws-main-header") || D.querySelector(".ws-header");
    if (!header || !mark(header, "hero")) return;
    const items = header.querySelectorAll(".ws-mode-tag, h1, p");
    gsap.from(items, {
      y: 14,
      opacity: 0,
      duration: 0.48,
      stagger: 0.07,
      ease: "power2.out",
      clearProps: "transform",
    });
  }

  function animateSidebar(_gsap) {
    /* 禁用 sidebar 动画，避免 opacity:0 导致内容不可见 */
  }

  function animateCards(gsap) {
    D.querySelectorAll(".ws-card:not([data-mjz-card])").forEach((card) => {
      card.setAttribute("data-mjz-card", "1");
      gsap.from(card, {
        y: 10,
        opacity: 0,
        duration: 0.42,
        ease: "power3.out",
        clearProps: "transform",
      });
    });

    D.querySelectorAll(".ws-empty:not([data-mjz-empty])").forEach((el) => {
      el.setAttribute("data-mjz-empty", "1");
      gsap.from(el.children, {
        y: 12,
        opacity: 0,
        duration: 0.5,
        stagger: 0.08,
        ease: "power2.out",
        clearProps: "transform",
      });
    });

    D.querySelectorAll(".ws-suggest-row:not([data-mjz-suggest])").forEach((el) => {
      el.setAttribute("data-mjz-suggest", "1");
      gsap.from(el.querySelectorAll(".stButton > button"), {
        y: 10,
        opacity: 0,
        duration: 0.42,
        stagger: 0.07,
        ease: "power2.out",
        clearProps: "transform",
      });
    });

    const composer = D.querySelector(".ws-composer-zone:not([data-mjz-comp])");
    if (composer) {
      composer.setAttribute("data-mjz-comp", "1");
      gsap.from(composer, {
        y: 8,
        opacity: 0,
        duration: 0.45,
        delay: 0.12,
        ease: "power2.out",
        clearProps: "transform",
      });
    }

    const attach = D.querySelector(".ws-composer-bar:not([data-mjz-attach])");
    if (attach) {
      attach.setAttribute("data-mjz-attach", "1");
      gsap.from(attach, {
        y: 6,
        opacity: 0,
        duration: 0.4,
        delay: 0.18,
        ease: "power2.out",
        clearProps: "transform",
      });
    }

    D.querySelectorAll("details[data-testid='stExpander']:not([data-mjz-exp])").forEach((el) => {
      el.setAttribute("data-mjz-exp", "1");
      gsap.from(el, { y: 8, opacity: 0, duration: 0.38, ease: "power2.out" });
    });
  }

  function animateMessages(gsap) {
    D.querySelectorAll('[data-testid="stChatMessage"]:not([data-mjz-msg])').forEach((msg) => {
      msg.setAttribute("data-mjz-msg", "1");
      const isUser = !!msg.querySelector('[data-testid="chatAvatarIcon-user"]');
      gsap.from(msg, {
        x: isUser ? 10 : -10,
        y: 6,
        opacity: 0,
        duration: 0.38,
        ease: "power2.out",
        clearProps: "transform",
      });
    });
  }

  function bindComposer(gsap) {
    const input = D.querySelector('[data-testid="stChatInput"]');
    if (!input || input.getAttribute("data-mjz-composer")) return;
    input.setAttribute("data-mjz-composer", "1");
    const ta = input.querySelector("textarea");
    if (!ta) return;

    ta.addEventListener("focus", () => {
      gsap.to(input, {
        scale: 1.008,
        duration: 0.28,
        ease: "power2.out",
        boxShadow: "0 4px 24px rgba(37, 99, 235, 0.14), 0 0 0 1px rgba(37, 99, 235, 0.12)",
      });
    });
    ta.addEventListener("blur", () => {
      gsap.to(input, {
        scale: 1,
        duration: 0.28,
        ease: "power2.out",
        boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04)",
      });
    });
  }

  function bindButtons(gsap) {
    D.querySelectorAll(
      'button:not([data-mjz-btn]):not([disabled]), [data-testid="stPopover"] > button:not([data-mjz-btn])'
    ).forEach((btn) => {
      btn.setAttribute("data-mjz-btn", "1");
      btn.addEventListener("mouseenter", () => {
        gsap.to(btn, { y: -1, duration: 0.2, ease: "power2.out" });
      });
      btn.addEventListener("mouseleave", () => {
        gsap.to(btn, { y: 0, duration: 0.2, ease: "power2.out" });
      });
    });
  }

  function runAll(gsap) {
    const mm = gsap.matchMedia();
    mm.add(
      {
        reduce: "(prefers-reduced-motion: reduce)",
        normal: "(prefers-reduced-motion: no-preference)",
      },
      (context) => {
        if (context.conditions.reduce) {
          gsap.set(".ws-header, .ws-card, .ws-nav-card, .ws-empty, [data-testid='stChatMessage']", {
            opacity: 1,
            y: 0,
            x: 0,
          });
          return;
        }
        animateHero(gsap);
        animateSidebar(gsap);
        animateCards(gsap);
        animateMessages(gsap);
        bindComposer(gsap);
        bindButtons(gsap);
      }
    );
  }

  function boot() {
    loadGsap((gsap) => {
      P.__mjzGsapRun = () => runAll(gsap);
      if (!P.__mjzGsapObserver) {
        P.__mjzGsapObserver = new P.MutationObserver(() => {
          clearTimeout(P.__mjzGsapDebounce);
          P.__mjzGsapDebounce = setTimeout(() => P.__mjzGsapRun(), 90);
        });
        P.__mjzGsapObserver.observe(D.body, { childList: true, subtree: true });
      }
      setTimeout(() => P.__mjzGsapRun(), 100);
    });
  }

  boot();
})();
