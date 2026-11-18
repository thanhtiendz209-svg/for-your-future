/**
 * For Your Future — Client SPA Controller
 * Exactly matching the GUI, features, routes, and layout of Trachngiemtinhcach (Lumina):
 * - Home (Hero, IntroCards, HowItWorks, QuizPicker, TypeGrid, CareerPreview, Faq, CtaBand)
 * - Quizzes (MBTI, RIASEC, Big Five + QuizPlayer + Results)
 * - Personalities (16 MBTI types + 6 RIASEC types + Detail modal)
 * - Careers & Universities (UniversityExplorer + Career fields + Filters)
 * - Universities Directory (126 Universities + Admission scores + Floor scores)
 * - Profile (Merged quiz results + History)
 * - About (Methodologies, Data policy, Contact, FAQ)
 * 
 * TUYỆT ĐỐI KHÔNG TỰ THÊM HAY BỚT TÍNH NĂNG.
 */

// --- STATE & STORAGE ---
const state = {
  currentRoute: window.location.hash || '#home',
  quizzes: [],
  questions: {},
  personalities: [],
  riasecTypes: [],
  riasecCombinations: [],
  riasecCombFilter: '',
  riasecCombLetter: 'ALL',
  careers: [],
  universities: [],
  floors: {},
  // Active quiz session
  activeQuiz: null,
  quizIndex: 0,
  quizAnswers: [],
  quizPhase: 'intro', // 'intro', 'quiz', 'analyzing', 'result'
  // Profile & Saved results
  currentUser: JSON.parse(localStorage.getItem('fyf_current_user') || 'null'),
  authToken: localStorage.getItem('fyf_auth_token') || null,
  results: {
    mbti: JSON.parse(localStorage.getItem('fyf_result_mbti') || 'null'),
    riasec: JSON.parse(localStorage.getItem('fyf_result_riasec') || 'null'),
    bigfive: JSON.parse(localStorage.getItem('fyf_result_bigfive') || 'null'),
    cognitive: JSON.parse(localStorage.getItem('fyf_result_cognitive') || 'null'),
  },
  // Explorer filters
  uniFilter: {
    query: '',
    region: 'Tất cả',
    tuition: 'Tất cả',
    score: 'Tất cả',
  },
  activePersonalityTab: 'mbti', // 'mbti' | 'riasec'
  // Student Profile 4-tab model
  studentProfile: JSON.parse(localStorage.getItem('fyf_student_profile') || 'null') || {
    fullName: 'Nguyễn Văn A',
    schoolName: 'THPT Chuyên Long An',
    province: 'Long An',
    priorityZone: 'KV2',
    priorityBonus: 0.5,
    gpa5Semesters: 8.4,
    conduct12: 'Tốt',
    subjectGroup: 'A01',
    scores: {
      math: 8.5,
      physics: 8.0,
      english: 8.5,
      chemistry: 7.0,
      literature: 7.5,
      biology: 6.5,
    },
    ielts: 6.5,
    dgnlHcm: 850,
    annualBudget: 40000000,
    heightCm: 172,
    weightKg: 65,
    eyesightDiop: 1.5,
  },
  activeProfileTab: 'tests', // 'tests' | 'personal' | 'academic' | 'finance-health'
  comparisonSchools: ['uni-001', 'uni-002'],
  schoolDetails: [],
  schoolProgramFilter: '',
  schoolProgramMethod: 'Tất cả',
};

// --- DATA INITIALIZATION ---
// Fetch each file once per visit. Failed requests can be retried without losing
// successful datasets; stable URLs still revalidate against server updates.
const staticDataRequests = new Map();
const staticDataReady = new Set();
function loadStaticData(key, file) {
  if (staticDataReady.has(key)) return Promise.resolve();
  if (staticDataRequests.has(key)) return staticDataRequests.get(key);
  const request = fetch(`/data/${file}`, { cache: 'no-cache' })
    .then(response => {
      if (!response.ok) throw new Error(`Không tải được ${file}`);
      return response.json();
    })
    .then(data => { state[key] = data; staticDataReady.add(key); })
    .finally(() => staticDataRequests.delete(key));
  staticDataRequests.set(key, request);
  return request;
}
async function loadAllData() {
  const core = [
    ['quizzes', 'quizzes.json'], ['questions', 'questions.json'],
    ['personalities', 'personalities.json'], ['riasecTypes', 'riasec_types.json'],
    ['careers', 'careers.json'], ['universities', 'universities.json'],
    ['floors', 'admission_floor_summaries.json'],
  ];
  const results = await Promise.allSettled(core.map(([key, file]) => loadStaticData(key, file)));
  results.forEach(result => { if (result.status === 'rejected') console.error('Lỗi khi tải dữ liệu tĩnh:', result.reason); });
}
function routeDataFiles(base, param) {
  const files = [];
  if (['huong-nghiep', 'tra-cuu-nganh', 'truong-dai-hoc', 'so-sanh'].includes(base)) {
    files.push(['schoolDetails', 'school_details.json']);
  }
  if ((base === 'home' && state.activePersonalityTab === 'riasec') || base === 'nhom-tinh-cach' || (base === 'ket-qua' && (!param || param === 'riasec'))) {
    files.push(['riasecCombinations', 'riasec_combinations.json']);
  }
  return files.filter(([key]) => !staticDataReady.has(key));
}

// --- UTILITIES ---
function refreshIcons() {
  if (!window.lucide || typeof window.lucide.createIcons !== 'function') return;
  // Lucide retains data-lucide on its SVGs. Mark only fresh placeholders so
  // subsequent updates do not recreate icons already displayed on the page.
  const placeholders = document.querySelectorAll('[data-lucide]:not(svg)');
  if (!placeholders.length) return;
  placeholders.forEach(icon => icon.setAttribute('data-fyf-icon', icon.getAttribute('data-lucide')));
  window.lucide.createIcons({ nameAttr: 'data-fyf-icon' });
  document.querySelectorAll('[data-fyf-icon]').forEach(icon => icon.removeAttribute('data-fyf-icon'));
}

const visibleMotion = { observer: null, targets: new Map(), preference: null };
function applyVisibleMotion(target, visible) {
  const active = visible && !document.hidden && !visibleMotion.preference.matches;
  if (target.matches('.founders-hero')) {
    target.classList.toggle('motion-paused', !active);
  } else if (!target.dataset.motionFailed) {
    const source = active ? target.dataset.animatedSrc : target.dataset.stillSrc;
    if (source && target.getAttribute('src') !== source) target.setAttribute('src', source);
  }
}
function refreshVisibleMotion() {
  if (typeof window.IntersectionObserver !== 'function') return;
  if (!visibleMotion.observer) {
    visibleMotion.preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    visibleMotion.observer = new window.IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!visibleMotion.targets.has(entry.target)) return;
        visibleMotion.targets.set(entry.target, entry.isIntersecting);
        applyVisibleMotion(entry.target, entry.isIntersecting);
      });
    }, { threshold: 0 });
    const update = () => visibleMotion.targets.forEach((visible, target) => applyVisibleMotion(target, visible));
    document.addEventListener('visibilitychange', update);
    visibleMotion.preference.addEventListener('change', update);
  }
  visibleMotion.targets.forEach((_, target) => {
    if (!target.isConnected) {
      visibleMotion.observer.unobserve(target);
      visibleMotion.targets.delete(target);
    }
  });
  document.querySelectorAll('.founders-hero, .quiz-cover-image[data-animated-src]:not([data-animated-src=""])').forEach(target => {
    if (visibleMotion.targets.has(target)) return;
    visibleMotion.targets.set(target, false);
    applyVisibleMotion(target, false);
    visibleMotion.observer.observe(target);
  });
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const styles = {
    info: 'bg-navy text-paper border border-white/20 shadow-border-hover',
    success: 'bg-emerald-700 text-white shadow-border-hover',
    warning: 'bg-amber-600 text-white shadow-border-hover',
    error: 'bg-danger text-white shadow-border-hover',
  };
  const toast = document.createElement('div');
  toast.className = `px-4 py-3 rounded-[14px] text-xs sm:text-sm font-medium transition-all transform duration-300 pointer-events-auto flex items-center space-x-2 ${styles[type] || styles.info}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function formatVND(amount) {
  if (!amount && amount !== 0) return 'Đang cập nhật';
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(amount);
}

let detailModalFocus=null;
function openDetailModal(contentHtml) {
  const modal = document.getElementById('detail-modal');
  const body = document.getElementById('detail-modal-body');
  if (modal && body) {
    if(modal.classList.contains('hidden'))detailModalFocus=document.activeElement;
    body.innerHTML = contentHtml;
    body.scrollTop=0;
    const card=document.getElementById('detail-modal-card');if(card)card.scrollTop=0;
    modal.classList.remove('hidden');
    document.body.classList.add('detail-modal-open');
    document.getElementById('btn-close-detail-modal')?.focus({preventScroll:true});
    refreshIcons();
  }
}

function closeDetailModal() {
  const modal = document.getElementById('detail-modal');
  if (modal) modal.classList.add('hidden');
  document.body.classList.remove('detail-modal-open');
  if(detailModalFocus?.isConnected)detailModalFocus.focus({preventScroll:true});
  detailModalFocus=null;
}

// --- ROUTER DISPATCHER ---
let routeRenderVersion = 0;
async function renderRoute() {
  const container = document.getElementById('app-container');
  if (!container) return;

  const renderVersion = ++routeRenderVersion;
  const rawHash = window.location.hash || '#home';
  state.currentRoute = rawHash;

  // Split route & params (e.g. #trac-nghiem/mbti -> base='#trac-nghiem', param='mbti')
  const parts = rawHash.slice(1).split('/');
  const base = parts[0] || 'home';
  if(base!=='tra-cuu-nganh')majorLookupRenderedGroups=new Map();
  document.body.classList.toggle('chat-page-active',base==='tu-van');
  document.body.classList.toggle('quiz-page-active',base==='trac-nghiem'&&Boolean(parts[1]));
  if(base!=='tu-van'){chatRuntime.onLeave?.();chatRuntime.onLeave=null;chatRuntime.controller?.abort();chatRuntime.cleanup?.();chatRuntime.cleanup=null;++chatRuntime.version;}
  const param = parts[1] || null;

  const requiredFiles = routeDataFiles(base, param);
  if (requiredFiles.length) {
    container.innerHTML = '<div class="mx-auto max-w-6xl px-4 py-12 text-muted" role="status">Đang tải dữ liệu…</div>';
    refreshVisibleMotion();
    try {
      await Promise.all(requiredFiles.map(([key, file]) => loadStaticData(key, file)));
    } catch (error) {
      if (renderVersion !== routeRenderVersion) return;
      container.innerHTML = '<div class="mx-auto max-w-6xl px-4 py-12"><p class="text-muted">Chưa tải được dữ liệu. Bạn kiểm tra kết nối rồi thử lại nhé.</p><button id="retry-route-data" class="mt-4 min-h-11 rounded-xl bg-navy px-4 text-paper">Thử lại</button></div>';
      container.querySelector('#retry-route-data').addEventListener('click', renderRoute);
      refreshVisibleMotion();
      return;
    }
    if (renderVersion !== routeRenderVersion) return;
  }

  // Update navbar active states matching Trachngiemtinhcach
  document.querySelectorAll('.nav-link').forEach((link) => {
    const href = link.getAttribute('href');
    if ((base === 'home' && href === '#home') || (base !== 'home' && href === `#${base==='tra-cuu-nganh'?'huong-nghiep':base}`)) {
      link.classList.add('bg-ice', 'text-navy', 'font-semibold');
      link.classList.remove('text-muted');
    } else {
      link.classList.remove('bg-ice', 'text-navy', 'font-semibold');
      link.classList.add('text-muted');
    }
  });

  // Mobile menu close
  const mobMenu = document.getElementById('mobile-menu');
  if (mobMenu) setMobileMenuOpen(false);

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'instant' });

  // Route mapping matching Trachngiemtinhcach exactly
  switch (base) {
    case 'home':
      renderHome(container);
      break;
    case 'trac-nghiem':
      if (param) {
        renderQuizPlayer(container, param);
      } else {
        renderQuizzes(container);
      }
      break;
    case 'ket-qua':
      renderQuizResult(container, param || 'riasec');
      break;
    case 'nhom-tinh-cach':
      renderPersonalities(container, param);
      break;
    case 'huong-nghiep':
      renderCareers(container, param);
      break;
    case 'tra-cuu-nganh':
      renderMajorLookup(container);
      break;
    case 'truong-dai-hoc':
      if (param && param.startsWith('uni-')) {
        renderSchoolDetailPage(container, param);
      } else {
        renderUniversities(container, param);
      }
      break;
    case 'tu-van':
      renderConsultation(container, param);
      break;
    case 'so-sanh':
      renderComparison(container);
      break;
    case 'quan-tri':
    case 'admin':
      renderAdmin(container);
      break;
    case 'thiet-lap-ho-so':
      await renderIntake(container);
      break;
    case 'ho-so':
      renderProfile(container);
      break;
    case 'dang-nhap':
    case 'login':
      renderLogin(container);
      break;
    case 'dang-ky':
    case 'register':
      renderRegister(container);
      break;
    case 'gioi-thieu':
      renderAbout(container);
      break;
    default:
      renderHome(container);
      break;
  }

  refreshIcons();
  refreshVisibleMotion();
}

// ==========================================================================
// 0. AUTHENTICATION MODULE (#dang-nhap, #dang-ky, JWT session)
// ==========================================================================
async function initAuth() {
  const token = localStorage.getItem('fyf_auth_token');
  if (token) {
    try {
      const res = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const user = await res.json();
        state.currentUser = { ...state.currentUser, ...user };
        localStorage.setItem('fyf_current_user', JSON.stringify(state.currentUser));
      } else {
        localStorage.removeItem('fyf_auth_token');
        localStorage.removeItem('fyf_current_user');
        state.currentUser = null;
        state.authToken = null;
      }
    } catch (e) {
      console.warn('Không thể xác thực phiên đăng nhập:', e);
    }
  }
  updateAuthHeader();
}

function updateAuthHeader() {
  const headerContainer = document.getElementById('header-auth-container');
  const mobileContainer = document.getElementById('mobile-auth-container');
  const user = state.currentUser;

  if (headerContainer) {
    if (user) {
      const initial = (user.name || user.first_name || user.email || 'U').charAt(0).toUpperCase();
      const displayName = user.name || (user.first_name ? `${user.last_name || ''} ${user.first_name}`.trim() : user.email);
      const isAdmin = user.role === 'admin';

      headerContainer.innerHTML = `
        <a href="#ho-so" aria-label="Hồ sơ của bạn" class="header-profile hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-md)] bg-ice hover:bg-ice/80 text-navy font-semibold text-xs border border-line/60 transition shadow-border">
          <span class="size-5 rounded-full bg-azure text-paper flex items-center justify-center text-[10px] font-bold">${initial}</span>
          <span class="header-profile-label">Hồ sơ của bạn</span>
        </a>
        ${
          isAdmin
            ? `
          <a href="#quan-tri" aria-label="Quản trị hệ thống" title="Quản trị hệ thống" class="header-admin hidden md:inline-flex items-center justify-center font-medium select-none rounded-[var(--radius-md)] text-xs min-h-9 px-2.5 bg-mist text-muted hover:text-navy hover:bg-ice border border-line transition">
            <i data-lucide="shield-check" class="size-3.5 mr-1 text-azure"></i>
            <span class="header-action-label">Quản trị</span>
          </a>
        `
            : ''
        }
        <button onclick="window.logoutUser()" aria-label="Đăng xuất" class="header-logout hidden sm:inline-flex items-center justify-center font-medium select-none rounded-[var(--radius-md)] text-xs min-h-9 px-2.5 text-rose-500 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition" title="Đăng xuất">
          <i data-lucide="log-out" class="size-3.5 mr-1"></i>
          <span class="header-action-label">Đăng xuất</span>
        </button>
      `;
    } else {
      headerContainer.innerHTML = `
        <a href="#dang-nhap" class="inline-flex items-center justify-center font-medium select-none rounded-[var(--radius-md)] text-xs sm:text-sm min-h-9 sm:min-h-10 px-3 sm:px-3.5 bg-mist text-navy hover:bg-ice border border-line transition shadow-border">
          Đăng nhập
        </a>
        <a href="#dang-ky" class="hidden sm:inline-flex items-center justify-center font-medium select-none rounded-[var(--radius-md)] text-xs sm:text-sm min-h-9 sm:min-h-10 px-3.5 bg-card text-azure hover:bg-ice border border-azure/40 font-semibold transition shadow-border">
          Đăng ký
        </a>
      `;
    }
  }

  if (mobileContainer) {
    if (user) {
      const displayName = user.name || user.email;
      mobileContainer.innerHTML = `
        <div class="px-3 py-2 text-xs text-muted flex items-center justify-between">
          <span>Tài khoản:</span>
          <strong class="text-navy font-semibold">${displayName}</strong>
        </div>
        <button onclick="window.logoutUser()" class="w-full text-left px-3 py-2 rounded-[var(--radius-sm)] text-sm font-semibold text-rose-500 hover:bg-ice flex items-center gap-2">
          <i data-lucide="log-out" class="size-4"></i>
          Đăng xuất
        </button>
      `;
    } else {
      mobileContainer.innerHTML = `
        <a href="#dang-nhap" class="block px-3 py-2 rounded-[var(--radius-sm)] text-sm font-semibold text-azure hover:bg-ice">Đăng nhập</a>
        <a href="#dang-ky" class="block px-3 py-2 rounded-[var(--radius-sm)] text-sm font-semibold text-cyan hover:bg-ice">Đăng ký tài khoản</a>
      `;
    }
  }

  refreshIcons();
}

function logoutUser() {
  clearChatResume(state.currentUser?.user_id);
  chatRuntime.onLeave=null;
  localStorage.removeItem('fyf_auth_token');
  localStorage.removeItem('fyf_current_user');
  state.currentUser = null;
  state.authToken = null;
  state.results = {mbti:null, riasec:null, bigfive:null, cognitive:null};
  updateAuthHeader();
  showToast('Đã đăng xuất tài khoản thành công', 'info');
  window.location.hash = '#home';
}
window.logoutUser = logoutUser;

window.togglePasswordVisibility = function (inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPass = input.type === 'password';
  input.type = isPass ? 'text' : 'password';
  if (btn) {
    btn.innerHTML = `<i data-lucide="${isPass ? 'eye-off' : 'eye'}" class="size-4"></i>`;
    refreshIcons();
  }
};

function authDestination(role) {
  return role === 'admin' ? '#quan-tri' : '#thiet-lap-ho-so';
}

function renderLogin(container) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-xl px-4 py-12 sm:px-6 text-center">
        <span class="inline-grid size-12 place-items-center rounded-2xl bg-ice text-azure mx-auto mb-3 border border-line shadow-sm">
          <i data-lucide="lock" class="size-6"></i>
        </span>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Tài khoản & Xác thực</p>
        <h1 class="mt-2 font-display text-3xl sm:text-4xl font-bold text-navy">Đăng nhập For Your Future</h1>
        <p class="mt-2 text-sm sm:text-base text-muted leading-relaxed">
          Đồng bộ kết quả trắc nghiệm tính cách, năng lực nhận thức và nguyện vọng xét tuyển đại học.
        </p>
      </div>
    </div>

    <div class="mx-auto max-w-md px-4 py-10 sm:px-6">
      <div class="rounded-[28px] bg-card border border-line p-6 sm:p-8 shadow-border">
        <div class="mb-5 rounded-[14px] bg-ice border border-line p-3 text-sm text-navy">
          Đăng nhập để bắt đầu trắc nghiệm và khám phá bản thân.
        </div>
        <label class="flex items-center gap-2 mb-5 text-sm font-semibold text-navy">
          <input id="login-admin-mode" type="checkbox" class="accent-blue-700">
          Đăng nhập quản trị viên (chỉ cần mật khẩu)
        </label>
        <form id="form-login" class="space-y-4">
          <div id="login-email-field">
            <label for="login-email" class="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
              Email đăng nhập
            </label>
            <div class="relative">
              <i data-lucide="mail" class="size-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"></i>
              <input 
                id="login-email" 
                type="email" 
                required 
                placeholder="vidu@foryourfuture.edu.vn" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 pl-10 pr-3.5 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label for="login-password" class="block text-xs font-semibold uppercase tracking-wider text-muted">
                Mật khẩu
              </label>
            </div>
            <div class="relative">
              <i data-lucide="key" class="size-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"></i>
              <input 
                id="login-password" 
                type="password" 
                required 
                placeholder="••••••••" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 pl-10 pr-11 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
              <button 
                type="button" 
                onclick="window.togglePasswordVisibility('login-password', this)"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-navy p-1 rounded-lg transition"
                title="Hiện/Ẩn mật khẩu"
                aria-label="Hiện hoặc ẩn mật khẩu"
              >
                <i data-lucide="eye" class="size-4"></i>
              </button>
            </div>
          </div>

          <div id="login-error-msg" class="hidden p-3 rounded-[12px] bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs font-medium"></div>

          <button 
            type="submit" 
            id="btn-login-submit" 
            class="w-full py-3 rounded-[14px] bg-navy text-paper font-semibold text-sm hover:bg-navy-deep cta-glow transition flex items-center justify-center gap-2 mt-2"
          >
            <span>Đăng nhập</span>
            <i data-lucide="arrow-right" class="size-4"></i>
          </button>
        </form>

        <!-- Switch to Register -->
        <div class="mt-6 text-center text-xs text-muted">
          Chưa có tài khoản học sinh? 
          <a href="#dang-ky" class="font-semibold text-azure hover:underline ml-1">Đăng ký ngay</a>
        </div>
      </div>
    </div>
  `;

  window.quickFillLogin = function (email, password) {
    const elEmail = document.getElementById('login-email');
    const elPass = document.getElementById('login-password');
    if (elEmail) elEmail.value = email;
    if (elPass) elPass.value = password;
  };

  const adminMode = document.getElementById('login-admin-mode');
  adminMode.addEventListener('change', () => {
    document.getElementById('login-email-field').classList.toggle('hidden', adminMode.checked);
    document.getElementById('login-email').required = !adminMode.checked;
  });
  const form = document.getElementById('form-login');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value.replace(/\s/g, '');
      const errBox = document.getElementById('login-error-msg');
      const btn = document.getElementById('btn-login-submit');

      if (errBox) errBox.classList.add('hidden');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<div class="size-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></div><span>Đang kiểm tra...</span>`;
      }

      try {
        const res = await fetch(adminMode.checked ? '/api/v1/auth/admin-login' : '/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(adminMode.checked ? { password } : { email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Email hoặc mật khẩu không chính xác');
        }

        // Save auth data
        localStorage.setItem('fyf_auth_token', data.access_token);
        localStorage.setItem('fyf_current_user', JSON.stringify(data));
        state.currentUser = data;
        state.authToken = data.access_token;
        updateAuthHeader();
        await loadAccountAssessments();

        showToast(`Đăng nhập thành công! Xin chào, ${data.name || data.email}`, 'success');
        window.location.hash = authDestination(data.role);
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message || 'Lỗi khi đăng nhập. Vui lòng thử lại!';
          errBox.classList.remove('hidden');
        }
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = `<span>Đăng nhập</span><i data-lucide="arrow-right" class="size-4"></i>`;
          refreshIcons();
        }
      }
    });
  }

  refreshIcons();
}

function renderRegister(container) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-xl px-4 py-12 sm:px-6 text-center">
        <span class="inline-grid size-12 place-items-center rounded-2xl bg-ice text-azure mx-auto mb-3 border border-line shadow-sm">
          <i data-lucide="user-plus" class="size-6"></i>
        </span>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Tài khoản & Xác thực</p>
        <h1 class="mt-2 font-display text-3xl sm:text-4xl font-bold text-navy">Tạo tài khoản học sinh</h1>
        <p class="mt-2 text-sm sm:text-base text-muted leading-relaxed">
          Đăng ký để lưu trữ hồ sơ hướng nghiệp, tính toán điểm sàn và tư vấn tuyển sinh đại học cá nhân hóa.
        </p>
      </div>
    </div>

    <div class="mx-auto max-w-lg px-4 py-10 sm:px-6">
      <div class="rounded-[28px] bg-card border border-line p-6 sm:p-8 shadow-border">
        <form id="form-register" class="space-y-4">
          <!-- Name inputs -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label for="reg-lastname" class="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
                Họ & tên đệm *
              </label>
              <input 
                id="reg-lastname" 
                type="text" 
                required 
                placeholder="Nguyễn Văn" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 px-3.5 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
            </div>
            <div>
              <label for="reg-firstname" class="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
                Tên *
              </label>
              <input 
                id="reg-firstname" 
                type="text" 
                required 
                placeholder="An" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 px-3.5 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
            </div>
          </div>

          <!-- Email & Password -->
          <div>
            <label for="reg-email" class="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
              Email tài khoản *
            </label>
            <div class="relative">
              <i data-lucide="mail" class="size-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"></i>
              <input 
                id="reg-email" 
                type="email" 
                required 
                placeholder="hocsinh@example.com" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 pl-10 pr-3.5 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
            </div>
          </div>

          <div>
            <label for="reg-password" class="block text-xs font-semibold uppercase tracking-wider text-muted mb-1.5">
              Mật khẩu (Tối thiểu 6 ký tự) *
            </label>
            <div class="relative">
              <i data-lucide="key" class="size-4 text-muted absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"></i>
              <input 
                id="reg-password" 
                type="password" 
                required 
                minlength="6"
                placeholder="••••••••" 
                class="w-full rounded-[14px] bg-mist border border-line py-2.5 pl-10 pr-11 text-sm text-navy placeholder:text-muted/60 focus:border-azure focus:outline-none focus:ring-1 focus:ring-azure transition"
              >
              <button 
                type="button" 
                onclick="window.togglePasswordVisibility('reg-password', this)"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-navy p-1 rounded-lg transition"
                title="Hiện/Ẩn mật khẩu"
                aria-label="Hiện hoặc ẩn mật khẩu"
              >
                <i data-lucide="eye" class="size-4"></i>
              </button>
            </div>
          </div>

          <!-- Academic background info -->
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label for="reg-grade" class="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1.5">
                Khối lớp
              </label>
              <select id="reg-grade" class="w-full rounded-[14px] bg-mist border border-line py-2.5 px-3 text-xs sm:text-sm text-navy focus:border-azure focus:outline-none transition">
                <option value="12" selected>Lớp 12</option>
                <option value="11">Lớp 11</option>
                <option value="10">Lớp 10</option>
              </select>
            </div>
            <div>
              <label for="reg-year" class="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1.5">
                Năm thi
              </label>
              <select id="reg-year" class="w-full rounded-[14px] bg-mist border border-line py-2.5 px-3 text-xs sm:text-sm text-navy focus:border-azure focus:outline-none transition">
                <option value="2026" selected>2026</option>
                <option value="2025">2025</option>
                <option value="2027">2027</option>
              </select>
            </div>
            <div>
              <label for="reg-gender" class="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1.5">
                Giới tính
              </label>
              <select id="reg-gender" class="w-full rounded-[14px] bg-mist border border-line py-2.5 px-3 text-xs sm:text-sm text-navy focus:border-azure focus:outline-none transition">
                <option value="Nam">Nam</option>
                <option value="Nữ">Nữ</option>
                <option value="Other" selected>Khác</option>
              </select>
            </div>
          </div>

          <div id="reg-error-msg" class="hidden p-3 rounded-[12px] bg-rose-500/10 border border-rose-500/30 text-rose-500 text-xs font-medium"></div>

          <button 
            type="submit" 
            id="btn-register-submit" 
            class="w-full py-3 rounded-[14px] bg-navy text-paper font-semibold text-sm hover:bg-navy-deep cta-glow transition flex items-center justify-center gap-2 mt-2"
          >
            <span>Tạo tài khoản học sinh</span>
            <i data-lucide="arrow-right" class="size-4"></i>
          </button>
        </form>

        <!-- Switch to Login -->
        <div class="mt-6 text-center text-xs text-muted">
          Đã có tài khoản? 
          <a href="#dang-nhap" class="font-semibold text-azure hover:underline ml-1">Đăng nhập</a>
        </div>
      </div>
    </div>
  `;

  const form = document.getElementById('form-register');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const lastName = document.getElementById('reg-lastname').value.trim();
      const firstName = document.getElementById('reg-firstname').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value.replace(/\s/g, '');
      const gradeLevel = parseInt(document.getElementById('reg-grade').value, 10);
      const targetYear = parseInt(document.getElementById('reg-year').value, 10);
      const gender = document.getElementById('reg-gender').value;

      const errBox = document.getElementById('reg-error-msg');
      const btn = document.getElementById('btn-register-submit');

      if (errBox) errBox.classList.add('hidden');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<div class="size-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></div><span>Đang khởi tạo tài khoản...</span>`;
      }

      try {
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email,
            password,
            first_name: firstName,
            last_name: lastName,
            grade_level: gradeLevel,
            target_year: targetYear,
            gender,
          }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Không thể tạo tài khoản. Vui lòng kiểm tra thông tin!');
        }

        // Save auth data
        localStorage.setItem('fyf_auth_token', data.access_token);
        localStorage.setItem('fyf_current_user', JSON.stringify(data));
        state.currentUser = data;
        state.authToken = data.access_token;
        updateAuthHeader();
        await loadAccountAssessments();

        showToast(`Đăng ký thành công! Chào mừng ${data.name || firstName}`, 'success');
        window.location.hash = authDestination(data.role);
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message || 'Lỗi khi tạo tài khoản.';
          errBox.classList.remove('hidden');
        }
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = `<span>Tạo tài khoản học sinh</span><i data-lucide="arrow-right" class="size-4"></i>`;
          refreshIcons();
        }
      }
    });
  }

  refreshIcons();
}

