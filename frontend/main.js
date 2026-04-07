const app = document.getElementById("app");

let token = localStorage.getItem("token");
let user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : null;
let mode = "login";

function fireAndForgetInteraction(endpoint, body) {
  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).catch((error) => {
    console.error(`Interaction tracking error (${endpoint}):`, error);
  });
}

function renderProductDetail(product) {
  app.innerHTML = `
    <div id="product-detail">
      <button id="back-to-search">← Back to Search</button>
      <div style="border: 1px solid #ddd; padding: 20px; margin-top: 20px;">
        ${product.image_url ? `<img src="${product.image_url}" style="max-width: 200px; height: auto; margin-bottom: 15px;" alt="${product.name}">` : ""}
        <h2>${product.name}</h2>
        <p><strong>Author:</strong> ${product.author || "Unknown"}</p>
        <p><strong>Category:</strong> ${product.category || "N/A"}</p>
        <p><strong>Description:</strong> ${product.description || "No description available"}</p>
        <h3>Price: $${(product.price || 0).toFixed(2)}</h3>
      </div>
    </div>
  `;

  // Fire-and-forget product visit tracking
  if (user && user.user_id) {
    fireAndForgetInteraction("/interaction/product-visit", {
      user_id: user.user_id,
      product_id: product.id
    });
  }

  document.getElementById("back-to-search").addEventListener("click", () => {
    renderSearchPage();
  });
}

function renderSearchPage(searchResults = null) {
  app.innerHTML = `
    <div id="search-page">
      <button id="logout-from-search">Logout</button>
      <p>Logged in as ${user && user.email ? user.email : ""}</p>
      <h1>Search Books</h1>
      <form id="search-form" style="margin-bottom: 20px;">
        <input id="search-query" type="text" placeholder="Search for books..." required style="padding: 8px; width: 300px;" />
        <button type="submit" style="padding: 8px 16px;">Search</button>
      </form>
      <div id="search-results"></div>
    </div>
  `;

  document.getElementById("logout-from-search").addEventListener("click", () => {
    token = null;
    user = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    renderAuth();
  });

  document.getElementById("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("search-query").value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById("search-results");
    resultsDiv.innerHTML = "<p>Loading...</p>";

    try {
      const resp = await fetch(`/productsearch/search?q=${encodeURIComponent(query)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!resp.ok) {
        throw new Error("Search failed");
      }

      const data = await resp.json();
      const results = data.results || [];

      // Fire-and-forget search tracking
      if (user && user.user_id) {
        fireAndForgetInteraction("/interaction/search", {
          user_id: user.user_id,
          searched_keyword: query.trim().toLowerCase()
        });
      }

      if (results.length === 0) {
        resultsDiv.innerHTML = "<p>No results found.</p>";
        return;
      }

      resultsDiv.innerHTML = results.map((product) => `
        <div class="product-card" style="border: 1px solid #ccc; padding: 15px; margin-bottom: 10px; cursor: pointer; background-color: #f9f9f9;" data-product-id="${product.id}">
          ${product.image_url ? `<img src="${product.image_url}" style="max-width: 100px; height: auto; margin-right: 15px; float: left;" alt="${product.name}">` : ""}
          <h3 style="margin: 0 0 5px 0;">${product.name}</h3>
          <p style="margin: 3px 0;"><strong>Author:</strong> ${product.author || "Unknown"}</p>
          <p style="margin: 3px 0;"><strong>Price:</strong> $${(product.price || 0).toFixed(2)}</p>
          <div style="clear: both;"></div>
        </div>
      `).join("");

      // Attach click handlers to product cards
      document.querySelectorAll(".product-card").forEach((card) => {
        card.addEventListener("click", () => {
          const productId = parseInt(card.getAttribute("data-product-id"), 10);
          const product = results.find((p) => p.id === productId);
          if (product) {
            renderProductDetail(product);
          }
        });
      });
    } catch (error) {
      resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
  });

  // If search results were passed in, display them
  if (searchResults) {
    document.getElementById("search-query").value = searchResults.query;
  }
}

function renderWelcome() {
  renderSearchPage();
}

function renderAuth() {
  const isLogin = mode === "login";
  app.innerHTML = `
    <div>
      <h2>${isLogin ? "Login" : "Register"}</h2>
      <form id="auth-form">
        ${!isLogin ? '<input id="full_name" placeholder="Full name" required />' : ""}
        ${!isLogin ? '<input id="phone" placeholder="Phone" required />' : ""}
        <input id="email" type="email" placeholder="Email" required />
        <input id="password" type="password" placeholder="Password" required />
        <button type="submit">${isLogin ? "Login" : "Register"}</button>
      </form>
      <button id="switch-mode">Switch to ${isLogin ? "Register" : "Login"}</button>
      <p id="message"></p>
    </div>
  `;

  document.getElementById("switch-mode").addEventListener("click", () => {
    mode = isLogin ? "register" : "login";
    renderAuth();
  });

  document.getElementById("auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = document.getElementById("message");
    message.textContent = "";

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
      if (isLogin) {
        const loginResp = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        if (!loginResp.ok) {
          const err = await loginResp.json().catch(() => ({ detail: "Login failed" }));
          throw new Error(err.detail || "Login failed");
        }

        const loginData = await loginResp.json();
        token = loginData.access_token;
        localStorage.setItem("token", token);

        const meResp = await fetch("/auth/me", {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (!meResp.ok) {
          throw new Error("Could not load profile");
        }

        user = await meResp.json();
        localStorage.setItem("user", JSON.stringify(user));
        renderWelcome();
      } else {
        const full_name = document.getElementById("full_name").value.trim();
        const phone = document.getElementById("phone").value.trim();

        const registerResp = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name, phone })
        });

        if (!registerResp.ok) {
          const err = await registerResp.json().catch(() => ({ detail: "Register failed" }));
          throw new Error(err.detail || "Register failed");
        }

        message.textContent = "Registration successful. Please login.";
        mode = "login";
        setTimeout(renderAuth, 500);
      }
    } catch (error) {
      message.textContent = error.message;
    }
  });
}

if (token && user) {
  renderWelcome();
} else {
  renderAuth();
}
