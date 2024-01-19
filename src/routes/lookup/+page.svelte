<script lang="ts">
  import db from '$lib/db';
  import debouncePromise from '$lib/debouncePromise';

  let numberOfPins: number;

  let footprintLibraries: Array<{ name: string }> = [];
  let footprintLibrarySearch: string = '';
  let selectedFootprintLibrary: string | null = null;

  async function updateFootprintLibraries(numberOfPins: number) {
    footprintLibraries = await debouncePromise(
      () => {
        const sql = `
          SELECT DISTINCT library as name FROM footprints
          WHERE 1=1
          ${numberOfPins ? `AND pads = ${numberOfPins}` : ''}
          ORDER BY library ASC;
        `;

        const res = db
          .exec({ sql, returnValue: 'resultRows', rowMode: 'object' })
          .then(({ result }) => result.resultRows) as Promise<Array<{ name: string }>>;
        console.log(res);
        return res;
      },
      { ref: 'footprint-libraries', val: Promise.resolve(footprintLibraries) },
    );
  }

  let footprints: Array<{ id: number; name: string }> = [];
  let footprintSearch: string = '';
  let selectedFootprint: number | null = null;

  async function updateFootprints(numberOfPins: number, selectedFootprintLibrary: string | null) {
    footprints = await debouncePromise(
      () => {
        const query = `
          SELECT rowid, name FROM footprints
          WHERE 1=1
          ${numberOfPins ? `AND pads = ${numberOfPins}` : ''}
          ${selectedFootprintLibrary ? `AND library = '${selectedFootprintLibrary}'` : ''}
          ORDER BY name ASC;
        `;

        const q = db.query(query) as Promise<Array<{ id: number; name: string }>>;
        return q;
      },
      { ref: 'footprints', val: Promise.resolve(footprints) },
    );
  }

  $: updateFootprintLibraries(numberOfPins);
  $: updateFootprints(numberOfPins, selectedFootprintLibrary);
  $: console.log(footprintLibraries);
</script>

<h2>Reverse Lookup</h2>

<!-- Pin number -->
<label class="form-control w-full max-w-xs">
  <div class="label">
    <span class="label-text">Number of pins</span>
    <span class="label-text-alt"></span>
  </div>
  <input
    type="number"
    min="0"
    required
    placeholder="#"
    class="input input-bordered w-full max-w-xs"
    bind:value={numberOfPins}
  />
  <div class="label">
    <span class="label-text-alt"></span>
    <span class="label-text-alt"></span>
  </div>
</label>
<p>{numberOfPins}</p>

<!-- Footprint selection -->
<div class="flex flex-col overflow-y-auto">
  <div class="flex flex-row">
    <div class="m-0 w-36 p-0">
      <input
        type="text"
        placeholder="search"
        class="input input-xs p-0"
        bind:value={footprintLibrarySearch}
      />
    </div>
    <div class="m-0 w-36 p-0"></div>
    <div class="m-0 w-36 p-0"></div>
  </div>
  <div class="flex flex-row">
    <div class="m-0 max-h-48 w-36 overflow-x-auto p-0">
      <table class="table table-xs">
        <thead>
          <tr>Footprint Libraries</tr>
        </thead>
        <tbody>
          {#each footprintLibraries as fpl}
            <tr>
              <td
                ><button
                  on:click={() => {
                    selectedFootprintLibrary = fpl.name;
                  }}>{fpl.name}</button
                ></td
              >
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <div></div>
    <div></div>
  </div>
</div>
