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
const ComicContent: NextPage = ({ images }: { images: ImageProps[] }) => {
	const router = useRouter();
	const slug = router.query.slug;

	// console.log('slug', slug);

	const photoId = slug ? slug[0] : '';
	const subId = slug ? slug[1] : '';
	// console.log('subId', subId, 'photoId', photoId);

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
					{images.map(({ id, public_id, format, blurDataUrl }) => (
						<Link
							key={id}
							href={`/p/${photoId}/${id}`}
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
		.sort_by('public_id', 'desc')
		.max_results(10)
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
	// const results = await cloudinary.v2.api.sub_folders(process.env.CLOUDINARY_FOLDER);
	// const folders = results.folders;
	// // console.log(results)

	// let fullPaths = [];
	// for (let i = 0; i < folders.length; i++) {
	// 	fullPaths.push({ params: { photoId: folders[i].name ,subId:0} });
	// }
	// // console.log(fullPaths);
	// return {
	// 	paths: fullPaths,
	// 	fallback: false,
	// };
	return {
		paths: [
			{ params: { slug: ['3'] } },
			{ params: { slug: ['3', '0'] } },
			{ params: { slug: ['3', '1'] } },
			{ params: { slug: ['3', 'x'] } },
		],
		// paths: [],
		fallback: false,
	};
}
