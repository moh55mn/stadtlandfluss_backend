<script>
  let isAdmin = true; // Simuliere Adminstatus

  let newTerm = '';
  let newCategory = '';
  let editIndex = -1;

  let terms = [
    { term: 'Karlsruhe', category: 'Stadt' },
    { term: 'Kroatien', category: 'Land' },
    { term: 'Känguru', category: 'Tier' }
  ];

  function removeTerm(index) {
    if (isAdmin) terms = terms.filter((_, i) => i !== index);
  }

  function saveTerm() {
    if (!newTerm || !newCategory) return;
    if (editIndex >= 0) {
      terms[editIndex] = { term: newTerm, category: newCategory };
      editIndex = -1;
    } else {
      terms.push({ term: newTerm, category: newCategory });
    }
    newTerm = '';
    newCategory = '';
  }

  function editTerm(index) {
    newTerm = terms[index].term;
    newCategory = terms[index].category;
    editIndex = index;
  }
</script>

<h2>Begriffverwaltung</h2>

{#if isAdmin}
  <input bind:value={newTerm} placeholder="Begriff" />
  <input bind:value={newCategory} placeholder="Kategorie" />
  <button on:click={saveTerm}>{editIndex >= 0 ? 'Ändern' : 'Hinzufügen'}</button>
{/if}

<table>
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
        <td>
          {#if isAdmin}
            <button on:click={() => editTerm(i)}>Bearbeiten</button>
            <button on:click={() => removeTerm(i)}>Entfernen</button>
          {/if}
        </td>
      </tr>
    {/each}
  </tbody>
</table>
