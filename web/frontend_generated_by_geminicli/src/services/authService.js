import axios from 'axios';

const API_URL = '/workers-api/'; // Vite 会自动代理到我们的 Functions
axios.interceptors.request.use(function (config) {
  // 在请求被发送出去之前，在浏览器的控制台打印出它的最终 URL
  console.log('Axios is requesting this exact URL:', config.url);
  return config;

}, function (error) {
  return Promise.reject(error);

});
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