// ==========================================================================
// 1. HOME VIEW (HERO, INTROCARDS, HOWITWORKS, QUIZPICKER, TYPEGRID, CAREERPREVIEW, FAQ, CTABAND)
// ==========================================================================
let homeTypeGridVersion = 0;
async function renderHomeTypeGrid() {
  const grid = document.getElementById('type-grid-container');
  if (!grid) return;
  const version = ++homeTypeGridVersion;
  if (state.activePersonalityTab === 'riasec' && !staticDataReady.has('riasecCombinations')) {
    grid.innerHTML = '<p class="text-muted py-6" role="status">Đang tải nhóm tính cách…</p>';
    try { await loadStaticData('riasecCombinations', 'riasec_combinations.json'); }
    catch (error) {
      if (!grid.isConnected || version !== homeTypeGridVersion) return;
      grid.innerHTML = '<p class="text-muted py-4">Chưa tải được nhóm tính cách.</p><button id="retry-type-grid" class="min-h-11 rounded-xl bg-navy px-4 text-paper">Thử lại</button>';
      grid.querySelector('#retry-type-grid').addEventListener('click', renderHomeTypeGrid);
      return;
    }
  }
  if (!grid.isConnected || version !== homeTypeGridVersion) return;
  grid.innerHTML = renderTypeGridContent();
  refreshIcons();
}
function renderHome(container) {
  container.innerHTML = `
    <!-- HERO SECTION (TWO COLUMNS) -->
    <section class="hero-wash relative overflow-hidden">
      <div class="pointer-events-none absolute -left-20 top-10 size-56 rounded-full bg-cyan/15 blur-3xl"></div>
      <div class="pointer-events-none absolute -right-10 bottom-0 size-72 rounded-full bg-azure/10 blur-3xl"></div>
      <div class="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:gap-12 lg:pb-24 lg:pt-12">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">
            Trắc nghiệm tính cách & hướng nghiệp
          </p>
          <h1 class="mt-4 max-w-xl font-display text-[2.05rem] font-semibold tracking-tight text-navy sm:text-5xl leading-[1.15]">
            Khám phá tính cách – Hiểu bản thân – Chọn đúng hướng đi
          </h1>
          <p class="mt-5 max-w-lg text-base leading-relaxed text-muted sm:text-lg">
            For Your Future đồng hành cùng bạn qua từng câu hỏi, từng lớp kết quả — chậm, rõ, và luôn mang tính tham khảo.
          </p>
          <div class="mt-8 flex flex-col gap-3 sm:flex-row">
            <a href="#trac-nghiem" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-lg)] transition-[transform,background-color,color,box-shadow,opacity] duration-150 ease-out bg-navy text-paper hover:bg-navy-deep cta-glow px-5 min-h-12 text-sm sm:text-base w-full sm:w-auto">
              <span>Bắt đầu trắc nghiệm</span>
              <i data-lucide="arrow-right" class="size-4"></i>
            </a>
            <a href="#tu-van" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-lg)] transition-[transform,background-color,color,box-shadow,opacity] duration-150 ease-out bg-azure text-paper hover:bg-navy-deep cta-glow px-5 min-h-12 text-sm sm:text-base w-full sm:w-auto">
              <i data-lucide="sparkles" class="size-4 text-cyan-soft"></i>
              <span>Tư vấn AI & Nguyện vọng</span>
            </a>
            <a href="#nhom-tinh-cach" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-lg)] transition-[transform,background-color,color,box-shadow,opacity] duration-150 ease-out bg-card text-navy shadow-border hover:shadow-border-hover px-5 min-h-12 text-sm sm:text-base w-full sm:w-auto">
              <span>Khám phá nhóm tính cách</span>
            </a>
          </div>
          <dl class="mt-10 grid grid-cols-3 gap-3 max-w-md">
            <div class="rounded-[var(--radius-lg)] bg-card/70 px-3.5 py-3 shadow-border">
              <dt class="font-display text-xl font-semibold tabular-nums text-navy">4</dt>
              <dd class="text-xs text-muted mt-0.5">bài test</dd>
            </div>
            <div class="rounded-[var(--radius-lg)] bg-card/70 px-3.5 py-3 shadow-border">
              <dt class="font-display text-xl font-semibold tabular-nums text-navy">136</dt>
              <dd class="text-xs text-muted mt-0.5">nhóm MBTI & RIASEC</dd>
            </div>
            <div class="rounded-[var(--radius-lg)] bg-card/70 px-3.5 py-3 shadow-border">
              <dt class="font-display text-xl font-semibold tabular-nums text-navy">10+</dt>
              <dd class="text-xs text-muted mt-0.5">nhóm ngành</dd>
            </div>
          </dl>
        </div>
        <figure class="founders-hero">
          <div class="founders-media">
            <img
              src="/illustrations/co-founders.png"
              alt="Hai đồng sáng lập For Your Future: Trịnh Thị Như Quỳnh và Nguyễn Thành Tiến"
              width="479"
              height="640"
              fetchpriority="high"
              decoding="async"
              class="founders-photo"
            />
          </div>
          <figcaption class="founders-caption">
            <div class="founders-names">
              <div class="founder-person">
                <span class="founders-label">Đồng sáng lập</span>
                <p>TRỊNH THỊ NHƯ QUỲNH</p>
              </div>
              <div class="founder-person">
                <span class="founders-label">Đồng sáng lập</span>
                <p>NGUYỄN THÀNH TIẾN</p>
              </div>
            </div>
          </figcaption>
        </figure>
      </div>
    </section>

    <!-- AI CONSULTATION TEASER BANNER (GRAPHRAG & GEMINI) -->
    <section class="mx-auto max-w-6xl px-4 -mt-6 sm:-mt-8 mb-8 sm:px-6 relative z-10">
      <div class="rounded-[24px] bg-gradient-to-r from-navy-deep via-navy to-azure p-6 sm:p-8 text-paper shadow-2xl border border-white/10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="max-w-xl">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-semibold uppercase tracking-wider text-cyan-soft mb-3">
            <i data-lucide="sparkles" class="size-3.5 text-cyan"></i>
            GraphRAG + Ollama API (qwen2.5:7b)
          </div>
          <h2 class="font-display text-xl sm:text-2xl font-bold tracking-tight text-white">
            Nhận chiến lược phân bổ nguyện vọng Reach – Target – Safe
          </h2>
          <p class="mt-2 text-sm text-cyan-soft/90 leading-relaxed">
            Nhập điểm thi THPT, khối thi hoặc ngành yêu thích. Trợ lý AI sẽ đối chiếu dữ liệu điểm chuẩn thực tế và việc làm CareerViet để phân bổ danh mục cho bạn tức thì.
          </p>
        </div>
        <div class="w-full md:w-auto flex-shrink-0">
          <a href="#tu-van" class="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-[16px] bg-cyan hover:bg-cyan-soft text-navy font-bold text-sm tracking-wide shadow-lg hover:scale-105 transition-all w-full md:w-auto no-underline">
            <span>Trải nghiệm Tư vấn AI</span>
            <i data-lucide="arrow-right" class="size-4"></i>
          </a>
        </div>
      </div>
    </section>

    <!-- INTRO CARDS (VÌ SAO FOR YOUR FUTURE) -->
    <section class="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Vì sao For Your Future</p>
        <h2 class="mt-2 max-w-xl font-display text-3xl font-semibold text-navy">
          Một hành trình, nhiều lớp hiểu
        </h2>
      </div>
      <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article class="rounded-[24px] bg-card p-5 shadow-border hover:-translate-y-1 hover:shadow-border-hover transition duration-200">
          <span class="grid size-11 place-items-center rounded-[14px] bg-ice text-azure">
            <i data-lucide="user-round" class="size-5"></i>
          </span>
          <h3 class="mt-4 font-display text-lg font-semibold text-navy">Hiểu bản thân</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">
            Nhìn ra cách bạn nạp năng lượng, nghĩ, quyết và sống — bằng ngôn ngữ đời thường.
          </p>
        </article>
        <article class="rounded-[24px] bg-card p-5 shadow-border hover:-translate-y-1 hover:shadow-border-hover transition duration-200">
          <span class="grid size-11 place-items-center rounded-[14px] bg-ice text-azure">
            <i data-lucide="sparkles" class="size-5"></i>
          </span>
          <h3 class="mt-4 font-display text-lg font-semibold text-navy">Khám phá điểm mạnh</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">
            Nhận diện những khả năng nổi bật của bản thân và tìm hiểu cách phát huy chúng trong học tập, cuộc sống.
          </p>
        </article>
        <article class="rounded-[24px] bg-card p-5 shadow-border hover:-translate-y-1 hover:shadow-border-hover transition duration-200">
          <span class="grid size-11 place-items-center rounded-[14px] bg-ice text-azure">
            <i data-lucide="compass" class="size-5"></i>
          </span>
          <h3 class="mt-4 font-display text-lg font-semibold text-navy">Khám phá sở thích</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">
            Tìm hiểu những lĩnh vực và hoạt động khiến bạn hứng thú, từ đó khám phá những điều thực sự phù hợp với mình.
          </p>
        </article>
        <article class="rounded-[24px] bg-card p-5 shadow-border hover:-translate-y-1 hover:shadow-border-hover transition duration-200">
          <span class="grid size-11 place-items-center rounded-[14px] bg-ice text-azure">
            <i data-lucide="target" class="size-5"></i>
          </span>
          <h3 class="mt-4 font-display text-lg font-semibold text-navy">Định hướng nghề nghiệp</h3>
          <p class="mt-2 text-sm leading-relaxed text-muted">
            Khám phá các ngành học và nghề nghiệp phù hợp với sở thích, năng lực và định hướng phát triển của bản thân.
          </p>
        </article>
      </div>
    </section>

    <!-- HOW IT WORKS (BA BƯỚC, KHÔNG VỘI) -->
    <section class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Cách hoạt động</p>
        <h2 class="mt-2 font-display text-3xl font-semibold text-navy">Ba bước, không vội</h2>
      </div>
      <div class="mt-8 grid gap-4 md:grid-cols-3">
        <article class="rounded-[24px] bg-card p-6 shadow-border">
          <p class="font-display text-sm font-semibold tabular-nums text-cyan">01</p>
          <h3 class="mt-3 font-display text-xl font-semibold text-navy">Chọn bài test</h3>
          <p class="mt-2 text-sm text-muted">Bốn bài trắc nghiệm: RIASEC, Đánh giá năng lực nhận thức, Big Five và MBTI. Ưu tiên làm RIASEC và Đánh giá năng lực nhận thức trước.</p>
        </article>
        <article class="rounded-[24px] bg-card p-6 shadow-border">
          <p class="font-display text-sm font-semibold tabular-nums text-cyan">02</p>
          <h3 class="mt-3 font-display text-xl font-semibold text-navy">Trả lời từng câu</h3>
          <p class="mt-2 text-sm text-muted">Một câu một nhịp, có thể quay lại. Tiến độ được giữ trên máy bạn.</p>
        </article>
        <article class="rounded-[24px] bg-card p-6 shadow-border">
          <p class="font-display text-sm font-semibold tabular-nums text-cyan">03</p>
          <h3 class="mt-3 font-display text-xl font-semibold text-navy">Đọc kết quả theo lớp</h3>
          <p class="mt-2 text-sm text-muted">Không dồn hết một lúc. Kéo xuống để mở điểm mạnh, cách nghĩ, gợi ý nghề.</p>
        </article>
      </div>
    </section>

    <!-- QUIZ PICKER SECTION -->
    <section class="bg-mist/80 py-16 sm:py-20 my-10">
      <div class="mx-auto max-w-7xl px-4 sm:px-6">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Bài test</p>
          <h2 class="mt-2 max-w-xl font-display text-3xl font-semibold text-navy">Chọn bài trắc nghiệm phù hợp với bạn</h2>
          <p class="mt-3 max-w-2xl text-muted">
            Làm từng câu một, lưu tiến độ trên máy bạn, xem lại kết quả bất cứ lúc nào.
          </p>
        </div>
        <div class="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          ${renderQuizPickerCards()}
        </div>
      </div>
    </section>

    <!-- TYPE GRID SECTION (16 NHÓM MBTI & 6 NHÓM RIASEC) -->
    <section class="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">16 nhóm MBTI · 6 nhóm RIASEC</p>
        <h2 class="mt-2 font-display text-3xl font-semibold text-navy">Khám phá các nhóm tính cách</h2>
        <p class="mt-3 max-w-2xl text-muted">
          Chọn “Nhóm MBTI” để khám phá 16 nhóm tính cách MBTI hoặc “Nhóm RIASEC” để xem 6 nhóm tính cách RIASEC.
        </p>
      </div>

      <!-- Tab Buttons -->
      <div class="mt-6 flex flex-wrap gap-2">
        <button id="tab-btn-mbti" class="min-h-11 rounded-full px-4 text-sm font-medium transition-[background-color,color] duration-150 ${state.activePersonalityTab === 'mbti' ? 'bg-navy text-paper' : 'bg-mist text-muted hover:text-navy'}">
          Nhóm MBTI
        </button>
        <button id="tab-btn-riasec" class="min-h-11 rounded-full px-4 text-sm font-medium transition-[background-color,color] duration-150 ${state.activePersonalityTab === 'riasec' ? 'bg-navy text-paper' : 'bg-mist text-muted hover:text-navy'}">
          Nhóm RIASEC
        </button>
      </div>

      <!-- Grid Content -->
      <div id="type-grid-container" class="mt-8">
        ${renderTypeGridContent()}
      </div>
    </section>

    <!-- CAREER PREVIEW SECTION (NAVY BAND) -->
    <section class="bg-navy py-16 text-paper sm:py-20">
      <div class="mx-auto max-w-6xl px-4 sm:px-6">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-soft">Hướng đi</p>
          <h2 class="mt-2 font-display text-3xl font-semibold">Khám phá hướng đi phù hợp</h2>
          <p class="mt-3 max-w-2xl text-cyan-soft/90">
            Đây là gợi ý tham khảo — không phải lời khẳng định một nghề là “chắc chắn phù hợp”.
          </p>
        </div>
        <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          ${(state.careers.slice(0, 5) || [])
            .map(
              (c) => `
            <a href="#huong-nghiep/${c.id}" class="block h-full rounded-[20px] bg-white/10 p-4 transition-[background-color,transform] duration-200 hover:-translate-y-0.5 hover:bg-white/15">
              <span class="size-6 text-cyan-soft block mb-3 font-display font-bold">●</span>
              <h3 class="font-display font-semibold text-paper text-base">${c.name}</h3>
              <p class="mt-1 line-clamp-2 text-xs text-paper/70 leading-relaxed">${c.description}</p>
            </a>
          `
            )
            .join('')}
        </div>
        <div class="mt-8">
          <a href="#huong-nghiep" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-md)] text-[0.95rem] min-h-11 px-5 bg-cyan text-navy-deep hover:bg-cyan-soft cta-glow transition">
            Khám phá trường Đại học
          </a>
        </div>
      </div>
    </section>

    <!-- FAQ SECTION (ACCORDION) -->
    <section class="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Câu hỏi thường gặp</p>
        <h2 class="mt-2 font-display text-3xl font-semibold text-navy">Trước khi bắt đầu</h2>
      </div>
      <div class="mt-8 divide-y divide-line rounded-[24px] bg-card shadow-border border border-line/60 overflow-hidden">
        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Kết quả trắc nghiệm có ‘đúng’ không?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            Không có đáp án đúng. For Your Future mô tả xu hướng — cách bạn hay nghĩ, quyết và thích kiểu việc nào. Dùng để soi gương, không phải chẩn đoán hay lời kết nghề nghiệp.
          </div>
        </div>

        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Bốn bài trắc nghiệm khác nhau thế nào?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            RIASEC (Holland) khám phá sở thích nghề theo 6 nhóm. Đánh giá năng lực nhận thức giúp tìm hiểu tư duy ngôn ngữ, định lượng và hình ảnh/quy luật. Bạn nên làm hai bài này trước, rồi bổ sung Big Five để hiểu năm chiều tính cách và MBTI để khám phá 16 nhóm tính cách. Xem các kết quả trong mục Hồ sơ.
          </div>
        </div>

        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Có cần tài khoản không? Dữ liệu nằm đâu?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            Không bắt buộc. Câu trả lời và kết quả lưu trên thiết bị của bạn. Bạn có thể xem lại kết quả bất cứ lúc nào trong mục Hồ sơ.
          </div>
        </div>

        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Làm lại có mất hồ sơ cũ không?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            Hồ sơ cũ vẫn xem được cho đến khi bạn hoàn thành bài mới. Tiến độ dở được giữ, có thể tiếp tục hoặc bắt đầu lại.
          </div>
        </div>

        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Dùng kết quả để chọn ngành được không?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            Được như bản đồ tham khảo — không như lệnh. Mức phù hợp là ước lượng. Hãy thử việc thật, nói với người trong nghề, rồi mới chốt.
          </div>
        </div>

        <div class="faq-row px-5 sm:px-6 py-4 cursor-pointer" onclick="toggleFaq(this)">
          <div class="flex items-center justify-between font-display text-base font-semibold text-navy">
            <span>Làm bài mất bao lâu? Có được quay lại không?</span>
            <i data-lucide="chevron-down" class="size-4 text-muted transition-transform"></i>
          </div>
          <div class="faq-answer hidden mt-2 text-sm leading-relaxed text-muted">
            Khoảng 7–15 phút tùy bài. Một câu một nhịp, quay lại câu trước, đáp án cũ được giữ. Phím 1–5 để chọn, Enter để tiếp tục.
          </div>
        </div>
      </div>
    </section>

    <!-- CTA BAND SECTION -->
    <section class="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      <div class="overflow-hidden rounded-[28px] bg-gradient-to-br from-navy to-azure px-6 py-10 text-paper sm:px-10 shadow-border">
        <h2 class="max-w-lg font-display text-3xl font-semibold">
          Sẵn sàng nhìn mình rõ hơn một chút?
        </h2>
        <p class="mt-3 max-w-lg text-cyan-soft text-sm sm:text-base leading-relaxed">
          Bắt đầu với một bài test. Kết quả ở lại trên thiết bị của bạn — không cần tài khoản.
        </p>
        <a href="#trac-nghiem" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-lg)] text-base min-h-12 px-6 bg-cyan text-navy-deep hover:bg-cyan-soft cta-glow mt-6 transition">
          Bắt đầu trắc nghiệm
        </a>
      </div>
    </section>
  `;

  // Attach Tab switcher for TypeGrid
  const btnMbti = document.getElementById('tab-btn-mbti');
  const btnRiasec = document.getElementById('tab-btn-riasec');
  if (btnMbti && btnRiasec) {
    btnMbti.addEventListener('click', () => {
      state.activePersonalityTab = 'mbti';
      btnMbti.className = 'min-h-11 rounded-full px-4 text-sm font-medium transition duration-150 bg-navy text-paper';
      btnRiasec.className = 'min-h-11 rounded-full px-4 text-sm font-medium transition duration-150 bg-mist text-muted hover:text-navy';
      renderHomeTypeGrid();
    });
    btnRiasec.addEventListener('click', () => {
      state.activePersonalityTab = 'riasec';
      btnRiasec.className = 'min-h-11 rounded-full px-4 text-sm font-medium transition duration-150 bg-navy text-paper';
      btnMbti.className = 'min-h-11 rounded-full px-4 text-sm font-medium transition duration-150 bg-mist text-muted hover:text-navy';
      renderHomeTypeGrid();
    });
  }
}

function renderQuizPickerCards() {
  const quizzes = state.quizzes.length > 0 ? state.quizzes : [
    { id: 'riasec', name: 'RIASEC', tagline: 'Sở thích nghề theo 6 nhóm Holland', duration: '10–15 phút', questionCount: 60, icon: 'compass', image: '/illustrations/quiz-riasec-animated.svg', description: 'Khám phá bạn bị cuốn bởi kiểu việc nào: thao tác, nghiên cứu, sáng tạo, hỗ trợ người, dẫn dắt hay vận hành hệ thống.' },
    { id: 'cognitive', name: 'Năng lực nhận thức', tagline: '3 miền tư duy: Ngôn ngữ, Định lượng & Quy luật', duration: '15 phút', questionCount: 30, icon: 'brain', image: '/illustrations/quiz-cognitive-animated.svg', description: 'Bộ câu hỏi chuẩn hóa gồm 30 câu kiểm tra 3 nhóm năng lực cốt lõi: Verbal (ngôn ngữ), Numerical (định lượng) và Figural (hình ảnh/quy luật).' },
    { id: 'bigfive', name: 'Big Five', tagline: 'Năm chiều tính cách cốt lõi', duration: '7–9 phút', questionCount: 25, icon: 'layers', image: '/illustrations/quiz-bigfive-animated.svg', description: 'Một bức tranh cân bằng về mức độ cởi mở, tận tâm, hướng ngoại, hòa hợp và ổn định cảm xúc — để hiểu cách bạn vận hành hằng ngày.' },
    { id: 'mbti', name: 'MBTI', tagline: '16 nhóm tính cách', duration: '10–12 phút', questionCount: 40, icon: 'sparkles', image: '/illustrations/quiz-mbti-animated.svg', description: 'Tìm nhóm gần với cách bạn nạp năng lượng, tiếp nhận thông tin, ra quyết định và sắp xếp đời sống. Kết quả mang tính tham khảo.' },
  ];

  const priority = ['riasec', 'cognitive', 'bigfive', 'mbti'];
  return [...quizzes].sort((a, b) => (priority.indexOf(a.id) < 0 ? 99 : priority.indexOf(a.id)) - (priority.indexOf(b.id) < 0 ? 99 : priority.indexOf(b.id)))
    .map((q) => {
      const hasResult = Boolean(state.results[q.id]);
      const stillImage = q.image?.endsWith('-animated.svg') ? q.image.replace('-animated.svg', '-still.svg') : null;
      return `
      <article class="group flex h-full flex-col overflow-hidden rounded-[24px] bg-card shadow-border transition-[transform,box-shadow] duration-200 ease-out hover:-translate-y-1 hover:shadow-border-hover border border-line/60">
        <div class="relative aspect-[4/3] overflow-hidden bg-ice">
          <picture class="block h-full w-full">
            ${stillImage ? `<source media="(prefers-reduced-motion: reduce)" srcset="${stillImage}">` : ''}
            <img src="${stillImage || q.image || '/illustrations/hero.webp'}" data-animated-src="${stillImage ? q.image : ''}" data-still-src="${stillImage || ''}" alt="${q.name}" width="800" height="600" loading="lazy" decoding="async" class="quiz-cover-image h-full w-full object-contain" onerror="this.dataset.motionFailed='true';this.closest('picture')?.querySelector('source')?.remove();this.onerror=null;this.src='/illustrations/hero.webp'">
          </picture>
        </div>
        <div class="flex flex-1 flex-col p-5 sm:p-6">
          <h3 class="font-display text-xl font-semibold text-navy">${q.name}</h3>
          <p class="mt-1 text-xs sm:text-sm text-azure font-medium">${q.tagline}</p>
          <p class="mt-2 text-xs sm:text-sm leading-relaxed text-muted flex-1">${q.description}</p>
          <p class="mt-3 flex flex-wrap gap-3 text-xs font-medium text-muted">
            <span class="inline-flex items-center gap-1"><i data-lucide="clock" class="size-3.5"></i> ${q.duration}</span>
            <span>${q.questionCount} câu hỏi</span>
          </p>
          <div class="mt-auto flex flex-col gap-2 pt-5">
            <a href="#trac-nghiem/${q.id}" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-md)] text-xs min-h-10 px-4 bg-navy text-paper hover:bg-navy-deep cta-glow transition w-full">
              <span>${hasResult ? 'Làm lại bài test' : 'Bắt đầu'}</span>
              <i data-lucide="arrow-right" class="size-3.5"></i>
            </a>
            ${
              hasResult
                ? `<a href="#ket-qua/${q.id}" class="inline-flex items-center justify-center gap-2 font-medium select-none rounded-[var(--radius-md)] text-xs min-h-10 px-4 bg-card text-navy shadow-border hover:shadow-border-hover transition w-full">
                    Xem kết quả
                  </a>`
                : ''
            }
          </div>
        </div>
      </article>
    `;
    })
    .join('');
}

function renderTypeGridContent() {
  if (state.activePersonalityTab === 'riasec') {
    const list = state.riasecTypes.length > 0 ? state.riasecTypes : [
      { id: 'R', name: 'Thực tế', slogan: 'Làm bằng tay, hiểu bằng việc.', summary: 'Thích thao tác, máy móc, ngoài trời, kết quả sờ được.' },
      { id: 'I', name: 'Nghiên cứu', slogan: 'Hỏi đến khi ra bản chất.', summary: 'Thích phân tích, thí nghiệm, dữ liệu và câu hỏi khó.' },
      { id: 'A', name: 'Nghệ thuật/Sáng tạo', slogan: 'Tạo thứ chưa từng có.', summary: 'Thích biểu đạt, hình ảnh, ngôn ngữ, không gian tự do.' },
      { id: 'S', name: 'Xã hội', slogan: 'Đồng hành để người khác lớn.', summary: 'Thích lắng nghe, giảng dạy, hỗ trợ, làm việc vì người.' },
      { id: 'E', name: 'Quản lý/Thuyết phục', slogan: 'Dẫn dắt để việc thành.', summary: 'Thích mục tiêu, đàm phán, kết nối nguồn lực, tạo đà.' },
      { id: 'C', name: 'Nghiệp vụ/Quy chuẩn', slogan: 'Rõ ràng, trật tự, chuẩn xác.', summary: 'Thích số liệu, quy trình, kiểm soát chất lượng, trật tự.' },
    ];
    return `
      <!-- 6 Nhóm cốt lõi -->
      <div class="mb-12">
        <div class="mb-5">
          <h3 class="font-display text-xl sm:text-2xl font-bold text-navy">6 Nhóm sở thích Holland cốt lõi</h3>
          <p class="text-xs sm:text-sm text-muted mt-1">Nền tảng của mô hình RIASEC phân loại theo 6 đặc trưng công việc và hoạt động.</p>
        </div>
        <div class="personality-showcase-grid grid sm:grid-cols-2 lg:grid-cols-3">
          ${list
            .map(
              (r, index) => `
            <article class="personality-showcase-card group" tabindex="0" role="button" aria-label="Xem chi tiết ${universityEscape(r.name)}" onclick="viewRiasecDetail('${r.id}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();viewRiasecDetail('${r.id}')}">
              <!-- Khung hình ảnh động lớn -->
              <div class="personality-showcase-art">
                <img src="/riasec/animated/RIASEC_${r.id}_animated.svg" alt="${universityEscape(r.name)} — Nhóm ${r.id}" loading="${index < 3 ? 'eager' : 'lazy'}" decoding="async" width="400" height="440" class="personality-showcase-image" onerror="this.src='/riasec/${r.id}.webp'">
              </div>
              <!-- Nội dung bên dưới -->
              <div class="personality-showcase-copy">
                <h3 class="sr-only">${r.name}</h3>
                <p class="personality-showcase-slogan">${r.slogan}</p>
                <p class="personality-showcase-summary">${r.summary}</p>
              </div>
            </article>
          `
            )
            .join('')}
        </div>
      </div>

      <!-- 120 Tổ hợp RIASEC -->
      <div class="pt-8 border-t border-line">
        <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
          <div>
            <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-azure/15 text-azure border border-azure/30 mb-2">
              <i data-lucide="sparkles" class="size-3.5"></i>
              <span>Cẩm nang toàn diện</span>
            </div>
            <h3 class="font-display text-2xl sm:text-3xl font-bold text-navy">120 Tổ hợp RIASEC (3 chữ cái)</h3>
            <p class="text-xs sm:text-sm text-muted mt-1">Phân tích tính cách • Điểm mạnh • Định hướng nghề nghiệp • Lời khuyên chi tiết cho từng tổ hợp.</p>
          </div>
          <span id="riasec-combs-count" class="shrink-0 px-3 py-1 rounded-full text-xs font-bold bg-ice text-azure border border-line">
            ${(state.riasecCombinations || []).length || 120} tổ hợp
          </span>
        </div>

        <!-- Filter bar -->
        <div class="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 mb-6 bg-card p-3 rounded-[20px] border border-line shadow-sm">
          <!-- Search box -->
          <div class="relative flex-1">
            <input type="text" id="riasec-comb-search" placeholder="Tìm kiếm theo mã (RIA, SEC...) hoặc ngành nghề, tính cách..." oninput="filterRiasecCombinations(this.value)" class="w-full pl-9 pr-4 py-2 rounded-xl bg-mist border border-line text-xs sm:text-sm text-navy focus:outline-none focus:border-azure">
            <i data-lucide="search" class="size-4 text-muted absolute left-3 top-1/2 -translate-y-1/2"></i>
          </div>

          <!-- Letters pills -->
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            <button id="riasec-pill-ALL" onclick="setRiasecLetterFilter('ALL')" class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-navy text-paper shadow-sm transition">Tất cả</button>
            ${['R', 'I', 'A', 'S', 'E', 'C'].map((l) => `
              <button id="riasec-pill-${l}" onclick="setRiasecLetterFilter('${l}')" class="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-card text-muted hover:text-navy border border-line shadow-sm transition">
                Nhóm ${l}
              </button>
            `).join('')}
          </div>
        </div>

        <!-- Combinations Grid Container -->
        <div id="riasec-combs-grid" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          ${renderRiasecCombsCardsHTML()}
        </div>
      </div>
    `;
  }

  // MBTI 16 Types Grid
  const list = state.personalities.length > 0 ? state.personalities : [
    { id: 'INTJ', name: 'Nhà chiến lược', slogan: 'Nhìn xa, tính kỹ, đi đúng hướng.', summary: 'Bạn thích nhìn bức tranh lớn, dựng mô hình trong đầu rồi mới hành động.' },
    { id: 'INTP', name: 'Nhà tư duy', slogan: 'Tò mò đến cùng, hỏi đến khi thông.', summary: 'Bạn sống với câu hỏi. Thế giới là một hệ thống có thể tháo ra để hiểu.' },
    { id: 'ENTJ', name: 'Nhà chỉ huy', slogan: 'Dẫn dắt bằng mục tiêu và hiệu quả.', summary: 'Tự tin, quyết đoán, nhìn ra cách tổ chức nguồn lực để đạt kết quả.' },
    { id: 'ENTP', name: 'Người tranh biện', slogan: 'Thử góc nhìn mới, cọ xát ý tưởng.', summary: 'Thích thử thách các tiền đề, tìm kiếm giải pháp đột phá.' },
    { id: 'INFJ', name: 'Người che chở', slogan: 'Lắng nghe sâu, đi cùng lý tưởng.', summary: 'Nhạy bén với con người, kiên trì với giá trị nhân văn.' },
    { id: 'INFP', name: 'Người lý tưởng', slogan: 'Trung thực với lòng mình, tử tế với đời.', summary: 'Giàu cảm xúc, trân trọng giọng riêng, tìm kiếm ý nghĩa đích thực.' },
    { id: 'ENFJ', name: 'Người truyền cảm hứng', slogan: 'Gắn kết mọi người vì điều tốt đẹp.', summary: 'Ấm áp, biết cách khích lệ và đồng hành cùng tập thể.' },
    { id: 'ENFP', name: 'Người truyền cảm hứng', slogan: 'Hào hứng khám phá mọi khả năng.', summary: 'Nhiệt huyết, sáng tạo, kết nối ý tưởng và con người nhanh chóng.' },
    { id: 'ISTJ', name: 'Người trách nhiệm', slogan: 'Làm đúng, giữ lời, bền bỉ đến cùng.', summary: 'Ngăn nắp, thực tế, giữ trật tự và kỷ luật vững vàng.' },
    { id: 'ISFJ', name: 'Người nuôi dưỡng', slogan: 'Chu đáo, tận tụy, âm thầm nâng đỡ.', summary: 'Ân cần, tỉ mỉ, luôn là chỗ dựa tin cậy cho người thân.' },
    { id: 'ESTJ', name: 'Người điều hành', slogan: 'Rõ ràng, quy củ, giải quyết việc gọn.', summary: 'Thực tế, có năng lực quản lý dự án và duy trì kỷ luật.' },
    { id: 'ESFJ', name: 'Người chăm sóc', slogan: 'Hòa nhã, chu toàn, giữ ấm không khí.', summary: 'Nhiệt tình, chu đáo, xây dựng môi trường gắn kết.' },
    { id: 'ISTP', name: 'Thợ cơ khí', slogan: 'Thao tác khéo léo, xử lý tại chỗ.', summary: 'Thực tế, thích làm việc với công cụ và giải quyết sự cố tức thì.' },
    { id: 'ISFP', name: 'Nghệ sĩ', slogan: 'Cảm nhận thế giới bằng từng giác quan.', summary: 'Tự do, nhạy cảm với cái đẹp, sống trọn với hiện tại.' },
    { id: 'ESTP', name: 'Người thực thi', slogan: 'Hành động ngay, không ngại thử thách.', summary: 'Năng động, thích ứng nhanh, tận hưởng nhịp sống sôi động.' },
    { id: 'ESFP', name: 'Người trình diễn', slogan: 'Sống hết mình, lan tỏa năng lượng vui.', summary: 'Hài hước, tự nhiên, mang lại tiếng cười cho xung quanh.' },
  ];

  return `
    <div class="personality-showcase-grid grid sm:grid-cols-2 lg:grid-cols-4">
      ${list
        .map(
          (p, index) => `
        <article class="personality-showcase-card group" tabindex="0" role="button" aria-label="Xem chi tiết ${universityEscape(p.name)}" onclick="viewMbtiDetail('${p.id}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();viewMbtiDetail('${p.id}')}">
          <!-- Khung hình ảnh động lớn, nền gradient nhẹ -->
          <div class="personality-showcase-art">
            <img
              src="/personality/MBTI_${p.id}_animated.svg"
              alt="${universityEscape(p.name)} — ${p.id}"
              loading="${index < 4 ? 'eager' : 'lazy'}" decoding="async" width="400" height="440"
              class="personality-showcase-image"
              onerror="this.src='/personality/${p.id}.webp'"
            >
          </div>
          <!-- Nội dung bên dưới -->
          <div class="personality-showcase-copy">
            <h3 class="sr-only">${p.name}</h3>
            <p class="personality-showcase-slogan">"${p.slogan}"</p>
            <p class="personality-showcase-summary">${p.summary}</p>
          </div>
        </article>
      `
        )
        .join('')}
    </div>
  `;
}

// Global helpers
window.toggleFaq = function (row) {
  const ans = row.querySelector('.faq-answer');
  const icon = row.querySelector('i');
  if (ans) {
    const isHidden = ans.classList.contains('hidden');
    ans.classList.toggle('hidden');
    if (icon) icon.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
  }
};


// --- RICH PERSONALITY & COMBINATION RENDERERS (MBTI & 120 RIASEC) ---

// --- RIASEC 3-AVATAR TRIPLET RENDERER (Chữ đứng đầu to nhất, 2 chữ còn lại) ---
function renderRiasecTripletImages(code, sizeMode = 'normal') {
  const letters = (code || 'RIA').slice(0, 3).split('');
  const lead = letters[0] || 'R';
  const sub1 = letters[1] || 'I';
  const sub2 = letters[2] || 'A';

  const leadNames = {
    R: 'Thực tế',
    I: 'Nghiên cứu',
    A: 'Nghệ thuật',
    S: 'Xã hội',
    E: 'Quản lý',
    C: 'Nghiệp vụ'
  };

  if (sizeMode === 'large') {
    // Large layout for detail modal & result banner (matching user image 1)
    return `
      <div class="inline-flex items-center gap-3 sm:gap-4 p-3.5 sm:p-4 rounded-[26px] bg-ice/80 dark:bg-slate-800/80 border border-azure/30 shadow-sm">
        <!-- Chữ đứng đầu to nhất có khung viền nổi bật -->
        <div class="flex flex-col items-center">
          <div class="rounded-[22px] bg-card ring-3 ring-azure p-2 shadow-md overflow-hidden flex items-center justify-center">
            <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${lead}_animated.svg" alt="Nhóm ${lead}" class="size-24 sm:size-28 object-contain" onerror="this.src='/riasec/${lead}.webp'">
          </div>
          <span class="mt-2 text-sm sm:text-base font-extrabold text-azure tracking-tight">Nhóm ${lead}</span>
          <span class="text-[11px] font-semibold text-muted">${leadNames[lead] || ''}</span>
        </div>

        <!-- Chữ thứ hai nhỏ hơn -->
        <div class="flex flex-col items-center opacity-90 hover:opacity-100 transition">
          <div class="rounded-[18px] bg-card border border-line p-1.5 shadow-xs overflow-hidden flex items-center justify-center">
            <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${sub1}_animated.svg" alt="Nhóm ${sub1}" class="size-16 sm:size-18 object-contain" onerror="this.src='/riasec/${sub1}.webp'">
          </div>
          <span class="mt-1.5 text-xs sm:text-sm font-bold text-navy">Nhóm ${sub1}</span>
          <span class="text-[10px] font-medium text-muted">${leadNames[sub1] || ''}</span>
        </div>

        <!-- Chữ thứ ba nhỏ hơn -->
        <div class="flex flex-col items-center opacity-90 hover:opacity-100 transition">
          <div class="rounded-[18px] bg-card border border-line p-1.5 shadow-xs overflow-hidden flex items-center justify-center">
            <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${sub2}_animated.svg" alt="Nhóm ${sub2}" class="size-16 sm:size-18 object-contain" onerror="this.src='/riasec/${sub2}.webp'">
          </div>
          <span class="mt-1.5 text-xs sm:text-sm font-bold text-navy">Nhóm ${sub2}</span>
          <span class="text-[10px] font-medium text-muted">${leadNames[sub2] || ''}</span>
        </div>
      </div>
    `;
  }

  // Compact layout for 120 cards in grid (matching user image 1)
  return `
    <div class="inline-flex items-center gap-2.5 p-2 rounded-[20px] bg-ice/70 dark:bg-slate-800/60 border border-azure/20 shadow-xs mb-3">
      <!-- Chữ đứng đầu to nhất -->
      <div class="flex flex-col items-center">
        <div class="rounded-[16px] bg-card ring-2 ring-azure p-1 shadow-sm overflow-hidden flex items-center justify-center">
          <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${lead}_animated.svg" alt="Nhóm ${lead}" class="size-14 sm:size-16 object-contain" onerror="this.src='/riasec/${lead}.webp'">
        </div>
        <span class="mt-1 text-xs font-black text-azure">Nhóm ${lead}</span>
      </div>

      <!-- Chữ thứ hai -->
      <div class="flex flex-col items-center opacity-90">
        <div class="rounded-[12px] bg-card border border-line/80 p-0.5 shadow-xs overflow-hidden flex items-center justify-center">
          <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${sub1}_animated.svg" alt="Nhóm ${sub1}" class="size-9 sm:size-10 object-contain" onerror="this.src='/riasec/${sub1}.webp'">
        </div>
        <span class="mt-0.5 text-[10px] font-bold text-muted">Nhóm ${sub1}</span>
      </div>

      <!-- Chữ thứ ba -->
      <div class="flex flex-col items-center opacity-90">
        <div class="rounded-[12px] bg-card border border-line/80 p-0.5 shadow-xs overflow-hidden flex items-center justify-center">
          <img loading="lazy" decoding="async" width="400" height="440" src="/riasec/animated/RIASEC_${sub2}_animated.svg" alt="Nhóm ${sub2}" class="size-9 sm:size-10 object-contain" onerror="this.src='/riasec/${sub2}.webp'">
        </div>
        <span class="mt-0.5 text-[10px] font-bold text-muted">Nhóm ${sub2}</span>
      </div>
    </div>
  `;
}

