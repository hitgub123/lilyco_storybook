import { Dialog } from '@headlessui/react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/router';
import { useRef, useState } from 'react';
import useKeypress from 'react-use-keypress';
import type { ImageProps } from '../utils/types';
import SharedModal from './SharedModal';

export default function Modal({ images, protoId, onClose }: { images: ImageProps[]; protoId?: string; onClose?: () => void }) {
	let overlayRef = useRef();
	const router = useRouter();
  const slug = router.query.slug;

  // console.log('slug', slug);

  const photoId = slug ? slug[0] : '';
  const subId = slug ? slug[1] : '';
  // console.log('subId', subId, 'photoId', photoId);

	let index = Number(subId);

	const [direction, setDirection] = useState(0);
	const [curIndex, setCurIndex] = useState(index);

	function handleClose() {
		router.push(`/p/${protoId}`, undefined, { shallow: true });
		onClose();
	}

	function changePhotoId(newVal: number) {
		if (newVal > index) {
			setDirection(1);
		} else {
			setDirection(-1);
		}
		setCurIndex(newVal);
		router.push(
			{
				query: { photoId: newVal },
			},
			`/p/${protoId}/${newVal}`,
			{ shallow: true }
		);
	}

	useKeypress('ArrowRight', () => {
		if (index + 1 < images.length) {
			changePhotoId(index + 1);
		}
	});

	useKeypress('ArrowLeft', () => {
		if (index > 0) {
			changePhotoId(index - 1);
		}
	});

	return (
		<Dialog
			static
			open={true}
			onClose={handleClose}
			initialFocus={overlayRef}
			className="fixed inset-0 z-10 flex items-center justify-center"
		>
			<Dialog.Overlay
				ref={overlayRef}
				as={motion.div}
				key="backdrop"
				className="fixed inset-0 z-30 bg-black/70 backdrop-blur-2xl"
				initial={{ opacity: 0 }}
				animate={{ opacity: 1 }}
			/>
			<SharedModal
				index={curIndex}
				direction={direction}
				images={images}
				changePhotoId={changePhotoId}
				closeModal={handleClose}
				navigation={true}
			/>
		</Dialog>
	);
}
