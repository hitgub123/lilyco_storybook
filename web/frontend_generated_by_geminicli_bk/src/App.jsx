import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext'; // 导入 useAuth hook
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import NovelList from './pages/NovelList'; // 导入 NovelList

function App() {
  const { user, logout } = useAuth(); // 使用 useAuth hook

  return (
    <Router>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          {!user ? (
            <>
              <li>
                <Link to="/login">Login</Link>
              </li>
              <li>
                <Link to="/register">Register</Link>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link to="/novels">Novels</Link> {/* 添加 Novels 链接 */}
              </li>
              <li>
                <button onClick={logout}>Logout</button>
              </li>
            </>
          )}
        </ul>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/novels" element={<NovelList />} /> {/* 添加 NovelList 路由 */}
      </Routes>
    </Router>
  );
}

export default App;
