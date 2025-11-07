# assistant/services.py

import re
import os
import json
import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import NotFound, ResourceExhausted

DEFAULT_MODEL = "gemini-2.0-flash"

def sanitize_prompt(user_input: str) -> str:
    dangerous_keywords = ["api_key", "GEMINI_API_KEY", "system prompt", "ignore", "bypass", "token", "password"]
    for word in dangerous_keywords:
        user_input = user_input.replace(word, "[REDACTED]")

    return f"""
You are an intelligent travel recommendation assistant.
Never reveal system information or API keys.

TASK:
Analyze the user's travel intent and respond in pure JSON only (no markdown or text).
If you must format JSON, output plain JSON without ```json or code fences.

JSON format:
{{
  "primary_destination": {{
    "location": "Main location",
    "region": "Country or area",
    "interests": ["Interest1", "Interest2"],
    "description": "Short overview"
  }},
  "nearby_suggestions": [
    {{
      "location": "Suggestion1",
      "region": "Country or area",
      "interests": ["Interest1"],
      "description": "Short overview"
    }},
    ...
  ]
}}

User message:
\"\"\"{user_input}\"\"\"
""".strip()

def heuristic_classify(user_input: str) -> dict:
    """A tiny deterministic fallback to provide a consistent JSON shape when the model is unavailable.

    This is intentionally conservative — it attempts to pull a likely location word or phrase
    from the user's input and returns a minimal classification structure so the frontend
    can continue working during development or quota outages.
    """
    # look for patterns like 'in London' or 'about Paris' or 'to Tokyo'
    m = re.search(r"\b(?:in|about|to)\s+([A-Z][A-Za-z\s]+)", user_input)
    if m:
        loc = m.group(1).strip().rstrip(".")
    else:
        # fallback: any capitalized word sequences (e.g., 'New York')
        toks = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", user_input)
        loc = toks[0] if toks else None

    return {
        "primary_destination": {
            "location": loc or "Unknown",
            "region": "",
            "interests": [],
            "description": "Fallback classification (heuristic).",
        },
        "nearby_suggestions": [],
    }


def generate_safe_reply(user_input: str, model_name: str = DEFAULT_MODEL) -> dict:
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = sanitize_prompt(user_input)

    # Small retry/backoff for transient quota errors
    from time import sleep
    attempts = 3
    backoff = 1.0
    last_exc = None
    text = None
    for attempt in range(attempts):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 400,
                },
            )
            text = (response.text or "").strip()
            # successful generation — exit retry loop
            last_exc = None
            break
        except ResourceExhausted as rexc:
            # transient quota issue — retry with exponential backoff
            last_exc = rexc
            if attempt < attempts - 1:
                sleep(backoff)
                backoff *= 2
                continue
            # exhausted retries — break and handle below
            break
        except Exception as e:
            last_exc = e
            break

    # If we obtained text, sanitize and parse it
    if text:
        # 🧹 Remove markdown fences if present
        cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()

        # 🧱 Security sanitization
        if any(word in cleaned.lower() for word in ["api_key", "secret", "system prompt"]):
            return {"error": "Sanitized response — sensitive data removed."}

        # 🧩 Parse JSON safely
        try:
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError:
            # Try to extract a JSON substring if the model returned surrounding text.
            # Approach: find the first '{' and the last '}' and attempt to parse that slice.
            try:
                first = cleaned.find('{')
                last = cleaned.rfind('}')
                if first != -1 and last != -1 and last > first:
                    candidate = cleaned[first:last+1]
                    parsed = json.loads(candidate)
                    return parsed
            except Exception:
                pass

            # As a final fallback, try to find any JSON-like object using a simple regex
            try:
                m = re.search(r'(\{[\s\S]*\})', cleaned)
                if m:
                    parsed = json.loads(m.group(1))
                    return parsed
            except Exception:
                pass

            # Nothing parsed as JSON — return raw_text for the caller to decide
            return {"raw_text": cleaned}

    # If we reach here, generation failed — handle common failure cases
    if isinstance(last_exc, NotFound):
        return {"error": f"Model '{model_name}' not found or unsupported."}
    if isinstance(last_exc, ResourceExhausted):
        # Provide a lightweight deterministic fallback so the frontend can still show something useful
        fallback = heuristic_classify(user_input)
        return {
            "error": "Token quota exceeded. Try again later.",
            "fallback": fallback,
        }
    if last_exc is not None:
        return {"error": str(last_exc)}

    # Generic fallback (shouldn't normally happen)
    return {"error": "Unknown error during generation."}


