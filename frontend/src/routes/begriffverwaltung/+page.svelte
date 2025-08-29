<script>
  let terms = [
    { term: 'Karlsruhe', category: 'Stadt' },
    { term: 'Kroatien', category: 'Land' },
    { term: 'Känguru', category: 'Tier' }
  ];
  function removeTerm(index) {
    terms = terms.filter((_, i) => i !== index);
  }
</script>

<div class="card w-full max-w-2xl mx-auto mt-8 shadow-xl bg-base-100">
  <div class="card-body">
    <h2 class="card-title mb-4">Begriffverwaltung</h2>
    <div class="overflow-x-auto">
      <table class="table table-zebra w-full">
        <thead>
          <tr>
            <th>Begriff</th>
            <th>Kategorie</th>
            <th>Aktion</th>
          </tr>
        </thead>
        <tbody>
          {#each terms as term, i}
            <tr>
              <td>{term.term}</td>
              <td>{term.category}</td>
              <td><button class="btn btn-error btn-sm" on:click={() => removeTerm(i)}>Entfernen</button></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
