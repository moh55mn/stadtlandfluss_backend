<script>
  let terms = [
    { term: 'Karlsruhe', category: 'Stadt' },
    { term: 'Kroatien', category: 'Land' },
    { term: 'Känguru', category: 'Tier' }
  ];

  function removeTerm(index) {
    terms = terms.filter((_, i) => i !== index);
  }

  function editTerm(index) {
    const newTerm = prompt('Neuer Begriff:', terms[index].term);
    const newCategory = prompt('Neue Kategorie:', terms[index].category);
    if (newTerm && newCategory) {
      terms[index] = { term: newTerm, category: newCategory };
    }
  }

  function addTerm() {
    const newTerm = prompt('Begriff erfassen:');
    const newCategory = prompt('Kategorie:');
    if (newTerm && newCategory) {
      terms = [...terms, { term: newTerm, category: newCategory }];
    }
  }
</script>

<h2>Begriffverwaltung</h2>
<button on:click={addTerm}>Erfassen</button>

<table>
  <thead>
    <tr>
      <th>Nr.</th>
      <th>Begriff</th>
      <th>Kategorie</th>
      <th>Aktion</th>
    </tr>
  </thead>
  <tbody>
    {#each terms as term, i}
      <tr>
        <td>{i + 1}</td>
        <td>{term.term}</td>
        <td>{term.category}</td>
        <td>
          <button on:click={() => editTerm(i)}>Ändern</button>
          <button on:click={() => removeTerm(i)}>Löschen</button>
        </td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  border: 1px solid #bbb;
  padding: 8px;
  text-align: left;
}
th {
  background: #eee;
}
button {
  background: #888;
  color: #fff;
  border: none;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 5px;
}
button:hover {
  background: #666;
}
</style>
