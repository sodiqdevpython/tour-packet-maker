from openai import OpenAI
client = OpenAI(api_key="TOKEN")
r = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"Salom men Samarqand viloyatiga bormoqchi edim sayohat qilish uchun tour packet tuzib ber"}]
)
print(r.choices[0].message.content)