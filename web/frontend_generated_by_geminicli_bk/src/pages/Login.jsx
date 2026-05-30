import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import { useAuth } from '../context/AuthContext';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const response = await authService.login({ email, password });
      login(response.data.token); // 使用 context 的 login 方法
      navigate('/novels'); // 使用 react-router 的 navigate 方法进行跳转
    } catch (error) {
      setMessage(error.response.data.message);
    }
  };

  return (
    <div>
      <h2>登录</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="邮箱" required />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="密码" required />
        <button type="submit">登录</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}

export default Login;
