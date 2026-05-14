// ── Theme ─────────────────────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('eklase-theme', theme);
  if (typeof Chart !== 'undefined') {
    const dark = theme === 'dark';
    Chart.defaults.color       = dark ? '#71717a' : '#737373';
    Chart.defaults.borderColor = dark ? '#2e2e33' : '#e5e5e5';
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// ── i18n ──────────────────────────────────────────────────────────────────
const I18N = {
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.grades': 'All Grades',
    'nav.subjects': 'By Subjects',
    'nav.calculator': 'Calculator',
    'nav.ai': 'AI Recommendations',
    'nav.subtitle': 'Grade Analytics',
    'topbar.refresh': 'Refresh',
    'topbar.updated': 'Updated:',
    'topbar.logout': 'Logout',
    'page.dashboard': 'Dashboard',
    'page.grades': 'All Grades',
    'page.subjects': 'Subject Analysis',
    'page.calculator': 'Grade Calculator',
    'page.ai': 'AI Recommendations',
    'dash.overall_avg': 'Overall Average',
    'dash.all_subjects': 'across all subjects',
    'dash.grades_received': 'Grades Received',
    'dash.full_period': 'for the entire period',
    'dash.best_subject': 'Best Subject',
    'dash.weak_subjects': 'Weak Subjects',
    'dash.below': 'below',
    'dash.weekly_trend': 'Weekly Average Trend',
    'dash.subject_avg': 'Average by Subject',
    'dash.recent_grades': 'Recent Grades',
    'dash.no_grades': 'No grades yet',
    'dash.load_grades': 'Click «Refresh» to load grades from e-klase.lv',
    'col.grade': 'Grade',
    'col.subject': 'Subject',
    'col.work_type': 'Work Type',
    'col.topic': 'Topic',
    'col.date': 'Date',
    'col.appeared': 'Added',
    'col.type': 'Type',
    'col.lesson_topic': 'Lesson Topic',
    'col.work_date': 'Work Date',
    'col.grade_abbr': 'Gr.',
    'grades.newest_first': 'sorted: newest first',
    'grades.no_grades': 'No grades yet',
    'grades.load_grades': 'Click «Refresh» at the top to load grades from e-klase.lv',
    'subjects.weak_label': 'Weak subjects (average < ',
    'subjects.breakdown': 'Breakdown by Work Types',
    'subjects.recent_grades': 'Recent Grades',
    'subjects.no_data_types': 'No data on work types.',
    'subjects.no_data': 'No subject data',
    'subjects.load': 'Click «Refresh» to load grades.',
    'subjects.no_ratings': 'no grades',
    'subjects.weak_badge': 'Weak',
    'subjects.grades_abbr': 'gr.',
    'calc.description': 'Choose a subject, specify the desired final grade and how many works remain — the system will calculate the average you need to achieve.',
    'calc.subject': 'Subject',
    'calc.choose_subject': '— choose subject —',
    'calc.desired_avg': 'Desired Grade',
    'calc.remaining': 'Remaining Works',
    'calc.calculate': 'Calculate',
    'calc.current_avgs': 'Current Averages',
    'calc.avg_col': 'Average',
    'calc.grades_col': 'Grades',
    'calc.needed_avg': 'required average',
    'calc.current_avg_label': 'Current average:',
    'calc.desired': 'Desired:',
    'calc.remaining_works': 'Works left:',
    'calc.impossible': 'Impossible',
    'calc.achieved': 'Already achieved',
    'calc.scenarios': 'Scenario Table',
    'calc.works_col': 'Works',
    'calc.needed_col': 'Required Average',
    'calc.achievable_col': 'Achievable?',
    'calc.choose_params': 'Choose subject and parameters',
    'calc.result_here': 'Calculation result will appear here.',
    'ai.subtitle': 'Claude AI finds theory resources for the specific topics you have studied, prioritising topics with lower grades. Cache is refreshed every 7 days.',
    'ai.refresh': 'Refresh',
    'ai.open': 'Open →',
    'ai.no_data': 'No data',
    'ai.no_grades': 'Load your grades first, then AI can find theory resources.',
    'ai.no_rec': 'Click «Refresh» to get recommendations.',
    'ai.topics_count': 'topics',
    'ai.studied_topics': 'Studied topics:',
    'login.subtitle': 'Grade Analytics',
    'login.username': 'e-klase Login',
    'login.password': 'Password',
    'login.profile_id': 'Profile ID',
    'login.optional': '(optional)',
    'login.placeholder': 'Leave empty for auto-selection',
    'login.submit': 'Login via e-klase.lv',
    'login.note': 'Authorization via Keycloak OIDC. Credentials are not stored in plain text.',
    'empty.no_grades': 'No grades yet',
    'empty.load': 'Click «Refresh» to load grades from e-klase.lv',
    'empty.load_top': 'Click «Refresh» at the top to load grades from e-klase.lv',
    'empty.no_ai': 'No data',
    'empty.ai_load': 'First load your grades, then AI can select materials.',
  },
  lv: {
    'nav.dashboard': 'Panelis',
    'nav.grades': 'Visas atzīmes',
    'nav.subjects': 'Pa priekšmetiem',
    'nav.calculator': 'Kalkulators',
    'nav.ai': 'AI Ieteikumi',
    'nav.subtitle': 'Atzīmju analītika',
    'topbar.refresh': 'Atjaunot',
    'topbar.updated': 'Atjaunots:',
    'topbar.logout': 'Iziet',
    'page.dashboard': 'Panelis',
    'page.grades': 'Visas atzīmes',
    'page.subjects': 'Priekšmetu analīze',
    'page.calculator': 'Atzīmju kalkulators',
    'page.ai': 'AI Ieteikumi',
    'dash.overall_avg': 'Kopējais vidējais',
    'dash.all_subjects': 'pa visiem priekšmetiem',
    'dash.grades_received': 'Saņemtās atzīmes',
    'dash.full_period': 'par visu periodu',
    'dash.best_subject': 'Labākais priekšmets',
    'dash.weak_subjects': 'Vāji priekšmeti',
    'dash.below': 'zem',
    'dash.weekly_trend': 'Vidējais pa nedēļām',
    'dash.subject_avg': 'Vidējais pa priekšmetiem',
    'dash.recent_grades': 'Pēdējās atzīmes',
    'dash.no_grades': 'Atzīmju vēl nav',
    'dash.load_grades': 'Spiediet «Atjaunot», lai ielādētu atzīmes no e-klase.lv',
    'col.grade': 'Atzīme',
    'col.subject': 'Priekšmets',
    'col.work_type': 'Darba veids',
    'col.topic': 'Tēma',
    'col.date': 'Datums',
    'col.appeared': 'Pievienota',
    'col.type': 'Veids',
    'col.lesson_topic': 'Stundas tēma',
    'col.work_date': 'Darba datums',
    'col.grade_abbr': 'atk.',
    'grades.newest_first': 'kārtots: jaunākais vispirms',
    'grades.no_grades': 'Atzīmju vēl nav',
    'grades.load_grades': 'Spiediet «Atjaunot» augšpusē, lai ielādētu atzīmes',
    'subjects.weak_label': 'Vāji priekšmeti (vidējais < ',
    'subjects.breakdown': 'Sadalījums pa darbu veidiem',
    'subjects.recent_grades': 'Pēdējās atzīmes',
    'subjects.no_data_types': 'Nav datu par darbu veidiem.',
    'subjects.no_data': 'Nav priekšmetu datu',
    'subjects.load': 'Spiediet «Atjaunot», lai ielādētu atzīmes.',
    'subjects.no_ratings': 'nav atzīmju',
    'subjects.weak_badge': 'Vājš',
    'subjects.grades_abbr': 'atk.',
    'calc.description': 'Izvēlieties priekšmetu, norādiet vēlamo gala atzīmi un cik darbu vēl atlikuši — sistēma aprēķinās nepieciešamo vidējo.',
    'calc.subject': 'Priekšmets',
    'calc.choose_subject': '— izvēlieties priekšmetu —',
    'calc.desired_avg': 'Vēlamā atzīme',
    'calc.remaining': 'Atlikušie darbi',
    'calc.calculate': 'Aprēķināt',
    'calc.current_avgs': 'Pašreizējie vidējie',
    'calc.avg_col': 'Vidējais',
    'calc.grades_col': 'Atzīmes',
    'calc.needed_avg': 'nepieciešamais vidējais',
    'calc.current_avg_label': 'Pašreizējais vidējais:',
    'calc.desired': 'Vēlamais:',
    'calc.remaining_works': 'Atlikušie darbi:',
    'calc.impossible': 'Neiespējami',
    'calc.achieved': 'Jau sasniegts',
    'calc.scenarios': 'Scenāriju tabula',
    'calc.works_col': 'Darbi',
    'calc.needed_col': 'Nepieciešamais vidējais',
    'calc.achievable_col': 'Sasniedzams?',
    'calc.choose_params': 'Izvēlieties priekšmetu un parametrus',
    'calc.result_here': 'Aprēķina rezultāts parādīsies šeit.',
    'ai.subtitle': 'Claude AI meklē teorijas resursus konkrētajām tēmām, kuras esi apguvis — prioritāte tēmām ar zemākām atzīmēm. Kešatmiņa atjaunojas ik 7 dienas.',
    'ai.refresh': 'Atjaunot',
    'ai.open': 'Atvērt →',
    'ai.no_data': 'Nav datu',
    'ai.no_grades': 'Vispirms ielādē atzīmes, tad AI varēs atrast teorijas resursus.',
    'ai.no_rec': 'Spiediet «Atjaunot», lai saņemtu ieteikumus.',
    'ai.topics_count': 'tēmas',
    'ai.studied_topics': 'Apgūtās tēmas:',
    'login.subtitle': 'Atzīmju analītika',
    'login.username': 'e-klase Lietotājvārds',
    'login.password': 'Parole',
    'login.profile_id': 'Profila ID',
    'login.optional': '(neobligāti)',
    'login.placeholder': 'Atstājiet tukšu automātiskajai izvēlei',
    'login.submit': 'Pieteikties ar e-klase.lv',
    'login.note': 'Autorizācija caur Keycloak OIDC. Parole netiek glabāta atklātā veidā.',
    'empty.no_grades': 'Atzīmju vēl nav',
    'empty.load': 'Spiediet «Atjaunot», lai ielādētu atzīmes no e-klase.lv',
    'empty.load_top': 'Spiediet «Atjaunot» augšpusē, lai ielādētu atzīmes',
    'empty.no_ai': 'Nav datu',
    'empty.ai_load': 'Vispirms ielādējiet atzīmes, tad AI varēs atlasīt materiālus.',
  }
};

