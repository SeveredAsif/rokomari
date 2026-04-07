import "./App.css";
import { useAuth } from "./hooks/useAuth";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";

export default function App() {
  const { token, user, login, logout } = useAuth();

  if (token && user) {
    return <HomePage user={user} token={token} onLogout={logout} />;
  }

  return <AuthPage onLogin={login} />;
}