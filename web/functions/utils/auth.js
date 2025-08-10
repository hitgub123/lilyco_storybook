// JWT 生成函数
export async function createJWT(user, secret) {
  const header = {
    alg: 'HS256',
    typ: 'JWT',
  };
  const payload = {
    sub: user.id,
    email: user.email,
    exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24 * 7), // 7天有效期
  };

  const encodedHeader = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const encodedPayload = btoa(JSON.stringify(payload)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${encodedHeader}.${encodedPayload}`));

  const encodedSignature = btoa(String.fromCharCode(...new Uint8Array(signature))).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

  return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
}

// 密码验证函数
export async function verifyPassword(password, storedHash) {
  const [saltHex, hashHex] = storedHash.split(':');
  const salt = new Uint8Array(saltHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
  
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );
  
  const derivedKey = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    passwordKey,
    256
  );

  const derivedKeyHex = Array.from(new Uint8Array(derivedKey)).map(b => b.toString(16).padStart(2, '0')).join('');
  
  return derivedKeyHex === hashHex;
}

// 密码哈希函数
export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );
  const hashedPassword = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    passwordKey,
    256
  );

  // 将 salt 和哈希后的密码组合存储
  const password_hash = `${Array.from(salt).map(b => b.toString(16).padStart(2, '0')).join('')}:${Array.from(new Uint8Array(hashedPassword)).map(b => b.toString(16).padStart(2, '0')).join('')}`;
  
  return password_hash;
}