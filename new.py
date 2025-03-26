from google import genai

client = genai.Client(api_key="AIzaSyCEF9yd8lx8LPorSGvs1lnYH-yk5o5SlAM")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain how AI works",
)

print(response.text)