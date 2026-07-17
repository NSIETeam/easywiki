/** EasyWiki API client — unified fetch with JWT */
const BASE = "http://127.0.0.1:8080";

let _token: string | null = localStorage.getItem("ew_token");

export function getToken() {
  return _token;
}

export function setToken(t: string | null) {
  _token = t;
  if (t) localStorage.setItem("ew_token", t);
  else localStorage.removeItem("ew_token");
}

/** Fetch wrapper with JWT auth */
async function request<T = any>(method: string, path: string, body?: any): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;
  const res = await fetch(`${BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export { request };

// Auth
export const login = (email: string, password: string) =>
  request<{ token: string; user: any }>("POST", "/api/v1/auth/login", { email, password });

// Projects
export const listProjects = () =>
  request<{ projects: any[] }>("GET", "/api/v1/easywiki/projects");
export const createProject = (name: string) =>
  request<{ id: string; name: string }>("POST", "/api/v1/easywiki/projects", { name });
export const getManifest = (pid: string) =>
  request<any>("GET", `/api/v1/easywiki/projects/${pid}/manifest`);

// Pages
export const listPages = (pid: string, section: string) =>
  request<{ pages: any[] }>("GET", `/api/v1/easywiki/projects/${pid}/sections/${section}/pages`);
export const createPage = (pid: string, section: string, title: string, parentId: string | null = null) =>
  request<{ id: string }>("POST", `/api/v1/easywiki/projects/${pid}/sections/${section}/pages`, { title, parent_page_id: parentId });
export const getPage = (pageId: string) =>
  request<any>("GET", `/api/v1/easywiki/pages/${pageId}`);
export const updatePage = (pageId: string, doc: string, basedOnVersion?: string) =>
  request<any>("PUT", `/api/v1/easywiki/pages/${pageId}`, { blocksuite_doc: doc, based_on_version: basedOnVersion });

// Pending entries
export const listPending = (pid: string, status = "pending") =>
  request<{ entries: any[] }>("GET", `/api/v1/easywiki/projects/${pid}/pending-entries?status=${status}`);
export const approveEntry = (id: string, editedContent?: string) =>
  request<any>("POST", `/api/v1/easywiki/pending-entries/${id}/approve`, editedContent !== undefined ? { edited_content: editedContent } : {});
export const rejectEntry = (id: string, reason: string) =>
  request<any>("POST", `/api/v1/easywiki/pending-entries/${id}/reject`, { reason });
export const batchApprove = (ids: string[]) =>
  request<any>("POST", `/api/v1/easywiki/pending-entries/batch-approve`, { ids });

// Conflicts
export const listConflicts = (status = "open") =>
  request<{ conflicts: any[] }>("GET", `/api/v1/easywiki/conflicts?status=${status}`);
export const resolveConflict = (id: string, resolution: string, mergedContent?: string, note?: string) =>
  request<any>("POST", `/api/v1/easywiki/conflicts/${id}/resolve`, { resolution, merged_content: mergedContent, note });

// Versions
export const listVersions = (targetType: string, targetId: string) =>
  request<{ versions: any[] }>("GET", `/api/v1/easywiki/versions?target_type=${targetType}&target_id=${targetId}`);
