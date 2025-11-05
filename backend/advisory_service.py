"""
AI-powered health advisory service using OpenAI.
Returns structured advisories with reasoning and precautions.
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def get_advisory(disease: str, city: str, aqi: float, temp: float) -> Dict[str, any]:
    """
    Get AI-generated health advisory for a disease in a city.
    
    Args:
        disease: Disease name
        city: City name
        aqi: Air Quality Index
        temp: Average temperature
    
    Returns:
        Dict with 'reasoning' (str) and 'precautions' (list)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        logger.info("OPENAI_API_KEY not set, using fallback advisory")
        return _get_fallback_advisory(disease, city, aqi, temp)
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        prompt = f"""Act as a public health officer for {city}, India. For the disease {disease} (confirmed by social media trends), provide a single, structured advisory.

Use a paragraph of AI-driven reasoning explaining probable causes (e.g., humidity, AQI, or recent news).

Immediately follow it with an ordered list of 5–7 localized safety measures specific to that disease and city.

Output must be clearly separable into two parts: "Reasoning" and "Precautions".

Format your response as:
Reasoning: [your paragraph here]

Precautions:
1. [first precaution]
2. [second precaution]
...
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a public health expert providing concise, actionable health advisories for Indian cities."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        text = response.choices[0].message.content
        
        # Parse response
        reasoning, precautions = _parse_advisory_response(text)
        
        return {
            "reasoning": reasoning,
            "precautions": precautions
        }
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return _get_fallback_advisory(disease, city, aqi, temp)


def _parse_advisory_response(text: str) -> tuple:
    """Parse OpenAI response into reasoning and precautions."""
    lines = text.split('\n')
    reasoning_parts = []
    precautions = []
    in_reasoning = True
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.lower().startswith('precautions:'):
            in_reasoning = False
            continue
        
        if in_reasoning:
            if line.lower().startswith('reasoning:'):
                reasoning_parts.append(line.replace('Reasoning:', '').strip())
            else:
                reasoning_parts.append(line)
        else:
            # Extract numbered list items
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                precaution = line.split('.', 1)[-1].strip().lstrip('- ').strip()
                if precaution:
                    precautions.append(precaution)
    
    reasoning = ' '.join(reasoning_parts) if reasoning_parts else _get_default_reasoning()
    
    # If no precautions found, try to extract from full text
    if not precautions:
        # Try alternative parsing
        if 'precautions' in text.lower():
            parts = text.lower().split('precautions')
            if len(parts) > 1:
                prec_text = parts[1]
                for line in prec_text.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-')):
                        prec = line.split('.', 1)[-1].strip().lstrip('- ').strip()
                        if prec:
                            precautions.append(prec)
    
    # Ensure we have at least 5 precautions
    if len(precautions) < 5:
        default_precautions = _get_default_precautions(disease)
        precautions = precautions + default_precautions[:5 - len(precautions)]
    
    return reasoning, precautions[:7]  # Max 7 precautions


def _get_fallback_advisory(disease: str, city: str, aqi: float, temp: float) -> Dict[str, any]:
    """Return deterministic fallback advisory."""
    # Determine risk level based on AQI and temp
    if aqi > 100:
        aqi_risk = "elevated air pollution levels"
    elif aqi > 150:
        aqi_risk = "high air pollution levels"
    else:
        aqi_risk = "moderate air quality"
    
    if temp > 30:
        temp_risk = "high temperatures"
    elif temp < 20:
        temp_risk = "cooler weather conditions"
    else:
        temp_risk = "moderate temperatures"
    
    reasoning = f"Based on current health monitoring data for {city}, there has been an uptick in {disease} cases. This increase is likely associated with {aqi_risk} (AQI: {aqi:.0f}) and {temp_risk} (avg: {temp:.1f}°C). Seasonal factors and environmental conditions may be contributing to the spread. It is important to take preventive measures and monitor symptoms closely."
    
    precautions = [
        f"Maintain personal hygiene and wash hands frequently, especially in {city}'s climate conditions",
        "Avoid crowded places and maintain social distancing where possible",
        "Wear appropriate protective gear when outdoors, considering the current AQI levels",
        f"Stay hydrated and maintain a healthy diet to boost immunity, adapting to {city}'s weather",
        "Monitor symptoms daily and consult a healthcare provider if you experience any signs",
        "Ensure proper ventilation in indoor spaces to reduce exposure risk",
        "Follow local health department guidelines and get vaccinated if available"
    ]
    
    return {
        "reasoning": reasoning,
        "precautions": precautions
    }


def _get_default_reasoning() -> str:
    """Default reasoning text."""
    return "Based on current health monitoring data, there has been an increase in reported cases. This may be associated with environmental factors, seasonal patterns, or local transmission. It is important to take preventive measures and monitor symptoms closely."


def _get_default_precautions(disease: str) -> list:
    """Default precaution list."""
    return [
        f"Maintain personal hygiene and wash hands frequently",
        "Avoid crowded places and maintain social distancing",
        "Wear appropriate protective gear when outdoors",
        "Stay hydrated and maintain a healthy diet",
        "Monitor symptoms daily and consult healthcare provider if needed",
        "Ensure proper ventilation in indoor spaces",
        "Follow local health department guidelines"
    ]