// Global Tab switcher for Facets
window.switchRiasecFacetTab = function (combCode, activeIndex) {
  const container = document.getElementById(`riasec-facets-box-${combCode}`);
  if (!container) return;
  const tabs = container.querySelectorAll('.riasec-facet-tab-btn');
  tabs.forEach((t) => {
    const idx = t.getAttribute('data-tab-idx');
    if (idx === String(activeIndex)) {
      t.className = 'riasec-facet-tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-navy text-paper shadow-sm transition';
    } else {
      t.className = 'riasec-facet-tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-card text-muted hover:text-navy border border-line shadow-sm transition';
    }
  });

  const panels = container.querySelectorAll('.riasec-facet-panel');
  panels.forEach((p) => {
    const idx = p.getAttribute('data-panel-idx');
    if (idx === String(activeIndex)) {
      p.classList.remove('hidden');
    } else {
      p.classList.add('hidden');
    }
  });
  refreshIcons();
};

window.switchMbtiFacetTab = function (mbtiId, activeIndex) {
  const container = document.getElementById(`mbti-facets-box-${mbtiId}`);
  if (!container) return;
  const tabs = container.querySelectorAll('.mbti-facet-tab-btn');
  tabs.forEach((t) => {
    const idx = t.getAttribute('data-tab-idx');
    if (idx === String(activeIndex)) {
      t.className = 'mbti-facet-tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-navy text-paper shadow-sm transition';
    } else {
      t.className = 'mbti-facet-tab-btn px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-card text-muted hover:text-navy border border-line shadow-sm transition';
    }
  });

  const panels = container.querySelectorAll('.mbti-facet-panel');
  panels.forEach((p) => {
    const idx = p.getAttribute('data-panel-idx');
    if (idx === String(activeIndex)) {
      p.classList.remove('hidden');
    } else {
      p.classList.add('hidden');
    }
  });
  refreshIcons();
};


