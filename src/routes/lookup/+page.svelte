<script lang="ts">
  import db from '$lib/db';

  let numberOfPins: number;

  let footprintLibraries: Array<string>;

  let debounceTimeoutId: number | undefined;
  function debounce(fn: () => unknown, delay = 2000) {
    clearTimeout(debounceTimeoutId);
    debounceTimeoutId = setTimeout(fn, delay);
  }

  async function updateOptions() {
    if (!numberOfPins) return;
    db.query('select distinct library from footprints order by library asc;').then((rows) => {
      footprintLibraries = rows as Array<string>;
    });
    await db.query('drop table if exists test;');
    console.log(await db.query('create virtual table test using fts5(test1, test2);'));
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
