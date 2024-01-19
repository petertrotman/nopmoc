<script lang="ts">
  import db from '$lib/db';
  import debouncePromise from '$lib/debouncePromise';
  import unwrapPromise from '$lib/unwrapPromise';

  let numberOfPins: number;
  let selectedFootprintLibrary: string | null = null;

  $: footprintLibraries = unwrapPromise(
    debouncePromise(() =>
      db.query(`
      SELECT DISTINCT library FROM footprints
      ORDER BY library ASC;
    `),
    ),
  );

  async function updateOptions() {
    if (!numberOfPins) return;
    db.query('select distinct library from footprints order by library asc;').then((rows) => {
      footprintLibraries = rows as Array<string>;
    });
  }
</script>

<h2>Reverse Lookup</h2>

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
    on:focusout={() => debounce(updateOptions, 0)}
  />
  <div class="label">
    <span class="label-text-alt"></span>
    <span class="label-text-alt"></span>
  </div>
</label>
<p>{numberOfPins}</p>
