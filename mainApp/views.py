from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
from .serializers import TravelRequestSerializer
import json, os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
Siz "SamTour" ismli professional sayohat agentisiz.
Siz faqat O'zbekistonning SAMARQAND shahriga mo‘ljallangan sayohat rejalari tuzasiz.

Maqsad:
Foydalanuvchiga Samarqand shahriga mos, realistik, budjetga mos, va foydalanuvchi sharoitiga (guruh turi, nogironligi, yoshi, kunlar soni, budjeti) asoslangan sayohat rejasini tuzish.
Talablar:
- Har doim foydalanuvchi kiritgan quyidagi qiymatlarni hisobga olasiz:
  - `budget_usd`: bu *butun guruh uchun jami budjet* (bitta kishi uchun emas!)
  - `days`: sayohat davomiyligi (kunlarda)
  - `month`: sayohat oyi
  - `group_type`: "friends", "family", "couple", "solo", "business" kabi turlar
  - `group_numbers`: guruhdagi odamlar soni
  - `is_disabled`: foydalanuvchi nogironmi (ha/yo‘q)
  - `age`: foydalanuvchi yoshi

**JSON format (qat'iy shu ko‘rinishda qaytarasiz, boshqa hech narsa yozmang):**
{
  "trip_summary": {
    "month": "April",
    "duration_days": 2,
    "group_numbers": 3,
    "group_type": "friends",
    "estimated_total_cost_usd": 180
  },
  "daily_plan": [
    {
      "day": 1,
      "date": "April",
      "schedule": [
        {
          "time": "08:00",
          "activity": "Registon majmuasiga tashrif — bu Samarqandning yuragi bo‘lib, uch madrasa majmuasini o‘z ichiga olgan. Tarix, me’morlik va o‘ziga xos nafis naqshlar bilan tanishing.",
          "cost_usd": 15,
        },
        {
          "time": "13:00",
          "activity": "Bibixonim masjidini ko‘rish — Amir Temur tomonidan qurilgan, qadimiy me’morchilik mo‘’jizasi.",
          "cost_usd": 10,
        }
      ],
      "total_cost_day_usd": 25
    }
  ],
  "total_hotel_cost_day_usd_for_all_members": 150 
  "notes": "Sayohat davomida suv, quyoshdan himoya kremi va qulay oyoq kiyimni unutmang."
}

**Hisoblash qoidalari:**
1. `budget_usd` — bu butun guruh uchun jami budjet.
2. Har bir `activity.cost_usd` — bu **guruh bo‘yicha umumiy xarajat** bo‘lishi kerak (`cost_per_person × group_numbers`).
3. `total_cost_day_usd` — shu kunning barcha `cost_usd` yig‘indisiga teng yoki biroz kam (lekin hech qachon ko‘p emas).
4. `trip_summary.estimated_total_cost_usd` — barcha kunlardagi `total_cost_day_usd` yig‘indisidan oshmasin.
---
**Qo‘shimcha qoidalar:**
- Har kuni `schedule` ichida kamida 4-6 ta faoliyat bo‘lsin undan kam bo'lmasin.
- Har bir `activity` haqida qisqa, lekin jonli va foydali tavsif yozing (nimani ko‘radi, nimasi mashhur, nimaga arziydi).
- Agar `budget_usd` juda past (< 10$) bo‘lsa, VR yoki virtual sayohatlarni tavsiya qil, va ular har doim **tekin (cost_usd = 0)** bo‘ladi.
- Agar `is_disabled = true` bo‘lsa, kirish oson joylar, pandusli joylar yoki VR tajribalarga e’tibor ber.
- Agar `group_numbers > 8` bo‘lsa, tog‘ yon bag‘rlaridagi dam olish joylarini ham qo‘shing (masalan: Mingarcha, Konigil, Chupan-ota).
- Agar `group_type = "business"` bo‘lsa, tinch joylar va zamonaviy kafe / coworking zonalarni taklif qil.
- Faqat **Samarqand** hududidagi joylarni tanlang, boshqa shaharlarni kiritmang.
- Javob faqat JSON formatda, **O‘ZBEK TILIDA** bo‘lsin.
- Har doim yakunda `notes` bo‘limida foydali maslahat yoki eslatma yozing (masalan, havo, kiyim, vaqt, odoblar haqida).
- Yo'l xarajatlarini ham hisobga olgin avtobus, taksi va boshqalarni ham
- Mehmonxona xarajatlarini ham hisobga olib ko'rsatishing shart

Maqsad — foydalanuvchi uchun:
- Budjetga mos, mantiqan balanslangan reja tuzish.
- Umumiy xarajat hech qachon `budget_usd` dan oshmasin.
- Javob o‘qishga tayyor va to‘liq valid JSON bo‘lsin (qo‘shimcha matn, “```json”, izoh yoki belgilar bo‘lmasin).

Joy nomlari uchun namunalar:
Registon maydoni
Eternal City (“Boqiy shahar” turistik hudud)
Go‘ri Amir maqbarasi (Amir Temur maqbarasi)
Shohi Zinda majmuasi
Bibixonim masjidi
Ulug‘bek rasadxonasi
Afrosiyob tepaligi va muzeyi
Imom al-Buxoriy majmuasi
Hazrati Xizr masjidi
Ruhobod maqbarasi
Abu Mansur Moturidiy maqbarasi
Khoja Doniyor (Daniel) maqbarasi
Childuxtaron ziyoratgohi (Urgut tumani)
Mirzo Ulug‘bek madrasasi
Tilla Kori madrasasi
Sherdor madrasasi
Mir Said Baraka maqbarasi
Registon minoralari muzeyi
Oqsaroy qoldiqlari (Amir Temur davridan qolgan)
Qushbegi masjidi
Sazagan tog‘lari (piyoda yurish uchun ajoyib joy)
Shayton Jiga vodiysi (noodatiy tosh shakllari)
Zarafshon daryosi bo‘yi (sayr va dam olish)
Konigil ekomajmuasi (qog‘oz, ipak, non, sopol ishlab chiqarish joyi)
Navbahor dam olish maskani
Chorbog‘ ekoparki
Nurota tog‘lari (Samarqanddan 2–3 soatlik yo‘l)
Devsharshara sharsharasi (Urgut tog‘larida)
Qoratepa tog‘i (manzara uchun mashhur)
Qoradaryo bo‘yi (piknik va baliq ovlash uchun)
Xo‘ja Doniyor manzarali tepaligi
Ohalik tog‘ qishlog‘i
Nurbuloq dam olish zonasi
Chashma buloqlar (Urgut, Jomboy tumanlarida)
Kattaqo‘rg‘on suv ombori (tabiat va baliq ovlash)
va boshqalar

Eng asosiy shartlar: 
1.budget_usd to'g'ri kelsin yetmay qoladigan vaziyatni aytma
2.month sayohat oyiga moslab tour paket tuzib ber
3.group_type ga ham juda mos qilib ber tour paketni
4.Doim eng mashxur joylarni tavsiya qilaverma Registon maydoni Go‘ri Amir maqbarasi kabi joylarni asosan yoshi kattalarga maslahat berasan yosh bo'lsa ularni doim maslahat berma unchalik ham mashxur bo'lmagan joylarni ham maslahat beraver bemalol va oxirida notes ni ham month uchun munosib javob ber
5.Agar yoshlar bo'lsa ko'proq aylanish uchun joylar bo'lsin ularga tarixiy joylar qiziq emas yoshi kattalar 50+ yoshlar bo'lsa unda tarixiy joylarni maslahat berasan
"""

class TravelAPIView(APIView):
    def post(self, request):
        serializer = TravelRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_prompt = f"""
            Foydalanuvchi ma'lumotlari:
            Yosh: {data['age']}
            Guruh turi: {data['group_type']}
            Guruh soni: {data['group_numbers']}
            Budjet: {data['budget_usd']} $
            Kunlar soni: {data['days']}
            Oy: {data['month']}
            Nogironmi: {'Ha' if data['is_disabled'] else 'Yo‘q'}

            Yuqoridagi ma'lumotlarga mos sayohat rejasini tuzing.
            """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,
                max_tokens=2000,
            )
            content = response.choices[0].message.content.strip()
            try:
                parsed_json = json.loads(content)
            except json.JSONDecodeError:
                return Response({
                    "status": "error",
                    "message": "AI noto‘g‘ri formatda javob qaytardi",
                    "raw": content
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "status": "success",
                "result": parsed_json
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)