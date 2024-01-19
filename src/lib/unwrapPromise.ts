export default async function unwrapPromise(p: Promise<unknown> | unknown) {
	/*
	* unwrapPromise recursively awaits any nested promises below p
	* and returns the first non-promise value
	*/
	if (p instanceof Promise) {
		return unwrapPromise(await p);
	}
	return p;
}