function renderRiasecCombinationContent(comb) {
  if (!comb) return '<p class="text-sm text-muted">Không tìm thấy thông tin tổ hợp.</p>';
  const letters = (comb.code || "").split("");
  const lead = (comb.code || "R")[0];
  const facets = comb.facets || [];

  return `
    <div class="space-y-7">
      <!-- Header Banner với biểu tượng 3 chữ cái (Chữ đứng đầu to nhất) -->
      <div class="rounded-[26px] bg-gradient-to-br from-azure/10 via-card to-card border border-azure/30 p-6 sm:p-8 shadow-border flex flex-col lg:flex-row items-center lg:items-start justify-between gap-6">
        <div class="flex-1 text-center lg:text-left">
          <div class="flex flex-wrap items-center justify-center lg:justify-start gap-2.5 mb-2.5">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-azure/15 text-azure border border-azure/30">
              <span>Tổ hợp RIASEC</span>
              <span class="font-display text-sm tracking-wider text-navy">${comb.code}</span>
            </span>
            <span class="text-xs font-medium text-muted">Mô hình Holland 3 chữ cái</span>
          </div>
          <h3 class="font-display text-2xl sm:text-3xl font-bold text-navy leading-tight">${comb.title}</h3>
          <p class="text-sm sm:text-base font-semibold text-azure italic mt-2">"${comb.quote}"</p>
          <div class="mt-4 pt-4 border-t border-line/70">
            <h4 class="text-xs font-bold uppercase tracking-wider text-muted mb-2">I. Tổng quan tính cách</h4>
            <p class="text-sm sm:text-base text-navy/90 leading-relaxed">${comb.overview}</p>
          </div>
        </div>

        <!-- 3 biểu tượng: Chữ đứng đầu to nhất, 2 chữ còn lại nhỏ hơn -->
        <div class="shrink-0 flex flex-col items-center">
          ${renderRiasecTripletImages(comb.code, 'large')}
          <span class="mt-2 text-[11px] font-bold text-muted uppercase tracking-wider">Cấu trúc 3 thành tố</span>
        </div>
      </div>

      <!-- Section II: Phân tích 3 chỉ số cấu thành với TABS (TAG RIÊNG) RỘNG RÃI -->
      <div id="riasec-facets-box-${comb.code}" class="rounded-[26px] bg-card border border-line p-5 sm:p-7 shadow-border">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
          <div>
            <h4 class="font-display text-xl sm:text-2xl font-bold text-navy">II. Phân tích 3 chỉ số cấu thành (${letters.join(" • ")})</h4>
            <p class="text-xs sm:text-sm text-muted mt-1">Chọn từng nhóm để xem chi tiết chuyên sâu hoặc xem tổng hợp toàn bộ 3 nhóm.</p>
          </div>
        </div>

        <!-- Tag / Tab Navigation Buttons -->
        <div class="flex items-center gap-2 overflow-x-auto pb-2 mb-6 border-b border-line/60">
          ${facets.map((f, idx) => `
            <button type="button" data-tab-idx="${idx}" onclick="switchRiasecFacetTab('${comb.code}', ${idx})" class="riasec-facet-tab-btn px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition ${idx === 0 ? 'bg-navy text-paper font-bold shadow-sm' : 'bg-card text-muted hover:text-navy border border-line'}">
              <span class="inline-flex items-center gap-1.5">
                <span class="size-2 rounded-full ${idx === 0 ? 'bg-emerald-400' : 'bg-azure'}"></span>
                <span>Nhóm ${f.letter} · ${f.name || f.letter}</span>
                ${idx === 0 ? '<span class="text-[10px] px-1.5 py-0.2 rounded-md bg-white/20 text-white ml-1">Chủ đạo</span>' : ''}
              </span>
            </button>
          `).join('')}
          <button type="button" data-tab-idx="all" onclick="switchRiasecFacetTab('${comb.code}', 'all')" class="riasec-facet-tab-btn px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-card text-muted hover:text-navy border border-line transition">
            Xem tất cả 3 nhóm
          </button>
        </div>

        <!-- Individual Panels (Spacious, wide layout, enlarged avatar) -->
        ${facets.map((f, idx) => `
          <div data-panel-idx="${idx}" class="riasec-facet-panel ${idx === 0 ? '' : 'hidden'} space-y-6">
            <div class="flex flex-col md:flex-row items-center md:items-start gap-5 p-5 rounded-[22px] bg-mist/60 border border-line">
              <!-- Hình tượng trưng to lên -->
              <div class="relative shrink-0 flex flex-col items-center">
                <img src="/riasec/animated/RIASEC_${f.letter}_animated.svg" alt="${f.letter}" class="size-24 sm:size-28 rounded-[22px] bg-card p-2 shadow-md border-2 border-azure/40 object-contain" onerror="this.src='/riasec/${f.letter}.webp'">
                <span class="mt-2 text-xs font-black text-azure uppercase tracking-wider">Nhóm ${f.letter}</span>
              </div>
              <div class="flex-1 text-center md:text-left">
                <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-ice text-azure border border-azure/20 mb-2">
                  <span>Chỉ số thành phần ${idx + 1}/3</span>
                  <span>•</span>
                  <span>${idx === 0 ? 'Vị trí đứng đầu (Chủ đạo)' : 'Vị trí bổ trợ'}</span>
                </div>
                <h5 class="font-display text-xl sm:text-2xl font-bold text-navy">Chỉ số ${f.letter} — ${f.name || f.letter}</h5>
                <p class="text-sm sm:text-base text-navy/90 leading-relaxed mt-2.5">${f.description}</p>
              </div>
            </div>

            <!-- 2 khối Thế mạnh & Lưu ý cực kỳ rộng rãi -->
            <div class="grid gap-4 md:grid-cols-2">
              <div class="p-5 sm:p-6 rounded-[22px] bg-emerald-500/10 border border-emerald-500/30">
                <div class="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-bold text-base mb-2.5">
                  <i data-lucide="sparkles" class="size-5"></i>
                  <span>Thế mạnh đặc trưng</span>
                </div>
                <p class="text-xs sm:text-sm text-emerald-950 dark:text-emerald-100 leading-relaxed">${f.strength || 'Phát huy tính hành động và tư duy thực tiễn.'}</p>
              </div>
              <div class="p-5 sm:p-6 rounded-[22px] bg-amber-500/10 border border-amber-500/30">
                <div class="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-bold text-base mb-2.5">
                  <i data-lucide="alert-triangle" class="size-5"></i>
                  <span>Điểm cần lưu ý & Cân bằng</span>
                </div>
                <p class="text-xs sm:text-sm text-amber-950 dark:text-amber-100 leading-relaxed">${f.caution || 'Cần chú ý giữ tính kiên trì và phối hợp đội ngũ.'}</p>
              </div>
            </div>
          </div>
        `).join('')}

        <!-- "Xem tất cả 3 nhóm" Panel (Stacked full-width cards, never squished) -->
        <div data-panel-idx="all" class="riasec-facet-panel hidden space-y-6">
          ${facets.map((f, idx) => `
            <div class="p-5 sm:p-6 rounded-[22px] bg-card border border-line shadow-xs">
              <div class="flex flex-col sm:flex-row items-center sm:items-start gap-4 mb-4 pb-4 border-b border-line/60">
                <img src="/riasec/animated/RIASEC_${f.letter}_animated.svg" alt="${f.letter}" class="size-20 rounded-[18px] bg-ice p-1.5 shadow-sm border border-azure/30 shrink-0" onerror="this.src='/riasec/${f.letter}.webp'">
                <div class="flex-1 text-center sm:text-left">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-azure/15 text-azure mb-1">
                    Nhóm ${f.letter} · ${idx === 0 ? 'Chủ đạo' : 'Bổ trợ'}
                  </span>
                  <h5 class="font-display text-lg font-bold text-navy">${f.letter} — ${f.name || f.letter}</h5>
                  <p class="text-xs sm:text-sm text-muted mt-1 leading-relaxed">${f.description}</p>
                </div>
              </div>
              <div class="grid gap-3 sm:grid-cols-2 text-xs sm:text-sm">
                <div class="p-3.5 rounded-[16px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-950 dark:text-emerald-100">
                  <strong class="font-bold text-emerald-700 dark:text-emerald-300 block mb-1">Thế mạnh:</strong>
                  <span>${f.strength}</span>
                </div>
                <div class="p-3.5 rounded-[16px] bg-amber-500/10 border border-amber-500/20 text-amber-950 dark:text-amber-100">
                  <strong class="font-bold text-amber-700 dark:text-amber-300 block mb-1">Lưu ý:</strong>
                  <span>${f.caution}</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Section III: Điểm mạnh & Điểm nên phát triển -->
      <div>
        <h4 class="font-display text-lg sm:text-xl font-bold text-navy mb-3">III. Điểm mạnh nổi bật & Vùng cần phát triển</h4>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-[22px] bg-card border border-emerald-500/30 p-5 sm:p-6 shadow-sm">
            <div class="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-base mb-3.5">
              <i data-lucide="sparkles" class="size-5"></i>
              <span>Điểm mạnh nổi bật</span>
            </div>
            <ul class="space-y-2.5 text-xs sm:text-sm text-navy/90">
              ${(comb.strengths || []).map((s) => `
                <li class="flex items-start gap-2.5">
                  <span class="text-emerald-500 font-bold shrink-0 mt-0.5">✓</span>
                  <span>${s}</span>
                </li>
              `).join("")}
            </ul>
          </div>
          <div class="rounded-[22px] bg-card border border-amber-500/30 p-5 sm:p-6 shadow-sm">
            <div class="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold text-base mb-3.5">
              <i data-lucide="alert-triangle" class="size-5"></i>
              <span>Những điểm nên phát triển</span>
            </div>
            <ul class="space-y-2.5 text-xs sm:text-sm text-navy/90">
              ${(comb.improvements || []).map((imp) => `
                <li class="flex items-start gap-2.5">
                  <span class="text-amber-500 font-bold shrink-0 mt-0.5">!</span>
                  <span>${imp}</span>
                </li>
              `).join("")}
            </ul>
          </div>
        </div>
      </div>

      <!-- Section IV: Định hướng nghề nghiệp -->
      <div class="rounded-[22px] bg-card border border-line p-5 sm:p-6 shadow-sm">
        <h4 class="font-display text-lg sm:text-xl font-bold text-navy mb-2">IV. Định hướng sự nghiệp & Lĩnh vực phù hợp</h4>
        ${comb.careersIntroduction ? `<p class="text-xs sm:text-sm text-muted mb-3.5">${comb.careersIntroduction}</p>` : ""}
        <div class="flex flex-wrap gap-2 mb-3">
          ${(comb.careers || []).map((c) => `
            <span class="inline-flex items-center px-3.5 py-1.5 rounded-xl bg-ice text-azure border border-azure/20 text-xs sm:text-sm font-semibold">
              ${c}
            </span>
          `).join("")}
        </div>
        ${comb.careersNote ? `
          <div class="p-3.5 rounded-[16px] bg-mist border border-line text-xs text-muted leading-relaxed">
            <strong class="text-navy">📌 Ghi chú:</strong> ${comb.careersNote}
          </div>
        ` : ""}
      </div>

      <!-- Section V: Lời khuyên -->
      <div class="rounded-[22px] bg-gradient-to-r from-sky-50 to-indigo-50/60 dark:from-slate-800/80 dark:to-slate-800/40 border border-azure/30 p-5 sm:p-6 shadow-sm">
        <div class="flex items-center gap-2 text-azure font-bold text-base mb-2">
          <i data-lucide="lightbulb" class="size-5"></i>
          <span>V. Lời khuyên dành cho bạn (${comb.code})</span>
        </div>
        <p class="text-xs sm:text-sm text-navy/90 leading-relaxed">${comb.advice}</p>
      </div>
    </div>
  `;
}


function renderMbtiDetailContent(pInfo) {
  if (!pInfo) return '<p class="text-sm text-muted">Không tìm thấy thông tin MBTI.</p>';
  const facets = pInfo.facets || [];

  return `
    <div class="space-y-7">
      <!-- Header Banner với hình minh họa MBTI phóng to -->
      <div class="rounded-[26px] bg-gradient-to-br from-azure/10 via-card to-card border border-azure/30 p-6 sm:p-8 shadow-border flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex-1 text-center md:text-left">
          <div class="flex flex-wrap items-center justify-center md:justify-start gap-2.5 mb-2.5">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-azure/15 text-azure border border-azure/30">
              <span>Nhóm tính cách MBTI</span>
              <span class="font-display text-sm tracking-wider text-navy">${pInfo.id}</span>
            </span>
            <span class="text-xs font-semibold text-muted">${pInfo.name}</span>
          </div>
          <h3 class="font-display text-2xl sm:text-3xl font-bold text-navy">${pInfo.title || (pInfo.id + " · " + pInfo.name)}</h3>
          <p class="text-sm sm:text-base font-semibold text-azure italic mt-2">"${pInfo.quote || pInfo.slogan}"</p>
          <div class="mt-4 pt-4 border-t border-line/70">
            <h4 class="text-xs font-bold uppercase tracking-wider text-muted mb-2">I. Tổng quan tính cách</h4>
            <p class="text-sm sm:text-base text-navy/90 leading-relaxed">${pInfo.description || pInfo.summary}</p>
          </div>
        </div>
        <div class="shrink-0 flex flex-col items-center">
          <div class="rounded-[24px] bg-card ring-3 ring-azure/40 p-2 shadow-md overflow-hidden flex items-center justify-center">
            <img src="/personality/MBTI_${pInfo.id}_animated.svg" alt="${pInfo.id}" class="size-28 sm:size-36 object-contain" onerror="this.src='/personality/${pInfo.id}.webp'">
          </div>
          <span class="mt-2 text-xs font-black text-azure uppercase tracking-wider">${pInfo.id} · ${pInfo.name}</span>
        </div>
      </div>

      <!-- Section II: Phân tích 4 chỉ số cấu thành với TABS (TAG RIÊNG) RỘNG RÃI -->
      ${facets.length ? `
        <div id="mbti-facets-box-${pInfo.id}" class="rounded-[26px] bg-card border border-line p-5 sm:p-7 shadow-border">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
            <div>
              <h4 class="font-display text-xl sm:text-2xl font-bold text-navy">II. Phân tích 4 chỉ số cấu thành (${pInfo.id.split("").join(" • ")})</h4>
              <p class="text-xs sm:text-sm text-muted mt-1">Chọn từng trục để xem chi tiết không bị co hẹp chữ hoặc bấm Xem tất cả 4 trục.</p>
            </div>
          </div>

          <!-- Tag Navigation Buttons -->
          <div class="flex items-center gap-2 overflow-x-auto pb-2 mb-6 border-b border-line/60">
            ${facets.map((f, idx) => `
              <button type="button" data-tab-idx="${idx}" onclick="switchMbtiFacetTab('${pInfo.id}', ${idx})" class="mbti-facet-tab-btn px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition ${idx === 0 ? 'bg-navy text-paper font-bold shadow-sm' : 'bg-card text-muted hover:text-navy border border-line'}">
                <span class="inline-flex items-center gap-1.5">
                  <span class="size-2 rounded-full ${idx === 0 ? 'bg-emerald-400' : 'bg-azure'}"></span>
                  <span>${f.name || f.letter}</span>
                </span>
              </button>
            `).join('')}
            <button type="button" data-tab-idx="all" onclick="switchMbtiFacetTab('${pInfo.id}', 'all')" class="mbti-facet-tab-btn px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold bg-card text-muted hover:text-navy border border-line transition">
              Xem tất cả 4 trục
            </button>
          </div>

          <!-- Individual Panels (Spacious, wide layout) -->
          ${facets.map((f, idx) => `
            <div data-panel-idx="${idx}" class="mbti-facet-panel ${idx === 0 ? '' : 'hidden'} space-y-6">
              <div class="flex flex-col md:flex-row items-center md:items-start gap-5 p-5 rounded-[22px] bg-mist/60 border border-line">
                <div class="size-20 sm:size-24 rounded-[22px] bg-ice ring-2 ring-azure/30 p-2 shadow-sm grid place-items-center shrink-0">
                  <span class="font-display font-black text-3xl sm:text-4xl text-azure">${f.letter}</span>
                </div>
                <div class="flex-1 text-center md:text-left">
                  <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-ice text-azure border border-azure/20 mb-2">
                    <span>Trục tính cách ${idx + 1}/4</span>
                  </div>
                  <h5 class="font-display text-xl sm:text-2xl font-bold text-navy">${f.name || f.letter}</h5>
                  <p class="text-sm sm:text-base text-navy/90 leading-relaxed mt-2.5">${f.description}</p>
                </div>
              </div>

              <div class="grid gap-4 md:grid-cols-2">
                <div class="p-5 sm:p-6 rounded-[22px] bg-emerald-500/10 border border-emerald-500/30">
                  <div class="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-bold text-base mb-2.5">
                    <i data-lucide="sparkles" class="size-5"></i>
                    <span>Thế mạnh nổi bật</span>
                  </div>
                  <p class="text-xs sm:text-sm text-emerald-950 dark:text-emerald-100 leading-relaxed">${f.strength}</p>
                </div>
                <div class="p-5 sm:p-6 rounded-[22px] bg-amber-500/10 border border-amber-500/30">
                  <div class="flex items-center gap-2 text-amber-700 dark:text-amber-300 font-bold text-base mb-2.5">
                    <i data-lucide="alert-triangle" class="size-5"></i>
                    <span>Điểm cần lưu ý & Phát triển</span>
                  </div>
                  <p class="text-xs sm:text-sm text-amber-950 dark:text-amber-100 leading-relaxed">${f.caution}</p>
                </div>
              </div>
            </div>
          `).join('')}

          <!-- "Xem tất cả 4 trục" Panel (2-column wide layout) -->
          <div data-panel-idx="all" class="mbti-facet-panel hidden grid gap-5 md:grid-cols-2">
            ${facets.map((f, idx) => `
              <div class="p-5 sm:p-6 rounded-[22px] bg-card border border-line shadow-xs flex flex-col justify-between">
                <div>
                  <div class="flex items-center gap-3 mb-3">
                    <span class="grid size-10 place-items-center rounded-xl bg-ice font-display font-extrabold text-azure text-lg">
                      ${f.letter}
                    </span>
                    <div>
                      <h5 class="font-display text-base font-bold text-navy">${f.name || f.letter}</h5>
                      <span class="text-xs font-medium text-muted">Trục ${idx + 1}/4</span>
                    </div>
                  </div>
                  <p class="text-xs sm:text-sm text-muted leading-relaxed mb-4">${f.description}</p>
                </div>
                <div class="space-y-2 text-xs">
                  <div class="p-3 rounded-[14px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-950 dark:text-emerald-100">
                    <strong class="text-emerald-700 dark:text-emerald-300 block mb-0.5">Thế mạnh:</strong>
                    <span>${f.strength}</span>
                  </div>
                  <div class="p-3 rounded-[14px] bg-amber-500/10 border border-amber-500/20 text-amber-950 dark:text-amber-100">
                    <strong class="text-amber-700 dark:text-amber-300 block mb-0.5">Lưu ý:</strong>
                    <span>${f.caution}</span>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Section III: Điểm mạnh & Điểm nên phát triển -->
      <div>
        <h4 class="font-display text-lg sm:text-xl font-bold text-navy mb-3">III. Điểm mạnh nổi bật & Vùng cần phát triển</h4>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-[22px] bg-card border border-emerald-500/30 p-5 sm:p-6 shadow-sm">
            <div class="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-base mb-3.5">
              <i data-lucide="sparkles" class="size-5"></i>
              <span>Điểm mạnh nổi bật</span>
            </div>
            <ul class="space-y-2.5 text-xs sm:text-sm text-navy/90">
              ${(pInfo.strengths || []).map((s) => `
                <li class="flex items-start gap-2.5">
                  <span class="text-emerald-500 font-bold shrink-0 mt-0.5">✓</span>
                  <span>${s}</span>
                </li>
              `).join("")}
            </ul>
          </div>
          <div class="rounded-[22px] bg-card border border-amber-500/30 p-5 sm:p-6 shadow-sm">
            <div class="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold text-base mb-3.5">
              <i data-lucide="alert-triangle" class="size-5"></i>
              <span>Những điểm nên phát triển</span>
            </div>
            <ul class="space-y-2.5 text-xs sm:text-sm text-navy/90">
              ${(pInfo.improvements || []).map((imp) => `
                <li class="flex items-start gap-2.5">
                  <span class="text-amber-500 font-bold shrink-0 mt-0.5">!</span>
                  <span>${imp}</span>
                </li>
              `).join("")}
            </ul>
          </div>
        </div>
      </div>

      <!-- Section IV: Gợi ý nghề nghiệp -->
      <div class="rounded-[22px] bg-card border border-line p-5 sm:p-6 shadow-sm">
        <h4 class="font-display text-lg sm:text-xl font-bold text-navy mb-2">IV. Gợi ý ngành nghề & Môi trường phù hợp</h4>
        <p class="text-xs sm:text-sm text-muted mb-3.5">Các lĩnh vực và vai trò công việc phát huy tốt đặc trưng của ${pInfo.id}:</p>
        <div class="flex flex-wrap gap-2 mb-3">
          ${(pInfo.careers || []).map((c) => `
            <span class="inline-flex items-center px-3.5 py-1.5 rounded-xl bg-ice text-azure border border-azure/20 text-xs sm:text-sm font-semibold">
              ${c}
            </span>
          `).join("")}
        </div>
        ${pInfo.environment ? `
          <div class="p-3.5 rounded-[16px] bg-mist border border-line text-xs text-muted leading-relaxed">
            <strong class="text-navy">Môi trường lý tưởng:</strong> ${pInfo.environment}
          </div>
        ` : ""}
      </div>

      <!-- Section V: Lời khuyên -->
      ${pInfo.advice ? `
        <div class="rounded-[22px] bg-gradient-to-r from-sky-50 to-indigo-50/60 dark:from-slate-800/80 dark:to-slate-800/40 border border-azure/30 p-5 sm:p-6 shadow-sm">
          <div class="flex items-center gap-2 text-azure font-bold text-base mb-2">
            <i data-lucide="lightbulb" class="size-5"></i>
            <span>V. Lời khuyên dành cho bạn (${pInfo.id})</span>
          </div>
          <p class="text-xs sm:text-sm text-navy/90 leading-relaxed">${pInfo.advice}</p>
        </div>
      ` : ""}
    </div>
  `;
}


function renderRiasecCombsCardsHTML() {
  const letter = state.riasecCombLetter || 'ALL';
  const q = state.riasecCombFilter || '';

  const leadNames = {
    R: 'Thực tế',
    I: 'Nghiên cứu',
    A: 'Nghệ thuật',
    S: 'Xã hội',
    E: 'Quản lý',
    C: 'Nghiệp vụ'
  };

  const combs = (state.riasecCombinations || []).filter((c) => {
    const matchLetter = letter === 'ALL' || c.code.startsWith(letter);
    const matchQuery =
      !q ||
      c.code.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      (c.quote && c.quote.toLowerCase().includes(q)) ||
      (c.careers && c.careers.some((car) => car.toLowerCase().includes(q)));
    return matchLetter && matchQuery;
  });

  if (combs.length === 0) {
    return `
      <div class="col-span-full py-12 text-center text-muted text-sm">
        Không tìm thấy tổ hợp phù hợp với từ khóa "${q}".
      </div>
    `;
  }

  return combs
    .map((c) => {
      const lead = (c.code || 'R')[0];
      const leadTitle = leadNames[lead] || ('Nhóm ' + lead);
      return `
    <article class="flex h-full flex-col justify-between rounded-[24px] bg-card p-5 shadow-border hover:-translate-y-1.5 hover:shadow-border-hover transition duration-200 border border-line/70 cursor-pointer group" onclick="viewRiasecCombinationDetail('${c.code}')">
      <div>
        <!-- 3 biểu tượng RIASEC: Chữ đứng đầu to nhất, 2 chữ còn lại nhỏ hơn (như hình mẫu) -->
        <div class="mb-3.5">
          ${renderRiasecTripletImages(c.code, 'compact')}
        </div>

        <div class="flex items-center gap-2 mb-1.5">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-black bg-ice text-azure border border-azure/20 tracking-wider">
            ${c.code}
          </span>
          <span class="text-xs font-bold text-muted">${leadTitle} (${lead}) dẫn đầu</span>
        </div>

        <h4 class="font-display text-base font-bold text-navy group-hover:text-azure transition leading-snug mb-1.5 line-clamp-2">
          ${c.title}
        </h4>
        <p class="text-xs text-azure font-medium italic line-clamp-1 mb-2">
          "${c.quote}"
        </p>
        <p class="text-xs text-muted leading-relaxed line-clamp-2">
          ${c.overview}
        </p>
      </div>
      <div class="mt-4 pt-3 border-t border-line/60 flex items-center justify-between text-xs font-bold text-azure group-hover:text-navy transition">
        <span>Xem chi tiết ${c.code}</span>
        <i data-lucide="chevron-right" class="size-4"></i>
      </div>
    </article>
  `;
    })
    .join('');
}

window.setRiasecLetterFilter = function (letter) {
  state.riasecCombLetter = letter;
  renderRiasecCombsGrid();
};

window.filterRiasecCombinations = function (q) {
  state.riasecCombFilter = (q || '').trim().toLowerCase();
  renderRiasecCombsGrid();
};

function renderRiasecCombsGrid() {
  const container = document.getElementById('riasec-combs-grid');
  if (!container) return;
  const letter = state.riasecCombLetter || 'ALL';
  const q = state.riasecCombFilter || '';

  const combs = (state.riasecCombinations || []).filter((c) => {
    const matchLetter = letter === 'ALL' || c.code.startsWith(letter);
    const matchQuery =
      !q ||
      c.code.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      (c.quote && c.quote.toLowerCase().includes(q)) ||
      (c.careers && c.careers.some((car) => car.toLowerCase().includes(q)));
    return matchLetter && matchQuery;
  });

  const countBadge = document.getElementById('riasec-combs-count');
  if (countBadge) {
    countBadge.textContent = `${combs.length} tổ hợp`;
  }

  ['ALL', 'R', 'I', 'A', 'S', 'E', 'C'].forEach((l) => {
    const btn = document.getElementById(`riasec-pill-${l}`);
    if (btn) {
      if (l === letter) {
        btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-bold bg-navy text-paper shadow-sm transition';
      } else {
        btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-semibold bg-card text-muted hover:text-navy border border-line shadow-sm transition';
      }
    }
  });

  container.innerHTML = renderRiasecCombsCardsHTML();
  refreshIcons();
}

window.viewRiasecCombinationDetail = function (code) {
  const item = (state.riasecCombinations || []).find((c) => c.code === code);
  if (!item) return;
  openDetailModal(renderRiasecCombinationContent(item));
};

window.viewMbtiDetail = function (id) {
  const item = state.personalities.find((p) => p.id === id);
  if (!item) return;
  openDetailModal(renderMbtiDetailContent(item));
};

window.viewRiasecDetail = function (id) {
  const item = state.riasecTypes.find((r) => r.id === id);
  if (!item) return;
  openDetailModal(`
    <div class="flex items-center gap-4 mb-4">
      <img src="/riasec/animated/RIASEC_${item.id}_animated.svg" alt="${item.id}" class="size-16 rounded-[16px] bg-ice object-contain p-1 shadow-border" onerror="this.src='/riasec/animated/${item.id}.svg'">
      <div>
        <h3 class="font-display text-2xl font-bold text-navy">${item.id} · ${item.name}</h3>
        <p class="text-sm font-semibold text-azure mt-1">"${item.slogan}"</p>
      </div>
    </div>
    <p class="text-sm text-muted leading-relaxed mb-6">${item.description || item.summary}</p>
    <div class="space-y-3 text-xs sm:text-sm">
      <div class="p-3.5 rounded-[16px] bg-mist border border-line">
        <strong class="text-navy block mb-1">Đặc điểm tương tác:</strong>
        <p class="text-muted">${item.interacting || 'Rõ ràng, tôn trọng sự độc lập và công việc thực tế.'}</p>
      </div>
      <div class="p-3.5 rounded-[16px] bg-mist border border-line">
        <strong class="text-navy block mb-1">Ngành nghề tiêu biểu:</strong>
        <p class="text-navy font-semibold">${item.careers?.join(', ') || 'Kỹ thuật, Công nghệ, Quản trị, Y tế'}</p>
      </div>
    </div>
  `);
};

// ==========================================================================
// 2. QUIZZES VIEW & QUIZ PLAYER (MBTI, RIASEC, BIG FIVE)
// ==========================================================================
function renderQuizzes(container) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Trắc nghiệm</p>
        <h1 class="mt-2 font-display text-3xl font-semibold text-navy sm:text-4xl">Chọn bài trắc nghiệm</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Bốn góc nhìn đa chiều về con người bạn: Sở thích nghề nghiệp (RIASEC), Năng lực nhận thức cốt lõi, Năm chiều tính cách (Big Five), và Phong cách tư duy (MBTI).
        </p>
      </div>
    </div>
    <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        ${renderQuizPickerCards()}
      </div>
    </div>
  `;
}

async function renderQuizPlayer(container, quizId) {
  const requestedRoute = window.location.hash;
  let authenticated = false;
  if (state.authToken) {
    try {
      const response = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${state.authToken}` },
      });
      authenticated = response.ok;
    } catch (_) { /* Fail closed when the session cannot be verified. */ }
  }
  if (window.location.hash !== requestedRoute) return;
  if (!authenticated) {
    sessionStorage.setItem('fyf_after_login', `#trac-nghiem/${encodeURIComponent(quizId)}`);
    showToast('Vui lòng đăng nhập để làm bài trắc nghiệm.', 'info');
    window.location.hash = '#dang-nhap';
    return;
  }

  const quiz = state.quizzes.find((q) => q.id === quizId) || {
    id: quizId,
    name: quizId.toUpperCase(),
    duration: '10–12 phút',
    questionCount: 60,
  };

  const rawQuestions = state.questions[quizId] || [];
  if (rawQuestions.length === 0) {
    container.innerHTML = `
      <div class="max-w-2xl mx-auto py-16 px-4 text-center">
        <p class="text-base text-muted">Đang tải bộ câu hỏi ${quiz.name}...</p>
      </div>
    `;
    loadAllData().then(() => renderQuizPlayer(container, quizId));
    return;
  }

  // Session state
  state.activeQuiz = quizId;
  if (!state.quizAnswers || state.quizAnswers.length !== rawQuestions.length) {
    state.quizAnswers = Array(rawQuestions.length).fill(-1);
    state.quizIndex = 0;
  }

  function drawCurrentStep() {
    const qIndex = state.quizIndex;
    const currentQ = rawQuestions[qIndex];
    const total = rawQuestions.length;
    const answered = state.quizAnswers.filter((a) => a >= 0).length;
    const pct = Math.round((answered / total) * 100);

    // Standard 5 Likert labels for RIASEC & Big Five, or specific options for MBTI
    const options = currentQ.options || [
      { label: 'Hoàn toàn không', score: 1 },
      { label: 'Ít khi', score: 2 },
      { label: 'Ở giữa', score: 3 },
      { label: 'Khá đúng', score: 4 },
      { label: 'Rất đúng', score: 5 },
    ];

    container.innerHTML = `
      <div class="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <!-- Top bar with Back button and progress -->
        <div class="flex items-center justify-between gap-4 mb-6">
          <a href="#trac-nghiem" class="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-navy transition">
            <i data-lucide="arrow-left" class="size-4"></i>
            <span>Trở lại danh sách</span>
          </a>
          <span class="font-display text-xs font-semibold text-azure tabular-nums">
            Câu ${qIndex + 1} / ${total} (${pct}%)
          </span>
        </div>

        <!-- Smooth Progress Bar -->
        <div class="h-2 w-full bg-mist rounded-full overflow-hidden mb-8 border border-line/60">
          <div class="h-full bg-gradient-to-r from-azure to-cyan rounded-full transition-all duration-300" style="width: ${pct}%"></div>
        </div>

        <!-- Question Box -->
        <div class="rounded-[28px] bg-card border border-line p-6 sm:p-10 shadow-border">
          <div class="flex items-center gap-2 mb-3 flex-wrap">
            <span class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">
              Bài test: ${quiz.name}
            </span>
            ${currentQ.domainName ? `<span class="px-2.5 py-0.5 rounded-full bg-ice text-azure font-bold text-[11px] border border-line/50">${currentQ.domainName}</span>` : ''}
          </div>
          <h2 class="font-display text-xl sm:text-2xl font-bold text-navy leading-snug mb-8">
            ${currentQ.text || currentQ.prompt}
          </h2>

          <!-- Options -->
          <div class="space-y-3">
            ${options
              .map((opt, oIdx) => {
                const isSelected = state.quizAnswers[qIndex] === oIdx;
                return `
                <button class="option-card w-full p-4 text-left flex items-center justify-between rounded-[16px] ${isSelected ? 'is-on' : ''}" onclick="selectAnswer(${oIdx})">
                  <span class="text-sm sm:text-base font-medium ${isSelected ? 'text-navy font-semibold' : 'text-ink'}">${opt.label}</span>
                  <span class="grid size-6 place-items-center rounded-full border border-line text-xs font-bold ${isSelected ? 'bg-azure text-paper border-azure' : 'text-muted'}">
                    ${isSelected ? '✓' : oIdx + 1}
                  </span>
                </button>
              `;
              })
              .join('')}
          </div>

          <!-- Bottom controls -->
          <div class="quiz-step-actions flex items-center justify-between pt-8 mt-8 border-t border-line">
            <button id="btn-q-prev" class="inline-flex items-center gap-1.5 px-4 py-2 rounded-[12px] border border-line bg-card text-navy text-xs font-semibold hover:bg-mist transition ${qIndex === 0 ? 'opacity-40 pointer-events-none' : ''}">
              <i data-lucide="chevron-left" class="size-4"></i>
              <span>Câu trước</span>
            </button>
            <span class="text-xs text-muted">Dùng phím số 1-${options.length} để chọn nhanh</span>
            <button id="btn-q-next" class="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-[12px] bg-navy text-paper text-xs font-semibold hover:bg-navy-deep cta-glow transition ${state.quizAnswers[qIndex] < 0 ? 'opacity-40 pointer-events-none' : ''}">
              <span>${qIndex === total - 1 ? 'Hoàn thành' : 'Câu tiếp theo'}</span>
              <i data-lucide="chevron-right" class="size-4"></i>
            </button>
          </div>
        </div>
      </div>
    `;
    refreshIcons();

    // Attach Prev / Next handlers
    const btnPrev = document.getElementById('btn-q-prev');
    const btnNext = document.getElementById('btn-q-next');
    if (btnPrev) {
      btnPrev.addEventListener('click', () => {
        if (state.quizIndex > 0) {
          state.quizIndex--;
          drawCurrentStep();
        }
      });
    }
    if (btnNext) {
      btnNext.addEventListener('click', () => {
        if (state.quizIndex < total - 1) {
          state.quizIndex++;
          drawCurrentStep();
        } else {
          finishQuizSession(container, quizId, rawQuestions);
        }
      });
    }
  }

  window.selectAnswer = function (optIdx) {
    state.quizAnswers[state.quizIndex] = optIdx;
    if (state.quizIndex < rawQuestions.length - 1) {
      state.quizIndex++;
      drawCurrentStep();
    } else {
      drawCurrentStep();
    }
  };

  drawCurrentStep();
}

function finishQuizSession(container, quizId, questions) {
  const quizOwner = state.currentUser?.user_id;
  const quizToken = state.authToken;
  // Show analyzing screen
  container.innerHTML = `
    <div class="max-w-md mx-auto py-24 px-4 text-center">
      <div class="relative size-16 mx-auto mb-6">
        <div class="size-16 rounded-full border-4 border-azure/20 border-t-azure animate-spin"></div>
      </div>
      <h3 class="font-display text-2xl font-bold text-navy mb-2">Đang phân tích kết quả...</h3>
      <p class="text-xs sm:text-sm text-muted">Hệ thống đang đối chiếu câu trả lời và tạo hồ sơ tính cách của bạn.</p>
    </div>
  `;
  refreshIcons();

  // Compute scores based on quizId
  setTimeout(async () => {
    let result = null;

    if (quizId === 'riasec') {
      const scores = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 };
      questions.forEach((q, idx) => {
        const ans = state.quizAnswers[idx];
        const val = ans >= 0 ? ans + 1 : 1; // 1-5 điểm
        const trait = q.trait || q.group || 'R';
        scores[trait] = (scores[trait] || 0) + val;
      });
      const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
      const code = `${sorted[0][0]}${sorted[1][0]}${sorted[2][0]}`;
      result = { quizId: 'riasec', code, scores, sorted, completedAt: new Date().toISOString() };
    } else if (quizId === 'mbti') {
      const counts = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
      questions.forEach((q, idx) => {
        const ans = state.quizAnswers[idx];
        const opt = q.options && q.options[ans];
        if (opt && opt.scores) {
          Object.entries(opt.scores).forEach(([k, v]) => {
            counts[k] = (counts[k] || 0) + v;
          });
        }
      });
      const type = `${counts.E >= counts.I ? 'E' : 'I'}${counts.S >= counts.N ? 'S' : 'N'}${counts.T >= counts.F ? 'T' : 'F'}${counts.J >= counts.P ? 'J' : 'P'}`;
      result = { quizId: 'mbti', type, counts, completedAt: new Date().toISOString() };
    } else if (quizId === 'cognitive') {
      let verbalScore = 0;
      let numericalScore = 0;
      let figuralScore = 0;
      let totalScore = 0;

      const userAnswersDetail = questions.map((q, idx) => {
        const userChoice = state.quizAnswers[idx];
        const isCorrect = userChoice === q.correctAnswer;
        if (isCorrect) {
          totalScore++;
          if (q.domain === 'verbal') verbalScore++;
          else if (q.domain === 'numerical') numericalScore++;
          else if (q.domain === 'figural') figuralScore++;
        }
        return {
          questionId: q.id,
          number: idx + 1,
          text: q.text || q.prompt || '',
          domain: q.domain,
          domainName: q.domainName,
          userChoice: userChoice,
          userChoiceLabel: (userChoice >= 0 && q.options && q.options[userChoice]) ? q.options[userChoice].label : 'Chưa trả lời',
          correctAnswer: q.correctAnswer,
          correctAnswerLabel: (q.options && q.options[q.correctAnswer]) ? q.options[q.correctAnswer].label : '',
          isCorrect,
          explanation: q.explanation || ''
        };
      });

      const totalPct = Math.round((totalScore / 30) * 100);
      const verbalPct = Math.round((verbalScore / 10) * 100);
      const numericalPct = Math.round((numericalScore / 10) * 100);
      const figuralPct = Math.round((figuralScore / 10) * 100);

      const getTier = (pct) => {
        if (pct >= 70) return 'Nổi bật';
        if (pct >= 40) return 'Khá';
        return 'Cần củng cố';
      };

      const domains = [
        { id: 'verbal', name: 'Ngôn ngữ (Verbal)', score: verbalScore, pct: verbalPct },
        { id: 'numerical', name: 'Định lượng (Numerical)', score: numericalScore, pct: numericalPct },
        { id: 'figural', name: 'Hình ảnh & Quy luật (Figural)', score: figuralScore, pct: figuralPct }
      ];
      domains.sort((a, b) => b.score - a.score);

      result = {
        quizId: 'cognitive',
        totalScore,
        totalPct,
        tier: getTier(totalPct),
        dominantDomain: domains[0].name,
        verbalScore,
        verbalPct,
        verbalTier: getTier(verbalPct),
        numericalScore,
        numericalPct,
        numericalTier: getTier(numericalPct),
        figuralScore,
        figuralPct,
        figuralTier: getTier(figuralPct),
        userAnswersDetail,
        completedAt: new Date().toISOString()
      };
    } else {
      // Big Five Standardization (25 questions, O-C-E-A-N 5 each, reverse: 3, 7, 11, 15, 19)
      const rawScores = { O: 0, C: 0, E: 0, A: 0, N: 0 };
      const reverseIndices = new Set([2, 6, 10, 14, 18]); // 0-based for Q3, Q7, Q11, Q15, Q19
      const domainMap = {
        0: 'O', 1: 'O', 2: 'O', 3: 'O', 20: 'O',
        4: 'C', 5: 'C', 6: 'C', 7: 'C', 21: 'C',
        8: 'E', 9: 'E', 10: 'E', 11: 'E', 22: 'E',
        12: 'A', 13: 'A', 14: 'A', 15: 'A', 23: 'A',
        16: 'N', 17: 'N', 18: 'N', 19: 'N', 24: 'N'
      };

      questions.forEach((q, idx) => {
        const ans = state.quizAnswers[idx];
        const rawChoice = ans >= 0 ? ans + 1 : 3;
        const isRev = reverseIndices.has(idx) || q.isReverse;
        const val = isRev ? (6 - rawChoice) : rawChoice;
        const domain = q.trait || q.group || domainMap[idx] || 'O';
        rawScores[domain] = (rawScores[domain] || 0) + val;
      });

      const getBfTier = (pct) => {
        if (pct >= 67) return { label: 'Cao', class: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' };
        if (pct >= 34) return { label: 'Trung bình', class: 'bg-azure/15 text-azure border border-azure/30' };
        return { label: 'Thấp', class: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30' };
      };

      const normalizedScores = {};
      const tiers = {};
      ['O', 'C', 'E', 'A', 'N'].forEach((k) => {
        const raw = rawScores[k] || 5;
        // Formula: ((tổng - 5) / 20) * 100
        const pct = Math.max(0, Math.min(100, Math.round(((raw - 5) / 20) * 100)));
        normalizedScores[k] = pct;
        tiers[k] = getBfTier(pct);
      });

      result = {
        quizId: 'bigfive',
        rawScores,
        scores: normalizedScores,
        tiers,
        completedAt: new Date().toISOString()
      };
    }

    if (state.currentUser?.user_id !== quizOwner || state.authToken !== quizToken) return;
    state.results[quizId] = result;
    localStorage.setItem(`fyf_result_${quizId}`, JSON.stringify(result));
    const queueKey = `fyf_pending_assessments_${quizOwner}`;
    const queue = JSON.parse(localStorage.getItem(queueKey) || '{}');
    queue[quizId] = result;
    localStorage.setItem(queueKey, JSON.stringify(queue));
    try { await syncAccountAssessments(); }
    catch (_) { showToast('Kết quả đã lưu tạm. Hệ thống sẽ thử đồng bộ lại trước khi tư vấn.', 'warning'); }
    window.location.hash = `#ket-qua/${quizId}`;
  }, 1000);
}

function renderQuizResult(container, quizId) {
  const result = state.results[quizId];
  if (!result) {
    container.innerHTML = `
      <div class="max-w-md mx-auto py-20 px-4 text-center">
        <p class="text-sm text-muted mb-4">Bạn chưa hoàn thành bài test này.</p>
        <a href="#trac-nghiem/${quizId}" class="inline-flex items-center gap-2 px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
          Làm bài test ngay
        </a>
      </div>
    `;
    return;
  }

  if (quizId === 'cognitive') {
    const totalScore = result.totalScore !== undefined ? result.totalScore : 0;
    const totalPct = result.totalPct !== undefined ? result.totalPct : Math.round((totalScore / 30) * 100);
    const tier = result.tier || (totalPct >= 70 ? 'Nổi bật' : totalPct >= 40 ? 'Khá' : 'Cần củng cố');
    const dominantDomain = result.dominantDomain || 'Định lượng (Numerical)';
    const details = result.userAnswersDetail || [];

    const getTierBadge = (t) => {
      if (t === 'Nổi bật') return '<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">⭐ Nổi bật (70–100%)</span>';
      if (t === 'Khá') return '<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">🔷 Khá (40–69%)</span>';
      return '<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">⚡ Cần củng cố (0–39%)</span>';
    };

    // Cross integration with RIASEC
    let riasecSynthesis = '';
    if (state.results.riasec && state.results.riasec.code) {
      const rCode = state.results.riasec.code;
      let sweetSpot = '';
      if ((result.numericalScore || 0) >= 7 && (rCode.includes('I') || rCode.includes('R') || rCode.includes('C'))) {
        sweetSpot = 'Khả năng định lượng xuất sắc kết hợp thiên hướng Nghiên cứu & Kỹ thuật (' + rCode + ') mở ra tiềm năng tối ưu trong các ngành: Khoa học máy tính & AI, Khoa học dữ liệu, Kỹ thuật phần mềm, Kỹ thuật tự động hóa và Công nghệ tài chính (Fintech).';
      } else if ((result.verbalScore || 0) >= 7 && (rCode.includes('S') || rCode.includes('E') || rCode.includes('A'))) {
        sweetSpot = 'Khả năng ngôn ngữ và lập luận nhạy bén kết hợp thiên hướng Xã hội & Quản trị (' + rCode + ') là lợi thế vượt trội trong các ngành: Luật kinh tế, Truyền thông & Báo chí, Quan hệ đối ngoại, Marketing chiến lược và Ngoại giao.';
      } else if ((result.figuralScore || 0) >= 7 && (rCode.includes('A') || rCode.includes('R'))) {
        sweetSpot = 'Tư duy hình học - không gian nhạy bén kết hợp thẩm mỹ & kỹ thuật thực hành (' + rCode + ') đưa bạn đến đỉnh cao trong: Kiến trúc & Quy hoạch, Thiết kế công nghiệp, Thiết kế Game 3D & UI/UX, Robotics.';
      } else {
        sweetSpot = 'Hồ sơ năng lực nhận thức đa dạng kết hợp nhóm sở thích ' + rCode + ' cho thấy bạn có khả năng thích ứng cao, phù hợp với các chương trình đào tạo liên ngành (Interdisciplinary) và quản trị dự án.';
      }

      riasecSynthesis = `
        <div class="rounded-[24px] bg-card border border-azure/30 p-6 sm:p-8 shadow-border">
          <div class="flex items-center gap-3 mb-3">
            <span class="grid size-10 place-items-center rounded-xl bg-azure text-paper shadow-sm">
              <i data-lucide="sparkles" class="size-5"></i>
            </span>
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">Giao thoa đa chiều Độc lập</p>
              <h4 class="font-display text-lg sm:text-xl font-bold text-navy">Kết nối Năng lực Nhận thức & Sở thích RIASEC (${rCode})</h4>
            </div>
          </div>
          <p class="text-sm sm:text-base text-muted leading-relaxed mb-4">
            ${sweetSpot}
          </p>
          <div class="flex flex-wrap gap-2 text-xs font-semibold">
            <a href="#huong-nghiep" class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-navy text-paper hover:bg-navy-deep transition">
              <span>Khám phá ngành nghề chi tiết</span>
              <i data-lucide="arrow-right" class="size-3.5"></i>
            </a>
            <a href="#ho-so" class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-mist text-navy border border-line hover:bg-card transition">
              <span>Xem hồ sơ học sinh toàn diện</span>
            </a>
          </div>
        </div>
      `;
    } else {
      riasecSynthesis = `
        <div class="rounded-[24px] bg-card border border-line p-6 sm:p-8 shadow-border flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-azure mb-1">Mảnh ghép định hướng tiếp theo</p>
            <h4 class="font-display text-lg font-bold text-navy mb-1">Bạn chưa hoàn thành bài test RIASEC</h4>
            <p class="text-xs sm:text-sm text-muted">Kết hợp Năng lực Nhận thức với Sở thích Holland (RIASEC) để mở khóa bản đồ giao thoa nghề nghiệp 3 chiều chuẩn xác nhất.</p>
          </div>
          <a href="#trac-nghiem/riasec" class="shrink-0 px-5 py-2.5 rounded-xl bg-navy text-paper font-semibold text-xs cta-glow">
            Làm bài test RIASEC ngay
          </a>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="hero-wash border-b border-line">
        <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Kết quả Đánh giá Năng lực Nhận thức · Lumina Aptitude</p>
          <div class="mt-2 flex flex-wrap items-baseline gap-3">
            <h1 class="font-display text-3xl sm:text-5xl font-bold text-navy">
              ${totalScore} <span class="text-xl sm:text-2xl text-muted font-normal">/ 30 điểm (${totalPct}%)</span>
            </h1>
            <div>${getTierBadge(tier)}</div>
          </div>
          <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
            Thế mạnh nhận thức nổi trội nhất của bạn thuộc nhóm <strong>${dominantDomain}</strong>. Bài đánh giá cung cấp thước đo độc lập về tốc độ và sự chuẩn xác trong việc xử lý các dạng bài toán logic.
          </p>
          <div class="mt-6 flex flex-wrap gap-3">
            <a href="#huong-nghiep" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
              Khám phá ngành đào tạo phù hợp
            </a>
            <a href="#ho-so" class="px-5 py-2.5 rounded-[12px] bg-card text-navy border border-line font-semibold text-xs shadow-border">
              Xem hồ sơ tích hợp
            </a>
            <a href="#trac-nghiem/cognitive" class="px-5 py-2.5 rounded-[12px] bg-card text-muted hover:text-navy border border-line font-semibold text-xs shadow-border">
              Làm lại bài test
            </a>
          </div>
        </div>
      </div>

      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6 space-y-10">
        <!-- 3 Domain Breakdown Cards -->
        <div>
          <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">Chi tiết 3 nhóm năng lực</p>
              <h3 class="font-display text-2xl font-bold text-navy">Điểm số phân loại theo miền tư duy</h3>
            </div>
            <span class="text-xs text-muted">Thang điểm chuẩn hóa: 10 điểm / miền</span>
          </div>

          <div class="grid gap-6 md:grid-cols-3">
            <!-- Verbal -->
            <div class="rounded-[24px] bg-card border border-line p-6 shadow-border flex flex-col justify-between hover:shadow-border-hover transition">
              <div>
                <div class="flex items-center justify-between mb-3">
                  <span class="font-display font-bold text-sm text-azure">1. Verbal (Ngôn ngữ)</span>
                  ${getTierBadge(result.verbalTier || 'Khá')}
                </div>
                <div class="font-display text-3xl font-bold text-navy tabular-nums mb-1">
                  ${result.verbalScore !== undefined ? result.verbalScore : 0} <span class="text-sm text-muted font-normal">/ 10</span>
                </div>
                <div class="w-full bg-mist h-2 rounded-full overflow-hidden mb-4 border border-line/60">
                  <div class="bg-gradient-to-r from-azure to-cyan h-full rounded-full bar-fill" style="width: ${result.verbalPct || 0}%"></div>
                </div>
                <p class="text-xs text-muted leading-relaxed mb-4">
                  Đánh giá vốn từ vựng, mức độ hiểu sâu sắc ngữ nghĩa, quan hệ tương đồng từ vựng và cấu trúc lập luận logic ngôn ngữ.
                </p>
              </div>
              <div class="pt-4 border-t border-line/60 text-xs">
                <strong class="text-navy block mb-1.5">Khối ngành đề xuất:</strong>
                <p class="text-muted leading-relaxed">Luật, Truyền thông & Báo chí, Ngôn ngữ học, Quan hệ quốc tế, Marketing & PR, Sư phạm.</p>
              </div>
            </div>

            <!-- Numerical -->
            <div class="rounded-[24px] bg-card border border-line p-6 shadow-border flex flex-col justify-between hover:shadow-border-hover transition">
              <div>
                <div class="flex items-center justify-between mb-3">
                  <span class="font-display font-bold text-sm text-azure">2. Numerical (Định lượng)</span>
                  ${getTierBadge(result.numericalTier || 'Khá')}
                </div>
                <div class="font-display text-3xl font-bold text-navy tabular-nums mb-1">
                  ${result.numericalScore !== undefined ? result.numericalScore : 0} <span class="text-sm text-muted font-normal">/ 10</span>
                </div>
                <div class="w-full bg-mist h-2 rounded-full overflow-hidden mb-4 border border-line/60">
                  <div class="bg-gradient-to-r from-azure to-cyan h-full rounded-full bar-fill" style="width: ${result.numericalPct || 0}%"></div>
                </div>
                <p class="text-xs text-muted leading-relaxed mb-4">
                  Đo lường năng lực giải quyết bài toán định lượng, tỷ lệ phần trăm, quy luật chuỗi số logic và ứng dụng đại số thực tiễn.
                </p>
              </div>
              <div class="pt-4 border-t border-line/60 text-xs">
                <strong class="text-navy block mb-1.5">Khối ngành đề xuất:</strong>
                <p class="text-muted leading-relaxed">CNTT & AI, Khoa học dữ liệu, Tài chính - Ngân hàng, Kế toán & Kiểm toán, Kỹ thuật viễn thông, Kinh tế lượng.</p>
              </div>
            </div>

            <!-- Figural -->
            <div class="rounded-[24px] bg-card border border-line p-6 shadow-border flex flex-col justify-between hover:shadow-border-hover transition">
              <div>
                <div class="flex items-center justify-between mb-3">
                  <span class="font-display font-bold text-sm text-azure">3. Figural (Hình ảnh / Quy luật)</span>
                  ${getTierBadge(result.figuralTier || 'Khá')}
                </div>
                <div class="font-display text-3xl font-bold text-navy tabular-nums mb-1">
                  ${result.figuralScore !== undefined ? result.figuralScore : 0} <span class="text-sm text-muted font-normal">/ 10</span>
                </div>
                <div class="w-full bg-mist h-2 rounded-full overflow-hidden mb-4 border border-line/60">
                  <div class="bg-gradient-to-r from-azure to-cyan h-full rounded-full bar-fill" style="width: ${result.figuralPct || 0}%"></div>
                </div>
                <p class="text-xs text-muted leading-relaxed mb-4">
                  Đo lường tư duy trừu tượng, nhận diện quy luật chuyển động và biến đổi hình học không gian, xoay hình và ma trận thị giác.
                </p>
              </div>
              <div class="pt-4 border-t border-line/60 text-xs">
                <strong class="text-navy block mb-1.5">Khối ngành đề xuất:</strong>
                <p class="text-muted leading-relaxed">Kiến trúc, Thiết kế UI/UX & Đồ họa, Kỹ thuật cơ khí, Robotics & Tự động hóa, Xây dựng, Phát triển game 3D.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Multi-dimensional Alignment -->
        ${riasecSynthesis}

        <!-- Interactive 30-Question Review Section -->
        <div class="rounded-[28px] bg-card border border-line p-6 sm:p-8 shadow-border">
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">Đối chiếu chi tiết</p>
              <h3 class="font-display text-2xl font-bold text-navy">Xem lại 30 câu hỏi và lời giải khoa học</h3>
            </div>
            <!-- Filter Pills -->
            <div class="flex flex-wrap gap-1.5" id="cog-filter-tabs">
              <button onclick="window.filterCognitiveReview('all')" data-filter="all" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-navy text-paper shadow-border transition">
                Tất cả (30)
              </button>
              <button onclick="window.filterCognitiveReview('correct')" data-filter="correct" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition">
                Đúng (${totalScore})
              </button>
              <button onclick="window.filterCognitiveReview('incorrect')" data-filter="incorrect" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition">
                Sai (${30 - totalScore})
              </button>
              <button onclick="window.filterCognitiveReview('verbal')" data-filter="verbal" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition">
                Verbal (10)
              </button>
              <button onclick="window.filterCognitiveReview('numerical')" data-filter="numerical" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition">
                Numerical (10)
              </button>
              <button onclick="window.filterCognitiveReview('figural')" data-filter="figural" class="cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition">
                Figural (10)
              </button>
            </div>
          </div>

          <!-- Question Cards List -->
          <div id="cog-review-list" class="space-y-4">
            ${details
              .map((item, idx) => `
              <div class="cog-q-card rounded-[20px] bg-mist/60 border ${item.isCorrect ? 'border-line/70' : 'border-rose-500/30'} p-5 sm:p-6 transition" data-correct="${item.isCorrect}" data-domain="${item.domain}">
                <div class="flex items-center justify-between flex-wrap gap-2 mb-3">
                  <div class="flex items-center gap-2">
                    <span class="font-display font-bold text-sm text-navy">Câu ${idx + 1}</span>
                    <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-card text-azure border border-line/60">${item.domainName || ''}</span>
                  </div>
                  <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${item.isCorrect ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'}">
                    <i data-lucide="${item.isCorrect ? 'check-circle' : 'x-circle'}" class="size-3.5"></i>
                    ${item.isCorrect ? 'Chính xác (+1)' : 'Chưa đúng (0)'}
                  </span>
                </div>
                
                <h4 class="text-sm sm:text-base font-semibold text-navy leading-relaxed mb-4">
                  ${item.text}
                </h4>

                <div class="grid gap-2 sm:grid-cols-2 text-xs sm:text-sm mb-4">
                  <div class="p-3 rounded-[14px] ${item.isCorrect ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' : 'bg-rose-500/10 border border-rose-500/30 text-rose-400'} font-medium">
                    <span class="font-bold block text-[11px] uppercase tracking-wider mb-0.5">Lựa chọn của bạn:</span>
                    <span>${item.userChoiceLabel}</span>
                  </div>
                  ${!item.isCorrect ? `
                  <div class="p-3 rounded-[14px] bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
                    <span class="font-bold block text-[11px] uppercase tracking-wider mb-0.5">Đáp án chính xác:</span>
                    <span>${item.correctAnswerLabel}</span>
                  </div>
                  ` : ''}
                </div>

                ${item.explanation ? `
                <div class="p-3.5 rounded-[14px] bg-card border border-line/70 text-xs sm:text-sm text-muted leading-relaxed">
                  <strong class="text-navy flex items-center gap-1.5 mb-1">
                    <i data-lucide="lightbulb" class="size-4 text-amber-500"></i>
                    <span>Giải thích chi tiết:</span>
                  </strong>
                  ${item.explanation}
                </div>
                ` : ''}
              </div>
            `)
              .join('')}
          </div>
        </div>

        <!-- Scientific Disclaimer -->
        <div class="rounded-[20px] bg-mist/50 border border-line p-5 text-xs text-muted leading-relaxed flex items-start gap-3">
          <i data-lucide="info" class="size-5 text-azure shrink-0 mt-0.5"></i>
          <div>
            <strong class="text-navy block mb-0.5">Lưu ý khoa học từ Lumina Aptitude Assessment:</strong>
            Bài kiểm tra năng lực nhận thức đo lường tốc độ và độ chuẩn xác xử lý logic tại thời điểm làm bài. Năng lực nhận thức không phải là chỉ số cố định bất biến mà có thể rèn luyện, củng cố và nâng cao thông qua phương pháp học tập chủ động và giải quyết bài toán thực tế liên tục.
          </div>
        </div>
      </div>
    `;

    window.filterCognitiveReview = function (type) {
      const list = document.getElementById('cog-review-list');
      if (!list) return;
      const cards = list.querySelectorAll('.cog-q-card');
      cards.forEach((card) => {
        const isCorrect = card.getAttribute('data-correct') === 'true';
        const domain = card.getAttribute('data-domain');
        let visible = false;
        if (type === 'all') visible = true;
        else if (type === 'correct') visible = isCorrect;
        else if (type === domain) visible = true;
        else if (type === 'incorrect') visible = !isCorrect;
        card.style.display = visible ? 'block' : 'none';
      });

      const buttons = document.querySelectorAll('.cog-filter-btn');
      buttons.forEach((btn) => {
        if (btn.getAttribute('data-filter') === type) {
          btn.className = 'cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-navy text-paper shadow-border transition';
        } else {
          btn.className = 'cog-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-mist text-muted hover:text-navy border border-line transition';
        }
      });
    };

    refreshIcons();
    return;
  }

  if (quizId === 'riasec') {
    const code = result.code || 'RIA';
    const scores = result.scores || { R: 28, I: 32, A: 24, S: 20, E: 18, C: 15 };
    const matchingCareers = state.careers.filter((c) => (c.riasec || []).some((r) => code.includes(r))).slice(0, 4);

    const topLetters = code.slice(0, 3).split('');
    const topLetterImages = topLetters.map((l, idx) => `
      <div class="flex flex-col items-center">
        <img src="/riasec/animated/RIASEC_${l}_animated.svg" alt="${l}" class="${idx === 0 ? 'size-24 sm:size-28 ring-2 ring-azure' : 'size-16 sm:size-20 opacity-90'} rounded-[18px] bg-card p-1.5 shadow-border object-contain" onerror="this.src='/riasec/animated/${l}.svg'">
        <span class="mt-1.5 text-xs font-bold ${idx === 0 ? 'text-azure' : 'text-muted'}">Nhóm ${l}</span>
      </div>
    `).join('');

    const riasecInfo = [
      { id: 'R', name: 'Thực tế', category: 'THỰC TẾ', subtitle: 'Làm bằng tay, hiểu bằng việc' },
      { id: 'I', name: 'Nghiên cứu', category: 'NGHIÊN CỨU', subtitle: 'Hỏi đến khi ra bản chất' },
      { id: 'A', name: 'Nghệ thuật', category: 'NGHỆ THUẬT', subtitle: 'Tạo thứ chưa từng có' },
      { id: 'S', name: 'Xã hội', category: 'XÃ HỘI', subtitle: 'Làm việc vì con người' },
      { id: 'E', name: 'Quản lý', category: 'QUẢN LÝ', subtitle: 'Dẫn dắt & Thuyết phục' },
      { id: 'C', name: 'Nghiệp vụ', category: 'NGHIỆP VỤ', subtitle: 'Rõ ràng, trật tự, chuẩn xác' },
    ];

    const riasecCards = riasecInfo.map((r) => {
      const score = scores[r.id] !== undefined ? scores[r.id] : 10;
      const pct = Math.min(Math.round((score / 50) * 100), 100);
      const isTop3 = code.slice(0, 3).includes(r.id);
      return {
        ...r,
        score,
        pct,
        isTop3,
      };
    });

    container.innerHTML = `
      <div class="hero-wash border-b border-line">
        <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-8">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Kết quả trắc nghiệm RIASEC</p>
            <h1 class="mt-2 font-display text-4xl sm:text-5xl font-bold text-navy">Mã của bạn: ${code}</h1>
            <p class="mt-3 max-w-xl text-muted text-sm sm:text-base leading-relaxed">
              Sở thích nghề nghiệp của bạn nổi trội ở 3 nhóm: <strong>${code[0]}</strong>, <strong>${code[1]}</strong>, và <strong>${code[2]}</strong>.
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <a href="#huong-nghiep" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
                Khám phá trường & nghề phù hợp
              </a>
              <a href="#trac-nghiem/riasec" class="px-5 py-2.5 rounded-[12px] bg-card text-navy border border-line font-semibold text-xs shadow-border">
                Làm lại bài test
              </a>
            </div>
          </div>
          <div class="flex items-center gap-3 sm:gap-4 p-4 rounded-[28px] bg-card/60 backdrop-blur border border-line shadow-border">
            ${topLetterImages}
          </div>
        </div>
      </div>

      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <!-- RIASEC Charts: Các chỉ số & Chi tiết 6 nhóm -->
        <div class="rounded-[28px] bg-card border border-line p-6 sm:p-8 shadow-border mb-8">
          <!-- Section 1: Các chỉ số -->
          <div class="mb-6">
            <h3 class="font-display text-xl sm:text-2xl font-bold text-navy">Các chỉ số</h3>
            <p class="text-xs sm:text-sm text-muted mt-1">Mức độ sở thích nghề nghiệp theo 6 nhóm Holland trên thang 50 câu.</p>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
            ${riasecCards
              .map((c) => {
                const r = 28;
                const circ = 2 * Math.PI * r;
                const offset = circ - (circ * c.pct) / 100;
                return `
                <div class="rounded-[20px] bg-card border ${c.isTop3 ? 'border-azure/50 shadow-sm' : 'border-line/80'} p-4 text-center relative flex flex-col items-center hover:-translate-y-0.5 transition">
                  ${c.isTop3 ? '<span class="absolute top-3 right-3 size-2 rounded-full bg-azure" title="Nhóm nổi trội"></span>' : ''}
                  <div class="relative size-20 mb-2.5">
                    <svg class="size-full -rotate-90" viewBox="0 0 68 68">
                      <circle cx="34" cy="34" r="${r}" fill="none" stroke="currentColor" stroke-width="4.5" class="text-mist" />
                      <circle cx="34" cy="34" r="${r}" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"
                        stroke-dasharray="${circ}" stroke-dashoffset="${offset}" class="text-azure transition-all duration-700 ease-out" />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span class="font-display text-lg font-bold text-navy leading-none">${c.id}</span>
                      <span class="text-[11px] font-bold text-navy mt-0.5 tabular-nums">${c.pct}%</span>
                    </div>
                  </div>
                  <span class="font-display font-bold text-xs uppercase tracking-wider text-azure block mb-0.5">${c.category}</span>
                  <span class="text-xs font-semibold text-navy block mb-2">${c.name}</span>
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-ice text-azure border border-line/60 tabular-nums">
                    ${c.score}/50 câu (${c.pct}%)
                  </span>
                </div>
              `;
              })
              .join('')}
          </div>

          <!-- Section 2: Chi tiết 6 nhóm -->
          <div class="mt-10 pt-8 border-t border-line">
            <div class="mb-6">
              <h3 class="font-display text-xl font-bold text-navy">Chi tiết 6 nhóm RIASEC</h3>
              <p class="text-xs sm:text-sm text-muted mt-1">Điểm đánh dấu là mức độ sở thích của bạn trên từng nhóm.</p>
            </div>

            <div class="space-y-6">
              ${riasecCards
                .map(
                  (spec) => `
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between text-xs sm:text-sm font-medium">
                    <span class="${spec.isTop3 ? 'text-azure font-bold' : 'text-navy font-semibold'}">Nhóm ${spec.id} — ${spec.name}</span>
                    <span class="text-muted text-xs italic">${spec.subtitle}</span>
                  </div>
                  <div class="relative w-full h-2.5 bg-mist rounded-full overflow-visible border border-line/50">
                    <div class="absolute left-0 top-0 h-full bg-gradient-to-r from-sky-400 to-azure rounded-full transition-all duration-500" style="width: ${spec.pct}%"></div>
                    <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 size-3.5 rounded-full bg-navy border-2 border-card shadow-sm transition-all duration-500" style="left: ${spec.pct}%"></div>
                  </div>
                  <div class="flex items-center justify-between text-xs font-bold tabular-nums">
                    <span class="text-azure">Đạt: ${spec.score}/50 câu</span>
                    <span class="text-navy">${spec.pct}% Nhóm ${spec.id} ${spec.isTop3 ? '· Nổi trội' : ''}</span>
                  </div>
                </div>
              `
                )
                .join('')}
            </div>
          </div>
        </div>

        <!-- Full 120 Combination Deep Dive for User's Code -->
        ${(() => {
          const comb = (state.riasecCombinations || []).find((c) => c.code === code);
          if (comb) {
            return `
              <div class="mb-10">
                <div class="mb-4">
                  <span class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">Giải thích chuyên sâu tổ hợp của bạn</span>
                  <h3 class="font-display text-2xl sm:text-3xl font-bold text-navy mt-1">Phân tích toàn diện mã ${code}</h3>
                </div>
                ${renderRiasecCombinationContent(comb)}
              </div>
            `;
          }
          return '';
        })()}

        <!-- Matching Careers -->
        <div>
          <h3 class="font-display text-2xl font-bold text-navy mb-2">Gợi ý ngành nghề bổ sung</h3>
          <p class="text-sm text-muted mb-6">Liên kết trực tiếp với cơ sở dữ liệu nghề nghiệp và đề án tuyển sinh.</p>
          <div class="grid gap-4 md:grid-cols-2 mb-10">
            ${matchingCareers
              .map(
                (c) => `
              <div class="rounded-[24px] bg-card border border-line p-6 shadow-border hover:shadow-border-hover transition">
                <h4 class="font-display text-xl font-bold text-navy mb-2">${c.name}</h4>
                <p class="text-sm text-muted leading-relaxed mb-4">${c.description}</p>
                <div class="text-xs text-muted mb-4">
                  <strong>Vị trí tiêu biểu:</strong> ${c.roles?.join(', ')}
                </div>
                <a href="#huong-nghiep/${c.id}" class="text-xs font-bold text-azure hover:text-navy flex items-center gap-1">
                  <span>Xem chi tiết nghề & trường đào tạo</span>
                  <i data-lucide="chevron-right" class="size-4"></i>
                </a>
              </div>
            `
              )
              .join('')}
          </div>

          <!-- RIASEC Note Box -->
          <div class="p-4 rounded-[18px] bg-mist border border-line text-xs sm:text-sm text-muted leading-relaxed">
            <strong class="text-navy block mb-1">📌 Lưu ý về diễn giải RIASEC:</strong>
            RIASEC phản ánh xu hướng sở thích nghề nghiệp theo mô hình 6 nhóm Holland, không phải thước đo trực tiếp về năng lực, điểm số hay mức thu nhập tương lai. Khi tư vấn chọn ngành cho học sinh, nên kết hợp kết quả RIASEC với năng lực học tập, môn học yêu thích, giá trị cá nhân và thông tin thực tế về tuyển sinh các trường.
          </div>
        </div>
      </div>
    `;
    refreshIcons();
    return;
  }

  if (quizId === 'mbti') {
    const type = result.type || 'INFP';
    const counts = result.counts || { E: 5, I: 5, S: 5, N: 5, T: 5, F: 5, J: 5, P: 5 };
    const pInfo = state.personalities.find((p) => p.id === type) || {
      id: type,
      name: 'Người lý tưởng',
      slogan: 'Trung thực với lòng mình, tử tế với đời.',
      description: 'Giàu cảm xúc, trân trọng giọng riêng, tìm kiếm ý nghĩa đích thực.',
      strengths: ['Tập trung vào giá trị', 'Sáng tạo', 'Thấu cảm cao'],
    };

    // 1. Energy: E vs I (thang 10 câu)
    const eScore = counts.E || 0;
    const iScore = counts.I || 0;
    const isE = eScore >= iScore;
    const energyCount = isE ? eScore : iScore;
    const energyPct = Math.round((energyCount / 10) * 100);
    const energyLetter = isE ? 'E' : 'I';
    const energySub = isE ? 'Hướng ngoại' : 'Hướng nội';

    // 2. Cognition: S vs N (thang 10 câu)
    const sScore = counts.S || 0;
    const nScore = counts.N || 0;
    const isS = sScore >= nScore;
    const cognCount = isS ? sScore : nScore;
    const cognPct = Math.round((cognCount / 10) * 100);
    const cognLetter = isS ? 'S' : 'N';
    const cognSub = isS ? 'Giác quan' : 'Trực giác';

    // 3. Decision: T vs F (thang 10 câu)
    const tScore = counts.T || 0;
    const fScore = counts.F || 0;
    const isT = tScore >= fScore;
    const decCount = isT ? tScore : fScore;
    const decPct = Math.round((decCount / 10) * 100);
    const decLetter = isT ? 'T' : 'F';
    const decSub = isT ? 'Lý trí' : 'Cảm xúc';

    // 4. Lifestyle: J vs P (thang 10 câu)
    const jScore = counts.J || 0;
    const pScore = counts.P || 0;
    const isJ = jScore >= pScore;
    const lifeCount = isJ ? jScore : pScore;
    const lifePct = Math.round((lifeCount / 10) * 100);
    const lifeLetter = isJ ? 'J' : 'P';
    const lifeSub = isJ ? 'Nguyên tắc' : 'Linh hoạt';

    const mbtiCards = [
      { category: 'NĂNG LƯỢNG', letter: energyLetter, pct: energyPct, count: energyCount, subTitle: energySub },
      { category: 'NHẬN THỨC', letter: cognLetter, pct: cognPct, count: cognCount, subTitle: cognSub },
      { category: 'RA QUYẾT ĐỊNH', letter: decLetter, pct: decPct, count: decCount, subTitle: decSub },
      { category: 'PHONG CÁCH SỐNG', letter: lifeLetter, pct: lifePct, count: lifeCount, subTitle: lifeSub },
    ];

    const mbtiSpectrums = [
      {
        leftLabel: 'Hướng nội I',
        rightLabel: 'E Hướng ngoại',
        markerPos: Math.max(4, Math.min(96, Math.round((eScore / 10) * 100))),
        isLeft: !isE,
        letter: energyLetter,
        pct: energyPct,
        count: energyCount,
      },
      {
        leftLabel: 'Trực giác N',
        rightLabel: 'S Giác quan',
        markerPos: Math.max(4, Math.min(96, Math.round((sScore / 10) * 100))),
        isLeft: !isS,
        letter: cognLetter,
        pct: cognPct,
        count: cognCount,
      },
      {
        leftLabel: 'Cảm xúc F',
        rightLabel: 'T Lý trí',
        markerPos: Math.max(4, Math.min(96, Math.round((tScore / 10) * 100))),
        isLeft: !isT,
        letter: decLetter,
        pct: decPct,
        count: decCount,
      },
      {
        leftLabel: 'Linh hoạt P',
        rightLabel: 'J Nguyên tắc',
        markerPos: Math.max(4, Math.min(96, Math.round((jScore / 10) * 100))),
        isLeft: !isJ,
        letter: lifeLetter,
        pct: lifePct,
        count: lifeCount,
      },
    ];

    container.innerHTML = `
      <div class="hero-wash border-b border-line">
        <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-8">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Kết quả trắc nghiệm MBTI</p>
            <h1 class="mt-2 font-display text-4xl sm:text-5xl font-bold text-navy">${pInfo.id} · ${pInfo.name}</h1>
            <p class="mt-3 max-w-xl text-muted text-base leading-relaxed italic">"${pInfo.slogan}"</p>
            <div class="mt-6 flex flex-wrap gap-3">
              <a href="#nhom-tinh-cach" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
                Khám phá 16 nhóm MBTI
              </a>
              <a href="#trac-nghiem/mbti" class="px-5 py-2.5 rounded-[12px] bg-card text-navy border border-line font-semibold text-xs shadow-border">
                Làm lại bài test
              </a>
            </div>
          </div>
          <img src="/personality/MBTI_${pInfo.id}_animated.svg" alt="${pInfo.id}" class="size-48 object-contain rounded-[28px] bg-card p-2 shadow-border" onerror="this.src='/personality/${pInfo.id}.webp'">
        </div>
      </div>

      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <!-- MBTI Charts: Các chỉ số & Hai cực chi tiết -->
        <div class="rounded-[28px] bg-card border border-line p-6 sm:p-8 shadow-border mb-8">
          <!-- Section 1: Các chỉ số -->
          <div class="mb-6">
            <h3 class="font-display text-xl sm:text-2xl font-bold text-navy">Các chỉ số</h3>
            <p class="text-xs sm:text-sm text-muted mt-1">Mức nghiêng về từng cực — không phải điểm tốt hay xấu.</p>
          </div>

          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            ${mbtiCards
              .map((c) => {
                const r = 28;
                const circ = 2 * Math.PI * r;
                const offset = circ - (circ * c.pct) / 100;
                return `
                <div class="rounded-[20px] bg-card border border-line/80 p-5 text-center shadow-sm flex flex-col items-center hover:-translate-y-0.5 transition">
                  <div class="relative size-20 mb-3">
                    <svg class="size-full -rotate-90" viewBox="0 0 68 68">
                      <circle cx="34" cy="34" r="${r}" fill="none" stroke="currentColor" stroke-width="4.5" class="text-mist" />
                      <circle cx="34" cy="34" r="${r}" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"
                        stroke-dasharray="${circ}" stroke-dashoffset="${offset}" class="text-azure transition-all duration-700 ease-out" />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span class="font-display text-lg font-bold text-navy leading-none">${c.letter}</span>
                      <span class="text-[11px] font-bold text-navy mt-0.5 tabular-nums">${c.pct}%</span>
                    </div>
                  </div>
                  <span class="font-display font-bold text-xs uppercase tracking-wider text-azure block mb-1">${c.category}</span>
                  <span class="text-xs sm:text-sm font-semibold text-navy block mb-2">${c.subTitle}</span>
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-ice text-azure border border-line/60 tabular-nums">
                    ${c.count}/10 câu (${c.pct}%)
                  </span>
                </div>
              `;
              })
              .join('')}
          </div>

          <!-- Section 2: Hai cực chi tiết -->
          <div class="mt-10 pt-8 border-t border-line">
            <div class="mb-6">
              <h3 class="font-display text-xl font-bold text-navy">Hai cực chi tiết</h3>
              <p class="text-xs sm:text-sm text-muted mt-1">Điểm đánh dấu là chỗ bạn nghiêng trên mỗi trục.</p>
            </div>

            <div class="space-y-6">
              ${mbtiSpectrums
                .map(
                  (spec) => `
                <div class="space-y-1.5">
                  <div class="flex items-center justify-between text-xs sm:text-sm font-medium">
                    <span class="${spec.isLeft ? 'text-azure font-bold' : 'text-muted'}">${spec.leftLabel}</span>
                    <span class="${!spec.isLeft ? 'text-azure font-bold' : 'text-muted'}">${spec.rightLabel}</span>
                  </div>
                  <div class="relative w-full h-2.5 bg-mist rounded-full overflow-visible border border-line/50">
                    <div class="absolute left-0 top-0 h-full bg-gradient-to-r from-sky-400 to-azure rounded-full transition-all duration-500" style="width: ${spec.markerPos}%"></div>
                    <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 size-3.5 rounded-full bg-navy border-2 border-card shadow-sm transition-all duration-500" style="left: ${spec.markerPos}%"></div>
                  </div>
                  <div class="flex items-center justify-between text-xs font-bold tabular-nums">
                    <span class="text-azure">Đạt: ${spec.count}/10 câu</span>
                    <span class="text-navy">${spec.pct}% ${spec.letter}</span>
                  </div>
                </div>
              `
                )
                .join('')}
            </div>
          </div>
        </div>

        <!-- Full MBTI Deep Dive for User's Type -->
        <div class="mb-8">
          <div class="mb-4">
            <span class="text-xs font-semibold uppercase tracking-[0.16em] text-azure">Giải thích chuyên sâu nhóm tính cách của bạn</span>
            <h3 class="font-display text-2xl sm:text-3xl font-bold text-navy mt-1">Hồ sơ năng lực & Định hướng ${pInfo.id}</h3>
          </div>
          ${renderMbtiDetailContent(pInfo)}
        </div>

        <!-- MBTI Advisory Note -->
        <div class="p-4 rounded-[18px] bg-mist border border-line text-xs sm:text-sm text-muted leading-relaxed mb-8">
          <strong class="text-navy block mb-1">📌 Lưu ý về diễn giải MBTI:</strong>
          MBTI phản ánh xu hướng sở thích và cách bạn tiếp nhận thông tin cũng như ra quyết định, không phải thước đo đánh giá năng lực, trí thông minh hay mức thu nhập tương lai. Khi tư vấn định hướng, hãy kết hợp MBTI cùng RIASEC, Big Five, môn học yêu thích và giá trị cá nhân.
        </div>
      </div>
    `;
    refreshIcons();
    return;
  }

  // Big Five result
  const rawScores = result.rawScores || { O: 18, C: 17, E: 16, A: 19, N: 13 };
  const scores = result.scores || { O: 65, C: 60, E: 55, A: 70, N: 40 };
  const tiers = result.tiers || {};

  const bfTraits = [
    {
      key: 'O',
      name: 'Cởi mở với trải nghiệm (Openness)',
      desc: 'Mức độ tò mò trí tuệ, trí tưởng tượng, khả năng sáng tạo và sự sẵn sàng đón nhận những góc nhìn mới lạ, trừu tượng.',
    },
    {
      key: 'C',
      name: 'Tận tâm & Kỷ luật (Conscientiousness)',
      desc: 'Mức độ tổ chức, tính chu toàn, tinh thần trách nhiệm, việc giữ lời hứa và sự kiên trì theo đuổi mục tiêu đúng hạn.',
    },
    {
      key: 'E',
      name: 'Hướng ngoại (Extraversion)',
      desc: 'Mức độ chủ động tương tác, năng lượng khi ở trong tập thể, tính cởi mở và xu hướng thể hiện bản thân trong nhóm mới.',
    },
    {
      key: 'A',
      name: 'Hòa hợp & Vị tha (Agreeableness)',
      desc: 'Mức độ thấu cảm, lòng tin vào thiện ý của người khác, tinh thần hợp tác và sự sẵn sàng nhường nhịn để gìn giữ hòa khí.',
    },
    {
      key: 'N',
      name: 'Nhạy cảm xúc (Neuroticism)',
      desc: 'Mức độ nhạy bén cảm xúc, phản ứng trước áp lực, nỗi lo lắng trước tình huống bất ngờ và nhịp độ lấy lại cân bằng tâm lý.',
    },
  ];

  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Kết quả trắc nghiệm Big Five (OCEAN)</p>
        <h1 class="mt-2 font-display text-4xl font-bold text-navy">Năm chiều tính cách cốt lõi</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Điểm số được chuẩn hóa theo thang 0–100% dựa trên công thức <code>((tổng điểm - 5) / 20) × 100</code>. Phân mức: ≤ 33% = Thấp, 34–66% = Trung bình, ≥ 67% = Cao.
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <a href="#huong-nghiep" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
            Khám phá trường & nghề phù hợp
          </a>
          <a href="#trac-nghiem/bigfive" class="px-5 py-2.5 rounded-[12px] bg-card text-navy border border-line font-semibold text-xs shadow-border">
            Làm lại bài test
          </a>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 space-y-4">
      ${bfTraits
        .map((trait) => {
          const val = scores[trait.key] !== undefined ? scores[trait.key] : 50;
          const raw = rawScores[trait.key] !== undefined ? rawScores[trait.key] : 15;
          const tier = tiers[trait.key] || (val >= 67 ? { label: 'Cao', class: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' } : val >= 34 ? { label: 'Trung bình', class: 'bg-azure/15 text-azure border border-azure/30' } : { label: 'Thấp', class: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30' });

          const barColor = val >= 67 ? 'bg-emerald-500' : val >= 34 ? 'bg-azure' : 'bg-amber-500';

          return `
        <div class="rounded-[22px] bg-card border border-line p-5 sm:p-6 shadow-border transition hover:shadow-border-hover">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div class="flex items-center gap-2.5">
              <span class="grid size-9 place-items-center rounded-[10px] bg-ice font-display font-bold text-azure text-base">
                ${trait.key}
              </span>
              <div>
                <span class="font-display font-bold text-base text-navy block leading-snug">${trait.name}</span>
                <span class="text-xs text-muted">Điểm thô: ${raw}/25</span>
              </div>
            </div>
            <div class="flex items-center gap-2 self-start sm:self-center">
              <span class="px-3 py-1 rounded-full text-xs font-bold ${tier.class}">
                Mức ${tier.label}
              </span>
              <span class="font-display font-bold text-lg text-navy tabular-nums">${val}%</span>
            </div>
          </div>

          <div class="w-full bg-mist h-2.5 rounded-full overflow-hidden mb-3 border border-line/60">
            <div class="${barColor} h-full rounded-full bar-fill transition-all duration-300" style="width: ${val}%"></div>
          </div>
          <p class="text-xs sm:text-sm text-muted leading-relaxed">${trait.desc}</p>
        </div>
      `;
        })
        .join('')}

      <!-- Big Five Advisory Note -->
      <div class="mt-8 p-4 rounded-[18px] bg-mist border border-line text-xs sm:text-sm text-muted leading-relaxed">
        <strong class="text-navy block mb-1">📌 Lưu ý về diễn giải Big Five:</strong>
        Big Five mô tả xu hướng tính cách trên 5 chiều liên tục, không phân loại cứng thành người tốt hay xấu. Mỗi mức điểm đều mang lại những lợi thế riêng trong từng môi trường học tập và công việc cụ thể. Khi tư vấn chọn ngành, nên kết hợp kết quả Big Five cùng RIASEC, MBTI và năng lực nhận thức để có bức tranh toàn diện nhất.
      </div>
    </div>
  `;
  refreshIcons();
}

// ==========================================================================
// 3. PERSONALITIES VIEW (#nhom-tinh-cach)
// ==========================================================================
function renderPersonalities(container, param) {
  if (param) {
    // If param is a type ID like INTJ or INFP
    const item = state.personalities.find((p) => p.id.toLowerCase() === param.toLowerCase());
    if (item) {
      viewMbtiDetail(item.id);
    }
  }

  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">16 nhóm MBTI · 6 nhóm RIASEC</p>
        <h1 class="mt-2 font-display text-3xl font-semibold text-navy sm:text-4xl">Khám phá các nhóm tính cách</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base">
          Mỗi nhóm là một cách nhìn thế giới. Hiểu nhóm của mình để phát huy thế mạnh tự nhiên và thấu hiểu người khác.
        </p>
        <div class="mt-6 flex flex-wrap gap-2">
          <button id="p-tab-mbti" class="min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 ${state.activePersonalityTab === 'mbti' ? 'bg-navy text-paper' : 'bg-card text-navy shadow-border'}">
            16 nhóm MBTI
          </button>
          <button id="p-tab-riasec" class="min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 ${state.activePersonalityTab === 'riasec' ? 'bg-navy text-paper' : 'bg-card text-navy shadow-border'}">
            6 nhóm RIASEC
          </button>
        </div>
      </div>
    </div>
    <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div id="p-grid-box">
        ${renderTypeGridContent()}
      </div>
    </div>
  `;
  refreshIcons();

  const tabMbti = document.getElementById('p-tab-mbti');
  const tabRiasec = document.getElementById('p-tab-riasec');
  if (tabMbti && tabRiasec) {
    tabMbti.addEventListener('click', () => {
      state.activePersonalityTab = 'mbti';
      tabMbti.className = 'min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 bg-navy text-paper';
      tabRiasec.className = 'min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 bg-card text-navy shadow-border';
      document.getElementById('p-grid-box').innerHTML = renderTypeGridContent();
      refreshIcons();
    });
    tabRiasec.addEventListener('click', () => {
      state.activePersonalityTab = 'riasec';
      tabRiasec.className = 'min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 bg-navy text-paper';
      tabMbti.className = 'min-h-11 rounded-full px-5 text-sm font-medium transition duration-150 bg-card text-navy shadow-border';
      document.getElementById('p-grid-box').innerHTML = renderTypeGridContent();
      refreshIcons();
    });
  }
}

// ==========================================================================
// 4. CAREERS & UNIVERSITIES (#huong-nghiep)
// ==========================================================================
function renderCareers(container, param) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Hướng nghiệp</p>
        <h1 class="mt-2 max-w-2xl font-display text-3xl font-semibold text-navy sm:text-4xl">
          Khám phá trường Đại học & hướng đi phù hợp
        </h1>
        <p class="mt-3 max-w-xl text-sm text-muted sm:text-base leading-relaxed">
          Lọc 126 trường theo khu vực, ngành và điểm trúng tuyển — rồi xem gợi ý nghề như bản đồ, không như lệnh.
        </p>
        <a href="#tra-cuu-nganh" class="major-lookup-cta mt-5">
          <i data-lucide="chart-no-axes-combined" class="size-5"></i>Tra cứu ngành & điểm của từng trường
        </a>
      </div>
    </div>

    <!-- UNIVERSITY EXPLORER -->
    <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      ${renderUniversityExplorerHtml()}
    </div>

    <!-- CAREER SUGGESTIONS SECTION -->
    <section id="nganh-nghe" class="mx-auto max-w-6xl px-4 py-12 sm:px-6 border-t border-line">
      <h2 class="font-display text-2xl font-semibold text-navy">Gợi ý ngành nghề</h2>
      <p class="mt-2 max-w-2xl text-sm text-muted">
        Dưới đây là các nhóm ngành trọng điểm, kỹ năng yêu cầu và lộ trình học tập để bạn tham khảo.
      </p>
      <div class="mt-8 grid gap-4 md:grid-cols-2">
        ${state.careers
          .map(
            (c) => `
          <article class="flex h-full flex-col rounded-[24px] bg-card p-6 shadow-border hover:shadow-border-hover transition border border-line/60">
            <h3 class="font-display text-xl font-semibold text-navy">${c.name}</h3>
            <p class="mt-2 text-sm leading-relaxed text-muted">${c.description}</p>
            <div class="mt-4 p-3 rounded-[14px] bg-mist text-xs space-y-1 border border-line/40">
              <p><strong class="text-navy">Vị trí:</strong> ${c.roles?.join(', ')}</p>
              <p><strong class="text-navy">Kỹ năng:</strong> ${c.skills?.join(', ')}</p>
              <p><strong class="text-navy">Lộ trình học:</strong> ${c.study || 'Đại học, cao đẳng hoặc tự học'}</p>
            </div>
          </article>
        `
          )
          .join('')}
      </div>
    </section>
  `;
  refreshIcons();
  attachUniversityExplorerEvents();
}

// ==========================================================================
// 5. UNIVERSITIES VIEW (#truong-dai-hoc)
// ==========================================================================
function renderUniversities(container, param) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Tra cứu trường và ngành</p>
        <h1 class="mt-2 font-display text-3xl font-semibold text-navy sm:text-4xl">126 trường đại học & học viện</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Xem ngành đào tạo, điểm trúng tuyển, điểm sàn và nguồn đối chiếu trong trang riêng của từng trường.
        </p>
        <div class="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 font-semibold">
          <span class="size-2 rounded-full bg-emerald-500 animate-pulse inline-block"></span>
          Dữ liệu mới · 14/11/2026 · 126 trường · 3.478 chương trình
        </div>
      </div>
    </div>
    <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      ${renderUniversityExplorerHtml()}
    </div>
  `;
  refreshIcons();
  attachUniversityExplorerEvents();
}

const UNIVERSITY_FILTER_DEFAULTS = {query:'',region:'Tất cả',provinceNew:'Tất cả',provinceOld:'Tất cả',tuition:'Tất cả',score:'Tất cả',fitMin:'Tất cả',groupId:'all',major:'',method:'Tất cả'};
const UNIVERSITY_GROUPS = [
 ['thuc-te','Nhóm thực tế - kỹ thuật',['R','I','C'],'Kỹ thuật'],
 ['nghien-cuu','Nhóm nghiên cứu - khoa học',['I','R','A'],'Khoa học'],
 ['sang-tao','Nhóm sáng tạo - thiết kế',['A','R','S'],'Nghệ thuật'],
 ['xa-hoi','Nhóm xã hội - giáo dục',['S','A','C'],'Sư phạm'],
 ['quan-ly','Nhóm quản lý - kinh doanh',['E','C','S'],'Kinh tế'],
 ['nghiep-vu','Nhóm nghiệp vụ - vận hành',['C','E','I'],'Kinh tế'],
];
function universityText(value) {
 return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' ');
}
function universityEscape(value) { return String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
const universitySearchCache = new WeakMap();
function universitySearchText(u) {
 if(!universitySearchCache.has(u)) {
  const aliases = universityText(u.provinceNew).includes('ho chi minh') ? 'hcm tphcm tp hcm sai gon saigon' : '';
  universitySearchCache.set(u,universityText([u.name,u.shortName,u.location,u.region,u.provinceNew,u.provinceOld,u.category,aliases,...(u.majors||[]),...(u.majorItems||[]).flatMap(m=>[m.code,m.name])].join(' ')));
 }
 return universitySearchCache.get(u);
}
function universityTuitionRange(u) {
 const detail = state.schoolDetails.find(d=>d.id===u.id);
 if(detail?.tuition?.min != null) return [detail.tuition.min,detail.tuition.max ?? detail.tuition.min];
 if(typeof u.tuition==='number') return [u.tuition,u.tuition];
 if(u.tuition?.amount != null) return [u.tuition.amount*1000000,u.tuition.amount*1000000];
 return null;
}
function universityFit(u) {
 const result=state.results.riasec;
 if(!result?.scores)return null;
 const keys=['R','I','A','S','E','C'];
 const v=keys.map(k=>(result.scores[k]||0)/(result.maxScores?.[k]||50));
 const p=keys.map(k=>{const i=(u.focusRiasec||[]).indexOf(k);return i<0?.15:([3,2,1][i]||1)});
 const denom=Math.hypot(...v)*Math.hypot(...p);
 return denom ? Math.round(Math.min(96,Math.max(8,v.reduce((s,x,i)=>s+x*p[i],0)/denom*100))) : 0;
}
// Clean presentation-only annotations; keep source program names and intrinsic numbers intact.
function cleanMajorLabel(name) {
 return String(name||'').normalize('NFC').replace(/^\s*(?:\(\d+\)|\d+[.)])\s*/,'').replace(/\(\s*\*+\s*\)|\*+/g,'').replace(/\s+/g,' ').trim();
}
function majorKey(name) {return universityText(cleanMajorLabel(name).replace(/&/g,' và '));}
let majorCatalogCache=null;
function universityMajorCatalog() {
 if(majorCatalogCache?.source===state.universities)return majorCatalogCache;
 const groups=new Map(),codes=new Set();
 for(const u of state.universities)for(const m of (u.majorItems?.length?u.majorItems:(u.majors||[]).map(name=>({name})))) {
  const label=cleanMajorLabel(m.name),key=majorKey(label);if(!key)continue;
  if(!groups.has(key))groups.set(key,new Map());const labels=groups.get(key);labels.set(label,(labels.get(label)||0)+1);
  if(m.code)codes.add(universityText(m.code));
 }
 const labels=new Map([...groups].map(([key,variants])=>[key,[...variants].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'vi'))[0][0]]));
 return majorCatalogCache={source:state.universities,labels,codes,names:[...labels.values()].sort((a,b)=>a.localeCompare(b,'vi'))};
}
function matchesSelectedMajor(program, query=state.uniFilter.major) {
 if(!query?.trim())return true;
 const key=majorKey(query),catalog=universityMajorCatalog();
 if(catalog.labels.has(key))return majorKey(program.name)===key;
 const code=universityText(query);
 if(catalog.codes.has(code))return universityText(program.code)===code;
 return majorKey(program.name).includes(key)||universityText(program.code).includes(code);
}
function selectedSchoolPrograms(u) {
 const sd=state.schoolDetails.find(d=>d.id===u.id);
 return (sd?.programs||u.majorItems||[]).filter(p=>matchesSelectedMajor(p));
}
function selectedMajorTitle() {
 return universityMajorCatalog().labels.get(majorKey(state.uniFilter.major))||cleanMajorLabel(state.uniFilter.major);
}
function matchesProgramFilters(p) {
 const f={...UNIVERSITY_FILTER_DEFAULTS,...state.uniFilter};
 if(!matchesSelectedMajor(p))return false;
 if(f.method!=='Tất cả'&&!(p.admissions||[]).some(a=>a.method===f.method))return false;
 if(f.score!=='Tất cả'&&!(p.admissions||[]).some(a=>a.method==='Điểm THPT 2026'&&a.scale===30&&a.value!=null&&(f.score==='Dưới 20'?a.value<20:f.score==='20–24'?a.value>=20&&a.value<24:f.score==='24–27'?a.value>=24&&a.value<=27:a.value>27)))return false;
 return true;
}
function majorLookupRows() {
 const f={...UNIVERSITY_FILTER_DEFAULTS,...state.uniFilter};
 return filterUniversities().flatMap(u=>{
  const sd=state.schoolDetails.find(d=>d.id===u.id);if(!sd)return [];
  return sd.programs.filter(p=>matchesSelectedMajor(p)).filter(p=>f.method==='Tất cả'||p.admissions.some(a=>a.method===f.method)).filter(p=>{
   if(f.score==='Tất cả')return true;
   return p.admissions.some(a=>a.method==='Điểm THPT 2026'&&a.scale===30&&a.value!=null&&(f.score==='Dưới 20'?a.value<20:f.score==='20–24'?a.value>=20&&a.value<24:f.score==='24–27'?a.value>=24&&a.value<=27:a.value>27));
  }).map(p=>({u,sd,p}));
 });
}
function majorLookupGroups() {
 const groups=new Map(),catalog=universityMajorCatalog();
 for(const row of majorLookupRows()) {
  const key=majorKey(row.p.name);
  if(!groups.has(key))groups.set(key,{key,name:catalog.labels.get(key)||cleanMajorLabel(row.p.name),rows:[]});
  groups.get(key).rows.push(row);
 }
 return [...groups.values()].sort((a,b)=>a.name.localeCompare(b.name,'vi'));
}
function renderMajorLookupGroupRows(group,page=0) {
 const size=20,pages=Math.max(1,Math.ceil(group.rows.length/size));
 page=Math.max(0,Math.min(page,pages-1));
 const items=group.rows.slice(page*size,(page+1)*size),esc=universityEscape;
 return `<div class="major-lookup-table-wrap"><table class="major-lookup-table"><caption class="sr-only">Điểm xét tuyển và học phí ngành ${esc(group.name)} theo trường</caption><thead><tr><th>Trường & chương trình</th><th>Điểm theo phương thức</th><th>Học phí / năm</th></tr></thead><tbody>${items.map(({u,sd,p})=>{
  const values=p.admissions.filter(a=>state.uniFilter.method==='Tất cả'||!state.uniFilter.method||a.method===state.uniFilter.method);
  const fee=p.tuition_annual!=null?formatVND(p.tuition_annual):sd.tuition.min!=null?[sd.tuition.min,sd.tuition.max??sd.tuition.min].map(formatVND).filter((v,i,a)=>i===0||v!==a[0]).join(' – '):'Chưa có dữ liệu';
  return `<tr><td><a href="#truong-dai-hoc/${esc(u.id)}" class="text-azure font-semibold">${esc(u.name)} ↗</a><p class="text-xs text-muted mt-1">${esc(u.provinceNew||'')}${u.provinceOld!==u.provinceNew?' · cũ: '+esc(u.provinceOld):''}</p><h3 class="text-sm font-semibold text-navy mt-3">${esc(cleanMajorLabel(p.name))}</h3><p class="text-xs text-muted mt-1">Mã: ${esc(p.code||'Chưa cung cấp')} · ${esc(p.type)}</p></td><td>${values.map(a=>`<div class="major-lookup-score"><span>${esc(a.method)}</span><strong>${esc(a.raw)}</strong></div>`).join('')||'<span class="text-muted">Chưa có điểm</span>'}</td><td><strong class="text-navy">${fee}</strong><p class="text-xs text-muted mt-2">${p.tuition_annual!=null?'Học phí riêng của chương trình':'Khoảng học phí cấp trường; cần đối chiếu chương trình cụ thể.'}</p><a href="#truong-dai-hoc/${esc(u.id)}" class="text-xs text-azure inline-block mt-3">Chi tiết & nguồn dữ liệu →</a></td></tr>`;
 }).join('')}</tbody></table></div>${pages>1?`<div class="major-lookup-pagination"><button type="button" data-major-program-page="${page-1}" ${page===0?'disabled':''}>← Trang trước</button><span role="status">${page*size+1}–${Math.min((page+1)*size,group.rows.length)} / ${group.rows.length} chương trình</span><button type="button" data-major-program-page="${page+1}" ${page+1>=pages?'disabled':''}>Trang sau →</button></div>`:''}`;
}
function renderMajorLookupGroupSummary(group) {
 const esc=universityEscape;
 return `<summary><span class="major-group-heading"><h3 class="major-group-title"><svg class="major-group-chevron" aria-hidden="true" width="10" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M3 1.5 9 6 3 10.5Z"/></svg><span>${esc(group.name)}</span></h3><span class="major-group-meta">${new Set(group.rows.map(r=>r.u.id)).size} trường · ${group.rows.length} chương trình</span></span></summary>`;
}
let majorLookupRenderedGroups=new Map();
function renderMajorLookupResults() {
 const groups=majorLookupGroups(),size=12,pages=Math.max(1,Math.ceil(groups.length/size));
 state.majorLookupPage=Math.max(0,Math.min(state.majorLookupPage||0,pages-1));
 majorLookupRenderedGroups=new Map(groups.map(group=>[group.key,group]));
 const page=state.majorLookupPage,esc=universityEscape;
 const schoolCount=new Set(groups.flatMap(g=>g.rows.map(r=>r.u.id))).size;
 return `<div class="major-lookup-summary"><div><h2 class="text-lg font-bold text-navy">Ngành đào tạo</h2><p class="text-sm text-muted mt-1" role="status">${groups.length} ngành tại ${schoolCount} trường khớp bộ lọc</p><p class="text-sm text-muted mt-2">Nhấn vào một ngành để xem điểm xét tuyển và học phí tại các trường.</p></div></div><div class="major-group-list">${groups.slice(page*size,(page+1)*size).map(g=>`<details class="major-group" data-major-key="${esc(g.key)}">${renderMajorLookupGroupSummary(g)}<div class="major-group-content"></div></details>`).join('')||'<p class="text-muted py-6">Không tìm thấy ngành phù hợp. Hãy đổi từ khóa hoặc xóa bớt bộ lọc.</p>'}</div>${pages>1?`<div class="major-lookup-pagination"><button type="button" data-major-page="${page-1}" ${page===0?'disabled':''}>← Trang trước</button><span>Trang ${page+1} / ${pages} · ${groups.length} ngành</span><button type="button" data-major-page="${page+1}" ${page+1>=pages?'disabled':''}>Trang sau →</button></div>`:''}`;
}
function attachMajorLookupPagination() {
 const root=document.querySelector('#ue-major-results');if(!root)return;
 root.querySelectorAll('[data-major-page]').forEach(b=>b.onclick=()=>{
  state.majorLookupPage=Number(b.dataset.majorPage);root.innerHTML=renderMajorLookupResults();attachMajorLookupPagination();root.scrollIntoView({block:'start',behavior:'instant'});
 });
 const groups=majorLookupRenderedGroups;
 root.querySelectorAll('.major-group').forEach(detail=>{
  const content=detail.querySelector('.major-group-content'),group=groups.get(detail.dataset.majorKey);
  const showPage=(page)=>{
   content.innerHTML=renderMajorLookupGroupRows(group,page);
   content.querySelectorAll('[data-major-program-page]').forEach(b=>b.onclick=()=>{
    showPage(Number(b.dataset.majorProgramPage));detail.scrollIntoView({block:'start',behavior:'instant'});
   });
  };
  detail.ontoggle=()=>{
   if(!detail.open)return;
   root.querySelectorAll('.major-group[open]').forEach(other=>{if(other!==detail)other.open=false;});
   if(!content.childElementCount)showPage(0);
  };
 });
}
function renderMajorLookup(container) {
 container.innerHTML=`<section class="hero-wash border-b border-line"><div class="max-w-6xl mx-auto px-4 sm:px-6 py-10"><a href="#huong-nghiep" class="text-sm text-azure font-semibold">← Bộ lọc trường</a><p class="mt-5 text-xs font-semibold uppercase tracking-widest text-azure">So sánh theo ngành</p><h1 class="mt-2 font-display text-3xl font-bold text-navy">Tra cứu ngành & điểm của từng trường</h1><p class="mt-3 text-muted max-w-2xl">Mỗi ngành được gom thành một khối. Nhấn vào ngành bạn quan tâm để xem các trường đào tạo, điểm xét tuyển và học phí; có thể tìm tên ngành không dấu hoặc lọc theo tỉnh thành.</p></div></section><div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">${renderUniversityExplorerHtml()}</div>`;
 attachUniversityExplorerEvents();refreshIcons();
}

let universityOptionsCache = null;
function universityFilterOptions() {
 if(universityOptionsCache?.source===state.universities)return universityOptionsCache.value;
 const unique=values=>[...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b,'vi'));
 const counts=new Map();state.universities.forEach(u=>counts.set(u.provinceNew,(counts.get(u.provinceNew)||0)+1));
 const value={provinceNew:unique(state.universities.map(u=>u.provinceNew)),provinceOld:unique(state.universities.map(u=>u.provinceOld)),popular:[...counts].filter(([name,n])=>n>=3).sort((a,b)=>b[1]-a[1]).map(([name])=>name),methods:unique(state.universities.flatMap(u=>u.admissionMethods||[])),majors:universityMajorCatalog().names};
 universityOptionsCache={source:state.universities,value};return value;
}
function filterUniversities() {
 const f={...UNIVERSITY_FILTER_DEFAULTS,...state.uniFilter}, opts=universityFilterOptions();
 const words=universityText(f.query).split(' ').filter(Boolean), major=universityText(f.major);
 return state.universities.filter(u=>{
  if(words.length&&!words.every(word=>universitySearchText(u).includes(word)))return false;
  if(f.region!=='Tất cả'&&u.region!==f.region)return false;
  if(f.provinceNew==='Tỉnh khác'?opts.popular.includes(u.provinceNew):f.provinceNew!=='Tất cả'&&u.provinceNew!==f.provinceNew)return false;
  if(f.provinceOld!=='Tất cả'&&u.provinceOld!==f.provinceOld)return false;
  if(major&&!(u.majorItems||u.majors?.map(name=>({name}))||[]).some(m=>matchesSelectedMajor(m,f.major)))return false;
  if(major&&state.schoolDetails.some(d=>d.id===u.id)&&!selectedSchoolPrograms(u).some(matchesProgramFilters))return false;
  const g=UNIVERSITY_GROUPS.find(g=>g[0]===f.groupId);
  if(g&&u.category!=='Đa ngành'&&u.category!==g[3]&&(u.focusRiasec||[]).filter(k=>g[2].includes(k)).length<2)return false;
  if(f.method!=='Tất cả'&&!(u.admissionMethods||[]).includes(f.method))return false;
  if(f.tuition!=='Tất cả') {
   const r=universityTuitionRange(u);if(!r)return false;
   if(f.tuition==='Dưới 20 triệu'&&r[0]>=20000000)return false;
   if(f.tuition==='20–40 triệu'&&!(r[1]>=20000000&&r[0]<40000000))return false;
   if(f.tuition==='40–60 triệu'&&!(r[1]>=40000000&&r[0]<=60000000))return false;
   if(f.tuition==='Trên 60 triệu'&&r[1]<=60000000)return false;
  }
  if(f.score!=='Tất cả') {
   const values=(u.admissions2026?.thptValues||[]).filter(n=>typeof n==='number'&&n>=0&&n<=30);
   if(!values.some(n=>f.score==='Dưới 20'?n<20:f.score==='20–24'?n>=20&&n<24:f.score==='24–27'?n>=24&&n<=27:n>27))return false;
  }
  if(f.fitMin!=='Tất cả') { const fit=universityFit(u);if(fit===null||fit<Number(f.fitMin.replace(/\D/g,'')))return false; }
  return true;
 });
}
function renderUniversityFilterPanel() {
 const f={...UNIVERSITY_FILTER_DEFAULTS,...state.uniFilter},opts=universityFilterOptions(),esc=universityEscape;
 const chips=(key,values)=>values.map(v=>{const [value,label]=Array.isArray(v)?v:[v,v];return `<button type="button" data-filter="${key}" data-value="${esc(value)}" aria-pressed="${f[key]===value}" ${key==='fitMin'&&value!=='Tất cả'&&!state.results.riasec?'disabled':''} class="ue-filter-chip ${f[key]===value?'bg-navy text-paper':'bg-mist text-muted'}">${esc(label)}</button>`}).join('');
 const row=(title,content)=>`<div class="ue-filter-row"><p class="ue-filter-label">${title}</p><div class="flex flex-wrap gap-2">${content}</div></div>`;
 const select=(key,title,values)=>`<label class="ue-filter-label" for="ue-${key}">${title}<select id="ue-${key}" data-select="${key}" class="ue-filter-input">${['Tất cả',...values].map(v=>`<option value="${esc(v)}" ${f[key]===v?'selected':''}>${esc(v)}</option>`).join('')}</select></label>`;
 return `<section id="ue-filters" class="ue-filter-panel" aria-label="Bộ lọc trường đại học">
 <h2 class="text-sm font-semibold text-navy flex items-center gap-2"><i data-lucide="sliders-horizontal" class="size-4 text-azure"></i>Bộ lọc</h2>
 <label for="ue-search" class="sr-only">Tìm trường, ngành, mã ngành hoặc tỉnh thành mới và cũ</label>
 <div class="relative"><i data-lucide="search" class="size-4 text-muted absolute left-3 top-3.5"></i><input id="ue-search" type="search" value="${esc(f.query)}" placeholder="Tìm trường, ngành, mã ngành, tỉnh/thành... (có hoặc không dấu)" class="ue-filter-input ue-search-input" autocomplete="off"></div>
 ${row('Miền',chips('region',['Tất cả','Miền Bắc','Miền Trung','Miền Nam','Chưa xác định']))}
 ${row('Tỉnh phổ biến',chips('provinceNew',['Tất cả',...opts.popular,'Tỉnh khác']))}
 <div class="ue-filter-columns">${select('provinceNew','Tỉnh/TP mới',[...opts.provinceNew,'Tỉnh khác'])}${select('provinceOld','Tỉnh/TP cũ',opts.provinceOld)}</div>
 ${row('Học phí',chips('tuition',['Tất cả','Dưới 20 triệu','20–40 triệu','40–60 triệu','Trên 60 triệu']))}
 ${row('Điểm trúng tuyển THPT /30',chips('score',['Tất cả','Dưới 20','20–24','24–27','Trên 27']))}
 <p class="text-xs text-muted leading-relaxed">Lọc trường có ít nhất một điểm trúng tuyển THPT trong khoảng đã chọn. Không gộp điểm sàn, phương thức khác hoặc ước tính; xem điều kiện của từng ngành trong trang trường.</p>
 ${row('Mức phù hợp RIASEC',chips('fitMin',['Tất cả','≥80%','≥70%','≥60%']))}
 ${!state.results.riasec?'<p class="text-xs text-muted">Làm bài RIASEC để mở bộ lọc mức phù hợp. Đây là độ tương đồng sở thích, không phải xác suất trúng tuyển.</p>':''}
 ${row('Nhóm ngành',chips('groupId',[['all','Tất cả'],...UNIVERSITY_GROUPS.map(g=>[g[0],g[1]])]))}
 <div class="ue-filter-columns"><label for="ue-major" class="ue-filter-label">Ngành<input id="ue-major" class="ue-filter-input" value="${esc(f.major)}" list="ue-major-options" placeholder="Chọn một ngành hoặc tìm mã ngành, không cần dấu" autocomplete="off"><datalist id="ue-major-options">${opts.majors.slice(0,60).map(m=>`<option value="${esc(m)}"></option>`).join('')}</datalist></label>${select('method','Phương thức xét tuyển',opts.methods)}</div>
 <div class="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4"><p id="ue-count" class="text-xs text-muted" role="status" aria-live="polite">${filterUniversities().length} trường khớp bộ lọc</p><button type="button" id="ue-reset" class="text-xs text-azure font-semibold min-h-10 px-2 inline-flex items-center gap-2"><i data-lucide="rotate-ccw" class="size-3.5"></i>Xóa bộ lọc</button></div>
 </section>`;
}
function renderUniversityExplorerHtml() {
 const lookup=window.location.hash.split('/')[0]==='#tra-cuu-nganh';
 return `<div id="ue-explorer" class="space-y-6">${renderUniversityFilterPanel()}${lookup?`<section id="ue-major-results" class="major-lookup-results">${renderMajorLookupResults()}</section>`:`<div id="ue-grid" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 pt-2">${renderUniversityCards(filterUniversities())}</div>`}</div>`;
}
function attachUniversityExplorerEvents() {
 const root=document.getElementById('ue-explorer');if(!root)return;
 attachMajorLookupPagination();
 const updateResults=()=>{
  if(resultsFrame!==null){cancelAnimationFrame(resultsFrame);resultsFrame=null;}
  const list=filterUniversities();state.majorLookupPage=0;
  if(root.querySelector('#ue-major-results')){root.querySelector('#ue-major-results').innerHTML=renderMajorLookupResults();attachMajorLookupPagination();}
  else root.querySelector('#ue-grid').innerHTML=renderUniversityCards(list);
  root.querySelector('#ue-count').textContent=`${list.length} trường khớp bộ lọc`;
  refreshIcons();
 };
 let resultsFrame=null;
 const queueResults=()=>{
  if(resultsFrame!==null)return;
  resultsFrame=requestAnimationFrame(()=>{resultsFrame=null;if(root.isConnected)updateResults();});
 };
 root.querySelector('#ue-search').addEventListener('input',e=>{state.uniFilter.query=e.target.value;queueResults();});
 root.querySelector('#ue-major').addEventListener('input',e=>{
  state.uniFilter.major=e.target.value;
  const q=universityText(e.target.value);
  root.querySelector('#ue-major-options').innerHTML=universityFilterOptions().majors.filter(m=>majorKey(m).includes(majorKey(e.target.value))).slice(0,60).map(m=>`<option value="${universityEscape(m)}"></option>`).join('');
  queueResults();
 });
 root.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{
  state.uniFilter[b.dataset.filter]=b.dataset.value;state.majorLookupPage=0;
  const scroll=window.scrollY;
  root.outerHTML=renderUniversityExplorerHtml();attachUniversityExplorerEvents();refreshIcons();window.scrollTo({top:scroll,behavior:'instant'});
 }));
 root.querySelectorAll('[data-select]').forEach(select=>select.addEventListener('change',()=>{
  state.uniFilter[select.dataset.select]=select.value;
  root.querySelectorAll('[data-filter="provinceNew"]').forEach(b=>{const selected=b.dataset.value===state.uniFilter.provinceNew;b.setAttribute('aria-pressed',selected);b.className=`ue-filter-chip ${selected?'bg-navy text-paper':'bg-mist text-muted'}`});
  updateResults();
 }));
 root.querySelector('#ue-reset').addEventListener('click',()=>{state.uniFilter={...UNIVERSITY_FILTER_DEFAULTS};state.majorLookupPage=0;root.outerHTML=renderUniversityExplorerHtml();attachUniversityExplorerEvents();refreshIcons();});
}

