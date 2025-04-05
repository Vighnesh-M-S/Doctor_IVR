async function fetchLogs() {
    const logDiv = document.getElementById('logDisplay');
    logDiv.innerHTML = "Loading logs...";
  
    try {
      const response = await fetch("http://localhost:8080/logs");
      const data = await response.json();
      let output = "";
  
      for (let session in data) {
        output += `Session: ${session}\n`;
        data[session].forEach((log, idx) => {
          output += `  ${idx + 1}. ${log}\n`;
        });
        output += "\n";
      }
  
      logDiv.innerText = output || "No logs yet.";
    } catch (err) {
      logDiv.innerText = "Failed to load logs.";
      console.error(err);
    }
  }
  