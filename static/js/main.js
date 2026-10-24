// ══════════════════════════════════════════════════
//  CONFIG
// ══════════════════════════════════════════════════
const SCHEMES_API = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:5000';
const ML_API = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:5000';
let allSchemes = [];
let currentLang = localStorage.getItem("language") || "en";
let activeSearchContext = null;
let currentlyDisplayedSchemes = null;
let currentActiveModalScheme = null;

// ══════════════════════════════════════════════════
//  LOAD SCHEMES
// ══════════════════════════════════════════════════
async function loadSchemes() {
  try {
    const res = await fetch(`${SCHEMES_API}/api/schemes`);
    const data = await res.json();
    allSchemes = data.schemes || [];
    const totalEl = document.getElementById('totalCount');
    if (totalEl) totalEl.textContent = allSchemes.length + '+';
    renderSchemes(allSchemes);
  } catch (err) {
    const grid = document.getElementById('schemesGrid');
    if (grid) {
      grid.innerHTML = `
        <div class="no-results">
          <h3>Could not connect to server</h3>
          <p>Make sure your Flask backend is running on port 5000</p>
        </div>`;
    }
    const countEl = document.getElementById('resultsCount');
    if (countEl) countEl.textContent = 'Connection error';
  }
}

// ══════════════════════════════════════════════════
//  RENDER SCHEMES
// ══════════════════════════════════════════════════
function renderSchemes(schemes, searchContext = null) {
    currentlyDisplayedSchemes = schemes;
    if (searchContext !== null) {
        activeSearchContext = searchContext;
    } else if (searchContext === null && !schemes) {
        activeSearchContext = null;
    }

    const grid = document.getElementById('schemesGrid');
    const count = document.getElementById('resultsCount');
    if (!grid || !count) return;

    // Current language
    const isHindi = currentLang === "hi";

    // Hindi category names
    const categoryNames = {
        agriculture: "कृषि",
        health: "स्वास्थ्य",
        education: "शिक्षा",
        housing: "आवास",
        employment: "रोजगार",
        women: "महिला",
        financial: "वित्तीय",
        elderly: "वृद्धावस्था",
        youth: "युवा",
        disability: "दिव्यांगजन",
        rural: "ग्रामीण क्षेत्र",
        "rural area": "ग्रामीण क्षेत्र"
    };

    // No schemes found
    if (!schemes || !schemes.length) {
        const noMatchMsg = activeSearchContext && activeSearchContext.age
            ? (isHindi ? `आयु ${activeSearchContext.age} के लिए कोई योजना नहीं मिली` : `No schemes found for age ${activeSearchContext.age}`)
            : (isHindi ? "कोई योजना नहीं मिली" : "No schemes found");

        grid.innerHTML = `
            <div class="no-results">
                <h3>${noMatchMsg}</h3>
                <p>${isHindi ? "कृपया कोई अन्य आयु, श्रेणी या खोज शब्द आज़माएं।" : "Try another age, category, or search term."}</p>
            </div>
        `;

        count.innerHTML = isHindi
            ? "कोई परिणाम नहीं मिला"
            : "No results found";

        return;
    }

    // Results count
    count.innerHTML = isHindi
        ? `कुल <strong>${schemes.length}</strong> योजनाएं दिखाई जा रही हैं`
        : `Showing <strong>${schemes.length}</strong> scheme${schemes.length !== 1 ? "s" : ""}`;

    // Render cards
    grid.innerHTML = schemes.map(s => {

        const title = isHindi
            ? (s.title_hi || s.title)
            : s.title;

        const description = isHindi
            ? (s.description_hi || s.description)
            : s.description;

        const benefits = isHindi
            ? (s.benefits_hi || s.benefits)
            : s.benefits;

        const ministry = isHindi
            ? (s.ministry_hi || s.ministry)
            : s.ministry;

        const category = isHindi
            ? (categoryNames[s.category] || s.category)
            : s.category;

        const isRural = (s.tags || []).some(t => t.toLowerCase() === 'rural area' || t.toLowerCase() === 'rural') ||
                        (s.tags_hi || []).some(t => t.includes('ग्रामीण'));

        return `
            <div class="scheme-card"
                 onclick="openModal(${JSON.stringify(s).replace(/"/g, '&quot;')})">

                <div class="card-top">

                    <div class="card-badges">
                        <span class="category-badge cat-${s.category}">
                            ${category}
                        </span>
                        ${isRural ? `<span class="tag-badge tag-rural" title="Rural Area Scheme">🏡 ${isHindi ? "ग्रामीण क्षेत्र" : "Rural Area"}</span>` : ''}
                    </div>

                    <div class="active-dot"></div>

                </div>

                <div class="card-title">
                    ${title}
                </div>

                <div class="card-desc">
                    ${description}
                </div>

                <div class="card-benefit">
                    ${benefits}
                </div>

                <div class="card-tags">
                    ${((isHindi && s.tags_hi && s.tags_hi.length) ? s.tags_hi : (s.tags || [])).slice(0, 3).map(t => {
                        const isRural = t.toLowerCase() === 'rural area' || t === 'ग्रामीण क्षेत्र';
                        return `<span class="card-tag ${isRural ? 'card-tag-rural' : ''}">#${t}</span>`;
                    }).join('')}
                </div>

                <div class="card-footer">

                    <span class="ministry-name">
                        ${ministry}
                    </span>

                    <a href="${s.application_url}"
                       target="_blank"
                       class="apply-btn"
                       onclick="event.stopPropagation()">

                       ${isHindi ? "आवेदन करें" : "Apply"}

                    </a>

                </div>

            </div>
        `;

    }).join('');
}

// ══════════════════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════════════════
async function handleSearch() {
  const searchInput = document.getElementById('searchInput');
  const q = searchInput ? searchInput.value.trim() : '';

  if (!q) {
    renderSchemes(allSchemes);
    return;
  }

  const grid = document.getElementById('schemesGrid');
  if (grid) grid.innerHTML = `<div class="loading"><div class="spinner"></div><span>Searching schemes...</span></div>`;

  try {
    const res = await fetch(`${SCHEMES_API}/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderSchemes(data.schemes || []);
  } catch {
    if (grid) grid.innerHTML = `<div class="no-results"><h3>Search failed</h3><p>Please try again</p></div>`;
  }
}