function renderUniversityCards(filtered) {
 if(!filtered.length)return '<div class="col-span-full rounded-[24px] border border-line bg-card p-8 text-center text-muted">Không tìm thấy trường phù hợp. Hãy thử từ khóa khác hoặc xóa bớt bộ lọc.</div>';
 return filtered
          .map((u) => {
            const short = u.shortName || u.name.split(' ').map((w) => w[0]).join('').slice(0, 3).toUpperCase();
            const scores = u.admissionScores || {};
            const matchedPrograms=state.uniFilter.major?selectedSchoolPrograms(u):[];
            const thpt = state.uniFilter.major?matchedPrograms.flatMap(p=>(p.admissions||[]).filter(a=>a.method==='Điểm THPT 2026'&&a.scale===30&&a.value!=null).map(a=>a.value)):(u.admissions2026?.thptValues || []);
            const scoreText = thpt.length > 0 ? `${Math.min(...thpt)}–${Math.max(...thpt)}` : 'Đang cập nhật';
            return `
            <article class="flex h-full flex-col rounded-[24px] bg-card p-5 shadow-border hover:shadow-border-hover transition border border-line/60 cursor-pointer group" onclick="window.location.hash='#truong-dai-hoc/${u.id}'">
              <div class="flex items-start gap-3">
                <span class="grid size-12 shrink-0 place-items-center rounded-[14px] bg-ice font-display text-sm font-semibold text-navy group-hover:bg-azure group-hover:text-white transition">
                  ${short}
                </span>
                <div class="min-w-0 flex-1">
                  <h3 class="font-display text-base font-semibold leading-snug text-navy truncate group-hover:text-azure transition" title="${u.name}">${u.name}</h3>
                  <p class="mt-0.5 text-xs font-medium text-azure">${u.shortName || ''} · ${u.region || ''} · ${u.provinceNew || ''}${u.provinceOld && u.provinceOld !== u.provinceNew ? ' · cũ: '+u.provinceOld : ''}</p>
                </div>
              </div>
              ${state.uniFilter.major?`<p class="mt-3 text-xs text-azure font-semibold">${universityEscape(selectedMajorTitle())} · ${matchedPrograms.length} chương trình</p>`:''}
              <p class="mt-3 text-xs text-muted leading-relaxed line-clamp-2">${u.description || 'Trường đại học trọng điểm đào tạo đa ngành tại Việt Nam.'}</p>
              <div class="mt-4 p-3 rounded-[14px] bg-mist text-xs space-y-1 border border-line/40">
                <p><span class="text-muted">Điểm chuẩn THPT:</span> <strong class="text-navy tabular-nums">${scoreText}</strong></p>
                <p><span class="text-muted">Học phí:</span> <strong class="text-azure tabular-nums">${universityTuitionRange(u) ? universityTuitionRange(u).map(formatVND).filter((v,i,a)=>i===0||v!==a[0]).join('–')+'/năm' : 'Đang cập nhật'}</strong></p>
              </div>
              <div class="university-card-actions mt-auto pt-4 border-t border-line/60" onclick="event.stopPropagation()">
                <a href="#truong-dai-hoc/${u.id}" class="university-card-primary">Xem ngành & điểm</a>
                ${/^https?:\/\//i.test(u.website || '') ? `<a href="${universityEscape(u.website)}" target="_blank" rel="noopener noreferrer" class="university-card-secondary">Trang trường <i data-lucide="external-link" class="size-3.5"></i></a>` : ''}
                ${/^https?:\/\//i.test(u.admissionsUrl || '') ? `<a href="${universityEscape(u.admissionsUrl)}" target="_blank" rel="noopener noreferrer" class="university-card-admissions"><i data-lucide="graduation-cap" class="size-4"></i>Trang tuyển sinh</a>` : ''}
              </div>
              ${universityFit(u) !== null ? '<p class="mt-3 text-[11px] text-muted leading-relaxed">Chỉ số phù hợp dựa trên RIASEC, không phải xác suất trúng tuyển.</p>' : ''}
            </article>
          `;
          })
          .join('');
}

