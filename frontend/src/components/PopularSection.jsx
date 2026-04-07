export default function Header({ user }) {
  const logout = () => {
    localStorage.clear();
    window.location.href = "/";
  };

  return (
    <header className="header">
      <h2>Welcome {user?.full_name || user?.email}</h2>
      <button onClick={logout}>Logout</button>
    </header>
  );
}