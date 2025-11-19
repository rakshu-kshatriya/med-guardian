"""
AI-powered health advisory service.
This version is Railway-safe and works fully even without OPENAI_API_KEY.
If OPENAI_API_KEY exists, it uses OpenAI. Otherwise, a high-quality
fallback advisory is returned with reasoning + precautions.
"""

import os
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PUBLIC FUNCTION
# ---------------------------------------------------------
def get_advisory(disease: str, city: str, aqi: float, temp: float) -> Dict[str, any]:
    """
    Returns a structured advisory:
    {
        "reasoning": "...",
        "precautions": ["...", "..."]
    }
    """

    api_key = os.getenv("OPENAI_API_KEY")

    # No API key → use fallback advisory
    if not api_key:
        logger.info("OPENAI_API_KEY not set, using fallback advisory")
        return _fallback_advisory(disease, city, aqi, temp)

    # If API key exists, attempt to call OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""
Act as a public health officer for {city}, India.
Provide a structured advisory for the disease: {disease}.

Include two parts only:

Reasoning:
(1 paragraph with local factors such as AQI {aqi:.0f}, temperature {temp:.1f}°C)

Precautions:
(5–7 bullet points specific to {city} and {disease})
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a public health expert generating concise advisories."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        text = response.choices[0].message.content
        reasoning, precautions = _parse(text)

        return {
            "reasoning": reasoning,
            "precautions": precautions
        }

    except Exception as e:
        logger.error(f"OpenAI API failed: {e}")
        return _fallback_advisory(disease, city, aqi, temp)


# ---------------------------------------------------------
# PARSER
# ---------------------------------------------------------
def _parse(text: str) -> Tuple[str, list]:
    """Parse advisory into (reasoning, precautions)."""

    lines = text.split("\n")
    reasoning = []
    precautions = []
    mode = "reasoning"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.lower().startswith("precautions"):
            mode = "prec"
            continue

        if mode == "reasoning":
            if line.lower().startswith("reasoning:"):
                reasoning.append(line.replace("Reasoning:", "").strip())
            else:
                reasoning.append(line)

        else:
            # extract numbered or bulleted items
            if line[0].isdigit() or line.startswith("-"):
                part = line.split(".", 1)[-1].strip().lstrip("- ").strip()
                if part:
                    precautions.append(part)

    # safety checks
    if not reasoning:
        reasoning = ["Based on current health monitoring data, risk levels are elevated."]

    if len(precautions) < 5:
        precautions.extend(_default_precautions()[:5 - len(precautions)])

    return " ".join(reasoning), precautions[:7]


# ---------------------------------------------------------
# FALLBACK ADVISORY (used when no OpenAI key)
# ---------------------------------------------------------
def _fallback_advisory(disease: str, city: str, aqi: float, temp: float) -> Dict[str, any]:
    """Deterministic, safe fallback advisory."""

    # AQI risk
    if aqi >= 150:
        aqi_desc = "high air pollution levels"
    elif aqi >= 100:
        aqi_desc = "moderate air pollution"
    else:
        aqi_desc = "good air quality"

    # temperature risk
    if temp > 30:
        temp_desc = "hot weather conditions"
    elif temp < 20:
        temp_desc = "cooler temperatures"
    else:
        temp_desc = "moderate climate"

    reasoning = (
        f"In {city}, recent monitoring shows an increased risk of {disease}. "
        f"Environmental conditions such as {aqi_desc} (AQI {aqi:.0f}) and "
        f"{temp_desc} (avg {temp:.1f}°C) may contribute to higher vulnerability. "
        f"Precautionary measures are recommended to reduce exposure and maintain health."
    )

    precautions = [
        f"Maintain personal hygiene and wash hands frequently in {city}.",
        "Avoid large crowds and practice social distancing when possible.",
        "Wear a mask outdoors if pollution levels are noticeable.",
        f"Stay hydrated and take rest breaks due to {temp_desc}.",
        "Monitor symptoms such as fever or cough and seek care if needed.",
        "Keep indoor spaces well ventilated.",
        "Follow local health advisories issued by government agencies."
    ]

    return {"reasoning": reasoning, "precautions": precautions}


# ---------------------------------------------------------
# DEFAULT PRECAUTIONS
# ---------------------------------------------------------
def _default_precautions():
    return [
        "Maintain personal hygiene and wash hands frequently.",
        "Avoid crowded places and maintain distance.",
        "Wear protective masks outdoors.",
        "Stay hydrated and follow a healthy diet.",
        "Seek medical care if symptoms develop.",
        "Ensure indoor ventilation.",
        "Follow local health guidelines."
    ]