// Search input event listeners
const searchEl = document.getElementById('searchInput');
if (searchEl) {
  searchEl.addEventListener('input', () => handleSearch());
  searchEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSearch();
  });
}

// ══════════════════════════════════════════════════
//  FILTER BY CATEGORY
// ══════════════════════════════════════════════════
async function filterByCategory(category, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.value = '';

  if (category === 'all') { renderSchemes(allSchemes); return; }

  const grid = document.getElementById('schemesGrid');
  if (grid) grid.innerHTML = `<div class="loading"><div class="spinner"></div><span>Filtering...</span></div>`;

  try {
    const ageVal = document.getElementById('ageInput') ? document.getElementById('ageInput').value.trim() : '';
    const params = new URLSearchParams({ category });
    if (ageVal) params.append('age', ageVal);

    const res = await fetch(`${SCHEMES_API}/api/filter?${params.toString()}`);
    const data = await res.json();
    renderSchemes(data.schemes || []);
  } catch {
    const filtered = allSchemes.filter(s => {
      if (category === 'rural' || category === 'rural area') {
        return (s.tags || []).some(t => t.toLowerCase().includes('rural')) ||
               (s.tags_hi || []).some(t => t.includes('ग्रामीण')) ||
               s.category === 'rural';
      }
      return s.category === category;
    });
    if (filtered.length) {
      renderSchemes(filtered);
    } else if (grid) {
      grid.innerHTML = `<div class="no-results"><h3>Filter failed</h3></div>`;
    }
  }
}

