/* OrionStar KB — Shared JS for Product Catalog & AI Writer */
const API = '/api/v1/easywiki';
const AUTH_API = '/api/v1/auth';

let _token = localStorage.getItem('os_token');
let _user = null;
try { _user = JSON.parse(localStorage.getItem('os_user') || 'null'); } catch(e) {}

async function api(method, path, data) {
  const headers = { 'Content-Type': 'application/json' };
  if (_token) headers['Authorization'] = 'Bearer ' + _token;
  const opts = { method, headers };
  if (data) opts.body = JSON.stringify(data);
  const r = await fetch(path, opts);
  if (!r.ok) {
    if (r.status === 401) { logout(); throw new Error('Session expired'); }
    const d = await r.json().catch(() => ({}));
    throw new Error(d.detail || 'Request failed');
  }
  return r.json();
}

async function login(email, password) {
  const d = await fetch(AUTH_API + '/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  }).then(r => r.json());
  if (!d.token) throw new Error('Login failed');
  _token = d.token;
  _user = d.user;
  localStorage.setItem('os_token', _token);
  localStorage.setItem('os_user', JSON.stringify(_user));
  return _user;
}

function logout() {
  _token = null;
  _user = null;
  localStorage.removeItem('os_token');
  localStorage.removeItem('os_user');
}

function isLoggedIn() { return !!_token; }
function getUser() { return _user; }

// Product APIs
async function getProducts(filters) {
  const params = new URLSearchParams(filters || {});
  return api('GET', API + '/products?' + params);
}

async function searchProducts(q) {
  return api('GET', API + '/products/search?q=' + encodeURIComponent(q));
}

async function getProduct(key) {
  return api('GET', API + '/products/' + key);
}

async function seedProducts() {
  return api('POST', API + '/products/seed');
}

// AI APIs
async function getModels() { return api('GET', API + '/models'); }
async function getLanguages() { return api('GET', API + '/languages'); }
async function getTemplates() { return api('GET', API + '/templates'); }
async function getOutputs(limit) { return api('GET', API + '/outputs?limit=' + (limit || 20)); }

async function generateContent(params) {
  return api('POST', API + '/generate', params);
}
