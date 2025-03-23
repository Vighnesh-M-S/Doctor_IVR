function sendText() {
    let inputText = document.getElementById("textInput").value;

    fetch("http://127.0.0.1:8080/submit", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: inputText })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("responseText").textContent = data.message;
    })
    .catch(error => console.error("Error:", error));
}
