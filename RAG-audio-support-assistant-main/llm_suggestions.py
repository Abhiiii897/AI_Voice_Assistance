"""
Generates suggestions using Google Gemini.
"""
import os
import re
import json
import logging
import time
from google import genai
from google.genai import types

log_dir = "logs/suggestions"
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger("suggestions")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(os.path.join(log_dir, "suggestions.log"))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)


class SuggestionGenerator:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.rate_limited_until = 0.0

    def generate_suggestions(self, conversation_history, context_docs, sentiment=None):
        now = time.time()
        if now < self.rate_limited_until:
            retry_in = int(self.rate_limited_until - now)
            print(f"[LLM] Skipping Gemini (cooldown active, retry in {retry_in}s)")
            return self._fallback(conversation_history, allow_remote=False, context_docs=context_docs)
        # ── 0. OFFLINE GREETING CHECK (Zero Latency / No Quota) ──
        # Fixes "Hi" not being conversational when API is slow/dead
        last_msg = conversation_history.strip().split('\n')[-1].lower()
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon"]
        if any(g in last_msg for g in greetings) and len(last_msg) < 20:
            print("[LLM] Offline greeting detected. Returning instant response.")
            return {
                "suggestions": [{
                    "title": "Answer", 
                    "description": "Hello! I'm your support assistant. I can help with troubleshooting errors, explaining machine features, or guiding you through maintenance. What's happening with your machine?"
                }]
            }

        # Build context
        context_items = []
        for i, doc in enumerate(context_docs):
            cleaned = doc.strip().replace('\n', ' ')[:400]
            context_items.append(f"[Source {i+1}]: {cleaned}")
        docs_context = "\n\n".join(context_items)

        # Build Sentiment Context
        sentiment_context = ""
        if sentiment:
            s_val = sentiment.get('sentiment', 'Neutral')
            sentiment_context = f"""
SENTIMENT ANALYSIS:
Current User Sentiment: {s_val}
Detected Intent: {sentiment.get('category', 'General')}

ADAPT YOUR TONE:
- If Frustrated: Be calm, empathetic, and extra clear.
- If Confused: Simplify explanations and provide step-by-step guidance.
- If Urgent: Be concise and direct.
- If Curious: Provide richer explanations.
- If Positive/Neutral/General: Be natural, professional, and helpful.

Always respond in a natural, human-friendly tone.
Never mention sentiment explicitly to the user.
"""

        prompt = f"""You are a support copilot.
{sentiment_context}

Goal:
- Return a short, conversational support answer for the agent.
- Do NOT summarize the user's sentence verbatim.
- Infer likely technical cause and give immediate next actions.

Return ONLY JSON:
{{
  "suggestions": [
    {{
      "title": "Answer",
      "description": "This usually points to .... First, check .... Then verify .... If that does not fix it, do ...."
    }}
  ],
  "doc_references": [
    {{
      "source_index": 0,
      "page": 1,
      "section": "General",
      "match_score": 85,
      "used": true
    }}
  ]
}}

Constraints:
- description max 70 words
- 2 to 4 short conversational sentences
- never paste raw manual text; paraphrase only

AVAILABLE MANUAL EXCERPTS:
{docs_context}

CUSTOMER INPUT:
{conversation_history}
"""

        raw_text = ""
        try:
            models_to_try = ['gemini-2.0-flash']
            
            for attempt, model_name in enumerate(models_to_try):
                try:
                    print(f"[LLM] Attempt {attempt+1}/{len(models_to_try)} using model: {model_name}")
                    config = types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=220,
                        response_mime_type='application/json'
                    )
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    raw_text = response.text.strip()
                    if raw_text:
                        break # Success
                except Exception as e:
                    error_str = str(e)
                    print(f"[LLM] Error with {model_name}: {error_str}")
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        self.rate_limited_until = time.time() + 120
                        print("[LLM] Rate limited (429). Entering 120s cooldown.")
                        return self._fallback(conversation_history, allow_remote=False, context_docs=context_docs)
                    raise e

            # ── Always print raw response to terminal ──
            print(f"\\n{'='*60}")
            print(f"[LLM] RAW GEMINI RESPONSE:")
            print(raw_text)
            print(f"{'='*60}\\n")

            # Strip markdown fences
            clean = re.sub(r'```(?:json)?', '', raw_text).replace('```', '').strip()

            # Find JSON boundaries
            start = clean.find("{")
            end = clean.rfind("}") + 1

            if start == -1 or end == 0:
                print(f"[LLM] ERROR: No {{ }} found in response!")
                return self._fallback(conversation_history, context_docs=context_docs)

            json_str = clean[start:end]
            data = json.loads(json_str)

            # Validate
            if not isinstance(data.get("suggestions"), list) or len(data["suggestions"]) == 0:
