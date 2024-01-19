const debouncePromiseTimeouts: Record<string, { cancel: () => void }> = {};
export default async function debouncePromise(
	fn: () => unknown,
	opts: { delay: number; ref: string; val?: unknown } = { delay: 2000, ref: '' },
) {
	/*
	* debouncePromise returns a promise that will 
	* resolve with the return value of fn() after opts.delay
	* unless debouncePromise is called again with the same ref,
	* in which case debouncePromise will resolve with opts.val
	*
	* Specifying opts.val is useful with debouncing reactive props
	* by passing the existing prop value so that it isn't overwritten
	* with undefined
	*/
	const ref = opts.ref ?? fn.name;
	debouncePromiseTimeouts[ref]?.cancel();

	return new Promise((resolve) => {
		const timeoutId = setTimeout(() => resolve(fn()), opts.delay);
		debouncePromiseTimeouts[ref] = { cancel: () => {
			clearTimeout(timeoutId);
			resolve(opts.val);
		}};
	});
}
