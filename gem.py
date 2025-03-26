import google.generativeai as genai
from flask import Flask, request, jsonify
key='kuch toh hai'
app = Flask(__name__)
genai.configure(api_key=Key)  
patient_data = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    patient_id = data.get("patient_id")
    user_input = data.get("message")

    if not patient_id or not user_input:
        return jsonify({"error": "Missing patient_id or message"}), 
    if patient_id not in patient_data:
        patient_data[patient_id] = []
    patient_data[patient_id].append(user_input)
    symptoms = "\n".join(patient_data[patient_id])

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"""
    A patient reports these ENT symptoms:\n{symptoms}
    Based on these symptoms, ask the patient a relevant follow-up question to narrow down possible causes.
    """)

    return jsonify({"reply": response.text})
if __name__ == "__main__":
    app.run()
