document.addEventListener("DOMContentLoaded", () => {
  let currentCategory = "all";
  let searchQuery = "";
  let bookmarkedFilter = false;

  const articlesContainer = document.getElementById("articlesContainer");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const categoryTabs = document.getElementById("categoryTabs");
  const bookmarkToggleBtn = document.getElementById("bookmarkToggleBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const refreshIcon = document.getElementById("refreshIcon");
  const feedModal = document.getElementById("feedModal");
  const openFeedModalBtn = document.getElementById("openFeedModalBtn");
  const closeFeedModalBtn = document.getElementById("closeFeedModalBtn");
  const cancelModalBtn = document.getElementById("cancelModalBtn");
  const addFeedForm = document.getElementById("addFeedForm");

  async function loadArticles() {
    articlesContainer.innerHTML = "";
    emptyState.classList.add("hidden");

    const params = new URLSearchParams();
    if (currentCategory && currentCategory !== "all") params.append("category", currentCategory);
    if (searchQuery) params.append("search", searchQuery);
    if (bookmarkedFilter) params.append("bookmarked", "true");

    try {
      const res = await fetch(`/api/articles?${params.toString()}`);
      const data = await res.json();
      const articles = data.articles || [];

      if (articles.length === 0) {
        emptyState.classList.remove("hidden");
        return;
      }

      articles.forEach((art) => {
        const card = createArticleCard(art);
        articlesContainer.appendChild(card);
      });
    } catch (err) {
      console.error("Failed to load articles:", err);
      emptyState.classList.remove("hidden");
    }
  }

  function createArticleCard(art) {
    const div = document.createElement("div");
    div.className = `card-article bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col justify-between ${art.is_read ? 'article-read' : ''}`;

    const formattedDate = art.published_at ? art.published_at.slice(0, 10) : "Recent";
    const fallbackImage = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&auto=format&fit=crop&q=80";
    const imageSrc = art.image_url || fallbackImage;

    div.innerHTML = `
      <div>
        <div class="relative h-44 w-full bg-slate-100 overflow-hidden">
          <img src="${imageSrc}" alt="Article cover" class="w-full h-full object-cover" onerror="this.src='${fallbackImage}'" />
          <span class="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md text-white text-xs px-2.5 py-1 rounded-full font-medium">
            ${art.category || 'News'}
          </span>
        </div>
        <div class="p-5">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>${art.source_name || 'PulseNews'}</span>
            <span>${formattedDate}</span>
          </div>
          <h3 class="font-bold text-slate-900 line-clamp-2 hover:text-indigo-600 transition-colors text-base">
            <a href="${art.link}" target="_blank" rel="noopener noreferrer">${art.title}</a>
          </h3>
          <p class="mt-2 text-xs text-slate-600 line-clamp-3 leading-relaxed">${art.summary || 'Click link to read full story.'}</p>
        </div>
      </div>
      <div class="p-5 pt-0 border-t border-slate-100 mt-4 flex items-center justify-between">
        <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1 mark-read-link">
          <span>Read Story</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
        <div class="flex items-center space-x-3 text-slate-400">
          <button class="toggle-read-btn hover:text-slate-700 text-sm" title="Toggle Read" data-id="${art.id}">
            <i class="${art.is_read ? 'fa-solid text-emerald-600' : 'fa-regular'} fa-circle-check"></i>
          </button>
          <button class="toggle-bookmark-btn hover:text-amber-500 text-sm" title="Bookmark" data-id="${art.id}">
            <i class="${art.is_bookmarked ? 'fa-solid text-amber-500' : 'fa-regular'} fa-bookmark"></i>
          </button>
        </div>
      </div>
    `;

    // Hook Bookmark
    div.querySelector(".toggle-bookmark-btn").addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      const icon = btn.querySelector("i");
      const res = await fetch(`/api/articles/${art.id}/bookmark`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.is_bookmarked) {
          icon.className = "fa-solid text-amber-500 fa-bookmark";
        } else {
          icon.className = "fa-regular fa-bookmark";
          if (bookmarkedFilter) div.remove();
        }
      }
    });

    // Hook Read State
    const readToggle = div.querySelector(".toggle-read-btn");
    readToggle.addEventListener("click", async () => {
      const icon = readToggle.querySelector("i");
      const res = await fetch(`/api/articles/${art.id}/read`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.is_read) {
          icon.className = "fa-solid text-emerald-600 fa-circle-check";
          div.classList.add("article-read");
        } else {
          icon.className = "fa-regular fa-circle-check";
          div.classList.remove("article-read");
        }
      }
    });

    return div;
  }

  // Category Filter
  categoryTabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;
    categoryTabs.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active");
      b.classList.add("text-slate-600");
    });
    btn.classList.add("active");
    btn.classList.remove("text-slate-600");
    currentCategory = btn.getAttribute("data-category");
    loadArticles();
  });

  // Bookmark Filter Toggle
  bookmarkToggleBtn.addEventListener("click", () => {
    bookmarkedFilter = !bookmarkedFilter;
    if (bookmarkedFilter) {
      bookmarkToggleBtn.classList.add("bg-amber-50", "text-amber-700", "border", "border-amber-200");
    } else {
      bookmarkToggleBtn.classList.remove("bg-amber-50", "text-amber-700", "border", "border-amber-200");
    }
    loadArticles();
  });

  // Debounced Search
  let searchTimeout = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      searchQuery = e.target.value.trim();
      loadArticles();
    }, 300);
  });

  // Refresh Feeds
  refreshBtn.addEventListener("click", async () => {
    refreshIcon.classList.add("fa-spin");
    try {
      await fetch("/api/refresh", { method: "POST" });
      await loadArticles();
    } catch (e) {
      console.error(e);
    } finally {
      refreshIcon.classList.remove("fa-spin");
    }
  });

  // Modal controls
  openFeedModalBtn.addEventListener("click", () => feedModal.classList.remove("hidden"));
  const closeModal = () => feedModal.classList.add("hidden");
  closeFeedModalBtn.addEventListener("click", closeModal);
  cancelModalBtn.addEventListener("click", closeModal);

  addFeedForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("feedName").value;
    const url = document.getElementById("feedUrl").value;
    const category = document.getElementById("feedCategory").value;

    const res = await fetch("/api/sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, url, category }),
    });

    if (res.ok) {
      closeModal();
      addFeedForm.reset();
      refreshBtn.click();
    } else {
      alert("Could not add feed. Check if the URL is valid or already exists.");
    }
  });

  // Initial Load
  loadArticles();
});
