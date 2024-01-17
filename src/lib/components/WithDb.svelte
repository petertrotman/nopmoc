<script lang="ts">
  import db from '$lib/db';

  const DB_FILE_NAME = 'nopmoc.sqlite3';

  enum ProgressState {
    CheckDbReady,
    DbNotReady,
    CapabilitiesOk,
    OPFSUnavailable,
    DbNotInitialised,
    InitialiseDb,
    UnknownErrorOccurred,
    Ready,
  }

  let progressState = ProgressState.CheckDbReady;

  async function checkDbReady() {
    try {
      await db.query('select * from nopmoc;');
    } catch {
      return ProgressState.DbNotReady;
    }
    return ProgressState.Ready;
  }

  async function verifyCapabilities() {
    const { result: configResult } = await db.configGet();
    if (!configResult.opfsEnabled) {
      return ProgressState.OPFSUnavailable;
    }

    return ProgressState.CapabilitiesOk;
  }

  async function checkExistingDb() {
    await db.open(`file:${DB_FILE_NAME}?vfs=opfs`);
    try {
      const result = (await db.query('select created_at from nopmoc;')) as unknown as string[][];
      const dbCreatedAt = Date.parse(result[0][0]);
      console.log(dbCreatedAt);
    } catch (e) {
      const errorClass = (e as { result: { errorClass: string } }).result?.errorClass;
      if (errorClass == 'SQLite3Error') {
        return ProgressState.DbNotInitialised;
      } else {
        throw e;
      }
    }
    return ProgressState.Ready;
  }

  let bytesRead = 0;

  async function initialiseDb() {
    const directoryHandle = await navigator.storage.getDirectory();
    const fileHandle = await directoryHandle.getFileHandle(DB_FILE_NAME, { create: true });

    const response = await fetch('nopmoc.sqlite3');
    if (!response.ok || !response.body) {
      throw new Error('fetch error', { cause: response.statusText });
    }

    const [checkReadableStream, pipeReadablStream] = response.body.tee();
    let pipeFinished = false;
    const pipePromise = pipeReadablStream
      .pipeTo(await fileHandle.createWritable({ keepExistingData: false }))
      .then(() => {
        pipeFinished = true;
      })
      .catch((e) => {
        throw e;
      });

    const checkReader = checkReadableStream.getReader();
    while (!pipeFinished) {
      const { done, value } = await checkReader.read();
      if (done) break;
      bytesRead += value.byteLength;
    }

    await pipePromise;
    if ((await checkExistingDb()) !== ProgressState.Ready) {
      throw new Error('The database could not be initialised.');
    }

    return ProgressState.Ready;
  }

  async function resetDb() {
    await db.close({ unlink: true });
    const directoryHandle = await navigator.storage.getDirectory();
    directoryHandle.removeEntry(DB_FILE_NAME);
    return ProgressState.DbNotInitialised;
  }

  async function run(fn: () => Promise<ProgressState>) {
    try {
      progressState = await fn();
    } catch (e) {
      console.error(e);
      progressState = ProgressState.UnknownErrorOccurred;
    }
    return progressState;
  }

  async function step() {
    switch (progressState) {
      case ProgressState.CheckDbReady:
        run(checkDbReady).then(step);
        break;
      case ProgressState.DbNotReady:
        run(verifyCapabilities).then(step);
        break;
      case ProgressState.CapabilitiesOk:
        run(checkExistingDb).then(step);
        break;
      case ProgressState.InitialiseDb:
        run(initialiseDb).then(step);
        break;
      default:
        break;
    }
  }

  step();
</script>

<button
  class="btn"
  on:click={() => {
    run(resetDb).then(step);
  }}>Reset</button
>
{#if progressState == ProgressState.OPFSUnavailable}
  <p>OPFS is disabled.</p>
  <p>
    Please try <a href={window.location.toString()} on:click={() => location.reload()}
      >reloading the page.</a
    >
  </p>
{/if}
{#if progressState == ProgressState.DbNotInitialised}
  <p>The database has not been initialised, would you like to do that now?</p>
  <p>
    This will store the database in your browser. The database is about 50MB in size so it may take
    a while.
  </p>
  <button
    class="btn btn-secondary"
    on:click={() => {
      progressState = ProgressState.InitialiseDb;
      step();
    }}>Begin</button
  >
{/if}
{#if progressState == ProgressState.InitialiseDb}
  <p>Initialising DB...</p>
  <p>{bytesRead} bytes read.</p>
{/if}
{#if progressState == ProgressState.Ready}
  <slot />
{/if}
