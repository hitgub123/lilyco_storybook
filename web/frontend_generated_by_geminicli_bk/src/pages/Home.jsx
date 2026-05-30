import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Home() {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>欢迎来到小说/漫画网站</h1>
      <nav>
        {user ? (
          <>
            <span>欢迎, {user.email}!</span>
            <button onClick={logout}>退出登录</button>
          </>
        ) : (
          <>
            <Link to="/login">登录</Link> | <Link to="/register">注册</Link>
          </>
        )}
      </nav>
      {/* 后续可以添加小说和漫画列表 */}
    </div>
  );
}

export default Home;
