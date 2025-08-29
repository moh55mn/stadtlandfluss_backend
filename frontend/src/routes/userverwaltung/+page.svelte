<script>
  let users = [
    { username: 'user1', role: 'admin' },
    { username: 'user2', role: 'player' },
    { username: 'user3', role: 'player' }
  ];
  function removeUser(index) {
    users = users.filter((_, i) => i !== index);
  }
</script>

<div class="card w-full max-w-2xl mx-auto mt-8 shadow-xl bg-base-100">
  <div class="card-body">
    <h2 class="card-title mb-4">Userverwaltung</h2>
    <div class="overflow-x-auto">
      <table class="table table-zebra w-full">
        <thead>
          <tr>
            <th>Username</th>
            <th>Rolle</th>
            <th>Aktion</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user, i}
            <tr>
              <td>{user.username}</td>
              <td>{user.role}</td>
              <td><button class="btn btn-error btn-sm" on:click={() => removeUser(i)}>Entfernen</button></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
