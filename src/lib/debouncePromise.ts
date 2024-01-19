const debouncePromiseTimeouts: Record<string, { cancel: () => void }> = {};
async function debouncePromise<T>(fn: () => T, opts: { delay?: number; ref?: string; val: T }): Promise<T>
async function debouncePromise<T>(
	fn: () => T,
	opts: { delay?: number; ref?: string; val?: T } = { delay: 2000, ref: '' },
): Promise<T | undefined> {
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

export default debouncePromise;
