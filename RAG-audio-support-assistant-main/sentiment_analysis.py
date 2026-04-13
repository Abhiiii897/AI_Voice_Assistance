"""
Performs sentiment and intent detection using Google Gemini.
"""
from google import genai
from google.genai import types
import json
import re
import os
import time


class SentimentAnalyzer:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.rate_limited_until = 0.0
        self.last_result = {"sentiment": "Neutral", "category": "Machine Operation"}

    def analyze(self, text):
        text = (text or "").strip()
        if not text:
            return self.last_result

        now = time.time()
        if now < self.rate_limited_until:
            retry_in = int(self.rate_limited_until - now)
            print(f"[Sentiment] Skipping Gemini (cooldown active, retry in {retry_in}s)")
            return self.last_result

        prompt = f"""Classify this customer support message.

Customer message: "{text}"

Return ONLY this exact JSON. No markdown. No explanation. Just raw JSON:
{{"sentiment":"Neutral","category":"Machine Operation"}}

{{"sentiment":"Neutral","category":"Machine Operation"}}

sentiment must be EXACTLY one of: Positive, Neutral, Negative, Agitated, Confused, Frustrated, Curious, Urgent
category must be EXACTLY one of: Machine Operation, Maintenance & Parts, Technical Troubleshooting

Rules:
- Greetings like "hi", "hello" should be Neutral or Positive.
- "I don't understand" -> Confused
- "Hurry" / "Urgent" -> Urgent
- "Why?" / "How?" -> Curious or Neutral
- Profanity or anger -> Negative / Agitated"""

        raw_text = ""
        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100
            )
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=config
            )
            raw_text = response.text.strip()

            # Always print to terminal for debugging
            print(f"[Sentiment] Raw: {raw_text}")

            # Strip markdown fences
            clean = re.sub(r'```(?:json)?', '', raw_text).replace('```', '').strip()

            # Extract JSON
            start = clean.find("{")
            end = clean.rfind("}") + 1

            if start == -1 or end == 0:
                print(f"[Sentiment] ERROR: No JSON found in: {raw_text}")
                return self._fallback()

            data = json.loads(clean[start:end])

            # Validate sentiment
            valid_sentiments = ['Positive', 'Neutral', 'Negative', 'Agitated', 'Confused', 'Frustrated', 'Curious', 'Urgent']
            sentiment = "Neutral"
            raw_s = data.get("sentiment", "").strip()
            for v in valid_sentiments:
                if v.lower() == raw_s.lower():
                    sentiment = v
                    break

            # Validate category
            valid_categories = [
                'Machine Operation',
                'Technical Troubleshooting',
                'Maintenance & Parts',
            ]
            category = "Machine Operation"
            raw_c = data.get("category", "").strip()
            for v in valid_categories:
                if v.lower() == raw_c.lower():
                    category = v
                    break

            result = {"sentiment": sentiment, "category": category}
            self.last_result = result
            print(f"[Sentiment] ✅ sentiment={sentiment} category={category}")
            return result

        except json.JSONDecodeError as e:
            print(f"[Sentiment] JSON error: {e} | Raw: {raw_text}")
            return self._fallback()

        except Exception as e:
            error_text = str(e)
            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                self.rate_limited_until = time.time() + 90
                print("[Sentiment] Rate limited (429). Entering 90s cooldown.")
                return self._fallback()
            print(f"[Sentiment] EXCEPTION: {type(e).__name__}: {e}")
            return self._fallback()

    def _fallback(self):
        return self.last_result
