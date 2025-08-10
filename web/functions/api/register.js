import { hashPassword } from '../utils/auth.js';

export async function onRequestPost({ request, env }) {
  try {
    const { email, password } = await request.json();
    const minPasswordLength = 3;
    // 1. 数据校验
    if (!email || !password || password.length < minPasswordLength) {
      return new Response(JSON.stringify({ success: false, message: `邮箱或密码无效 (密码至少${minPasswordLength}位)` }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // 2. 密码加密
    const password_hash = await hashPassword(password);

    // 3. 存入数据库
    const ps = env.DB.prepare('INSERT INTO Users (email, password_hash) VALUES (?, ?)');
    await ps.bind(email, password_hash).run();

    return new Response(JSON.stringify({ success: true, message: '注册成功' }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    // 捕获唯一的 email 约束冲突
    if (error.message.includes('UNIQUE constraint failed')) {
      return new Response(JSON.stringify({ success: false, message: '该邮箱已被注册' }), {
        status: 409, // Conflict
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return new Response(JSON.stringify({ success: false, message: '注册失败', error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
