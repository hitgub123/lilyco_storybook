import React, { createContext, useState, useContext, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode'; // 需要安装 jwt-decode 库

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 应用加载时，尝试从 localStorage 获取 token
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decodedUser = jwtDecode(token);
        // 检查 token 是否过期
        if (decodedUser.exp * 1000 > Date.now()) {
          setUser({ email: decodedUser.email });
        } else {
          // token 过期，清除它
          localStorage.removeItem('token');
        }
      } catch (error) {
        console.error("Token解码失败", error);
        localStorage.removeItem('token');
      }
    }
  }, []);

  const login = (token) => {
    const decodedUser = jwtDecode(token);
    localStorage.setItem('token', token);
    setUser({ email: decodedUser.email });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
