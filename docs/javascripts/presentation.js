/**
 * Protutech Engineering Documentation
 * Interactive Presentation Engine
 * 
 * Provides keyboard navigation, slide timeline controls, full-screen mode,
 * and hash navigation for section breakdown presentation decks.
 */

(function () {
  'use strict';

  function initPresentationDecks() {
    const decks = document.querySelectorAll('.pt-presentation-deck');
    if (!decks.length) return;

    decks.forEach((deck, deckIndex) => {
      if (deck.dataset.initialized === 'true') return;
      deck.dataset.initialized = 'true';

      const slides = deck.querySelectorAll('.pt-slide');
      if (!slides.length) return;

      let currentIndex = 0;

      // Check URL hash for initial slide index e.g. #slide-4
      const hashMatch = window.location.hash.match(/#slide-(\d+)/);
      if (hashMatch) {
        const parsed = parseInt(hashMatch[1], 10) - 1;
        if (parsed >= 0 && parsed < slides.length) {
          currentIndex = parsed;
        }
      }

      // Build Top Control Bar
      const topBar = document.createElement('div');
      topBar.className = 'pt-pres-topbar';

      const counter = document.createElement('div');
      counter.className = 'pt-pres-counter';

      const fsBtn = document.createElement('button');
      fsBtn.className = 'pt-pres-btn pt-pres-fs-btn';
      fsBtn.type = 'button';
      fsBtn.textContent = 'Toggle Fullscreen';

      topBar.appendChild(counter);
      topBar.appendChild(fsBtn);

      // Build Bottom Navigation Bar
      const navBar = document.createElement('div');
      navBar.className = 'pt-pres-navbar';

      const prevBtn = document.createElement('button');
      prevBtn.className = 'pt-pres-btn pt-pres-prev';
      prevBtn.type = 'button';
      prevBtn.textContent = 'Previous';

      const timeline = document.createElement('div');
      timeline.className = 'pt-pres-timeline';

      const nextBtn = document.createElement('button');
      nextBtn.className = 'pt-pres-btn pt-pres-next';
      nextBtn.type = 'button';
      nextBtn.textContent = 'Next';

      slides.forEach((slide, idx) => {
        const pill = document.createElement('button');
        pill.className = 'pt-pres-pill';
        pill.type = 'button';
        pill.setAttribute('aria-label', `Go to slide ${idx + 1}`);
        pill.dataset.slideIndex = idx;
        const slideTitle = slide.dataset.title || `Slide ${idx + 1}`;
        pill.title = `${idx + 1}. ${slideTitle}`;
        pill.addEventListener('click', () => {
          goToSlide(idx);
        });
        timeline.appendChild(pill);
      });

      navBar.appendChild(prevBtn);
      navBar.appendChild(timeline);
      navBar.appendChild(nextBtn);

      deck.insertBefore(topBar, deck.firstChild);
      deck.appendChild(navBar);

      function updateSlideClasses() {
        slides.forEach((slide, idx) => {
          if (idx === currentIndex) {
            slide.classList.add('pt-slide-active');
            slide.style.display = 'block';
          } else {
            slide.classList.remove('pt-slide-active');
            slide.style.display = 'none';
          }
        });

        const activeTitle = slides[currentIndex].dataset.title || 'Section Breakdown';
        counter.textContent = `Slide ${currentIndex + 1} of ${slides.length} : ${activeTitle}`;

        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex === slides.length - 1;

        const pills = timeline.querySelectorAll('.pt-pres-pill');
        pills.forEach((p, idx) => {
          if (idx === currentIndex) {
            p.classList.add('pt-pill-active');
          } else {
            p.classList.remove('pt-pill-active');
          }
        });

        // Trigger Mermaid rendering re-check if diagram is inside newly visible slide
        const mermaids = slides[currentIndex].querySelectorAll('.mermaid');
        if (mermaids.length && window.mermaid) {
          try {
            window.mermaid.contentLoaded();
          } catch (e) {
            // Ignore if already initialized
          }
        }
      }

      function goToSlide(targetIdx) {
        if (targetIdx < 0 || targetIdx >= slides.length) return;
        currentIndex = targetIdx;
        updateSlideClasses();
        history.replaceState(null, null, `#slide-${currentIndex + 1}`);
      }

      prevBtn.addEventListener('click', () => goToSlide(currentIndex - 1));
      nextBtn.addEventListener('click', () => goToSlide(currentIndex + 1));

      fsBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
          if (deck.requestFullscreen) {
            deck.requestFullscreen();
          } else if (deck.webkitRequestFullscreen) {
            deck.webkitRequestFullscreen();
          }
        } else {
          if (document.exitFullscreen) {
            document.exitFullscreen();
          }
        }
      });

      document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement === deck) {
          deck.classList.add('pt-deck-fullscreen');
          fsBtn.textContent = 'Exit Fullscreen';
        } else {
          deck.classList.remove('pt-deck-fullscreen');
          fsBtn.textContent = 'Toggle Fullscreen';
        }
      });

      // Global Keyboard Controls (Active when deck in view or fullscreen)
      window.addEventListener('keydown', (e) => {
        const isFullscreen = document.fullscreenElement === deck;
        const rect = deck.getBoundingClientRect();
        const isInViewport = rect.top < window.innerHeight && rect.bottom > 0;

        if (!isFullscreen && !isInViewport) return;

        if (e.key === 'ArrowRight' || e.key === 'PageDown' || (e.key === ' ' && isFullscreen)) {
          if (currentIndex < slides.length - 1) {
            e.preventDefault();
            goToSlide(currentIndex + 1);
          }
        } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
          if (currentIndex > 0) {
            e.preventDefault();
            goToSlide(currentIndex - 1);
          }
        } else if ((e.key === 'f' || e.key === 'F') && !e.ctrlKey && !e.metaKey && !e.altKey) {
          const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
          if (activeTag !== 'input' && activeTag !== 'textarea') {
            e.preventDefault();
            fsBtn.click();
          }
        }
      });

      // Touch Swipe Controls for Mobile/Tablet
      let touchStartX = 0;
      let touchEndX = 0;

      deck.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });

      deck.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
          if (diff > 0) {
            goToSlide(currentIndex + 1); // Swipe left -> Next
          } else {
            goToSlide(currentIndex - 1); // Swipe right -> Previous
          }
        }
      }, { passive: true });

      // Initialize initial state
      updateSlideClasses();
    });
  }

  // Hook into document load and MkDocs Material SPA instant transitions
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPresentationDecks);
  } else {
    initPresentationDecks();
  }

  // Material for MkDocs instant navigation listener
  if (typeof location$ !== 'undefined') {
    location$.subscribe(() => {
      setTimeout(initPresentationDecks, 100);
    });
  }
})();