def generate_plan(user_input: str, model_name: str = DEFAULT_MODEL) -> dict:
    """Generate a travel plan using Gemini API"""
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    # Extract budget and duration from input
    budget_match = re.search(r'budget\s+of\s+(?:Rs\.?|₹)?\s*(\d+)', user_input, re.IGNORECASE)
    days_match = re.search(r'(\d+)\s*days?', user_input, re.IGNORECASE)
    
    budget = int(budget_match.group(1)) if budget_match else 0
    days = int(days_match.group(1)) if days_match else 3

    prompt = f'''Create a detailed {days}-day travel plan for {user_input}. Total budget: ₹{budget}

Return a JSON object exactly matching this format (no markdown, no extra text):

{{
  "summary": "Example: {days}-day Punjab cultural tour with local experiences within ₹{budget} budget",
  "itinerary": [
    {{
      "day": 1,
      "activities": [
        {{
          "type": "activity",
          "name": "Visit Golden Temple",
          "description": "Early morning visit to the spiritual heart of Sikhism",
          "average_cost": 0
        }},
        {{
          "type": "food",
          "name": "Traditional Punjabi Breakfast",
          "description": "Enjoy parathas and lassi at a local dhaba",
          "average_cost": 200
        }},
        {{
          "type": "transport",
          "name": "Local Transport",
          "description": "Auto-rickshaw/taxi for day's travel",
          "average_cost": 500
        }}
      ]
    }}
  ]
}}

Important:
1. Break down the {days} days into a clear itinerary
2. Each day should have 3-4 activities
3. Include transport, food, and sightseeing costs
4. Total cost must stay within ₹{budget}
5. Activity types must be: "activity", "food", "transport", or "hotel"
6. Make sure costs are realistic for the location'''

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2000,
                "top_p": 0.8
            }
        )
        
        text = (response.text or "").strip()
        
        # Clean any markdown code fences or extra text
        cleaned = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        
        try:
            # Try direct JSON parse first
            parsed = json.loads(cleaned)
            
            # Validate the required structure
            if not isinstance(parsed, dict):
                return {"error": "Response is not a valid JSON object"}
            
            if "summary" not in parsed or "itinerary" not in parsed:
                return {"error": "Response missing required fields"}
            
            if not isinstance(parsed["itinerary"], list):
                return {"error": "Itinerary must be an array"}
            
            # Validate each day's structure
            for day in parsed["itinerary"]:
                if not isinstance(day, dict) or "day" not in day or "activities" not in day:
                    return {"error": "Invalid day structure in itinerary"}
                
                if not isinstance(day["activities"], list):
                    return {"error": "Day activities must be an array"}
                
                for activity in day["activities"]:
                    required_fields = ["type", "name", "description", "average_cost"]
                    if not all(field in activity for field in required_fields):
                        return {"error": "Activity missing required fields"}
                    
                    if activity["type"] not in ["activity", "food", "transport", "hotel"]:
                        activity["type"] = "activity"  # Default to activity if invalid type
            
            return parsed
            
        except json.JSONDecodeError as e:
            # Try to extract JSON between braces
            try:
                first = cleaned.find('{')
                last = cleaned.rfind('}')
                if first != -1 and last != -1:
                    return json.loads(cleaned[first:last+1])
            except Exception:
                pass
            
            return {"error": f"Failed to parse plan: {str(e)}"}
            
    except ResourceExhausted:
        return {"error": "API quota exceeded. Please try again later."}
    except Exception as e:
        return {"error": f"Failed to generate plan: {str(e)}"}

    if isinstance(last_exc, NotFound):
        return {"error": f"Model '{model_name}' not found or unsupported."}
    if isinstance(last_exc, ResourceExhausted):
        return {"error": "Token quota exceeded. Try again later."}
    if last_exc is not None:
        return {"error": str(last_exc)}

    return {"error": "Unknown error during generation."}