// ==========================================================================
// 5b. SCHOOL DETAIL PAGE (#truong-dai-hoc/uni-XXX) — Programs, Scores, Tuition
// ==========================================================================
async function renderSchoolDetailPage(container, schoolId) {
 const sd=state.schoolDetails.find(s=>s.id===schoolId);
 const esc=universityEscape;
 if(!sd){container.innerHTML='<p class="p-10 text-muted">Không tìm thấy trường trong dữ liệu mới.</p>';return;}
 const tuition=sd.tuition||{};
 const money=v=>v==null?'Chưa có dữ liệu':formatVND(v);
 const range=tuition.min==null?'Chưa có dữ liệu':tuition.max!=null&&tuition.max!==tuition.min?`${money(tuition.min)} – ${money(tuition.max)}`:money(tuition.min);
 const thpt=sd.programs.flatMap(p=>p.admissions.filter(a=>a.method==='Điểm THPT 2026'&&a.value!=null&&a.scale===30).map(a=>a.value));
 const link=(href,label)=>/^https?:\/\//i.test(href||'')?`<a href="${esc(href)}" target="_blank" rel="noopener noreferrer" class="text-azure text-sm font-semibold underline underline-offset-4">${label} ↗</a>`:'';
 container.innerHTML=`<section class="hero-wash border-b border-line"><div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12"><a href="#truong-dai-hoc" class="text-sm font-semibold text-azure">← Danh sách trường</a><p class="mt-6 text-xs uppercase tracking-widest text-azure font-semibold">Tuyển sinh 2026 · Cập nhật 14/11/2026</p><h1 class="mt-3 font-display text-2xl sm:text-4xl font-bold text-navy">${esc(sd.name)}</h1><div class="mt-4 flex flex-wrap gap-2 text-xs text-muted"><span class="bg-card px-3 py-2 rounded-full border border-line">${esc(sd.provinceNew||sd.region)}</span>${sd.provinceOld!==sd.provinceNew?`<span class="bg-card px-3 py-2 rounded-full border border-line">Tỉnh/TP cũ: ${esc(sd.provinceOld)}</span>`:''}<span class="bg-card px-3 py-2 rounded-full border border-line">${sd.programs.length} ngành / chương trình</span></div><div class="mt-5 flex flex-wrap gap-5">${link(sd.website,'Trang chủ')}${link(sd.admissionsUrl,'Trang tuyển sinh')}${link(sd.scoreSource,'Nguồn điểm')}</div></div></section>
 <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6"><div class="grid gap-4 sm:grid-cols-2"><article class="school-summary"><p class="ue-filter-label">Học phí năm học 2026–2027</p><h2 class="text-xl sm:text-2xl font-bold text-navy">${range}</h2><p class="mt-3 text-xs text-muted">${esc(tuition.label||'Học phí cấp trường')}. Không áp dụng đồng nhất cho mọi chương trình.</p><div class="mt-4 grid grid-cols-2 gap-4 text-sm"><p class="text-muted">Mỗi tín chỉ<br><strong class="text-ink">${money(tuition.perCredit)}</strong></p><p class="text-muted">Trung vị / năm<br><strong class="text-ink">${money(tuition.median)}</strong></p></div><div class="mt-4 flex flex-wrap gap-4">${(tuition.sources||[]).map((url,i)=>link(url,`Nguồn học phí ${i+1}`)).join('')}</div></article>
 <article class="school-summary"><p class="ue-filter-label">Điểm THPT riêng · thang 30</p><h2 class="text-xl sm:text-2xl font-bold text-navy">${thpt.length?`${Math.min(...thpt)} – ${Math.max(...thpt)}`:'Không có điểm THPT riêng trong file'}</h2><p class="mt-3 text-sm text-muted">${thpt.length?'Khoảng điểm của các ngành có điểm THPT riêng.':'Xem điểm theo phương thức kết hợp, năng khiếu hoặc bài thi riêng ở từng ngành bên dưới.'}</p><p class="mt-4 text-xs text-muted">Giữ nguyên số liệu, thang điểm và ghi chú của file bạn cung cấp. Ô trống không được thay bằng điểm cũ hoặc điểm quy đổi.</p></article></div>
 <section class="school-summary"><div class="flex flex-wrap gap-3 items-start justify-between"><div><p class="ue-filter-label">Tra cứu theo ngành</p><h2 class="text-xl font-bold text-navy">Ngành đào tạo & điểm xét tuyển</h2></div><p id="school-new-count" class="text-sm text-muted" aria-live="polite"></p></div><div class="ue-filter-columns mt-5"><label class="ue-filter-label">Tìm ngành hoặc mã<input id="school-new-search" class="ue-filter-input" placeholder="Gõ tên ngành hoặc mã, có hoặc không dấu"></label><label class="ue-filter-label">Phương thức<select id="school-new-method" class="ue-filter-input"><option value="">Tất cả phương thức</option>${sd.methods.map(m=>`<option value="${esc(m)}">${esc(m)}</option>`).join('')}</select></label></div><div id="school-new-programs" class="mt-5 space-y-3"></div></section>
 <p class="text-xs text-muted">Nguồn dữ liệu: ${esc(sd.sourceFile)} · Sheet ${esc(sd.sheet)} · Các ghi chú rà soát được giữ cùng dữ liệu nhập.</p></div>`;
 const render=()=>{
  const q=universityText(container.querySelector('#school-new-search').value),method=container.querySelector('#school-new-method').value;
  const programs=sd.programs.filter(p=>universityText(p.code+' '+p.name).includes(q)&&(!method||p.admissions.some(a=>a.method===method)));
  container.querySelector('#school-new-count').textContent=`${programs.length} / ${sd.programs.length} chương trình`;
  container.querySelector('#school-new-programs').innerHTML=programs.length?programs.map(p=>`<details class="school-program"><summary><div><span class="text-xs font-semibold text-azure">${esc(p.code||'Chưa có mã')}</span><h3 class="mt-1 font-semibold text-navy">${esc(p.name)}</h3><p class="mt-2 text-xs text-muted">${esc(p.type)}</p></div><span class="school-program-toggle" aria-hidden="true">+</span></summary><div class="school-program-content"><div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">${p.admissions.filter(a=>!method||a.method===method).map(a=>`<div class="rounded-xl bg-mist border border-line p-4"><h4 class="text-xs font-semibold text-azure">${esc(a.method)}</h4><p class="mt-2 text-sm font-semibold text-ink whitespace-pre-line">${esc(a.raw)}</p></div>`).join('')||'<p class="text-sm text-muted">Chưa có điểm trong file.</p>'}</div>${p.tuition_annual!=null?`<p class="mt-4 text-sm text-muted">Học phí của dòng chương trình: <strong class="text-ink">${money(p.tuition_annual)}/năm</strong></p>`:''}<p class="mt-4 text-xs text-muted">${esc(sd.sheet)} · Dòng ${p.row} của file nguồn</p></div></details>`).join(''):'<p class="p-6 text-center text-muted">Không có ngành phù hợp. Hãy đổi từ khóa hoặc phương thức.</p>';
 };
 container.querySelector('#school-new-search').addEventListener('input',render);
 container.querySelector('#school-new-method').addEventListener('change',render);
 render();refreshIcons();
}


// ==========================================================================
// 6. PROFILE VIEW (#ho-so) — 4-TAB STUDENT COMPREHENSIVE PROFILE
// ==========================================================================
function renderProfile(container) {
  const p = state.studentProfile;
  const tab = state.activeProfileTab || 'tests';
  const hasAnyTest = Boolean(state.results.mbti || state.results.riasec || state.results.bigfive || state.results.cognitive);

  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Hồ sơ học sinh</p>
        <h1 class="mt-2 font-display text-3xl sm:text-4xl font-semibold text-navy">Hồ sơ hướng nghiệp & tuyển sinh toàn diện</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Tích hợp 4 lớp dữ liệu: Trắc nghiệm tính cách, Thông tin cá nhân, Học bạ & điểm thi, Tài chính & thể lực để phục vụ đối chiếu đồ thị tất định (Zero-Hallucination).
        </p>

        <!-- 4-Tab Switcher -->
        <div class="mt-8 flex flex-wrap gap-2">
          <button id="prof-tab-tests" class="min-h-11 rounded-full px-5 text-xs sm:text-sm font-semibold transition ${tab === 'tests' ? 'bg-navy text-paper shadow-border' : 'bg-card text-muted hover:text-navy shadow-border'}">
            🎯 1. Trắc nghiệm tính cách
          </button>
          <button id="prof-tab-personal" class="min-h-11 rounded-full px-5 text-xs sm:text-sm font-semibold transition ${tab === 'personal' ? 'bg-navy text-paper shadow-border' : 'bg-card text-muted hover:text-navy shadow-border'}">
            👤 2. Cá nhân & Quê quán
          </button>
          <button id="prof-tab-academic" class="min-h-11 rounded-full px-5 text-xs sm:text-sm font-semibold transition ${tab === 'academic' ? 'bg-navy text-paper shadow-border' : 'bg-card text-muted hover:text-navy shadow-border'}">
            📚 3. Học bạ & Điểm thi
          </button>
          <button id="prof-tab-finance" class="min-h-11 rounded-full px-5 text-xs sm:text-sm font-semibold transition ${tab === 'finance-health' ? 'bg-navy text-paper shadow-border' : 'bg-card text-muted hover:text-navy shadow-border'}">
            💰 4. Tài chính & Thể lực
          </button>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <!-- Account Status Banner -->
      ${
        state.currentUser
          ? `
        <div class="rounded-[20px] bg-emerald-500/10 border border-emerald-500/30 p-4 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-border">
          <div class="flex items-center gap-3">
            <span class="size-10 rounded-full bg-emerald-600 text-paper font-bold flex items-center justify-center text-sm shadow-sm shrink-0">
              ${(state.currentUser.name || state.currentUser.first_name || state.currentUser.email || 'U').charAt(0).toUpperCase()}
            </span>
            <div>
              <h4 class="font-display font-bold text-sm text-navy">
                Tài khoản liên kết: ${state.currentUser.name || `${state.currentUser.last_name || ''} ${state.currentUser.first_name || ''}`.trim() || state.currentUser.email}
              </h4>
              <p class="text-xs text-muted">
                ${state.currentUser.email} · Quyền: <span class="capitalize font-semibold text-azure">${state.currentUser.role}</span> · Đã đồng bộ an toàn với CSDL trung tâm
              </p>
            </div>
          </div>
          <button onclick="window.logoutUser()" class="text-xs font-semibold px-3.5 py-1.5 rounded-xl border border-line bg-card hover:bg-mist text-rose-500 transition shadow-border">
            Đăng xuất
          </button>
        </div>
      `
          : `
        <div class="rounded-[20px] bg-amber-500/10 border border-amber-500/30 p-4 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-border">
          <div class="flex items-center gap-3">
            <i data-lucide="shield-alert" class="size-6 text-amber-500 shrink-0"></i>
            <div>
              <h4 class="font-display font-bold text-sm text-navy">
                Bạn đang xem hồ sơ ở chế độ Khách (Guest)
              </h4>
              <p class="text-xs text-muted">
                Dữ liệu hiện lưu tạm trên trình duyệt này. Đăng nhập hoặc tạo tài khoản để đồng bộ vĩnh viễn trên mọi thiết bị!
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <a href="#dang-nhap" class="px-4 py-2 rounded-xl bg-navy text-paper text-xs font-semibold hover:bg-navy-deep cta-glow transition">
              Đăng nhập
            </a>
            <a href="#dang-ky" class="px-4 py-2 rounded-xl bg-card border border-line text-xs font-semibold hover:bg-mist text-navy transition shadow-border">
              Đăng ký
            </a>
          </div>
        </div>
      `
      }

      <!-- TAB 1: TESTS -->
      <div id="prof-content-tests" class="${tab === 'tests' ? 'block' : 'hidden'} space-y-8">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          ${state.quizzes
            .map((q) => {
              const res = state.results[q.id];
              return `
              <div class="rounded-[24px] bg-card p-6 shadow-border border border-line flex flex-col justify-between hover:shadow-border-hover transition">
                <div>
                  <div class="flex items-center justify-between mb-2">
                    <h3 class="font-display font-semibold text-lg text-navy">${q.name}</h3>
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${res ? 'bg-emerald-100 text-emerald-800' : 'bg-mist text-muted'}">
                      ${res ? 'Đã hoàn thành' : 'Chưa làm'}
                    </span>
                  </div>
                  <p class="text-xs text-muted mb-4">${q.tagline}</p>
                  ${
                    res
                      ? `<div class="p-3 rounded-[12px] bg-ice text-xs text-azure font-semibold mb-2 flex items-center justify-between">
                          <span>Kết quả đạt:</span>
                          <strong class="font-display text-sm text-navy">${res.code || res.type || (res.totalScore !== undefined ? `${res.totalScore}/30 (${res.tier || 'Hoàn tất'})` : 'Hoàn tất')}</strong>
                        </div>`
                      : ''
                  }
                </div>
                <div class="pt-4 border-t border-line/60 flex items-center justify-between">
                  ${
                    res
                      ? `<a href="#ket-qua/${q.id}" class="text-xs font-semibold text-azure hover:underline">Xem chi tiết kết quả →</a>`
                      : `<a href="#trac-nghiem/${q.id}" class="text-xs font-semibold text-navy hover:underline">Làm bài test ngay ↗</a>`
                  }
                </div>
              </div>
            `;
            })
            .join('')}
        </div>

        ${
          !hasAnyTest
            ? `
          <div class="rounded-[24px] bg-card border border-line p-8 text-center max-w-xl mx-auto shadow-border">
            <i data-lucide="compass" class="size-12 text-muted mx-auto mb-3"></i>
            <h3 class="font-display text-lg font-bold text-navy mb-1">Chưa có kết quả trắc nghiệm nào</h3>
            <p class="text-xs text-muted mb-6">Làm bài trắc nghiệm Holland RIASEC hoặc MBTI để hệ thống có dữ liệu sở thích nghề nghiệp.</p>
            <a href="#trac-nghiem" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs cta-glow">
              Làm bài trắc nghiệm ngay
            </a>
          </div>
        `
            : ''
        }
      </div>

      <!-- TAB 2: PERSONAL & PROVINCE -->
      <div id="prof-content-personal" class="${tab === 'personal' ? 'block' : 'hidden'} max-w-3xl space-y-6">
        <div class="rounded-[24px] bg-card p-6 shadow-border border border-line space-y-4">
          <h2 class="font-display text-lg font-bold text-navy">Thông tin cá nhân & Quê quán</h2>
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Họ và tên</label>
              <input type="text" id="prof-input-name" value="${p.fullName || ''}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Trường THPT</label>
              <input type="text" id="prof-input-school" value="${p.schoolName || ''}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Tỉnh / Thành phố quê quán</label>
              <input type="text" id="prof-input-province" value="${p.province || 'Long An'}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Khu vực ưu tiên (Quy chế tuyển sinh 2025)</label>
              <select id="prof-input-zone" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
                <option value="KV1" ${p.priorityZone === 'KV1' ? 'selected' : ''}>Khu vực 1 (KV1) — Cộng 0.75đ</option>
                <option value="KV2-NT" ${p.priorityZone === 'KV2-NT' ? 'selected' : ''}>Khu vực 2 Nông thôn (KV2-NT) — Cộng 0.50đ</option>
                <option value="KV2" ${p.priorityZone === 'KV2' ? 'selected' : ''}>Khu vực 2 (KV2) — Cộng 0.25đ</option>
                <option value="KV3" ${p.priorityZone === 'KV3' ? 'selected' : ''}>Khu vực 3 (KV3) — Không cộng điểm (0.0đ)</option>
              </select>
            </div>
          </div>
          <p class="text-xs text-muted italic">
            * Ghi chú: Hệ thống tự động bóc tách quy chế ưu tiên và tính điểm cộng động theo công thức Bộ GD&ĐT khi gửi truy vấn đến Đồ thị Tri thức Neo4j.
          </p>
        </div>
      </div>

      <!-- TAB 3: ACADEMIC -->
      <div id="prof-content-academic" class="${tab === 'academic' ? 'block' : 'hidden'} max-w-3xl space-y-6">
        <div class="rounded-[24px] bg-card p-6 shadow-border border border-line space-y-4">
          <h2 class="font-display text-lg font-bold text-navy">Học bạ 5 học kỳ & Điểm thi tuyển sinh</h2>
          <div class="grid gap-4 sm:grid-cols-3">
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Điểm TB 5 học kỳ (GPA)</label>
              <input type="number" step="0.1" id="prof-input-gpa" value="${p.gpa5Semesters || 8.4}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Hạnh kiểm Lớp 12</label>
              <select id="prof-input-conduct" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
                <option value="Tốt" ${p.conduct12 === 'Tốt' ? 'selected' : ''}>Tốt</option>
                <option value="Khá" ${p.conduct12 === 'Khá' ? 'selected' : ''}>Khá</option>
                <option value="Trung bình" ${p.conduct12 === 'Trung bình' ? 'selected' : ''}>Trung bình</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Khối thi trọng tâm</label>
              <select id="prof-input-group" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
                <option value="A00" ${p.subjectGroup === 'A00' ? 'selected' : ''}>A00 (Toán - Lý - Hóa)</option>
                <option value="A01" ${p.subjectGroup === 'A01' ? 'selected' : ''}>A01 (Toán - Lý - Anh)</option>
                <option value="B00" ${p.subjectGroup === 'B00' ? 'selected' : ''}>B00 (Toán - Hóa - Sinh)</option>
                <option value="C00" ${p.subjectGroup === 'C00' ? 'selected' : ''}>C00 (Văn - Sử - Địa)</option>
                <option value="D01" ${p.subjectGroup === 'D01' ? 'selected' : ''}>D01 (Toán - Văn - Anh)</option>
              </select>
            </div>
          </div>

          <div class="pt-4 border-t border-line">
            <h3 class="text-xs font-bold uppercase tracking-wider text-azure mb-3">Điểm thi tốt nghiệp THPT theo môn</h3>
            <div class="grid grid-cols-2 sm:grid-cols-6 gap-3">
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Toán</label>
                <input type="number" step="0.25" id="prof-input-math" value="${p.scores?.math || 8.5}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Vật lý</label>
                <input type="number" step="0.25" id="prof-input-physics" value="${p.scores?.physics || 8.0}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Hóa học</label>
                <input type="number" step="0.25" id="prof-input-chem" value="${p.scores?.chemistry || 7.0}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Tiếng Anh</label>
                <input type="number" step="0.25" id="prof-input-eng" value="${p.scores?.english || 8.5}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Ngữ văn</label>
                <input type="number" step="0.25" id="prof-input-lit" value="${p.scores?.literature || 7.5}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
              <div>
                <label class="block text-[11px] font-medium text-muted mb-1">Sinh học</label>
                <input type="number" step="0.25" id="prof-input-bio" value="${p.scores?.biology || 6.5}" class="w-full px-2.5 py-2 rounded-[10px] border border-line bg-mist text-xs text-ink focus:outline-none focus:border-azure">
              </div>
            </div>
          </div>

          <div class="pt-4 border-t border-line grid gap-4 sm:grid-cols-2">
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Chứng chỉ IELTS</label>
              <input type="number" step="0.5" id="prof-input-ielts" value="${p.ielts || 6.5}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure" placeholder="VD: 6.5">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Điểm ĐGNL ĐHQG TP.HCM (Thang 1200)</label>
              <input type="number" id="prof-input-dgnl" value="${p.dgnlHcm || 850}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure" placeholder="VD: 850">
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 4: FINANCE & HEALTH -->
      <div id="prof-content-finance" class="${tab === 'finance-health' ? 'block' : 'hidden'} max-w-3xl space-y-6">
        <div class="rounded-[24px] bg-card p-6 shadow-border border border-line space-y-4">
          <h2 class="font-display text-lg font-bold text-navy">Ngân sách tài chính & Thể lực</h2>
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Ngân sách học phí tối đa (VND / Năm)</label>
              <input type="number" id="prof-input-budget" value="${p.annualBudget || 40000000}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
              <span class="text-[11px] text-azure font-medium mt-1 block">Tương đương: ${formatVND(p.annualBudget || 40000000)}/năm</span>
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Độ cận thị 2 mắt (Diop)</label>
              <input type="number" step="0.25" id="prof-input-eyesight" value="${p.eyesightDiop || 1.5}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Chiều cao (cm)</label>
              <input type="number" id="prof-input-height" value="${p.heightCm || 172}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
            <div>
              <label class="block text-xs font-semibold text-muted mb-1">Cân nặng (kg)</label>
              <input type="number" id="prof-input-weight" value="${p.weightKg || 65}" class="w-full px-3.5 py-2.5 rounded-[12px] border border-line bg-mist text-sm text-ink focus:outline-none focus:border-azure">
            </div>
          </div>
        </div>
      </div>

      <!-- BOTTOM ACTION BAR -->
      <div class="mt-8 pt-6 border-t border-line flex flex-wrap items-center justify-between gap-4 max-w-3xl">
        <button id="btn-save-profile" class="px-6 py-3 rounded-[14px] bg-card text-navy font-semibold text-sm border border-line shadow-border hover:shadow-border-hover transition flex items-center gap-2">
          <i data-lucide="save" class="size-4 text-azure"></i>
          <span>Lưu thông tin hồ sơ</span>
        </button>

        <button id="btn-push-to-ai" class="px-6 py-3 rounded-[14px] bg-gradient-to-r from-navy via-navy-deep to-azure text-paper font-semibold text-sm hover:opacity-95 cta-glow transition flex items-center gap-2">
          <i data-lucide="sparkles" class="size-4 text-cyan-soft animate-pulse"></i>
          <span>⚡ Nạp vào Tư vấn AI Nguyện vọng</span>
        </button>
      </div>
    </div>
  `;
  refreshIcons();
  attachProfileEvents();
}

function attachProfileEvents() {
  const tabs = ['tests', 'personal', 'academic', 'finance-health'];
  tabs.forEach((t) => {
    const btn = document.getElementById(`prof-tab-${t === 'finance-health' ? 'finance' : t}`);
    if (btn) {
      btn.addEventListener('click', () => {
        state.activeProfileTab = t;
        renderRoute();
      });
    }
  });

  const btnSave = document.getElementById('btn-save-profile');
  if (btnSave) {
    btnSave.addEventListener('click', () => {
      saveProfileFromInputs();
      showToast('Đã lưu thông tin hồ sơ thành công!', 'success');
    });
  }

  const btnPush = document.getElementById('btn-push-to-ai');
  if (btnPush) {
    btnPush.addEventListener('click', () => {
      saveProfileFromInputs();
      const promptText = 'Hãy tư vấn trường và ngành phù hợp dựa trên hồ sơ và kết quả RIASEC đã lưu của tôi.';
      window.location.hash = `#tu-van/${encodeURIComponent(promptText)}`;
    });
  }
}