data["suggestions"] = [{"title": "Answer", "description": "Please refer to the support documentation."}]

            # Force title = "Answer"
            for s in data["suggestions"]:
                s["title"] = "Answer"
                if "description" in s:
                    desc = re.sub(r'/[Gg]\d+', '', s["description"]).strip()
                    desc = re.sub(r'(?is)manual hint:\s*.*?(?=quick checks:|$)', '', desc).strip()
                    desc = re.sub(r'\.{3,}', '...', desc)
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    if len(desc) > 260 or desc.count('/') > 3:
                        desc = self._fallback(
                            conversation_history,
                            allow_remote=False,
                            context_docs=context_docs
                        )["suggestions"][0]["description"]
                    desc = desc.replace("Likely issue:", "").replace("Quick checks:", "").strip()
                    s["description"] = desc[:280]

            # Filter references
            refs = [r for r in data.get("doc_references", [])
                    if r.get("match_score", 0) >= 40 and r.get("used", False)]
            if refs:
                data["doc_references"] = refs
            else:
                data.pop("doc_references", None)

            print(f"[LLM] ✅ Answer: {data['suggestions'][0]['description'][:100]}...")
            return data

        except json.JSONDecodeError as e:
            print(f"[LLM] JSON PARSE ERROR: {e}")
            print(f"[LLM] String that failed: {raw_text[:300]}")
            return self._fallback(conversation_history, context_docs=context_docs)

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                self.rate_limited_until = time.time() + 120
                print("[LLM] Rate limited (429). Entering 120s cooldown.")
                return self._fallback(conversation_history, allow_remote=False, context_docs=context_docs)
            print(f"[LLM] EXCEPTION: {type(e).__name__}: {e}")
            return self._fallback(conversation_history, context_docs=context_docs)

    def _fallback(self, conversation_history="", allow_remote=True, context_docs=None):
        """
        Fallback that still calls Gemini but with the simplest possible prompt.
        This way we never return a hardcoded generic message.
        """
        def local_summary(history: str) -> str:
            text = (history or "").strip()
            if not text:
                return (
                    "I need one more detail to be precise. Please share the exact alarm text on the controller. "
                    "Then I can give a targeted fix path in one step."
                )

            lowered = text.lower()
            likely_issue = "machine state or setup mismatch near the failing operation"
            steps = [
                "Confirm exact alarm/error text shown on the controller.",
                "Check recent changes: tool, material, program, offsets, and setup.",
                "Run a safe re-test and record the first operation that fails.",
            ]

            if any(k in lowered for k in ["air", "pressure", "pneumatic"]):
                likely_issue = "pneumatic pressure instability or air-supply fault"
                steps[1] = "Check air supply pressure and stability against machine requirements."
            elif any(k in lowered for k in ["axis", "servo", "motor", "drive"]):
                likely_issue = "axis/servo/drive alarm or travel obstruction"
                steps[1] = "Check axis/servo status, drive alarms, and travel obstruction."
            elif any(k in lowered for k in ["vacuum", "hold", "suction"]):
                likely_issue = "insufficient vacuum hold or leakage"
                steps[1] = "Check vacuum level, leaks, and workpiece hold integrity."
            elif any(k in lowered for k in ["tool", "spindle"]):
                likely_issue = "spindle/tool condition or tool-change sequence fault"
                steps[1] = "Check tool condition, spindle load trend, and tool-change state."
            elif any(k in lowered for k in ["program", "nc", "g-code"]):
                likely_issue = "program path/offset mismatch near failure"
                steps[1] = "Verify recent program edits, offsets, and path around the failing step."

            return (
                f"This most likely points to {likely_issue}. "
                f"First, {steps[0].lower()} Then, {steps[1].lower()} "
                f"If it still fails, {steps[2].lower()}"
            )

        if not allow_remote:
            return {
                "suggestions": [{
                    "title": "Answer",
                    "description": local_summary(conversation_history)
                }]
            }

        print("[LLM] Attempting simple fallback call to Gemini...")
        try:
            simple_prompt = f"You are a helpful assistant. The user said: '{conversation_history}'. Respond naturally in 1 sentence."
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=simple_prompt,
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=100)
            )
            answer = response.text.strip()
            print(f"[LLM] Fallback answer: {answer[:100]}")
            return {
                "suggestions": [{"title": "Answer", "description": answer}]
            }
        except Exception as e:
            print(f"[LLM] Fallback also failed: {e}")
            return {
                "suggestions": [{"title": "Answer", "description": local_summary(conversation_history)}]
            }


