async function handleGet(context) {
  const { request, env } = context;
  const db = env.DB;
  const url = new URL(request.url);
  console.log(url)

  try {
    // Query the Novels table for a specific ID
    const stmt = db.prepare('SELECT * FROM Novels');
    const { results } = await stmt.all();


    return new Response(JSON.stringify(results), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    console.error(e);
    return new Response('An internal error occurred', { status: 500 });
  }
}

async function handlePost(context) {
  const { request, env } = context;
  const db = env.DB;

  try {
    const novelsToInsert = await request.json();
    console.log(novelsToInsert)
    if (!Array.isArray(novelsToInsert)) {
        return new Response('Request body must be a JSON array of novels', { status: 400 });
    }

    // Prepare a statement for inserting a novel
    // Columns are based on the schema: title, author, description
    const stmt = db.prepare(
      'INSERT INTO Novels (title,  description) VALUES (?,  ?)'
    );

    // Create a batch of statements
    const statements = novelsToInsert.map(novel =>
      stmt.bind(novel.title,  novel.index)
    );

    // Execute the batch
    const results = await db.batch(statements);

    return new Response(JSON.stringify(results), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    // Handle potential JSON parsing errors or other issues
    if (e instanceof SyntaxError) {
        return new Response('Invalid JSON format in request body', { status: 400 });
    }
    console.error(e);
    return new Response('An internal error occurred', { status: 500 });
  }
}

export async function onRequest(context) {
  const { request } = context;

  switch (request.method) {
    case 'GET':
      return handleGet(context);
    // case 'POST':
    //   return handlePost(context);
    default:
      return new Response(`${request.method} is not allowed.`, {
        status: 405,
        headers: {
          Allow: 'GET, POST',
        },
      });
  }
}