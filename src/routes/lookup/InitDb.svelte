<script lang="ts">
	import db from '$lib/db';

	enum ProgressState {
		Uninitialised,
		Downloading,
		Downloaded,
		Complete
	}

	let state = ProgressState.Uninitialised;

	console.log(db.close({ unlink: true }));

	async function beginDownload() {
		state = ProgressState.Downloading;
		const directoryHandle = await navigator.storage.getDirectory();
		const fileHandle = await directoryHandle.getFileHandle('nopmoc.sqlite3', { create: true });
		const response = await fetch('nopmoc.sqlite3');
		if (!response.ok || !response.body)
			throw new Error('fetch error', { cause: response.statusText });
		await response.body.pipeTo(await fileHandle.createWritable({ keepExistingData: false }));
		state = ProgressState.Complete;
		console.log(db);
	}
</script>

{#if state == ProgressState.Uninitialised}
	<p>The database has not been initialised, would you like to do that now?</p>
	<p>
		This will store the database in your browser. The database is about 50MB in size so it may take
		a while.
	</p>
	<button class="btn btn-secondary" on:click={beginDownload}>Begin</button>
{/if}