function saveProfileFromInputs() {
  const name = document.getElementById('prof-input-name')?.value;
  const school = document.getElementById('prof-input-school')?.value;
  const province = document.getElementById('prof-input-province')?.value;
  const zone = document.getElementById('prof-input-zone')?.value;
  const gpa = parseFloat(document.getElementById('prof-input-gpa')?.value || '8.4');
  const conduct = document.getElementById('prof-input-conduct')?.value;
  const group = document.getElementById('prof-input-group')?.value;
  const math = parseFloat(document.getElementById('prof-input-math')?.value || '8.5');
  const physics = parseFloat(document.getElementById('prof-input-physics')?.value || '8.0');
  const chem = parseFloat(document.getElementById('prof-input-chem')?.value || '7.0');
  const eng = parseFloat(document.getElementById('prof-input-eng')?.value || '8.5');
  const lit = parseFloat(document.getElementById('prof-input-lit')?.value || '7.5');
  const bio = parseFloat(document.getElementById('prof-input-bio')?.value || '6.5');
  const ielts = parseFloat(document.getElementById('prof-input-ielts')?.value || '6.5');
  const dgnl = parseInt(document.getElementById('prof-input-dgnl')?.value || '850', 10);
  const budget = parseInt(document.getElementById('prof-input-budget')?.value || '40000000', 10);
  const eyesight = parseFloat(document.getElementById('prof-input-eyesight')?.value || '1.5');
  const height = parseInt(document.getElementById('prof-input-height')?.value || '172', 10);
  const weight = parseInt(document.getElementById('prof-input-weight')?.value || '65', 10);

  state.studentProfile = {
    fullName: name || state.studentProfile.fullName,
    schoolName: school || state.studentProfile.schoolName,
    province: province || state.studentProfile.province,
    priorityZone: zone || state.studentProfile.priorityZone,
    gpa5Semesters: gpa,
    conduct12: conduct || 'Tốt',
    subjectGroup: group || 'A01',
    scores: { math, physics, chemistry: chem, english: eng, literature: lit, biology: bio },
    ielts,
    dgnlHcm: dgnl,
    annualBudget: budget,
    eyesightDiop: eyesight,
    heightCm: height,
    weightKg: weight,
  };
  localStorage.setItem('fyf_student_profile', JSON.stringify(state.studentProfile));
}

// ==========================================================================
// 8. COMPARISON VIEW (#so-sanh) — SIDE-BY-SIDE PROGRAM & UNIVERSITY MATRIX
// ==========================================================================
function renderComparison(container) {
  const schools = (state.comparisonSchools || ['uni-001', 'uni-002'])
    .map((id) => state.universities.find((u) => u.id === id))
    .filter(Boolean);

  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Đối chiếu & So sánh</p>
        <h1 class="mt-2 font-display text-3xl sm:text-4xl font-semibold text-navy">So sánh trường Đại học & Chương trình</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Đặt cạnh nhau các trường và ngành bạn quan tâm để đối chiếu minh bạch điểm chuẩn 3 năm, học phí thực tế, điểm sàn và chỉ tiêu tuyển sinh.
        </p>

        <!-- Selector Row -->
        <div class="mt-6 flex flex-wrap items-center gap-3">
          <span class="text-xs font-bold text-navy uppercase tracking-wider">Thêm trường so sánh:</span>
          <select id="compare-add-select" class="bg-card border border-line rounded-[12px] px-3.5 py-2 text-xs font-medium text-ink focus:outline-none focus:border-azure">
            <option value="">-- Chọn trường để thêm --</option>
            ${state.universities
              .map((u) => `<option value="${u.id}">${u.shortName || u.name} - ${u.name}</option>`)
              .join('')}
          </select>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      ${
        schools.length === 0
          ? `
        <div class="rounded-[24px] bg-card p-10 text-center border border-line shadow-border max-w-md mx-auto">
          <p class="text-sm text-muted mb-4">Chưa chọn trường nào để so sánh.</p>
          <a href="#truong-dai-hoc" class="px-5 py-2.5 rounded-[12px] bg-navy text-paper text-xs font-semibold">Khám phá danh sách trường</a>
        </div>
      `
          : `
        <div class="overflow-x-auto rounded-[24px] bg-card border border-line shadow-border">
          <table class="w-full text-left text-sm border-collapse">
            <thead>
              <tr class="border-b border-line bg-mist/60 text-navy">
                <th class="p-4 sm:p-5 w-48 font-display font-bold text-xs uppercase tracking-wider text-azure">Tiêu chí đối chiếu</th>
                ${schools
                  .map(
                    (u) => `
                  <th class="p-4 sm:p-5 min-w-[260px] align-top">
                    <div class="flex items-start justify-between gap-2">
                      <div>
                        <span class="inline-block px-2.5 py-0.5 rounded-full bg-ice text-[10px] font-bold text-navy mb-1">${u.shortName || 'ĐH'}</span>
                        <h3 class="font-display font-bold text-base text-navy leading-snug">${u.name}</h3>
                        <p class="text-xs text-muted mt-0.5">${u.region} · ${u.provinceNew}</p>
                      </div>
                      <button class="btn-remove-compare text-muted hover:text-danger p-1 rounded-lg" data-id="${u.id}" title="Xóa khỏi so sánh">
                        <i data-lucide="x" class="size-4"></i>
                      </button>
                    </div>
                  </th>
                `
                  )
                  .join('')}
              </tr>
            </thead>
            <tbody class="divide-y divide-line text-xs sm:text-sm">
              <tr>
                <td class="p-4 font-semibold text-muted bg-mist/20">Điểm chuẩn THPT</td>
                ${schools
                  .map((u) => {
                    const thpt = u.admissions2026?.thptValues || [];
                    const range = thpt.length > 0 ? `${Math.min(...thpt)} – ${Math.max(...thpt)} điểm` : 'Đang cập nhật';
                    return `<td class="p-4 font-display font-bold text-navy tabular-nums">${range}</td>`;
                  })
                  .join('')}
              </tr>
              <tr>
                <td class="p-4 font-semibold text-muted bg-mist/20">Học phí trung bình</td>
                ${schools
                  .map(
                    (u) => `
                  <td class="p-4 font-bold text-azure tabular-nums">${formatVND(u.tuition)}/năm</td>
                `
                  )
                  .join('')}
              </tr>
              <tr>
                <td class="p-4 font-semibold text-muted bg-mist/20">Phương thức xét tuyển</td>
                ${schools
                  .map(
                    (u) => `
                  <td class="p-4 text-xs text-ink leading-relaxed">
                    <ul class="list-disc list-inside space-y-1">
                      <li>Xét điểm thi tốt nghiệp THPT</li>
                      <li>Xét điểm ĐGNL (ĐHQG HCM / ĐHQG HN)</li>
                      <li>Xét tuyển kết hợp & Chứng chỉ Quốc tế</li>
                    </ul>
                  </td>
                `
                  )
                  .join('')}
              </tr>
              <tr>
                <td class="p-4 font-semibold text-muted bg-mist/20">Ngành đào tạo tiêu biểu</td>
                ${schools
                  .map(
                    (u) => `
                  <td class="p-4 text-xs text-ink leading-relaxed">
                    <div class="flex flex-wrap gap-1.5">
                      ${(u.majors || ['Công nghệ thông tin', 'Khoa học máy tính', 'Kinh tế', 'Quản trị'])
                        .slice(0, 4)
                        .map((m) => `<span class="px-2 py-0.5 rounded-full bg-ice text-[11px] text-navy">${m}</span>`)
                        .join('')}
                    </div>
                  </td>
                `
                  )
                  .join('')}
              </tr>
              <tr>
                <td class="p-4 font-semibold text-muted bg-mist/20">Đề án chính thức</td>
                ${schools
                  .map(
                    (u) => `
                  <td class="p-4">
                    <a href="${u.admissionsUrl || u.website || '#'}" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-azure hover:underline">
                      <span>Xem nguồn trường</span>
                      <i data-lucide="external-link" class="size-3.5"></i>
                    </a>
                  </td>
                `
                  )
                  .join('')}
              </tr>
            </tbody>
          </table>
        </div>
      `
      }
    </div>
  `;
  refreshIcons();

  const addSel = document.getElementById('compare-add-select');
  if (addSel) {
    addSel.addEventListener('change', (e) => {
      const id = e.target.value;
      if (id && !state.comparisonSchools.includes(id)) {
        if (state.comparisonSchools.length >= 4) {
          showToast('Tối đa so sánh cùng lúc 4 trường', 'warning');
          return;
        }
        state.comparisonSchools.push(id);
        renderComparison(container);
      }
    });
  }

  document.querySelectorAll('.btn-remove-compare').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.id;
      state.comparisonSchools = state.comparisonSchools.filter((s) => s !== id);
      renderComparison(container);
    });
  });
}

// ==========================================================================
// 9. ADMIN & HEALTH MONITOR VIEW (#quan-tri / #admin)
// ==========================================================================
function renderAdmin(container) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Quản trị & Giám sát</p>
        <h1 class="mt-2 font-display text-3xl sm:text-4xl font-semibold text-navy">Bảng điều khiển & Giám sát hệ thống</h1>
        <p class="mt-3 max-w-2xl text-muted text-sm sm:text-base leading-relaxed">
          Kiểm tra trực tiếp kết nối CSDL PostgreSQL (Aiven Cloud SSL), Knowledge Graph Neo4j, và Ollama LLM Engine theo kiến trúc Zero-Hallucination.
        </p>
        <button id="btn-admin-probe" class="mt-6 px-5 py-2.5 rounded-[12px] bg-navy text-paper font-semibold text-xs shadow-border hover:bg-navy-deep cta-glow transition flex items-center gap-2">
          <i data-lucide="activity" class="size-4 text-cyan-soft"></i>
          <span>Kiểm tra sức khỏe hệ thống (Live Probe)</span>
        </button>
      </div>
    </div>

    <div class="mx-auto max-w-6xl px-4 py-10 sm:px-6 space-y-8">
      <!-- Service Health Cards -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-[20px] bg-card p-5 shadow-border border border-line">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-azure uppercase tracking-wider">Cơ sở dữ liệu</span>
            <span id="health-pg-badge" class="px-2 py-0.5 rounded-full text-[10px] font-bold text-muted">Chưa kiểm tra</span>
          </div>
          <h3 class="font-display font-bold text-lg text-navy">PostgreSQL / SQLite</h3>
          <p class="text-xs text-muted mt-1" id="health-db-backend">Máy chủ sẽ báo cơ sở dữ liệu đang dùng.</p>
        </div>

        <div class="rounded-[20px] bg-card p-5 shadow-border border border-line">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-azure uppercase tracking-wider">Knowledge Graph</span>
            <span id="health-neo4j-badge" class="px-2 py-0.5 rounded-full text-[10px] font-bold text-muted">Chưa kiểm tra</span>
          </div>
          <h3 class="font-display font-bold text-lg text-navy">Neo4j Bolt</h3>
          <p class="text-xs text-muted mt-1">bolt://localhost:7687</p>
        </div>

        <div class="rounded-[20px] bg-card p-5 shadow-border border border-line">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-azure uppercase tracking-wider">AI Consultation</span>
            <span id="health-ollama-badge" class="px-2 py-0.5 rounded-full text-[10px] font-bold text-muted">Chưa kiểm tra</span>
          </div>
          <h3 class="font-display font-bold text-lg text-navy">Ollama API (Local LLM)</h3>
          <p class="text-xs text-muted mt-1">Grounding: Sub-graph</p>
        </div>

        <div class="rounded-[20px] bg-card p-5 shadow-border border border-line">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-bold text-azure uppercase tracking-wider">Static Store</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">126 trường</span>
          </div>
          <h3 class="font-display font-bold text-lg text-navy">Đề án 2026</h3>
          <p class="text-xs text-muted mt-1">60 câu RIASEC · 16 MBTI</p>
        </div>
      </div>

      <!-- Live Diagnostics Terminal Box -->
      <div class="rounded-[24px] bg-navy-deep text-paper p-6 shadow-2xl border border-white/10 font-mono text-xs">
        <div class="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div class="flex items-center gap-2">
            <span class="size-3 rounded-full bg-red-500"></span>
            <span class="size-3 rounded-full bg-amber-500"></span>
            <span class="size-3 rounded-full bg-emerald-500"></span>
            <span class="ml-2 font-bold text-cyan-soft">System Diagnostics Console</span>
          </div>
          <span class="text-paper/60 text-[11px]">API: /api/v1/admin/health</span>
        </div>
        <pre id="admin-log-output" class="text-emerald-400 overflow-x-auto leading-relaxed">
Bấm kiểm tra để xem trạng thái của từng dịch vụ.
        </pre>
      </div>
    </div>
  `;
  refreshIcons();

  const updateHealthCards = (data = {}) => {
    const labels = {
      healthy: 'Hoạt động',
      unhealthy: 'Lỗi kết nối',
      offline: 'Ngoại tuyến',
      not_checked: 'Chưa kiểm tra',
    };
    for (const [id, service] of [['pg', data.database], ['neo4j', data.neo4j], ['ollama', data.ollama]]) {
      const badge = document.getElementById(`health-${id}-badge`);
      if (!badge) continue;
      const isHealthy = service?.status === 'healthy';
      badge.textContent = labels[service?.status] || 'Chưa xác định';
      badge.classList.toggle('bg-emerald-100', isHealthy);
      badge.classList.toggle('text-emerald-800', isHealthy);
      badge.classList.toggle('text-muted', !isHealthy);
    }

    const backend = document.getElementById('health-db-backend');
    if (backend) {
      const backendNames = {postgresql: 'PostgreSQL', sqlite: 'SQLite cục bộ'};
      backend.textContent = backendNames[data.database?.backend] || 'Chưa xác định được cơ sở dữ liệu';
    }
  };

  const btnProbe = document.getElementById('btn-admin-probe');
  if (btnProbe) {
    btnProbe.addEventListener('click', async () => {
      const log = document.getElementById('admin-log-output');
      if (log) log.textContent = 'Đang gửi yêu cầu kiểm tra sức khỏe hệ thống đến backend...';
      try {
        const res = await fetch('/api/v1/admin/health');
        const data = await res.json();
        if (!data.database) throw new Error(`HTTP ${res.status}`);
        if (log) log.textContent = JSON.stringify(data, null, 2);

        updateHealthCards(data);
        if (!res.ok) showToast('Cơ sở dữ liệu tạm thời không khả dụng.', 'error');
        else if (data.database.backend === 'sqlite') showToast('Đang sử dụng SQLite cục bộ.', 'info');
        else showToast('Kết nối cơ sở dữ liệu hoạt động.', 'success');
      } catch (err) {
        updateHealthCards();
        if (log) log.textContent = `Không thể kiểm tra backend: ${err.message}.`;
      }
    });
  }
}


// ==========================================================================
// 7. ABOUT VIEW (#gioi-thieu)
// ==========================================================================
function renderAbout(container) {
  container.innerHTML = `
    <div class="hero-wash border-b border-line">
      <div class="mx-auto max-w-3xl px-4 py-14 sm:px-6">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-azure">Về For Your Future</p>
        <h1 class="mt-2 font-display text-4xl font-semibold text-navy">
          Ánh sáng vừa đủ để nhìn đường, không phải để chói mắt
        </h1>
        <p class="mt-4 text-muted leading-relaxed">
          For Your Future là nền tảng trắc nghiệm tính cách và hướng nghiệp dành cho học sinh, sinh viên và người đang tìm hướng đi. Chúng tôi tin việc hiểu mình nên chậm, rõ, và tử tế.
        </p>
      </div>
    </div>

    <div class="mx-auto max-w-3xl space-y-8 px-4 py-12 sm:px-6">
      <section>
        <h2 class="font-display text-2xl font-semibold text-navy">Phương pháp</h2>
        <p class="mt-3 text-sm leading-relaxed text-muted">
          Website có bốn bài trắc nghiệm: MBTI (xu hướng tính cách), RIASEC / Holland (sở thích nghề nghiệp), Big Five (năm chiều tính cách) và Năng lực nhận thức (ngôn ngữ, định lượng, hình ảnh và quy luật). Thuật toán hiện tại là phiên bản giáo dục — đủ để soi gương, chưa phải công cụ chẩn đoán lâm sàng.
        </p>
      </section>

      <section>
        <h2 class="font-display text-2xl font-semibold text-navy">Bốn bài trắc nghiệm, một hồ sơ</h2>
        <ul class="mt-4 space-y-3 text-sm leading-relaxed text-muted">
          <li>
            <strong class="text-navy">MBTI</strong> — 16 nhóm, kể cách bạn nạp năng lượng, nhận thông tin, ra quyết định và sắp xếp đời sống.
          </li>
          <li>
            <strong class="text-navy">RIASEC</strong> — sáu nhóm sở thích nghề nghiệp theo mô hình Holland.
          </li>
          <li>
            <strong class="text-navy">Big Five</strong> — năm chiều đo theo mức độ, ít ‘nhóm’ hơn, nhiều ‘mức’ hơn.
          </li>
          <li>
            <strong class="text-navy">Năng lực nhận thức</strong> — tìm hiểu khả năng ngôn ngữ, định lượng và nhận diện hình ảnh, quy luật qua các câu hỏi thực hành.
          </li>
        </ul>
      </section>

      <section id="chinh-sach">
        <h2 class="font-display text-2xl font-semibold text-navy">Chính sách dữ liệu</h2>
        <p class="mt-3 text-sm leading-relaxed text-muted">
          Câu trả lời và kết quả được lưu trên thiết bị của bạn (trình duyệt). For Your Future không yêu cầu tài khoản và không gửi hồ sơ cá nhân lên máy chủ cho bản trải nghiệm này. Xóa dữ liệu trình duyệt là xóa hồ sơ.
        </p>
      </section>

      <section id="lien-he">
        <h2 class="font-display text-2xl font-semibold text-navy">Liên hệ</h2>
        <p class="mt-3 text-sm leading-relaxed text-muted">
          Nếu bạn có câu hỏi về dữ liệu điểm tuyển sinh 126 trường hoặc muốn đóng góp bộ câu hỏi chuẩn hóa, vui lòng liên hệ ban biên tập For Your Future.
        </p>
      </section>
    </div>
  `;
}

// ==========================================================================
// 8. THEME & INITIALIZATION
// ==========================================================================
function initTheme() {
  const btn = document.getElementById('btn-toggle-theme');
  const isDark = localStorage.getItem('fyf_theme') === 'dark' || (!('fyf_theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  if (btn) {
    btn.addEventListener('click', () => {
      const willBeDark = !document.documentElement.classList.contains('dark');
      if (willBeDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('fyf_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('fyf_theme', 'light');
      }
      refreshIcons();
    });
  }
}

function setMobileMenuOpen(open,restoreFocus=false){
  const button=document.getElementById('btn-mobile-menu'),menu=document.getElementById('mobile-menu');
  if(!button||!menu)return;
  if(menu.classList.contains('hidden')===!open&&button.getAttribute('aria-expanded')===String(open)){if(restoreFocus)button.focus();return;}
  menu.classList.toggle('hidden',!open);
  button.setAttribute('aria-expanded',String(open));
  button.setAttribute('aria-label',open?'Đóng menu di động':'Mở menu di động');
  if(restoreFocus)button.focus();
}
function initMobileMenu() {
  const button=document.getElementById('btn-mobile-menu'),menu=document.getElementById('mobile-menu');
  if(!button||!menu)return;
  setMobileMenuOpen(false);
  button.addEventListener('click',()=>setMobileMenuOpen(menu.classList.contains('hidden')));
  menu.addEventListener('click',event=>{if(event.target.closest('a[href]'))setMobileMenuOpen(false);});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!menu.classList.contains('hidden')){event.preventDefault();setMobileMenuOpen(false,true);}});
  document.addEventListener('pointerdown',event=>{if(!menu.contains(event.target)&&!button.contains(event.target))setMobileMenuOpen(false);},{passive:true});
  window.matchMedia('(min-width:1300px)').addEventListener('change',event=>{if(event.matches)setMobileMenuOpen(false);});
}

function initDetailModal() {
  const btnClose = document.getElementById('btn-close-detail-modal');
  const modal = document.getElementById('detail-modal');
  if (btnClose) btnClose.addEventListener('click', closeDetailModal);
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeDetailModal();
    });
    modal.addEventListener('keydown',event=>{
      if(event.key==='Escape'){event.preventDefault();event.stopPropagation();closeDetailModal();return;}
      if(event.key!=='Tab')return;
      const controls=[...modal.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')].filter(el=>el.getClientRects().length);
      const first=controls[0],last=controls[controls.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
    });
  }
}

