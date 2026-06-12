(function () {
  "use strict";

  const header = document.querySelector(".header");
  const newsSection = document.querySelector(".news-fullpage");
  const newsTrack = document.querySelector(".news-track");
  const newsViewport = document.querySelector(".news-viewport");
  const newsCards = document.querySelectorAll(".news-full-card");
  const newsDots = document.querySelectorAll(".news-dot");
  const prevBtn = document.querySelector(".news-nav-prev");
  const nextBtn = document.querySelector(".news-nav-next");

  const apiBaseMeta = document.querySelector('meta[name="api-base"]');
  const API_BASE =
    (apiBaseMeta && apiBaseMeta.content.trim()) ||
    (location.hostname === "localhost" || location.hostname === "127.0.0.1"
      ? "http://127.0.0.1:8000"
      : "");

  let currentIndex = 0;

  function populateNewsCard(card, item) {
    const tag = card.querySelector(".tag");
    const timeEl = card.querySelector(".card-meta time");
    const body = card.querySelector(".card-body");
    const sourceLink = card.querySelector(".card-source");

    if (tag) tag.textContent = item.category;
    if (timeEl) {
      timeEl.textContent = item.date_label;
      timeEl.dateTime = item.published_at;
    }
    if (body) body.textContent = item.summary;
    if (sourceLink) {
      sourceLink.textContent = item.source_name;
      sourceLink.href = item.source_url;
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      sourceLink.setAttribute("aria-label", `${item.source_name} 원문 보기`);
    }
  }

  async function loadTodayNews() {
    if (!API_BASE) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/news`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const byCategory = Object.fromEntries(
        (data.items || []).map((item) => [item.category, item])
      );

      newsCards.forEach((card) => {
        const item = byCategory[card.dataset.category];
        if (item) populateNewsCard(card, item);
      });
    } catch (err) {
      console.warn("오늘 뉴스를 불러오지 못했습니다.", err);
    }
  }

  loadTodayNews();

  function updateHeader() {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 10);
  }

  window.addEventListener("scroll", updateHeader, { passive: true });
  updateHeader();

  // Scroll reveal
  const revealTargets = document.querySelectorAll(
    ".story-copy, .section > .container, .examples-intro .container, .beta-inner, .hero-content, .hero-visual"
  );

  revealTargets.forEach((el) => el.classList.add("reveal"));

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
  );

  revealTargets.forEach((el) => revealObserver.observe(el));

  // News carousel
  function setActiveCard(index) {
    newsCards.forEach((card, i) => {
      card.classList.toggle("is-active", i === index);
    });
    newsDots.forEach((dot, i) => {
      dot.classList.toggle("is-active", i === index);
    });
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === newsCards.length - 1;
  }

  function goTo(index) {
    if (!newsTrack || !newsCards.length) return;
    const nextIndex = Math.max(0, Math.min(index, newsCards.length - 1));
    if (nextIndex === currentIndex) return;

    currentIndex = nextIndex;
    newsTrack.style.transform = `translateX(-${currentIndex * 100}%)`;
    setActiveCard(currentIndex);
  }

  if (newsSection && newsCards.length && newsTrack) {
    setActiveCard(0);

    if (prevBtn) {
      prevBtn.addEventListener("click", () => goTo(currentIndex - 1));
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", () => goTo(currentIndex + 1));
    }

    newsDots.forEach((dot) => {
      dot.addEventListener("click", () => {
        goTo(Number(dot.dataset.target));
      });
    });

    document.addEventListener("keydown", (e) => {
      if (!newsSection.classList.contains("is-visible")) return;
      if (e.key === "ArrowRight") {
        e.preventDefault();
        goTo(currentIndex + 1);
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goTo(currentIndex - 1);
      }
    });

    // Touch swipe
    if (newsViewport) {
      let touchStartX = 0;
      let touchStartY = 0;

      newsViewport.addEventListener(
        "touchstart",
        (e) => {
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
        },
        { passive: true }
      );

      newsViewport.addEventListener(
        "touchend",
        (e) => {
          const diffX = touchStartX - e.changedTouches[0].clientX;
          const diffY = touchStartY - e.changedTouches[0].clientY;

          if (Math.abs(diffX) < 50 || Math.abs(diffX) < Math.abs(diffY)) return;

          if (diffX > 0) goTo(currentIndex + 1);
          else goTo(currentIndex - 1);
        },
        { passive: true }
      );
    }

    const sectionObserver = new IntersectionObserver(
      ([entry]) => {
        newsSection.classList.toggle("is-visible", entry.isIntersecting);
      },
      { threshold: 0.3 }
    );

    sectionObserver.observe(newsSection);
  }

  // Smooth anchor offset for fixed header
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const id = anchor.getAttribute("href");
      if (!id || id === "#") return;

      const target = document.querySelector(id);
      if (!target) return;

      e.preventDefault();
      const offset =
        parseInt(
          getComputedStyle(document.documentElement).getPropertyValue("--header-height"),
          10
        ) || 52;
      const top = target.getBoundingClientRect().top + window.scrollY - offset - 16;

      window.scrollTo({ top, behavior: "smooth" });

      if (id === "#examples") {
        goTo(0);
      }
    });
  });

  // Feedback modal
  const feedbackModal = document.getElementById("feedback-modal");
  const feedbackOpeners = document.querySelectorAll("[data-feedback-open]");
  const feedbackClosers = document.querySelectorAll("[data-feedback-close]");
  let feedbackLastFocus = null;

  function openFeedbackModal() {
    if (!feedbackModal) return;
    feedbackLastFocus = document.activeElement;
    feedbackModal.hidden = false;
    feedbackModal.classList.add("is-open");
    document.body.classList.add("modal-open");
    const textarea = feedbackModal.querySelector("#submit-advice");
    if (textarea) {
      window.setTimeout(() => textarea.focus(), 50);
    }
  }

  function closeFeedbackModal() {
    if (!feedbackModal) return;
    feedbackModal.classList.remove("is-open");
    feedbackModal.hidden = true;
    document.body.classList.remove("modal-open");
    if (feedbackLastFocus && typeof feedbackLastFocus.focus === "function") {
      feedbackLastFocus.focus();
    }
  }

  feedbackOpeners.forEach((btn) => {
    btn.addEventListener("click", openFeedbackModal);
  });

  feedbackClosers.forEach((el) => {
    el.addEventListener("click", closeFeedbackModal);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && feedbackModal && !feedbackModal.hidden) {
      closeFeedbackModal();
    }
  });

  // Coming soon links (Kakao, Instagram, etc.)
  let toastEl = null;
  let toastTimer = null;

  function showComingSoonToast() {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "site-toast";
      toastEl.setAttribute("role", "status");
      toastEl.setAttribute("aria-live", "polite");
      document.body.appendChild(toastEl);
    }

    toastEl.textContent = "준비 중입니다.";
    toastEl.classList.add("is-visible");

    if (toastTimer) window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastEl.classList.remove("is-visible");
    }, 2600);
  }

  document.querySelectorAll("[data-coming-soon]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      showComingSoonToast();
    });
  });
})();
