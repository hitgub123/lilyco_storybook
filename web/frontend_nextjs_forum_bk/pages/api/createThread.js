import useForumsApi from '@/hooks/data/useForumsApi';
export default async function handler(req, res) {
    const { title, body, userId } = req.body;
    const api = useForumsApi();
    try {
        const articleData = await api.createArticle(title, body, userId);
        return res.json(articleData);
    } catch (error) {
        console.error('Error creating article:', error);
        return res.status(500).json({ error: error.message });
    }
}