// ==========================================================================
// 7. AI CONSULTATION & GRAPHRAG STRATEGIC PORTFOLIO
// ==========================================================================
function renderChatText(element, message) {
  if (!window.marked?.parse) { element.textContent=message; return; }
  const safeInput=message.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const doc=new DOMParser().parseFromString(window.marked.parse(safeInput),'text/html');
  const allowed=new Set(['P','BR','STRONG','EM','UL','OL','LI','CODE','PRE','H1','H2','H3','H4','BLOCKQUOTE','A','HR','TABLE','THEAD','TBODY','TR','TH','TD','DEL']);
  for(const node of [...doc.body.querySelectorAll('*')]) {
    if(!allowed.has(node.tagName)){node.replaceWith(...node.childNodes);continue;}
    const href=node.tagName==='A'?node.getAttribute('href'):null;
    [...node.attributes].forEach(attr=>node.removeAttribute(attr.name));
    if(href && /^https?:\/\//i.test(href)){node.setAttribute('href',href);node.setAttribute('target','_blank');node.setAttribute('rel','noopener noreferrer');}
  }
  element.replaceChildren(...doc.body.childNodes);
}

const CHAT_RESUME_WINDOW_MS=5*60*1000;
function clearChatResume(owner){
  if(!owner)return;
  try {localStorage.removeItem(`fyf_chat_resume_${owner}`);sessionStorage.removeItem(`fyf_chat_active_${owner}`);}catch(_){}
}
function saveChatResume(owner,sessionId,leftAt=Date.now()){
  if(!owner)return;
  try {localStorage.setItem(`fyf_chat_resume_${owner}`,JSON.stringify({sessionId,leftAt}));}catch(_){}
}
function readChatResume(owner,now=Date.now()){
  if(!owner)return null;
  try {
    const saved=JSON.parse(localStorage.getItem(`fyf_chat_resume_${owner}`)||'null');
    const elapsed=now-saved?.leftAt;
    if(saved&&typeof saved.sessionId==='string'&&saved.sessionId&&Number.isFinite(saved.leftAt)&&elapsed>=0&&elapsed<CHAT_RESUME_WINDOW_MS)return saved.sessionId;
  }catch(_){}
  clearChatResume(owner);return null;
}
const chatRuntime = {controller:null,version:0,owner:null,sessionId:null,messages:[],busy:false,onLeave:null};
async function renderConsultation(container, param) {
  chatRuntime.onLeave?.();chatRuntime.onLeave=null;
  chatRuntime.cleanup?.();chatRuntime.cleanup=null;
  chatRuntime.controller?.abort();
  const version=++chatRuntime.version;
  const owner=state.currentUser?.user_id, token=state.authToken;
  const esc=universityEscape;
  if(!owner||!token){container.innerHTML='<div class="max-w-xl mx-auto px-4 py-16 text-center"><h1 class="text-2xl font-bold text-navy">Trò chuyện với trợ lý hướng nghiệp</h1><p class="text-muted mt-3">Đăng nhập để trò chuyện và lưu lịch sử của bạn.</p><a href="#dang-nhap" class="inline-flex mt-6 px-5 py-3 bg-navy text-paper rounded-xl">Đăng nhập</a></div>';return;}
  const resumeId=param?null:readChatResume(owner);
  clearChatResume(owner);
  chatRuntime.owner=owner;chatRuntime.sessionId=null;chatRuntime.messages=[];chatRuntime.busy=false;
  const current=()=>version===chatRuntime.version&&state.currentUser?.user_id===owner&&state.authToken===token&&container.isConnected&&window.location.hash.startsWith('#tu-van');
  const api=async(path,options={})=>{
    const r=await fetch('/api/v1/chat/sessions'+path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`}});
    if(!r.ok){const error=await r.json().catch(()=>({}));throw new Error(typeof error.detail==='string'?error.detail:'Không thể tải cuộc trò chuyện. Vui lòng thử lại.');}
    return r;
  };
  const rawName=state.currentUser.first_name||state.currentUser.name||state.currentUser.full_name||'';
  const greetingName=String(rawName).trim().split(/\s+/).pop();
  const suggestions=[
    {icon:'compass',label:'Tìm ngành phù hợp',prompt:'Tôi nên bắt đầu chọn ngành từ đâu?'},
    {icon:'graduation-cap',label:'Chọn trường cùng tôi',prompt:'Gợi ý trường phù hợp với hồ sơ của tôi'},
    {icon:'wallet',label:'Tìm hiểu học phí',prompt:'Tôi muốn tìm hiểu về học phí'},
  ];
  container.innerHTML=`
    <div class="ai-chat-layout">
      <aside id="chat-drawer" class="ai-chat-sidebar" aria-label="Cuộc trò chuyện">
        <div class="ai-chat-sidebar-top">
          <div class="chat-sidebar-heading"><h2 class="font-semibold text-ink">Cuộc trò chuyện</h2><button id="chat-history-close" type="button" aria-label="Đóng lịch sử" title="Đóng lịch sử">×</button></div>
          <button id="chat-new" class="chat-new-button" type="button"><i data-lucide="square-pen" class="size-4" aria-hidden="true"></i>Trò chuyện mới</button>
        </div>
        <nav id="chat-sessions" aria-label="Lịch sử trò chuyện"><p class="text-sm text-muted p-3">Đang tải lịch sử...</p></nav>
      </aside>
      <button type="button" id="chat-history-backdrop" class="chat-history-backdrop" tabindex="-1" aria-label="Đóng lịch sử" hidden></button>
      <section class="ai-chat-main is-chat-empty" aria-label="Trò chuyện với AI">
        <header class="ai-chat-header">
          <div class="chat-header-leading">
            <button id="chat-history-toggle" type="button" aria-expanded="false" aria-controls="chat-drawer" aria-label="Mở lịch sử trò chuyện" title="Mở lịch sử trò chuyện" class="chat-history-toggle"><i data-lucide="panel-left" class="size-5" aria-hidden="true"></i><span class="chat-toggle-text">Lịch sử</span></button>
            <div><h1>Trợ lý hướng nghiệp <span class="chat-ai-badge">AI</span></h1><p>Tư vấn chọn ngành và trường</p></div>
          </div>
          <button id="chat-new-shortcut" type="button" class="chat-new-shortcut" title="Cuộc trò chuyện mới" aria-label="Cuộc trò chuyện mới"><i data-lucide="square-pen" class="size-4" aria-hidden="true"></i><span>Trò chuyện mới</span></button>
        </header>
        <div id="chat-messages" class="ai-chat-messages" role="log" aria-label="Tin nhắn"></div>
        <form id="chat-form" class="ai-chat-composer">
          <p id="chat-error" class="chat-error" role="alert"></p>
          <div class="ai-chat-input-row">
            <label for="chat-input" class="sr-only">Tin nhắn cho trợ lý AI</label>
            <textarea id="chat-input" rows="1" maxlength="6000" placeholder="Bạn muốn tìm hiểu điều gì?"></textarea>
            <button id="chat-send" type="submit" class="chat-send-button" aria-label="Gửi tin nhắn" title="Gửi tin nhắn" disabled><i data-lucide="arrow-up" class="size-5" aria-hidden="true"></i></button>
            <button id="chat-stop" type="button" class="chat-stop-button" aria-label="Dừng phản hồi" title="Dừng phản hồi" hidden><i data-lucide="square" class="size-4" aria-hidden="true"></i></button>
          </div>
          <div class="ai-chat-composer-bottom"><label class="chat-year-label"><i data-lucide="calendar-days" class="size-3.5" aria-hidden="true"></i>Năm xét tuyển <select id="chat-year" aria-label="Năm xét tuyển"><option>2026</option><option>2027</option></select></label><span id="chat-status" role="status" aria-live="polite">Enter để gửi · Shift + Enter để xuống dòng</span></div>
        </form>
        <div id="chat-starters" class="chat-suggestions" aria-label="Gợi ý bắt đầu trò chuyện">${suggestions.map(item=>`<button type="button" data-chat-prompt="${esc(item.prompt)}"><i data-lucide="${item.icon}" class="size-4" aria-hidden="true"></i><span>${esc(item.label)}</span></button>`).join('')}</div>
      </section>
    </div>`;
  document.body.classList.add('chat-page-active');
  const log=container.querySelector('#chat-messages'),input=container.querySelector('#chat-input'),error=container.querySelector('#chat-error');
  const layout=container.querySelector('.ai-chat-layout'),drawer=container.querySelector('#chat-drawer'),main=container.querySelector('.ai-chat-main');
  const toggle=container.querySelector('#chat-history-toggle'),backdrop=container.querySelector('#chat-history-backdrop');
  const mobileQuery=window.matchMedia('(max-width: 767px)');
  let desktopOpen=false,mobileOpen=false;
  function setSidebar(open,focus=false){
    if(mobileQuery.matches)mobileOpen=open;else desktopOpen=open;
    applySidebar(focus);
  }
  function applySidebar(focus=false){
    const mobile=mobileQuery.matches,open=mobile?mobileOpen:desktopOpen;
    layout.classList.toggle('is-sidebar-closed',!open);
    layout.classList.toggle('is-sidebar-open',open);
    drawer.inert=!open;main.inert=mobile&&open;
    backdrop.hidden=!(mobile&&open);
    toggle.setAttribute('aria-expanded',String(open));
    toggle.setAttribute('aria-label',open?'Đóng lịch sử trò chuyện':'Mở lịch sử trò chuyện');
    toggle.title=open?'Đóng lịch sử trò chuyện':'Mở lịch sử trò chuyện';
    if(mobile&&open){drawer.setAttribute('role','dialog');drawer.setAttribute('aria-modal','true');}
    else {drawer.removeAttribute('role');drawer.removeAttribute('aria-modal');}
    if(focus)(open&&mobile?container.querySelector('#chat-history-close'):toggle).focus();
  }
  const responsiveSidebar=()=>{mobileOpen=false;desktopOpen=false;applySidebar();};
  mobileQuery.addEventListener('change',responsiveSidebar);
  let awayAt=null;
  function recordDeparture(){
    if(awayAt!==null||version!==chatRuntime.version||state.currentUser?.user_id!==owner||state.authToken!==token)return;
    awayAt=Date.now();saveChatResume(owner,chatRuntime.sessionId,awayAt);
  }
  function returnFromAway(){
    if(awayAt===null||!current())return;
    const elapsed=Date.now()-awayAt;
    if(elapsed<0||elapsed>=CHAT_RESUME_WINDOW_MS){
      clearChatResume(owner);chatRuntime.onLeave=null;
      renderConsultation(container);return;
    }
    awayAt=null;clearChatResume(owner);
  }
  const visibilityChanged=()=>{if(document.visibilityState==='hidden')recordDeparture();else returnFromAway();};
  document.addEventListener('visibilitychange',visibilityChanged);
  window.addEventListener('pagehide',recordDeparture);
  window.addEventListener('pageshow',returnFromAway);
  chatRuntime.onLeave=recordDeparture;
  chatRuntime.cleanup=()=>{
    mobileQuery.removeEventListener('change',responsiveSidebar);
    document.removeEventListener('visibilitychange',visibilityChanged);
    window.removeEventListener('pagehide',recordDeparture);
    window.removeEventListener('pageshow',returnFromAway);
  };
  toggle.onclick=()=>setSidebar(!(mobileQuery.matches?mobileOpen:desktopOpen),true);
  container.querySelector('#chat-history-close').onclick=()=>setSidebar(false,true);
  backdrop.onclick=()=>setSidebar(false,true);
  layout.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&(mobileQuery.matches?mobileOpen:desktopOpen)){event.preventDefault();setSidebar(false,true);}
    if(event.key==='Tab'&&mobileQuery.matches&&mobileOpen){
      const buttons=[...drawer.querySelectorAll('button:not(:disabled),a[href]')];const first=buttons[0],last=buttons[buttons.length-1];
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
    }
  });
  applySidebar();
  function resizeInput(){
    input.style.height='auto';
    input.style.height=Math.min(input.scrollHeight,160)+'px';
    container.querySelector('#chat-send').disabled=chatRuntime.busy||!input.value.trim();
  }
  function setDraft(text){input.value=text;resizeInput();input.focus();}
  function setConversationMode(){
    const empty=chatRuntime.messages.length===0;
    main.classList.toggle('is-chat-empty',empty);
    container.querySelector('#chat-starters').hidden=!empty;
  }
  input.addEventListener('input',resizeInput);
  container.querySelectorAll('[data-chat-prompt]').forEach(button=>button.onclick=()=>setDraft(button.dataset.chatPrompt));
  resizeInput();
  let sessions=[];
  function controls(){
    log.setAttribute('aria-busy',String(chatRuntime.busy));
    container.querySelector('#chat-send').disabled=chatRuntime.busy||!input.value.trim();
    container.querySelector('#chat-send').hidden=chatRuntime.busy;
    container.querySelector('#chat-stop').hidden=!chatRuntime.busy;
    container.querySelector('#chat-new').disabled=chatRuntime.busy;
    container.querySelector('#chat-new-shortcut').disabled=chatRuntime.busy;
    container.querySelector('#chat-year').disabled=chatRuntime.busy;
    container.querySelectorAll('[data-chat-session]').forEach(b=>b.disabled=chatRuntime.busy);
    container.querySelector('#chat-status').textContent=chatRuntime.busy?'Trợ lý đang trả lời...':'Enter để gửi · Shift + Enter để xuống dòng';
  }
  function drawSidebar(){
    container.querySelector('#chat-sessions').innerHTML=sessions.length?sessions.map(s=>`<button type="button" data-chat-session="${esc(s.session_id)}" class="chat-session-item ${s.session_id===chatRuntime.sessionId?'is-active':''}" ${s.session_id===chatRuntime.sessionId?'aria-current="true"':''}><span>${esc(s.title)}</span><time>${esc(new Date(s.started_at+'Z'.repeat(!/[zZ]|[+-]\d\d:\d\d$/.test(s.started_at))).toLocaleDateString('vi-VN'))}</time></button>`).join(''):'<p class="text-sm text-muted p-3">Chưa có cuộc trò chuyện.</p>';
    container.querySelectorAll('[data-chat-session]').forEach(b=>b.onclick=()=>openSession(b.dataset.chatSession));controls();
  }
  function createPortfolioWidget(portfolio, onAsk){
    if(!portfolio)return null;
    const reach=portfolio.reach||[];
    const target=portfolio.target||[];
    const safe=portfolio.safe||[];
    const topStrategic=[...reach,...target,...safe];
    const allCandidates=(portfolio.all_candidates&&portfolio.all_candidates.length>0)?portfolio.all_candidates:topStrategic;
    if(!topStrategic.length&&!allCandidates.length)return null;

    const widget=document.createElement('div');
    widget.className='chat-portfolio-widget';

    let currentTab='all';
    const header=document.createElement('div');
    header.className='chat-portfolio-header';
    header.innerHTML=`
      <div class="chat-portfolio-title">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:7px;background:var(--color-navy);color:#fff;font-size:12px;">📊</span>
        <span>Danh mục Chiến lược 3-Tier Đề Xuất</span>
        <span style="font-size:11px;font-weight:normal;color:var(--color-muted);">(${topStrategic.length} chiến lược tối ưu · ${allCandidates.length} ngành khớp)</span>
      </div>
    `;

    const tabs=document.createElement('div');
    tabs.className='chat-portfolio-tabs';
    const tabDefs=[
      {id:'all',label:`Top Chiến lược (${topStrategic.length})`,cls:''},
      {id:'Safe',label:`Safe (${safe.length})`,cls:'is-safe'},
      {id:'Target',label:`Target (${target.length})`,cls:'is-target'},
      {id:'Reach',label:`Reach (${reach.length})`,cls:'is-reach'},
    ];
    if(allCandidates.length>topStrategic.length){
      tabDefs.push({id:'all_cat',label:`Toàn bộ Đồ thị (${allCandidates.length})`,cls:'is-all-cat'});
    }

    const grid=document.createElement('div');
    grid.className='chat-portfolio-grid';

    function renderCards(tier){
      grid.innerHTML='';
      let list=[];
      if(tier==='all')list=topStrategic;
      else if(tier==='all_cat')list=allCandidates;
      else list=allCandidates.filter(p=>(p.tier||'').toLowerCase()===(tier||'').toLowerCase());

      list.forEach(p=>{
        const card=document.createElement('div');
        card.className='chat-portfolio-card';
        const tierLower=(p.tier||'Safe').toLowerCase();
        const marginVal=typeof p.score_margin==='number'?(p.score_margin>=0?`+${p.score_margin}`:`${p.score_margin}`):'--';
        const marginClass=typeof p.score_margin==='number'?(p.score_margin>=0?'is-positive':'is-negative'):'';
        const tuitionText=p.tuition_fee?`~${p.tuition_fee}tr/năm`:'Theo đề án';

        card.innerHTML=`
          <div>
            <div class="chat-portfolio-card-top">
              <span class="chat-portfolio-uni-code">${p.university_code||'UNI'}</span>
              <span class="chat-tier-badge tier-${tierLower}">${p.tier||'Safe'}</span>
            </div>
            <div class="chat-portfolio-prog-name" title="${p.program_name||''}">${p.program_name||''}</div>
            <div class="chat-portfolio-uni-name" title="${p.university_name||''}">${p.university_name||''}</div>
            <div class="chat-portfolio-metrics">
              <div>
                <span class="chat-portfolio-metric-label">Điểm chuẩn</span>
                <span class="chat-portfolio-metric-val">${p.admission_score??'--'}</span>
              </div>
              <div>
                <span class="chat-portfolio-metric-label">Biên độ</span>
                <span class="chat-portfolio-metric-val ${marginClass}">${marginVal}</span>
              </div>
              <div>
                <span class="chat-portfolio-metric-label">Học phí</span>
                <span class="chat-portfolio-metric-val">${tuitionText}</span>
              </div>
            </div>
          </div>
          <div class="chat-portfolio-card-bottom">
            <span class="chat-portfolio-location">📍 ${p.location||'Toàn quốc'}</span>
            <button type="button" class="chat-portfolio-ask-btn">Hỏi chi tiết →</button>
          </div>
        `;
        card.querySelector('.chat-portfolio-ask-btn').onclick=()=>{
          if(onAsk)onAsk(`Phân tích chi tiết cơ hội xét tuyển và việc làm ngành ${p.program_name} tại trường ${p.university_name}`);
        };
        grid.appendChild(card);
      });
    }

    tabDefs.forEach(def=>{
      const btn=document.createElement('button');
      btn.type='button';
      btn.className=`chat-portfolio-tab ${def.cls} ${def.id===currentTab?'is-active':''}`;
      btn.textContent=def.label;
      btn.onclick=()=>{
        currentTab=def.id;
        tabs.querySelectorAll('.chat-portfolio-tab').forEach(t=>t.classList.remove('is-active'));
        btn.classList.add('is-active');
        renderCards(currentTab);
      };
      tabs.appendChild(btn);
    });

    widget.appendChild(header);
    widget.appendChild(tabs);
    widget.appendChild(grid);
    renderCards('all');
    return widget;
  }
  function appendMessage(message){
    const row=document.createElement('article');row.className=`chat-message chat-message-${message.role==='user'?'user':'assistant'}`;
    const label=document.createElement('p');label.className='chat-message-label';label.textContent=message.role==='user'?'Bạn':'Trợ lý AI';
    const body=document.createElement('div');body.className='chat-message-text';if(message.role==='assistant')renderChatText(body,message.content);else body.textContent=message.content;
    row.append(label,body);

    const onAsk=setDraft;
    const evItem=Array.isArray(message.evidence)?message.evidence.find(e=>e.type==='portfolio'):message.evidence;
    const portData=message.portfolio||(evItem&&evItem.data)||evItem;
    if(portData&&message.role==='assistant'){
      const widget=createPortfolioWidget(portData.data||portData,onAsk);
      if(widget)row.append(widget);
    }

    log.append(row);return body;
  }
  function drawMessages(){
    log.replaceChildren();
    setConversationMode();
    if(!chatRuntime.messages.length){
      log.innerHTML=`<div class="chat-welcome"><span class="chat-welcome-icon" aria-hidden="true"><i data-lucide="compass" class="size-6"></i></span><p class="chat-welcome-greeting">${greetingName?`Chào ${esc(greetingName)},`:'Chào bạn,'}</p><h2>Hôm nay, bạn muốn khám phá điều gì?</h2><p class="chat-welcome-description">Cùng bạn tìm ngành phù hợp, chọn trường và chuẩn bị cho hướng đi tiếp theo.</p></div>`;
      refreshIcons();
    }else chatRuntime.messages.forEach(appendMessage);
    resizeInput();
    log.scrollTop=log.scrollHeight;
  }
  async function refreshSessions(){sessions=await(await api('')).json();if(current())drawSidebar();}
  async function openSession(id){
    if(chatRuntime.busy)return;
    error.textContent='';
    const requestId=++selection;
    try {const data=await(await api('/'+encodeURIComponent(id)+'/messages')).json();if(!current()||requestId!==selection)return;chatRuntime.sessionId=id;if(awayAt!==null)saveChatResume(owner,id,awayAt);chatRuntime.messages=data;drawMessages();drawSidebar();if(mobileQuery.matches)setSidebar(false,true);}
    catch(e){if(current())error.textContent=e.message;}
  }
  let selection=0;
  container.querySelector('#chat-new').onclick=()=>{if(chatRuntime.busy)return;++selection;chatRuntime.sessionId=null;clearChatResume(owner);chatRuntime.messages=[];error.textContent='';input.value='';drawMessages();drawSidebar();if(mobileQuery.matches)setSidebar(false);input.focus();};
  container.querySelector('#chat-new-shortcut').onclick=()=>container.querySelector('#chat-new').click();
  container.querySelector('#chat-stop').onclick=()=>chatRuntime.controller?.abort();
  input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();container.querySelector('#chat-form').requestSubmit();}});
  container.querySelector('#chat-form').onsubmit=async event=>{
    event.preventDefault();const prompt=input.value.trim();if(!prompt||chatRuntime.busy)return;
    ++selection;chatRuntime.busy=true;error.textContent='';controls();
    let submitted=false,assistant=null,bubble=null,paintFrame=null;
    const paintAnswer=()=>{
      if(paintFrame!==null)cancelAnimationFrame(paintFrame);
      paintFrame=null;
      if(!current()||!bubble||!assistant?.content.trim())return;
      const nearBottom=log.scrollHeight-log.scrollTop-log.clientHeight<100;
      renderChatText(bubble,assistant.content);
      if(nearBottom)log.scrollTop=log.scrollHeight;
    };
    const controller=new AbortController();chatRuntime.controller=controller;
    try {
      await syncAccountAssessments();if(!current())return;
      if(!chatRuntime.sessionId){const s=await(await api('',{method:'POST',body:'{}'})).json();if(!current())return;chatRuntime.sessionId=s.session_id;if(awayAt!==null)saveChatResume(owner,s.session_id,awayAt);sessions.unshift(s);drawSidebar();}
      log.querySelector('.chat-welcome')?.remove();
      const userMessage={role:'user',content:prompt};chatRuntime.messages.push(userMessage);setConversationMode();appendMessage(userMessage);input.value='';resizeInput();submitted=true;
      assistant = {role: 'assistant', content: ''};
      chatRuntime.messages.push(assistant);
      bubble = appendMessage(assistant);
      const thinking = document.createElement('span');
      thinking.className = 'chat-thinking';
      thinking.textContent = 'Đang suy nghĩ…';
      bubble.append(thinking);
      log.scrollTop = log.scrollHeight;
      const r=await api('/'+encodeURIComponent(chatRuntime.sessionId)+'/messages/stream',{method:'POST',body:JSON.stringify({prompt,target_year:Number(container.querySelector('#chat-year').value)}),signal:controller.signal});
      const reader=r.body.getReader(),decoder=new TextDecoder();let buffer='',doneSignal=false;
      const onAsk=setDraft;
      const consume=block=>{
        for(const line of block.split('\n')){
          if(!line.startsWith('data: '))continue;const payload=line.slice(6).trim();if(payload==='[DONE]'){doneSignal=true;continue;}
          try {
            const item=JSON.parse(payload);
            if(item.type==='portfolio'&&item.data){
              assistant.portfolio=item.data;
              try {
                if(!bubble.parentElement.querySelector('.chat-portfolio-widget')){
                  const widget=createPortfolioWidget(item.data,onAsk);
                  if(widget)bubble.parentElement.append(widget);
                }
              }catch(wErr){console.warn('Portfolio widget render error:', wErr);}
            }
            if(item.type==='token'&&item.token){
              assistant.content+=item.token;
              if(paintFrame===null)paintFrame=requestAnimationFrame(paintAnswer);
            }
          }catch(jsonErr){
            console.warn('Malformed SSE line in stream:', jsonErr);
          }
        }
      };
      while(true){const chunk=await reader.read();if(!current()){await reader.cancel();return;}buffer+=decoder.decode(chunk.value||new Uint8Array(),{stream:!chunk.done});const blocks=buffer.replace(/\r\n/g,'\n').split('\n\n');buffer=blocks.pop();blocks.forEach(consume);if(chunk.done)break;}
      if(buffer.trim())consume(buffer);
      paintAnswer();
      if (!assistant.content.trim()) {
        if (!doneSignal) throw new Error('Kết nối bị gián đoạn. Bạn có thể gửi lại câu hỏi.');
        bubble.textContent = 'Chưa nhận được phản hồi. Vui lòng thử lại.';
      }
      await refreshSessions();
    }catch(e){
      paintAnswer();
      if (current()) {
        const stopped = e.name === 'AbortError';
        error.textContent = stopped ? 'Đã dừng phản hồi.' : e.message;
        if (!submitted) input.value = prompt;
        if (bubble && !assistant.content.trim()) {
          bubble.textContent = stopped ? 'Đã dừng phản hồi.' : 'Chưa nhận được phản hồi.';
        }
      }
    }finally{if(paintFrame!==null)cancelAnimationFrame(paintFrame);if(current()){chatRuntime.busy=false;controls();resizeInput();input.focus();}if(chatRuntime.controller===controller)chatRuntime.controller=null;}
  };
  drawMessages();
  const resumeSelection=selection;
  try {await refreshSessions();if(current()&&selection===resumeSelection&&resumeId&&sessions.some(s=>s.session_id===resumeId))await openSession(resumeId);}
  catch(e){if(current()){container.querySelector('#chat-sessions').textContent='Không tải được lịch sử.';error.textContent=e.message;}}
  if(current()&&param){let prompt;try{prompt=decodeURIComponent(param);}catch(_){prompt=param;}history.replaceState(null,'','#tu-van');++selection;chatRuntime.sessionId=null;chatRuntime.messages=[];drawMessages();setDraft(prompt);container.querySelector('#chat-form').requestSubmit();}
}


// --- BOOTSTRAP ---
window.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initMobileMenu();
  initDetailModal();
  await loadAllData();
  await initAuth();
  await loadAccountAssessments();

  window.addEventListener('hashchange', renderRoute);
  renderRoute();
});

// Guided student intake after login. Values are loaded from the authenticated account.
async function renderIntake(container) {
  if (!state.authToken || !state.currentUser) { window.location.hash = '#dang-nhap'; return; }
  if (state.currentUser.role === 'admin') { window.location.hash = '#quan-tri'; return; }
  const owner = state.currentUser.user_id;
  container.innerHTML = '<p class="p-10 text-center text-muted">Đang tải hồ sơ của bạn...</p>';
  const request = async (path, body) => {
    const response = await fetch(`/api/v1/students/${path}`, {
      method: body === undefined ? 'GET' : 'PUT',
      headers: { Authorization: `Bearer ${state.authToken}`, 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Không thể lưu hồ sơ. Vui lòng kiểm tra thông tin và thử lại.');
    return data;
  };
  let profile;
  try { profile = await request('profile'); }
  catch (error) {
    container.innerHTML = '<div class="max-w-xl mx-auto p-8"><p id="intake-load-error" role="alert"></p><button id="intake-retry" class="mt-4 px-5 py-3 rounded-xl bg-navy text-paper">Thử lại</button></div>';
    container.querySelector('#intake-load-error').textContent = error.message;
    container.querySelector('#intake-retry').onclick = () => renderIntake(container);
    return;
  }
  if (window.location.hash !== '#thiet-lap-ho-so' || state.currentUser?.user_id !== owner) return;
  let step = 0;
  const labels = ['Cá nhân & Quê quán', 'Học bạ & Điểm thi', 'Tài chính & Thể lực'];
  const escape = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const field = (key, title, value, type = 'text', attrs = '') => `<label class="block text-sm font-medium text-navy">${title}<input name="${key}" type="${type}" value="${escape(value)}" ${attrs} class="mt-2 w-full px-4 py-3 rounded-[14px] border border-line bg-mist text-ink focus:outline-none focus:ring-2 focus:ring-azure"></label>`;
  function finish() {
    const b = profile.background || {}, a = profile.academic || {}, h = profile.health || {};
    const scores = a.subject_scores || {};
    state.studentProfile = {
      fullName: `${profile.last_name || ''} ${profile.first_name || ''}`.trim(), schoolName: profile.current_school,
      province: b.hometown_province, priorityZone: b.priority_zone, gpa5Semesters: a.gpa_5_semesters,
      conduct12: a.conduct_grade_12, scores: {math:scores['Toán'], physics:scores['Vật lý'], chemistry:scores['Hóa học'], english:scores['Tiếng Anh'], literature:scores['Ngữ văn'], biology:scores['Sinh học']},
      ielts:a.ielts_score, dgnlHcm:a.dgnl_hcm_score, annualBudget:b.max_annual_tuition,
      heightCm:h.height_cm, weightKg:h.weight_kg, eyesightDiop:h.eye_degree_left,
    };
    localStorage.setItem('fyf_student_profile', JSON.stringify(state.studentProfile));
    const pending = sessionStorage.getItem('fyf_after_login');
    sessionStorage.removeItem('fyf_after_login');
    window.location.hash = pending && /^#trac-nghiem\/[a-z0-9_-]+$/i.test(pending) ? pending : '#trac-nghiem';
  }
  function draw() {
    const b = profile.background || {}, a = profile.academic || {}, h = profile.health || {};
    let fields;
    if (step === 0) fields = field('last_name','Họ và tên đệm *',profile.last_name,'text','required maxlength="100"') + field('first_name','Tên *',profile.first_name,'text','required maxlength="100"') + field('current_school','Trường THPT *',profile.current_school,'text','required maxlength="255"') + field('hometown_province','Tỉnh / Thành phố quê quán *',b.hometown_province,'text','required maxlength="100"') + `<label class="block text-sm font-medium text-navy">Khu vực ưu tiên<select name="priority_zone" class="mt-2 w-full px-4 py-3 rounded-[14px] border border-line bg-mist">${['KV1','KV2-NT','KV2','KV3'].map(z=>`<option ${b.priority_zone===z?'selected':''}>${z}</option>`).join('')}</select></label>`;
    if (step === 1) fields = field('gpa_5_semesters','Điểm trung bình học bạ 5 học kỳ *',a.gpa_5_semesters,'number','required min="0" max="10" step="any"') + `<label class="block text-sm font-medium text-navy">Hạnh kiểm lớp 12<select name="conduct_grade_12" class="mt-2 w-full px-4 py-3 rounded-[14px] border border-line bg-mist">${['Tốt','Khá','Trung bình'].map(v=>`<option ${a.conduct_grade_12===v?'selected':''}>${v}</option>`).join('')}</select></label>` + ['Toán','Vật lý','Hóa học','Tiếng Anh','Ngữ văn','Sinh học','Lịch sử','Địa lý'].map((v,i)=>field(`score_${i}`,`Điểm thi ${v}`,a.subject_scores?.[v],'number','min="0" max="10" step="any"')).join('') + field('ielts_score','IELTS (nếu có)',a.ielts_score,'number','min="0" max="9" step="0.5"') + field('dgnl_hcm_score','ĐGNL ĐHQG TP.HCM (nếu có)',a.dgnl_hcm_score,'number','min="0" max="1200" step="1"');
    if (step === 2) fields = field('max_annual_tuition','Ngân sách học phí tối đa (đồng/năm)',b.max_annual_tuition,'number','min="0" step="1"') + field('height_cm','Chiều cao (cm)',h.height_cm,'number','min="100" max="250" step="any"') + field('weight_kg','Cân nặng (kg)',h.weight_kg,'number','min="30" max="200" step="any"') + field('eye_degree_left','Độ cận mắt trái (Diop)',h.eye_degree_left,'number','min="0" max="20" step="any"') + field('eye_degree_right','Độ cận mắt phải (Diop)',h.eye_degree_right,'number','min="0" max="20" step="any"');
    container.innerHTML = `<div class="hero-wash border-b border-line"><div class="max-w-3xl mx-auto px-4 py-10"><p class="text-sm text-azure font-semibold">Chuẩn bị hành trình hướng nghiệp</p><h1 class="font-display text-3xl font-bold text-navy mt-2">Hãy cho chúng tôi hiểu thêm về bạn</h1><p class="mt-3 text-muted">Hoàn thiện hồ sơ trước khi khám phá bản thân qua các bài trắc nghiệm.</p><ol class="mt-6 grid gap-3 sm:grid-cols-3">${labels.map((v,i)=>`<li class="p-3 rounded-xl border ${i===step?'bg-navy text-paper border-navy':'bg-card text-muted border-line'}" ${i===step?'aria-current="step"':''}>${i<step?'✓':i+1}. ${v}</li>`).join('')}</ol></div></div><div class="max-w-3xl mx-auto px-4 py-8"><form id="intake-form" class="rounded-[24px] border border-line bg-card p-6 sm:p-8 shadow-border"><p class="text-xs font-semibold text-azure">Bước ${step+1} / 3${step===2?' · Không bắt buộc':''}</p><h2 class="text-xl font-bold text-navy mt-2 mb-3">${labels[step]}</h2><p class="text-sm text-muted mb-6">${step===0?'Thông tin có dấu * là bắt buộc.':step===1?'Nhập học bạ của bạn. Điểm thi và chứng chỉ chưa có có thể để trống.':'Bạn có thể để trống từng mục hoặc bỏ qua bước này và bổ sung sau trong hồ sơ.'}</p><div class="grid gap-5 sm:grid-cols-2">${fields}</div><p id="intake-error" role="alert" class="text-sm text-rose-600 mt-4"></p><div class="mt-6 pt-5 border-t border-line flex flex-wrap gap-3">${step>0?'<button type="button" id="intake-back" class="px-5 py-3 rounded-xl border border-line text-navy">Quay lại</button>':''}${step===2?'<button type="button" id="intake-skip" class="px-5 py-3 rounded-xl border border-line text-azure">Bỏ qua và làm trắc nghiệm</button>':''}<button type="submit" class="px-5 py-3 rounded-xl bg-navy text-paper font-semibold sm:ml-auto">${step===2?'Lưu và làm trắc nghiệm':'Lưu và tiếp tục'}</button></div></form></div>`;
    window.scrollTo({top:0,behavior:'instant'});
    const form = container.querySelector('#intake-form');
    const values = () => Object.fromEntries([...new FormData(form)].map(([k,v])=>[k, v.trim()]));
    const remember = (v) => {
      if (step===0) { Object.assign(profile,{first_name:v.first_name,last_name:v.last_name,current_school:v.current_school}); Object.assign(profile.background,{hometown_province:v.hometown_province,priority_zone:v.priority_zone}); }
      if (step===1) Object.assign(profile.academic, academicBody(v));
      if (step===2) { profile.background.max_annual_tuition=num(v.max_annual_tuition); Object.assign(profile.health,healthBody(v)); }
    };
    container.querySelector('#intake-back')?.addEventListener('click',()=>{remember(values());step--;draw();});
    container.querySelector('#intake-skip')?.addEventListener('click',finish);
    form.addEventListener('submit',async event=>{
      event.preventDefault();
      const v=values();
      if (step===0 && ['first_name','last_name','current_school','hometown_province'].some(k=>!v[k])) { container.querySelector('#intake-error').textContent='Vui lòng điền đầy đủ thông tin bắt buộc.';return; }
      form.querySelectorAll('button').forEach(b=>b.disabled=true);
      try {
        if (step===0) {
          profile=await request('profile',{first_name:v.first_name,last_name:v.last_name,current_school:v.current_school});
          profile=await request('background',{hometown_province:v.hometown_province,priority_zone:v.priority_zone});
        } else if (step===1) profile=await request('academic',academicBody(v));
        else {
          profile=await request('background',{max_annual_tuition:num(v.max_annual_tuition)});
          profile=await request('health',healthBody(v));
        }
        if (window.location.hash !== '#thiet-lap-ho-so' || state.currentUser?.user_id !== owner) return;
        if (step===2) finish(); else { step++; draw(); }
      } catch(error) {
        container.querySelector('#intake-error').textContent=error.message;
        form.querySelectorAll('button').forEach(b=>b.disabled=false);
      }
    });
  }
  const num = v => v==='' ? null : Number(v);
  const academicBody = v => ({gpa_5_semesters:num(v.gpa_5_semesters),conduct_grade_12:v.conduct_grade_12,ielts_score:num(v.ielts_score),dgnl_hcm_score:num(v.dgnl_hcm_score),subject_scores:Object.fromEntries(['Toán','Vật lý','Hóa học','Tiếng Anh','Ngữ văn','Sinh học','Lịch sử','Địa lý'].flatMap((name,i)=>v[`score_${i}`]===''?[]:[[name,Number(v[`score_${i}`])]]))});
  const healthBody = v => Object.fromEntries(['height_cm','weight_kg','eye_degree_left','eye_degree_right'].map(k=>[k,num(v[k])]));
  draw();
}


async function syncAccountAssessments() {
  const owner = state.currentUser?.user_id, token = state.authToken;
  if (!owner || !token) throw new Error('Vui lòng đăng nhập để lưu kết quả trắc nghiệm.');
  const key = `fyf_pending_assessments_${owner}`;
  const queued = JSON.parse(localStorage.getItem(key) || '{}');
  for (const [id, result] of Object.entries(queued)) {
    if (state.currentUser?.user_id !== owner || state.authToken !== token) throw new Error('Phiên đăng nhập đã thay đổi.');
    const cognitive = id === 'cognitive';
    const body = cognitive ? {
      test_type:'INTERNAL', total_score:result.totalScore, max_scale:30,
      quant_score:result.numericalScore, verbal_score:result.verbalScore, logic_score:result.figuralScore,
    } : {
      test_type:id.toUpperCase(), result_code:result.code || result.type || 'BIGFIVE',
      scores_detail:result, top_traits:result.sorted?.slice(0,3).map(v=>v[0]) || [],
    };
    const response = await fetch(`/api/v1/assessments/${cognitive ? 'competency' : 'personality'}`, {
      method:'POST', headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`}, body:JSON.stringify(body),
    });
    if (!response.ok) throw new Error('Chưa đồng bộ được kết quả trắc nghiệm. Vui lòng thử lại trước khi tư vấn.');
    const latestQueue = JSON.parse(localStorage.getItem(key) || '{}');
    if (JSON.stringify(latestQueue[id]) === JSON.stringify(result)) delete latestQueue[id];
    localStorage.setItem(key, JSON.stringify(latestQueue));
  }
}

async function loadAccountAssessments() {
  state.results = {mbti:null, riasec:null, bigfive:null, cognitive:null};
  for (const id of Object.keys(state.results)) localStorage.removeItem(`fyf_result_${id}`);
  const owner = state.currentUser?.user_id, token = state.authToken;
  if (!owner || !token) return;
  try {
    const response = await fetch('/api/v1/assessments/personality/latest', {headers:{Authorization:`Bearer ${token}`}});
    if (!response.ok) return;
    const data = await response.json();
    if (state.currentUser?.user_id !== owner || state.authToken !== token) return;
    for (const [type, item] of Object.entries(data)) {
      const id = type.toLowerCase();
      if (['riasec','mbti','bigfive'].includes(id)) {
        state.results[id] = { ...item.scores_detail, quizId:id, completedAt:item.completed_at,
          ...(id==='riasec'?{code:item.result_code}:id==='mbti'?{type:item.result_code}:{}) };
      }
    }
    const pending = JSON.parse(localStorage.getItem(`fyf_pending_assessments_${owner}`) || '{}');
    Object.assign(state.results, pending);
    for (const [id, result] of Object.entries(state.results)) if (result) localStorage.setItem(`fyf_result_${id}`,JSON.stringify(result));
  } catch (_) { /* Leave results empty instead of showing another account's cached results. */ }
}
