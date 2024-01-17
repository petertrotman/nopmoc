<script lang="ts">
  import db from '$lib/db';
  import InitDb from './InitDb.svelte';

  class OPFSError extends Error{}
  class DbUninitialisedError extends Error{}

  async function openDb() {
    const { result: configResult } = await db.configGet();
    if (!configResult.opfsEnabled) throw new OPFSError();
    // const directoryHandle = await navigator.storage.getDirectory();
    // const fileHandle = await directoryHandle.getFileHandle('nopmoc.sqlite3', { create: true });
    const { result: openResult } = await db.open('file:nopmoc.sqlite3?vfs=opfs');
    console.log(openResult);
    // const { result: execResult } = await db.exec('select * from nopmoc;');
    // console.log(execResult);
    const { result: execResult } = await db.exec('select * from nopmoc;')
      .catch((e)  => {
	if (e.result.errorClass === 'SQLite3Error') throw new DbUninitialisedError();
	throw e;
    });
    console.log(execResult);
  }

  const dbPromise = openDb();
</script>

{#await dbPromise}

  <p>Waiting...</p>

{:then}

  <p>Done</p>

{:catch error}

  {#if error instanceof OPFSError}
    <p>OPFS is disabled. Please try <a href="/lookup" on:click={() => location.reload()}>reloading the page.</p>
  {:else if error instanceof DbUninitialisedError}
    <InitDb />
  {:else}
    <p>An error occurred.</p>
  {/if}

{/await}