let currentLang = localStorage.getItem('eklase-lang') || 'lv';

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || (I18N.lv[key]) || key;
}

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem('eklase-lang', lang);

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const val = I18N[lang] && I18N[lang][el.dataset.i18n];
    if (val !== undefined) el.textContent = val;
  });

  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const val = I18N[lang] && I18N[lang][el.dataset.i18nPh];
    if (val !== undefined) el.placeholder = val;
  });

  // Update native select option texts, then refresh custom select label
  document.querySelectorAll('option[data-i18n]').forEach(opt => {
    const val = I18N[lang] && I18N[lang][opt.dataset.i18n];
    if (val !== undefined) opt.textContent = val;
  });

  document.querySelectorAll('.custom-select-wrapper').forEach(wrapper => {
    const sel = wrapper.querySelector('select');
    const labelEl = wrapper.querySelector('.custom-select-label');
    if (sel && labelEl) {
      const chosen = sel.options[sel.selectedIndex];
      if (chosen) {
        labelEl.textContent = chosen.text;
        labelEl.style.color = chosen.value ? 'var(--text)' : 'var(--text-muted)';
      }
    }
  });

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}

function setLang(lang) { applyLang(lang); }

// ── Custom Select Dropdown ────────────────────────────────────────────────
function initCustomSelects() {
  document.querySelectorAll('select').forEach(select => {
    if (select.dataset.customInit) return;
    select.dataset.customInit = '1';

    const wrapper = document.createElement('div');
    wrapper.className = 'custom-select-wrapper';
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    select.style.display = 'none';

    const trigger = document.createElement('div');
    trigger.className = 'custom-select-trigger';
    trigger.setAttribute('role', 'combobox');
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('tabindex', '0');

    const labelEl = document.createElement('span');
    labelEl.className = 'custom-select-label';
    trigger.appendChild(labelEl);

    const arrowEl = document.createElement('span');
    arrowEl.className = 'custom-select-arrow';
    arrowEl.innerHTML = `<svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
      <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
    </svg>`;
    trigger.appendChild(arrowEl);
    wrapper.appendChild(trigger);

    const dropdown = document.createElement('div');
    dropdown.className = 'custom-select-dropdown';
    dropdown.setAttribute('role', 'listbox');

    const optsList = document.createElement('div');
    optsList.className = 'custom-select-options';
    dropdown.appendChild(optsList);
    wrapper.appendChild(dropdown);

    function renderOpts() {
      optsList.innerHTML = '';
      Array.from(select.options).forEach(opt => {
        const item = document.createElement('div');
        item.className = 'custom-select-option';
        if (!opt.value) item.classList.add('placeholder');
        if (opt.selected) item.classList.add('selected');
        item.textContent = opt.text;
        item.dataset.value = opt.value;
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', String(opt.selected));
        item.addEventListener('click', () => {
          select.value = opt.value;
          select.dispatchEvent(new Event('change'));
          updateLabel();
          closeDropdown();
        });
        optsList.appendChild(item);
      });
    }

    function updateLabel() {
      const chosen = select.options[select.selectedIndex];
      if (chosen) {
        labelEl.textContent = chosen.text;
        labelEl.style.color = chosen.value ? 'var(--text)' : 'var(--text-muted)';
      }
    }

    function openDropdown() {
      renderOpts();
      trigger.classList.add('open');
      dropdown.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
      trigger.classList.remove('open');
      dropdown.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', e => {
      e.stopPropagation();
      if (dropdown.classList.contains('open')) {
        closeDropdown();
      } else {
        document.querySelectorAll('.custom-select-dropdown.open').forEach(d => {
          d.classList.remove('open');
          d.previousElementSibling && d.previousElementSibling.classList.remove('open');
        });
        openDropdown();
      }
    });

    trigger.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger.click(); }
      else if (e.key === 'Escape') closeDropdown();
      else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const idx = select.selectedIndex;
        if (idx < select.options.length - 1) {
          select.selectedIndex = idx + 1;
          select.dispatchEvent(new Event('change'));
          updateLabel();
          if (dropdown.classList.contains('open')) renderOpts();
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const idx = select.selectedIndex;
        if (idx > 0) {
          select.selectedIndex = idx - 1;
          select.dispatchEvent(new Event('change'));
          updateLabel();
          if (dropdown.classList.contains('open')) renderOpts();
        }
      }
    });

    document.addEventListener('click', closeDropdown);
    dropdown.addEventListener('click', e => e.stopPropagation());

    updateLabel();
  });
}

// ── DOMContentLoaded ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Subject accordion — handled by toggleSubject() in subjects.html to allow lazy chart init

  // Mobile sidebar toggle
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.4s';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Calculator live preview / clamp
  const calcForm = document.querySelector('.calc-form');
  if (calcForm) {
    const desiredInput = calcForm.querySelector('[name="desired_avg"]');
    const remainingInput = calcForm.querySelector('[name="remaining_works"]');
    [desiredInput, remainingInput].forEach(el => {
      if (el) el.addEventListener('input', () => {
        if (desiredInput && parseFloat(desiredInput.value) > 10) desiredInput.value = 10;
        if (desiredInput && parseFloat(desiredInput.value) < 1) desiredInput.value = 1;
        if (remainingInput && parseInt(remainingInput.value) > 50) remainingInput.value = 50;
        if (remainingInput && parseInt(remainingInput.value) < 1) remainingInput.value = 1;
      });
    });
  }

  // Highlight active nav link
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath === href) {
      link.classList.add('active');
    } else if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    }
  });

  // Init custom selects
  initCustomSelects();

  // Apply saved language
  applyLang(currentLang);

  // Apply saved theme (chart defaults need DOM ready)
  applyTheme(localStorage.getItem('eklase-theme') || 'light');
});
