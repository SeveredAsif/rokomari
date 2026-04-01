const app = document.getElementById("app");

let token = localStorage.getItem("token");
let user = localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user")) : null;
let mode = "login";

function renderWelcome() {
  app.innerHTML = `
    <div>
      <p>Logged in${user && user.email ? ` as ${user.email}` : ""}</p>
      <h1>Welcome to Rokomari</h1>
      <button id="logout">Logout</button>
    </div>
  `;

  document.getElementById("logout").addEventListener("click", () => {
    token = null;
    user = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    renderAuth();
  });
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
