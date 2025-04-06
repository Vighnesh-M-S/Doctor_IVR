async function fetchLogs() {
  const logDiv = document.getElementById('logs');
  logDiv.innerHTML = "Loading logs...";

  try {
    const response = await fetch("http://localhost:8080/logs");
    const data = await response.json();

    if (Object.keys(data).length === 0) {
      logDiv.innerHTML = "No logs yet.";
      return;
    }

    let output = "";

    for (let session in data) {
      output += `<strong>Session:</strong> ${session}<br/>`;
      data[session].forEach((log, idx) => {
        output += `&nbsp;&nbsp;&nbsp;&nbsp;${idx + 1}. ${log}<br/>`;
      });
      output += "<br/>";
    }

    logDiv.innerHTML = output;
  } catch (err) {
    logDiv.innerHTML = "Failed to load logs.";
    console.error(err);
  }
}