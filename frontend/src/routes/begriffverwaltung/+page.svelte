<script>
  // Dummy terms list
  let terms = [
    { term: 'Karlsruhe', category: 'Stadt' },
    { term: 'Kroatien', category: 'Land' },
    { term: 'Känguru', category: 'Tier' }
  ];
  function removeTerm(index) {
    terms = terms.filter((_, i) => i !== index);
  }
</script>

<h2>Begriffverwaltung</h2>
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
        <td><button on:click={() => removeTerm(i)}>Entfernen</button></td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
table {
  width: 100%; border-collapse: collapse; margin-top: 20px;
}
th, td {
  border: 1px solid #bbb; padding: 8px; text-align: left;
}
th { background: #eee; }
button {
  background: #888; color: #fff; border: none; padding: 6px 12px; cursor: pointer; font-size: 14px;
}
button:hover { background: #666; }
</style>


