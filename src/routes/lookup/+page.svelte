<script lang="ts">
	import db from '$lib/db';
	import InitDb from './InitDb.svelte';

	class OPFSError extends Error {}
	class DbUninitialisedError extends Error {}

	async function openDb() {
		const { result: configResult } = await db.configGet();
		if (!configResult.opfsEnabled) throw new OPFSError();

		await db.open('file:nopmoc.sqlite3?vfs=opfs');

		const result = await db
			.query('select * from nopmoc;')
			.catch((e: { result: { errorClass: string } }) => {
				if (e.result.errorClass === 'SQLite3Error') throw new DbUninitialisedError();
				throw e;
			});
		console.log(result[0][0]);
	}

	const dbPromise = openDb();
</script>

{#await dbPromise}
	<p>Waiting...</p>
{:then}
	<p>Done</p>
{:catch error}
	{#if error instanceof OPFSError}
		<p>
			OPFS is disabled. Please try <a href="/lookup" on:click={() => location.reload()}
				>reloading the page.</a
			>
		</p>
	{:else if error instanceof DbUninitialisedError}
		<InitDb />
	{:else}
		{error}
		<p>An error occurred.</p>
	{/if}
{/await}
