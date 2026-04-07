async function getErrorMessage(response, fallbackMessage) {
  try {
    const data = await response.json();
    return data.detail || data.message || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export async function loginUser(email, password) {
  const resp = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Login failed"));
  return resp.json();
}

export async function registerUser({ email, password, full_name, phone }) {
  const resp = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name, phone }),
  });
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Register failed"));
  return resp.json();
}

export async function fetchMe(token) {
  const resp = await fetch("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Failed to fetch user"));
  return resp.json();
}

export async function fetchPopularRecommendations() {
  const resp = await fetch("/recommendation/recommendations/popular?limit=6");
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Failed to load popular recommendations"));
  return resp.json();
}

export async function fetchTrendingSearches() {
  const resp = await fetch("/productsearch/search/trending?limit=8");
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Failed to load trending searches"));
  return resp.json();
}

export async function fetchSearchHistory(token) {
  const resp = await fetch("/productsearch/search/history?limit=8", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error(await getErrorMessage(resp, "Failed to load search history"));
  return resp.json();
}

export async function searchProducts(query, token) {
  const resp = await fetch(
    `/productsearch/search?q=${encodeURIComponent(query)}&limit=12&threshold=0.1`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!resp.ok) {
    if (resp.status === 401) throw Object.assign(new Error("Session expired. Please login again."), { status: 401 });
    throw new Error(await getErrorMessage(resp, "Search failed"));
  }
  return resp.json();
}