// ══════════════════════════════════════════════════
//  SCHEME DETAIL MODAL
// ══════════════════════════════════════════════════
function openModal(s) {
  const isHindi = currentLang === "hi";

  const title = isHindi ? (s.title_hi || s.title) : s.title;
  const description = isHindi ? (s.description_hi || s.description) : s.description;
  const benefits = isHindi ? (s.benefits_hi || s.benefits) : s.benefits;
  const ministry = isHindi ? (s.ministry_hi || s.ministry) : s.ministry;

  const categoryNames = {
    agriculture: "कृषि",
    health: "स्वास्थ्य",
    education: "शिक्षा",
    housing: "आवास",
    employment: "रोजगार",
    women: "महिला",
    financial: "वित्तीय",
    elderly: "वृद्धावस्था",
    youth: "युवा",
    disability: "दिव्यांगजन",
    rural: "ग्रामीण क्षेत्र",
    "rural area": "ग्रामीण क्षेत्र"
  };

  const category = isHindi ? (categoryNames[s.category] || s.category) : s.category;

  document.getElementById('modalCategory').textContent = '🏛 ' + category.toUpperCase();
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalMinistry').textContent =
    ministry + ' • ' + (isHindi ? 'शुरू किया गया: ' : 'Since ') + s.launched_year;
  document.getElementById('modalDesc').textContent = description;
  document.getElementById('modalBenefits').textContent = benefits;
  document.getElementById('modalApplyBtn').href = s.application_url;

  const e = s.eligibility || {};

  document.getElementById('modalEligibility').innerHTML = `
    <div class="elig-item">
      <div class="elig-label">${isHindi ? "आयु सीमा" : "Age Range"}</div>
      <div class="elig-value">
        ${e.min_age ?? 0} – ${e.max_age ?? (isHindi ? "कोई सीमा नहीं" : "No limit")} ${isHindi ? "वर्ष" : "years"}
      </div>
    </div>

    <div class="elig-item">
      <div class="elig-label">${isHindi ? "लिंग" : "Gender"}</div>
      <div class="elig-value">
        ${e.gender ?? (isHindi ? "सभी" : "All")}
      </div>
    </div>

    <div class="elig-item">
      <div class="elig-label">${isHindi ? "आय सीमा" : "Income Limit"}</div>
      <div class="elig-value">
        ${e.income_limit
          ? '₹' + e.income_limit.toLocaleString('en-IN')
          : (isHindi ? "कोई सीमा नहीं" : "No limit")}
      </div>
    </div>

    <div class="elig-item">
      <div class="elig-label">${isHindi ? "राज्य" : "State"}</div>
      <div class="elig-value">
        ${e.state ?? (isHindi ? "पूरे भारत में" : "All India")}
      </div>
    </div>
  `;

  currentActiveModalScheme = s;

  const tagsList = (isHindi && s.tags_hi && s.tags_hi.length) ? s.tags_hi : (s.tags || []);

  document.getElementById('modalTags').innerHTML =
    tagsList
      .map(t => {
        const isRuralTag = t.toLowerCase() === 'rural area' || t === 'ग्रामीण क्षेत्र';
        return `<span class="tag ${isRuralTag ? 'tag-rural-modal' : ''}" onclick="filterByTag('${t.replace(/'/g, "\\'")}')">#${t}</span>`;
      })
      .join('');

  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function filterByTag(tag) {
  closeModal();
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.value = tag;
    handleSearch();
    const schemesSection = document.getElementById('schemes');
    if (schemesSection) {
      schemesSection.scrollIntoView({ behavior: 'smooth' });
    }
  }
}

