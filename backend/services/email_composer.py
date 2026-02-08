"""Email composition service - LLM generates personalized demo request emails."""

import os
from typing import Optional

from db.models import Tool, TimeSlot


def _get_openai_client():
    """Get OpenAI client if available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _compose_template_email(
    tool: Tool,
    fingerprint: dict,
    match_reasons: list[dict],
    suggested_times: list[TimeSlot],
) -> tuple[str, str]:
    """Fallback template when LLM unavailable."""
    subject = f"Demo Request: {tool.name}"

    industry = fingerprint.get('industry', 'software')
    project_type = fingerprint.get('project_type', 'project')

    # Build reasons text
    reasons_text = ""
    if match_reasons:
        reasons = [r.get('matched', '') for r in match_reasons[:2] if r.get('matched')]
        if reasons:
            reasons_text = f"particularly for {', '.join(reasons)}"

    # Build times text
    times_text = ""
    if suggested_times:
        times_list = [s.formatted for s in suggested_times[:3]]
        times_text = f"\n\nI'm available for a call at:\n" + "\n".join(f"  - {t}" for t in times_list)

    body = f"""Hi,

I'm working on a {industry} {project_type} and came across {tool.name}. I'm interested in learning more about how it could help our team{', ' + reasons_text if reasons_text else ''}.

Would it be possible to schedule a brief demo?{times_text}

Looking forward to hearing from you.

Best regards"""

    return subject, body


def compose_demo_email(
    tool: Tool,
    fingerprint: dict,
    match_reasons: list[dict],
    explanation: str,
    suggested_times: list[TimeSlot],
    sender_name: str = "there",
    conversation_context: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Compose a personalized demo request email using LLM.
    Falls back to template if LLM unavailable.

    Args:
        conversation_context: Optional dict with 'transcript' key containing
            list of {speaker, text} from voice conversation

    Returns: (subject, body)
    """
    client = _get_openai_client()

    # Try LLM composition
    if client:
        try:
            times_formatted = "\n".join([f"  - {slot.formatted}" for slot in suggested_times[:3]]) if suggested_times else "Flexible"

            # Build conversation context section
            conversation_section = ""
            if conversation_context and conversation_context.get("transcript"):
                transcript = conversation_context["transcript"]
                # Extract user messages for context
                user_messages = [t["text"] for t in transcript if t.get("speaker") in ("user", "human")]
                if user_messages:
                    conversation_section = f"""
VOICE CONVERSATION CONTEXT:
The user discussed this tool in a voice conversation. Key points they mentioned:
{chr(10).join([f'- "{msg[:200]}"' for msg in user_messages[:5]])}

Use these insights to personalize the email - reference specific interests or questions they raised.
"""

            prompt = f"""Write a professional demo request email for a software tool.

TOOL INFO:
- Name: {tool.name}
- Category: {tool.category}
- Description: {tool.description or 'N/A'}

PROJECT CONTEXT:
- Industry: {fingerprint.get('industry', 'general')}
- Project Type: {fingerprint.get('project_type', 'N/A')}
- Keywords: {', '.join(fingerprint.get('keywords', [])[:5])}
- Use Cases: {', '.join(fingerprint.get('use_cases', [])[:3])}

WHY THIS TOOL:
{explanation}

MATCH REASONS:
{chr(10).join([f"- {r.get('type', 'match')}: {r.get('matched', '')}" for r in match_reasons[:3]])}
{conversation_section}
SUGGESTED MEETING TIMES:
{times_formatted}

INSTRUCTIONS:
1. Subject: Short, specific, mention demo request + tool name
2. Body: 2-3 paragraphs max
   - Brief intro of the project/use case (don't mention company name if unknown)
   - Why specifically interested in this tool (use match reasons{' and conversation context' if conversation_section else ''})
   - Propose 2-3 meeting times
   - Professional sign-off
3. Tone: Professional but concise, not salesy
4. Don't be overly enthusiastic or use too many exclamation marks

Output format:
SUBJECT: [subject line]
BODY:
[email body]"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You write concise, professional demo request emails."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.choices[0].message.content or ""

            if "SUBJECT:" in content and "BODY:" in content:
                parts = content.split("BODY:", 1)
                subject_part = parts[0].replace("SUBJECT:", "").strip()
                subject = subject_part.split("\n")[0].strip()
                body = parts[1].strip()
                return subject, body

        except Exception as e:
            print(f"LLM email composition failed: {e}")

    # Fallback to template
    return _compose_template_email(tool, fingerprint, match_reasons, suggested_times)


def compose_batch_email_intro(tools: list[Tool], fingerprint: dict) -> str:
    """Generate intro text for batch email panel."""
    return f"Requesting demos for {len(tools)} tools matching your {fingerprint.get('project_type', 'project')}."
