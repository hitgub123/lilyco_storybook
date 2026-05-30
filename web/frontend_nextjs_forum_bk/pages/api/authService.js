import axios from 'axios';

const API_URL = '/api/'; // Vite 会自动代理到我们的 Functions

const register = (userData) => {
  return axios.post(API_URL + 'register', userData);
};

const login = (userData) => {
  return axios.post(API_URL + 'login', userData);
};

const authService = {
  register,
  login,
};

export default authService;
