import type { NextPage } from 'next';
import Head from 'next/head';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useRef } from 'react';
import Modal from '../../components/Modal';
import cloudinary from '../../utils/cloudinary';
import getBase64ImageUrl from '../../utils/generateBlurPlaceholder';
import type { ImageProps } from '../../utils/types';
import { useLastViewedPhoto } from '../../utils/useLastViewedPhoto';
import fs from 'fs/promises'; // 导入 Node.js 文件系统模块
import path from 'path'; // 导入 Node.js 路径模块
const ComicContent: NextPage = ({ images }: { images: ImageProps[] }) => {
	const router = useRouter();
	const slug = router.query.slug;

	// console.log('images', images);
	
	// console.log('slug', slug);
	const photoId = slug ? slug[0] : '';
	const subId = slug ? slug[1] : '';
	console.log('subId', subId, 'photoId', photoId);

	const [lastViewedPhoto, setLastViewedPhoto] = useLastViewedPhoto();

	const lastViewedPhotoRef = useRef<HTMLAnchorElement>(null);

	useEffect(() => {
		// This effect keeps track of the last viewed photo in the modal to keep the index page in sync when the user navigates back
		if (lastViewedPhoto && !subId) {
			lastViewedPhotoRef.current.scrollIntoView({ block: 'center' });
			setLastViewedPhoto(null);
		}
	}, [subId, lastViewedPhoto, setLastViewedPhoto]);

	return (
		<>
			<Head>
				<title>Comic Page</title>
			</Head>
			{!images.length && (
				<div className="after:content shadow-highlight after:shadow-highlight relative mb-5 flex h-[256px] flex-col items-center justify-end gap-4 overflow-hidden rounded-lg bg-white/10 px-6 pb-16 pt-64 text-center text-white after:pointer-events-none after:absolute after:inset-0 after:rounded-lg lg:pt-0">
					<div className="absolute inset-0 flex items-center justify-center opacity-20">
						<span className="absolute left-0 right-0 bottom-0 h-[400px] bg-gradient-to-b from-black/0 via-black to-black"></span>
					</div>

					<h1 className="mt-8 mb-4 text-base font-bold uppercase tracking-widest">Comic Page</h1>
					<p className="max-w-[40ch] text-white/75 sm:max-w-[32ch]">No storybook found!</p>
				</div>
			)}
			<main className="mx-auto max-w-[1960px] p-4">
				{/* {subId && /^\d+$/.test(subId) && ( */}
				{subId && (
					<Modal
						images={images}
						protoId={photoId}
						onClose={() => {
							setLastViewedPhoto(Number(subId));
						}}
					/>
				)}
				<div className="columns-1 gap-4 sm:columns-2 xl:columns-3 2xl:columns-4">
					{images.map(({ id, public_id, public_id_short, public_id_photo, format, blurDataUrl }) => (
						<Link
							key={id}
							href={`/p/${public_id_photo}`}
							ref={id === Number(lastViewedPhoto) ? lastViewedPhotoRef : null}
							shallow
							className="after:content after:shadow-highlight group relative mb-5 block w-full cursor-pointer after:pointer-events-none after:absolute after:inset-0 after:rounded-lg"
						>
							<Image
								alt="Next.js Conf photo"
								className="transform rounded-lg brightness-90 transition will-change-auto group-hover:brightness-110"
								style={{ transform: 'translate3d(0, 0, 0)' }}
								placeholder="blur"
								blurDataURL={blurDataUrl}
								src={`https://res.cloudinary.com/${process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME}/image/upload/c_scale,w_720/${public_id}.${format}`}
								width={720}
								height={480}
								sizes="(max-width: 640px) 100vw,
                  (max-width: 1280px) 50vw,
                  (max-width: 1536px) 33vw,
                  25vw"
							/>
						</Link>
					))}
				</div>
			</main>
			{/* <footer className="p-6 text-center text-white/80 sm:p-12">Comic Page</footer> */}
		</>
	);
};

export default ComicContent;

export async function getStaticProps(context: any) {
	// console.log('[subId].tsx---------------------------');
	// let index = context.params.photoId;
	const slug = context.params.slug;
	const index = slug ? slug[0] : '';
	if (!index) {
		return {
			props: {
				images: [],
			},
		};
	}
	// console.log('context.params', context.params);
	const results = await cloudinary.v2.search
		.expression(`folder:${process.env.CLOUDINARY_FOLDER}/${index}`)
		// .expression(`folder:={process.env.CLOUDINARY_FOLDER}`)
		.sort_by('public_id', 'asc')
		.max_results(100)
		.execute();
	let reducedResults: ImageProps[] = [];
	// console.log('results', results);
	let i = 0;
	for (let result of results.resources) {
		reducedResults.push({
			id: i,
			height: result.height,
			width: result.width,
			public_id: result.public_id,
			// comic1/a/a-b → a/a-b
			public_id_short: result.public_id.replace('comic1/', ''),
			// comic1/a/a-b → a/b
			public_id_photo: result.public_id.split('/')[2].replace('-', '/'),
			format: result.format,
		});
		i++;
	}

	const blurImagePromises = results.resources.map((image: ImageProps) => {
		return getBase64ImageUrl(image);
	});
	const imagesWithBlurDataUrls = await Promise.all(blurImagePromises);

	for (let i = 0; i < reducedResults.length; i++) {
		reducedResults[i].blurDataUrl = imagesWithBlurDataUrls[i];
	}
	// console.log('reducedResults', reducedResults[0]);
	return {
		props: {
			images: reducedResults,
		},
	};
}

export async function getStaticPaths() {
	const BUILD_CACHE_DIR = path.join(process.cwd(), 'out-1', 'p');
	console.log('BUILD_CACHE_DIR', BUILD_CACHE_DIR);
	let existingSlugs = new Set(); // 使用 Set 存储已存在的 slug，方便快速查找

	// 尝试读取缓存目录中的文件
	const files = await fs.readdir(BUILD_CACHE_DIR);
	for (const file of files) {
		// 检查文件是否是 HTML 文件
		if (file.endsWith('.html')) {
			// 从文件名中提取 slug (例如 '1.html' -> '1')
			const slug = path.basename(file, '.html');
			existingSlugs.add(slug);
		}
	}
	// console.log('files', files);
	// console.log('existingSlugs', existingSlugs);
	let fullPaths = [];
	
	const results = await cloudinary.v2.api.sub_folders(process.env.CLOUDINARY_FOLDER);
	const folders = results.folders;
	// console.log('folders', folders);
	for(let i = 0; i < folders.length; i++) {
		let name = folders[i].name;
		if (!existingSlugs.has(name)) {
			fullPaths.push({ params: { slug: [name] } });
		}
	}
	// for(let i = 0; i < fullPaths.length; i++) {
	// 	console.log(`fullPaths[${i}}=`, fullPaths[i]);
	// }

	return {
		paths: fullPaths,
		// fallback: false,
		fallback: 'blocking',
	};
	// return {
	// 	paths: [
	// 		{ params: { slug: ['3'] } },
	// 	],
	// 	// paths: [],
	// 	fallback: false,
	// };
}
