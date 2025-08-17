import Meta from '@/components/Meta/index';
import Sidebar from '@/components/Sidebar/index';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

export default function NewArticle() {
    const router = useRouter();
    const forumUser={};
    const [isSubmitting, setSubmittingState] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        body: '',
    });

    useEffect(() => {
        if (!forumUser?.id) {
            router.push(`/login`);
        }
    }, [forumUser]);

    const onChange = (e) => {
        setFormData((prevFormData) => ({
            ...prevFormData,
            [e.target.name]: e.target.value,
        }));
    };

    const onSubmit = async (e) => {
        e.preventDefault();
        setSubmittingState(true);
        try {
            const response = await fetch('/api/createArticle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: formData.title,
                    body: formData.body,
                    userId: forumUser?.id,
                })
            });
            const data = await response.json();
            console.log('Article created:', data);
            setSubmittingState(false);
            if (response.errors) {
                Object.values(response.errors).forEach((error) =>
                    toast.error(error.msg)
                );
            } else if (data?.id) {
                toast.success('Article successfully created!');
                router.push(`/article/${data.id}`);
            }
        } catch (error) {
            console.error('Error creating article:', error);
            setSubmittingState(false);
            toast.error('An error occurred while creating the article.');
        }
    };

    return (
        <>
            <Meta title="New article" />
  <div className="flex flex-no-wrap">
            <Sidebar data={forumUser} />
    <div className="flex flex-row w-full">
        <div className="flex flex-col lg:w-full items-center justify-center mx-auto md:h-screen lg:py-0">
          <div className="w-full bg-white rounded-lg shadow dark:border md:mt-0 sm:max-w-md xl:p-0 dark:bg-gray-800 dark:border-gray-700">
            <div className="p-6 space-y-4 md:space-y-6 sm:p-8">
              <h1 className="text-xl font-bold leading-tight tracking-tight text-gray-900 md:text-2xl dark:text-white">
                                Post a new article
                            </h1>
                            <form
                                className="space-y-4 md:space-y-6"
                                action="POST"
                                onSubmit={onSubmit}
                            >
                                <div>
                                    <label
                                        htmlFor="title"
                                        className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                                    >
                                        Title
                                    </label>
                                    <input
                                        onChange={onChange}
                                        type="text"
                                        name="title"
                                        value={formData.title}
                                        id="title"
                                        className="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                        placeholder="Article title"
                                        required
                                    />
                                </div>

                                <div>
                                    <label
                                        htmlFor="body"
                                        className="block mb-2 text-sm font-medium text-gray-900 dark:text-white"
                                    >
                                        Body
                                    </label>
                                    <textarea
                                        onChange={onChange}
                                        name="body"
                                        id="body"
                                        rows="7"
                                        className="bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-blue-600 focus:border-blue-600 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                        placeholder="Article body"
                                        required
                                    ></textarea>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full text-white bg-blue-700 hover:bg-blue-600 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
                                >
                                    Submit article
                                </button>
                            </form>
                        </div>
                    </div>

                    <Link href="/" className="btn btn-outline btn-neutral btn-wide mt-5">
                        Back to the forums
                    </Link>
                </div>
                </div>
            </div>
        </>
    );
}

// export async function getServerSideProps(context) {
//   const api = useForumsApi();
//   const { forumUserToken } = context.req.cookies;
//   let forumUser = null;

//   if (forumUserToken) {
//       const userResponse = await api.fetchUser(forumUserToken);
//       if (userResponse?.id) {
//           forumUser = userResponse;
//       }
//   }
  
//   return {
//       props: {
//           forumUser,
//       }
//   };
// }