function closeModal() {
  currentActiveModalScheme = null;
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

function closeModalOnOverlay(e) {
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}

// ══════════════════════════════════════════════════
//  URL DETECTOR — OPEN / CLOSE
// ══════════════════════════════════════════════════
function openDetector() {
  document.getElementById('detOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeDetector() {
  document.getElementById('detOverlay').classList.remove('open');
  document.body.style.overflow = '';
  document.getElementById('urlInput').value = '';
  document.getElementById('fileInput').value = '';
  document.getElementById('fileName').style.display = 'none';
  document.getElementById('fileName').textContent = '';
  ['url', 'file'].forEach(t => {
    document.getElementById(t + 'Spinner').classList.remove('show');
    document.getElementById(t + 'Result').classList.remove('show');
    document.getElementById(t + 'ResultBox').textContent = '';
    document.getElementById(t + 'ResultBox').className = 'det-result-box';
    document.getElementById(t + 'Btn').disabled = false;
  });
}

function closeDetectorOnOverlay(e) {
  if (e.target === document.getElementById('detOverlay')) closeDetector();
}

// ══════════════════════════════════════════════════
//  URL DETECTOR — TABS
// ══════════════════════════════════════════════════
function switchDetectorTab(tab) {
  ['url', 'file'].forEach(t => {
    document.getElementById('tab-' + t).classList.toggle('active', t === tab);
    document.getElementById('panel-' + t).classList.toggle('active', t === tab);
  });
}

// ══════════════════════════════════════════════════
//  FILE SELECTED
// ══════════════════════════════════════════════════
function onFileSelected(input) {
  const nameEl = document.getElementById('fileName');
  if (input.files.length) {
    nameEl.textContent = '📎 ' + input.files[0].name;
    nameEl.style.display = 'block';
  } else {
    nameEl.style.display = 'none';
  }
}

// ══════════════════════════════════════════════════
//  ANALYZE URL
// ══════════════════════════════════════════════════
async function analyzeURL() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { alert('Please enter a URL first.'); return; }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    alert('URL must start with http:// or https://');
    return;
  }

  setDetectorLoading('url', true);

  try {
    const res = await fetch(`${ML_API}/api/detect-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (data.error) {
      showDetectorResult('url', '❌ Error: ' + data.error, 'fake');
    } else {
      showDetectorResult('url', data.result, classifyResult(data.result));
    }
  } catch (err) {
    showDetectorResult('url',
      '❌ Could not connect to ML backend.\n\nMake sure Flask server is running on port 5001.\n\nError: ' + err.message,
      'fake'
    );
  } finally {
    setDetectorLoading('url', false);
  }
}

// ══════════════════════════════════════════════════
//  ANALYZE FILE
// ══════════════════════════════════════════════════
async function analyzeFile() {
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files.length) { alert('Please select a file first.'); return; }

  const file = fileInput.files[0];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'txt'].includes(ext)) { alert('Only PDF and TXT files are supported.'); return; }

  setDetectorLoading('file', true);

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${ML_API}/api/detect-file`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.error) {
      showDetectorResult('file', '❌ Error: ' + data.error, 'fake');
    } else {
      showDetectorResult('file', data.result, classifyResult(data.result));
    }
  } catch (err) {
    showDetectorResult('file',
      '❌ Could not connect to ML backend.\n\nMake sure Flask server is running on port 5001.\n\nError: ' + err.message,
      'fake'
    );
  } finally {
    setDetectorLoading('file', false);
  }
}

// ══════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════
function setDetectorLoading(type, loading) {
  document.getElementById(type + 'Btn').disabled = loading;
  document.getElementById(type + 'Spinner').classList.toggle('show', loading);
  if (loading) document.getElementById(type + 'Result').classList.remove('show');
}

function showDetectorResult(type, text, cssClass) {
  const box = document.getElementById(type + 'ResultBox');
  box.textContent = text;
  box.className = 'det-result-box ' + cssClass;
  document.getElementById(type + 'Result').classList.add('show');
}

function classifyResult(text) {
  const t = text.toUpperCase();
  if (t.includes('FAKE') || t.includes('HIGH') || t.includes('SCAM')) return 'fake';
  if (t.includes('SUSPICIOUS') || t.includes('MEDIUM')) return 'suspicious';
  if (t.includes('REAL') || t.includes('LEGITIMATE') || t.includes('LOW')) return 'real';
  return '';
}

// ESC closes any modal
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeDetector(); }
});

// ══════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════
loadSchemes();

const placeholders = [
  "Search schemes or enter age (e.g. 25)...",
  "Type 18 for youth & scholarships...",
  "Search for farmer schemes...",
  "Type 60 for senior citizen & pensions...",
  "Search for student or youth schemes...",
  "Search e.g. 'farmer 45' or 'scholarship 20'..."
];

let pIndex = 0;
setInterval(() => {
  pIndex = (pIndex + 1) % placeholders.length;
  const sEl = document.getElementById('searchInput');
  if (sEl && !sEl.value) sEl.placeholder = placeholders[pIndex];
}, 3500);

