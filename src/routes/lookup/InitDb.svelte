<script lang="ts">
  import db from '$lib/db';
  console.log(db.close({unlink: true}));
</script>

<p>The database has not been initialised, would you like to do that now?</p>
<p>This will store the database in your browser. The database is about 50MB in size so it may take a while.</p>
<button class="btn btn-secondary">Begin</button>
