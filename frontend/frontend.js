const resetBtn = document.getElementById('resetBtn');
const statusEl = document.getElementById('status');

resetBtn.onclick = async () => {
  statusEl.textContent = "Sending reset command...";
  try {
    const res = await fetch('/reset-all', { method: 'POST' });
    if (res.ok) {
      statusEl.textContent = "Reset command sent!";
    } else {
      statusEl.textContent = "Error: " + (await res.text());
    }
  } catch (err) {
    statusEl.textContent = "Failed to send request: " + err;
  }
};
