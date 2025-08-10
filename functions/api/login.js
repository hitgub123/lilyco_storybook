import { createJWT, verifyPassword } from '../utils/auth.js';

export async function onRequestPost({ request, env }) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return new Response(JSON.stringify({ success: false, message: '需要邮箱和密码' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 1. 从数据库查找用户
    const ps = env.DB.prepare('SELECT id, email, password_hash FROM Users WHERE email = ?');
    const user = await ps.bind(email).first();

    if (!user) {
      return new Response(JSON.stringify({ success: false, message: '用户不存在或密码错误' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 2. 验证密码
    const passwordIsValid = await verifyPassword(password, user.password_hash);

    if (!passwordIsValid) {
      return new Response(JSON.stringify({ success: false, message: '用户不存在或密码错误' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 3. 生成 JWT
    const jwtSecret = await env.SETTINGS_KV.get('JWT_SECRET');
    const token = await createJWT({ id: user.id, email: user.email }, jwtSecret);

    return new Response(JSON.stringify({ success: true, token }), {
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    return new Response(JSON.stringify({ success: false, message: '登录失败', error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}


export async function onRequestGet({ request, env }) {

  return new Response(JSON.stringify({ success: false, message: '败败败败败败' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  
}
