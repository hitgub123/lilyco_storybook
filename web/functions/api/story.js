export async function onRequestPost({ request, env }) {
  const { index } = await request.json();
  console.log('index',  index);
  // console.log('env', env);
  const ps = env.DB.prepare('SELECT content FROM story WHERE index = ?');
  const story = await ps.bind(index).first();
  return new Response(JSON.stringify({ success: false, message: '败败a败败败败' }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

}

export async function onRequestGet({ request, env }) {
  console.log('request', request.url);
  // console.log('env', env);
  return new Response(JSON.stringify({ success: false, message: '败败a败败败败' }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });

}