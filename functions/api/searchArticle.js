

export async function onRequestPost({ request, env }) {
  // const ps = env.DB.prepare('SELECT id, email, password_hash FROM Users WHERE email = ?');
  // const user = await ps.bind("hotococoalj@163.com").first();

  const ps = env.DB.prepare('SELECT id, email, password_hash FROM Users');
  const users = await ps.all();
  // console.log(users)
  return new Response(JSON.stringify({ success: true, users }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function onRequestGet({ request, env }) {
  // const ps = env.DB.prepare('SELECT id, email, password_hash FROM Users WHERE email = ?');
  // const user = await ps.bind("hotococoalj@163.com").first();

  const ps = env.DB.prepare('SELECT id, email, password_hash FROM Users');
  let users = await ps.all();
  users = users.results
  for (let i = 0; i < users.length; i++) {
    users[i].body='这是第'+i+'篇文章'

  }
  console.log(users)
  // return new Response(JSON.stringify({ success: true, users }), {
  return new Response(JSON.stringify({ posts: users}), {
    headers: { 'Content-Type': 'application/json' },
  });
}
