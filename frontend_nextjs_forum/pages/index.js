import Meta from '@/components/Meta/index';
import Sidebar from '@/components/Sidebar/index';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import Articles from '@/components/Articles/index';
import Posts from '@/components/Posts/index';
import Search from '@/components/Search/index';
import useForumsApi from "@/hooks/data/useForumsApi";

const Support = ({ articles, posts }) => {
    const [articlesData, setArticlesData] = useState(articles || []);

    useEffect(() => {
        setArticlesData(articles);
    }, [articles]);

    return (
        <>
            <Meta title="Demo Foru.ms" />
            <div className="flex flex-no-wrap">
                {/* Sidebar can be passed null or default data since login is not required */}
                <Sidebar data={null} />
                <div className="w-full">
                    <div className="w-full px-6">
                        <div className="lg:flex flex-wrap">
                            <div className="py-10 w-full md:pr-6 md:border-r border-gray-300">
                                <div>
                                    <Link href="/"><h1 className="text-3xl text-gray-900 font-bold mb-3">Forum</h1></Link>
                                    <div className="flex flex-col mt-10 md:flex-row md:items-center">
                                        <Search onSearchResults={setArticlesData} />
                                        <div className="w-full md:w-1/2 pt-3 md:pt-0 md:pl-3">
                                            <h3 className="text-xl text-gray-900 mb-2">Post a article</h3>
                                            <div className="flex flex-col">
                                                <label
                                                    htmlFor="post_article"
                                                    className="hidden text-gray-800 text-sm font-bold leading-tight tracking-normal mb-2"
                                                />
                                                <div className="relative w-full mb-2">
                                                    <input
                                                        id="post_article"
                                                        className="text-gray-600 focus:outline-none focus:border focus:border-blue-700 bg-gray-100 font-normal w-full h-10 flex items-center pl-4 text-sm border-gray-300 rounded border"
                                                        placeholder="to be implemented"
                                                        disabled="disabled"
                                                    />
                                                </div>
                                            </div>
                                            <div className="flex flex-col md:flex-row md:items-center">
                                                <div className="w-full md:w-1/2" />
                                                <div className="w-full md:w-1/2 md:flex md:mb-0 mb-4 justify-end">
                                                    <Link
                                                        disabled="disabled"
                                                        className="bg-blue-700 text-sm text-white rounded hover:bg-blue-600 transition duration-150 ease-in-out py-2 px-6 sm:mt-0 mt-4"
                                                        href={'/new-article'}
                                                        onClick={e => e.preventDefault()}
                                                    >
                                                        Continue
                                                    </Link>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="mt-6">
                                        <Articles data={articlesData} />
                                    </div>
                                    {/* Pagination removed as it requires server-side logic not available in getStaticProps */}
                                    <div className="py-10 w-full md:pl-6">
                                        <h3 className="mb-5 text-gray-900 font-medium text-xl">
                                            Recent posts
                                        </h3>
                                        <Posts data={posts} limit={3} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export async function getStaticProps() {
    const api = useForumsApi();

    // Fetch initial data for articles (e.g., page 1) and posts
    // const articlesResponse = await api.fetchArticles(1);
    const articlesResponse = null;
    const postsResponse = await api.searchArticle();
    console.log(articlesResponse, postsResponse)

    return {
        props: {
            articles: articlesResponse?.articles || [],
            posts: postsResponse?.posts || [],
        },
        // Optional: Re-generate the page periodically (Incremental Static Regeneration)
        revalidate: 60, // In seconds
    };
}

export default Support;