function toggleDarkMode() {
  document.documentElement.classList.toggle('dark-mode');
  const icon = document.getElementById('darkIcon');
  if (document.documentElement.classList.contains('dark-mode')) {
    icon.classList.replace('fa-moon', 'fa-sun');
    localStorage.setItem('darkMode', 'on');
  } else {
    icon.classList.replace('fa-sun', 'fa-moon');
    localStorage.setItem('darkMode', 'off');
  }
}

// Page load pe dark mode check karo
window.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('darkMode') === 'on') {
    document.documentElement.classList.add('dark-mode');
    document.getElementById('darkIcon').classList.replace('fa-moon', 'fa-sun');
  }
});

// ══════════════════════════════════════════════════
//  MOBILE MENU TOGGLE (hamburger <-> X animation)
// ══════════════════════════════════════════════════
function toggleMenu() {
  const links = document.querySelector('.nav-links');
  const burger = document.querySelector('.hamburger');
  if (links) links.classList.toggle('open');
  if (burger) burger.classList.toggle('open');
} 

// ===============================
// LANGUAGE SWITCHER
// ===============================
const languageData = {
    en: {
        home: "Home",
        schemes: "All Schemes",
        about: "About",
        detector: "URL Detector",
        govt: "Government of India",
        search: "Search"
    },
    hi: {
        home: "होम",
        schemes: "सभी योजनाएँ",
        about: "जानकारी",
        detector: "URL डिटेक्टर",
        govt: "भारत सरकार",
        search: "खोजें"
    }
};

function changeLanguage(language) {
    currentLang = language;
    localStorage.setItem("language", language);
    document.documentElement.lang = language;

    const data = languageData[language] || languageData.en;
    if (typeof allSchemes !== "undefined" && allSchemes.length) {
      renderSchemes(currentlyDisplayedSchemes || allSchemes);
    }

    // Re-render modal in new language if currently open
    if (currentActiveModalScheme && document.getElementById('modalOverlay') && document.getElementById('modalOverlay').classList.contains('open')) {
      openModal(currentActiveModalScheme);
    }

    // NAVBAR
    document.querySelectorAll(".nav-links a").forEach(link => {
        const text = link.textContent.trim();
        if (text.includes("Home") || text.includes("होम")) {
            link.innerHTML = link.innerHTML.replace(/Home|होम/g, data.home);
        }
        if (text.includes("All Schemes") || text.includes("सभी योजनाएँ")) {
            link.innerHTML = link.innerHTML.replace(/All Schemes|सभी योजनाएँ/g, data.schemes);
        }
        if (text.includes("About") || text.includes("जानकारी")) {
            link.innerHTML = link.innerHTML.replace(/About|जानकारी/g, data.about);
        }
        if (text.includes("URL Detector") || text.includes("URL डिटेक्टर")) {
            link.innerHTML = link.innerHTML.replace(/URL Detector|URL डिटेक्टर/g, data.detector);
        }
    });

    // ALL PAGE TEXT & TAG BUTTONS
    document.querySelectorAll("[data-en]").forEach(element => {
        const val = language === "hi" ? element.getAttribute("data-hi") : element.getAttribute("data-en");
        if (val) {
            if (val.includes("<")) {
                element.innerHTML = val;
            } else {
                element.textContent = val;
            }
        }
    });

    // SEARCH INPUT PLACEHOLDER
    const sInput = document.getElementById("searchInput");
    if (sInput) {
        if (language === "hi") {
            sInput.placeholder = sInput.getAttribute("data-placeholder-hi") || "योजनाएं खोजें... जैसे किसान, 25, छात्र";
        } else {
            sInput.placeholder = sInput.getAttribute("data-placeholder-en") || "Search schemes... e.g. farmer, 25, student";
        }
    }
}

// SAVED LANGUAGE
document.addEventListener("DOMContentLoaded", function () {
    const savedLanguage = localStorage.getItem("language") || "en";
    const languageSelect = document.getElementById("languageSelect");

    if (languageSelect) {
        languageSelect.value = savedLanguage;
        languageSelect.addEventListener("change", function () {
            changeLanguage(this.value);
        });
    }

    changeLanguage(savedLanguage);
});