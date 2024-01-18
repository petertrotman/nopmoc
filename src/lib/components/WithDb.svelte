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
    DatabaseDownloaded,
    IndicesCreated,
    VirtualTablesCreated,
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
  let bytesLength: number | undefined = undefined;

  async function downloadDb() {
    const directoryHandle = await navigator.storage.getDirectory();
    const fileHandle = await directoryHandle.getFileHandle(DB_FILE_NAME, { create: true });

    const response = await fetch('nopmoc.sqlite3');
    if (!response.ok || !response.body) {
      throw new Error('fetch error', { cause: response.statusText });
    }
    const contentLength = response.headers.get('content-length');
    bytesLength = contentLength ? parseInt(contentLength) : undefined;
    bytesRead = 0;

    const [checkReadableStream, pipeReadableStream] = response.body.tee();
    let pipeFinished = false;
    const pipePromise = pipeReadableStream
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

    return ProgressState.DatabaseDownloaded;
  }

  async function createIndices() {
    console.log('creating indexes');
    db.exec('CREATE INDEX IF NOT EXISTS ix_pin_symbols ON pins (symbol_rowid);');
    db.exec('CREATE INDEX IF NOT EXISTS ix_pin_numbers ON pins (number);');
    db.exec('CREATE INDEX IF NOT EXISTS ix_footprint_pads ON footprints (pads);');
    console.log('indexes created');

    return ProgressState.IndicesCreated;
  }

  async function createVirtualTables() {
    console.log('creating virtual tables');
    db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS vt_symbols
    USING fts5(name, library, keywords, description, content='symbols');
    `);
    db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS vt_pins
    USING fts5(name, content='pins');
    `);
    db.exec(`
    CREATE VIRTUAL TABLE IF NOT EXISTS vt_footprints
    USING fts5(name, library, description, tags, content='footprints');
    `);
    db.exec(`INSERT INTO vt_symbols(vt_symbols) VALUES ('rebuild');`);
    db.exec(`INSERT INTO vt_pins(vt_pins) VALUES ('rebuild');`);
    db.exec(`INSERT INTO vt_footprints(vt_footprints) VALUES ('rebuild');`);
    console.log('created virtual tables');

    return ProgressState.VirtualTablesCreated;
  }

  async function resetDb() {
    await db.close({ unlink: true });
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
        run(downloadDb).then(step);
        break;
      case ProgressState.DatabaseDownloaded:
        run(createIndices).then(step);
        break;
      case ProgressState.IndicesCreated:
        run(createVirtualTables).then(step);
        break;
      case ProgressState.VirtualTablesCreated:
        progressState = ProgressState.Ready;
        break;
      default:
        break;
    }
  }

  step();
</script>

{#if progressState == ProgressState.OPFSUnavailable}
  <div role="alert" class="alert alert-error">
    <p class="my-0">
      OPFS is disabled. Please try <a
        href={window.location.toString()}
        on:click={() => location.reload()}>reloading the page.</a
      >
    </p>
  </div>
{/if}

{#if progressState == ProgressState.DbNotInitialised}
  <div role="alert" class="alert alert-warning">
    <p class="my-0">
      The database has not been initialised, would you like to do that now? It is a ~50MB download
    </p>
    <button
      class="btn btn-secondary"
      on:click={() => {
        progressState = ProgressState.InitialiseDb;
        step();
      }}>Begin</button
    >
  </div>
{/if}

{#if progressState == ProgressState.InitialiseDb || progressState == ProgressState.DatabaseDownloaded || progressState == ProgressState.IndicesCreated}
  <div role="alert" class="alert alert-warning">
    <p class="my-0">
      Downloading... {#if bytesLength}{((bytesRead * 100) / bytesLength).toFixed(0)}%{/if}
    </p>
    {#if progressState == ProgressState.DatabaseDownloaded || progressState == ProgressState.IndicesCreated}
      <p>Creating indices...</p>
    {/if}
    {#if progressState == ProgressState.IndicesCreated}
      <p>Creating full text search tables...</p>
    {/if}
  </div>
{/if}

{#if progressState == ProgressState.UnknownErrorOccurred}
  <div role="alert" class="alert alert-error">
    <p class="my-0">An unknown error occurred.</p>
  </div>
{/if}

{#if progressState == ProgressState.Ready}
  <div role="alert" class="alert alert-success">
    <p class="my-0">Database is ready</p>
    <button
      class="btn btn-secondary"
      on:click={() => {
        run(resetDb).then(step);
      }}>Reset</button
    >
  </div>
  <slot />
{/if}
