/* Minimal translation layer. English is written in index.html, so the page reads fine before any script runs. */
import en from '../i18n/en.js';
import languages from '../i18n/languages.js';
import drafts from '../i18n/drafts.js';

let dict = en;
export const listeners = new Set();

/** Look up a ui string by dotted path, e.g. t('why.split', {dur: '1 h'}). */
export function t(path, vars = {}) {
  const get = (d) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), d.ui);
  let s = get(dict) ?? get(en) ?? path;
  return s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
}

const isDraft = (code) => !languages.some((l) => l.code === code) && drafts.some((l) => l.code === code);

export async function setLanguage(code) {
  if (!languages.some((l) => l.code === code) && !isDraft(code)) code = 'en';
  try { dict = code === 'en' ? en : (await import(`../i18n/${code}.js`)).default; } catch { dict = en; code = 'en'; }
  document.documentElement.lang = code;
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const v = dict.page?.[el.dataset.i18n] ?? en.page[el.dataset.i18n];
    if (v != null) el.innerHTML = v;
  });
  // Drafts are preview-only: never remembered, always flagged.
  if (!isDraft(code)) { try { localStorage.setItem('lang', code); } catch {} }
  draftBanner(isDraft(code));
  listeners.forEach((fn) => fn(code));
}

/** Builds the language picker (only when more than one language exists) and applies the saved choice. */
export function initLanguage(mount) {
  let saved = new URLSearchParams(location.search).get('lang');
  if (!saved) { try { saved = localStorage.getItem('lang'); } catch {} }
  if (languages.length > 1 && mount) {
    const sel = document.createElement('select');
    sel.id = 'lang';
    sel.setAttribute('aria-label', 'Language');
    sel.className = 'lang';
    languages.forEach((l) => sel.add(new Option(l.name, l.code)));
    sel.value = saved || 'en';
    sel.addEventListener('change', () => setLanguage(sel.value));
    mount.appendChild(sel);
  }
  if (saved && saved !== 'en') setLanguage(saved);
}

/** A banner on draft (unreviewed) translations, with a way back to English. */
function draftBanner(on) {
  let b = document.getElementById('draftbar');
  if (!on) { b?.remove(); return; }
  if (!b) {
    b = document.createElement('div');
    b.id = 'draftbar';
    b.className = 'draftbar';
    b.setAttribute('role', 'note');
    document.body.prepend(b);
  }
  b.innerHTML = `${t('draft')} <a href="?lang=en">${t('draftEn')}</a>`;
}
