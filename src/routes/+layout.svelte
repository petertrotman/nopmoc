<script lang="ts">
	import '../app.pcss';
</script>

<!-- <svelte:head> -->
<!--   <script src="/coi-serviceworker.min.js"></script> -->
<!-- </svelte:head> -->

<div class="navbar bg-primary text-primary-content">
  <a class="btn btn-ghost text-xl" href='/'>
    <img src='/logo.svg' alt='logo'/>
	nopmoc
  </a>
  <ul class="menu menu-horizontal px-1">
	<li><a href='/lookup'>Lookup</a></li>
	<li>
	  <details>
	    <summary>Browser</summary>
		<ul class="p-2 bg-primary rounded-t-none">
		  <li><a href='/symbols'>Symbols</a></li>
		  <li><a href='/footprints'>Footprints</a></li>
		</ul>
	  </details>
	</li>
  </ul>
</div>
<div class="container prose mx-auto px-4 py-4">
	<slot />
</div>
