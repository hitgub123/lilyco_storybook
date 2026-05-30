import axios from 'axios';

const useForumsApi = () => {
    const forgotPassword = async (email) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ email }),
        });
        const data = await response.json();
        return data;
    };

    const resetPassword = async (email, password, token) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ email, password }),
        });
        const data = await response.json();
        return data;
    };

    const fetchUsers = async (page) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/users?page=${page}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const registerUser = async (username, email, password) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ username, email, password }),
        });
        const data = await response.json();
        return data;
    };

    const loginUser = async (email, password) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ login: email, password }),
        });
        const data = await response.json();
        return data;
    };

    const updateUser = async (id, username, email, password) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/user/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ username, email, password }),
        });
        const data = await response.json();
        return data;
    };

    const fetchUser = async (token) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
                'Authorization': `Bearer ${token}`,
            },
        });
        const data = await response.json();
        return data;
    };

    const deleteUser = async (id) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/user/${id}`, {
            method: 'DELETE',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const fetchArticles = async (page = 1) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/articles?page=${page}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const createArticle = async (title, body, userId) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/article`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ title, body, userId }),
        });
        const data = await response.json();
        return data;
    };

    const fetchArticle = async (id) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/article/${id}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const updateArticle = async (id, title, body) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/article/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ title, body }),
        });
        const data = await response.json();
        return data;
    };

    const deleteArticle = async (id) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/article/${id}`, {
            method: 'DELETE',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const fetchArticlePosts = async (articleId, page = 1) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/article/${articleId}/posts?page=${page}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const fetchPosts = async (page = 1) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/posts?page=${page}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const createPost = async (body, articleId, userId) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/post`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ body, articleId, userId }),
        });
        const data = await response.json();
        return data;
    };

    const fetchPost = async (id) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/post/${id}`, {
            method: 'GET',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const updatePost = async (id, body) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/post/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
            body: JSON.stringify({ body }),
        });
        const data = await response.json();
        return data;
    };

    const deletePost = async (id) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/post/${id}`, {
            method: 'DELETE',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    
    const search = async (query, type, page = 1) => {
        const response = await fetch(`${process.env.FORU_MS_API_URL}/search/${query}?type=${type}&page=${page}`, {
            method: 'POST',
            headers: {
                'x-api-key': process.env.FORU_MS_API_KEY,
            },
        });
        const data = await response.json();
        return data;
    };

    const searchArticle = async () => {
        // const response = await fetch('http://localhost:8788/api/searchArticle', {
        // const response = await fetch('http://localhost:8788/workers-api/searchArticle', {
        const response = await fetch(`${process.env.project_URL}/api/searchArticle`, {
        // const response = await fetch(`${process.env.project_URL}/workers-api/searchArticle`, {
            // method: 'POST',
            method: 'GET',
        });

        // 打印状态码和状态文本
        console.log('Response Status:', response.status, response.statusText);

        // 将返回结果作为纯文本读取
        const responseText = await response.text();
        // const responseText = await response.json();
        console.log('Response Text:', responseText);

        // 只有在确认是JSON后才尝试解析
        if (response.ok) {
            const data = JSON.parse(responseText);
            // console.log('Parsed Data:', data);
            return data;
        }

    };

    // const API_URL = '/api/'; // Vite 会自动代理到我们的 Functions
    // const searchArticle = (userData) => {
    //     return axios.post(API_URL + 'searchArticle');
    // };

    return {
        forgotPassword,
        resetPassword,
        fetchUsers,
        registerUser,
        loginUser,
        updateUser,
        fetchUser,
        deleteUser,
        fetchArticles,
        createArticle,
        fetchArticle,
        updateArticle,
        deleteArticle,
        fetchArticlePosts,
        fetchPosts,
        createPost,
        fetchPost,
        updatePost,
        deletePost,
        search,
        searchArticle

    };
};

export default useForumsApi;