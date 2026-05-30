async function handleGet(context) {
  const { request, env } = context;
  const db = env.DB;
  const url = new URL(request.url);
  const id = url.searchParams.get('index');
  console.log(url)
  if (!id) {
    return new Response('Missing "index" query parameter', { status: 400 });
  }

  try {
    // Query the Novels table for a specific ID
    const stmt = db.prepare('SELECT * FROM Novels WHERE description = ?').bind(id);
    const novel = await stmt.first();

    if (!novel) {
      return new Response('Novel not found', { status: 404 });
    }

    return new Response(JSON.stringify(novel), {
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
    if (!Array.isArray(novelsToInsert)) {
        return new Response('Request body must be a JSON array of novels', { status: 400 });
    }

    if (novelsToInsert.length === 0) {
        return new Response(JSON.stringify({ message: "Received empty array, no action taken." }), {
            headers: { 'Content-Type': 'application/json' },
        });
    }

    const inputIndexes = novelsToInsert.map(novel => novel.index).filter(Boolean);

    if (inputIndexes.length === 0) {
        return new Response('No valid "index" fields found in the input array.', { status: 400 });
    }

    const placeholders = inputIndexes.map(() => '?').join(',');
    const selectStmt = db.prepare(`SELECT description FROM Novels WHERE description IN (${placeholders})`);
    const { results: existingNovels } = await selectStmt.bind(...inputIndexes).all();
    
    const existingDescriptions = new Set(existingNovels.map(row => row.description));

    const newNovelsToInsert = novelsToInsert.filter(novel => !existingDescriptions.has(novel.index));

    if (newNovelsToInsert.length === 0) {
        return new Response(JSON.stringify({ message: "All submitted novels already exist in the database." }), {
            headers: { 'Content-Type': 'application/json' },
            status: 200
        });
    }

    const stmt = db.prepare(
      'INSERT INTO Novels (title,  description) VALUES (?,  ?)'
    );

    const statements = newNovelsToInsert.map(novel =>
      stmt.bind(novel.title,  novel.index)
    );

    const results = await db.batch(statements);

    return new Response(JSON.stringify(results), {
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (e) {
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
    case 'POST':
      return handlePost(context);
    default:
      return new Response(`${request.method} is not allowed.`, {
        status: 405,
        headers: {
          Allow: 'GET, POST',
        },
      });
  }
}