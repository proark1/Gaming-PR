"""
AI Pitch Generator — creates complete outreach emails from scratch.

Uses Claude Sonnet for high-quality pitch generation, combining company profile
data with contact-specific context to produce tailored investment pitches,
sponsorship proposals, press pitches, and review key requests.
"""
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.company import CompanyProfile
from app.models.investor import GamingInvestor
from app.models.outlet import GamingOutlet
from app.models.pitch import GeneratedPitch
from app.models.streamer import Streamer
from app.services.profile_service import (
    compile_investor_profile,
    compile_outlet_profile,
    compile_streamer_profile,
)

logger = logging.getLogger(__name__)

PITCH_MODEL = "claude-sonnet-4-20250514"

_TARGET_MODELS = {
    "vc": GamingInvestor,
    "streamer": Streamer,
    "outlet": GamingOutlet,
}

_PROFILE_COMPILERS = {
    "vc": compile_investor_profile,
    "streamer": compile_streamer_profile,
    "outlet": compile_outlet_profile,
}


def _build_pitch_prompt(
    company_profile: str,
    contact_profile: str,
    pitch_type: str,
    user_instructions: str = "",
    tone: str = "professional",
) -> str:
    """Build a Claude prompt for pitch generation based on type."""

    type_instructions = {
        "investment": (
            "Write a compelling investment pitch email. Focus on:\n"
            "- Traction metrics and growth potential\n"
            "- Market size and opportunity\n"
            "- Team background and credibility\n"
            "- Specific funding ask and use of funds\n"
            "- Why THIS investor specifically (portfolio synergy, thesis alignment)\n"
            "- Clear call to action (meeting request)\n"
            "Keep it concise — investors get hundreds of pitches."
        ),
        "sponsorship": (
            "Write a streamer sponsorship proposal. Focus on:\n"
            "- Why the game fits their audience and content style\n"
            "- Specific deliverables you're proposing (streams, videos, social posts)\n"
            "- Audience overlap and engagement value\n"
            "- What you're offering (payment, game keys, exclusivity)\n"
            "- Estimated value/CPM for the streamer\n"
            "- Make it exciting — streamers want to play games their audience will love."
        ),
        "press_coverage": (
            "Write a press pitch email to a gaming journalist/outlet. Focus on:\n"
            "- The news angle — why this story matters NOW\n"
            "- What makes the game unique or newsworthy\n"
            "- Available press assets (trailer, screenshots, media kit)\n"
            "- Exclusive or early access availability\n"
            "- Match the outlet's editorial focus and audience\n"
            "- Keep it short — journalists are busy."
        ),
        "review_key": (
            "Write a review key request email. Focus on:\n"
            "- Brief game description and platform availability\n"
            "- Release date and any embargo details\n"
            "- What makes the game review-worthy\n"
            "- Offer to provide additional assets or interviews\n"
            "- Very concise — this is a straightforward request."
        ),
    }

    tone_guide = {
        "formal": "Use a formal, professional business tone.",
        "casual": "Use a friendly, casual tone while remaining professional.",
        "enthusiastic": "Use an enthusiastic, energetic tone that conveys passion.",
        "professional": "Use a clean, professional tone — confident but not stiff.",
    }

    prompt = (
        f"You are an expert gaming industry PR and business development writer.\n\n"
        f"GAME/COMPANY PROFILE:\n{company_profile}\n\n"
        f"CONTACT PROFILE:\n{contact_profile}\n\n"
        f"PITCH TYPE: {pitch_type}\n\n"
        f"INSTRUCTIONS:\n{type_instructions.get(pitch_type, type_instructions['press_coverage'])}\n\n"
        f"TONE: {tone_guide.get(tone, tone_guide['professional'])}\n\n"
    )

    if user_instructions:
        prompt += f"ADDITIONAL INSTRUCTIONS FROM USER:\n{user_instructions}\n\n"

    prompt += (
        "Generate the email with this exact format:\n"
        "SUBJECT: [subject line]\n"
        "BODY:\n[email body]\n\n"
        "Do NOT include placeholder brackets. Use actual names and details from the profiles."
    )

    return prompt


def generate_pitch(
    db: Session,
    company_id: int,
    target_type: str,
    target_id: int,
    pitch_type: str,
    user_instructions: str = "",
    tone: str = "professional",
) -> GeneratedPitch:
    """Generate a single pitch using Claude AI."""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    model_cls = _TARGET_MODELS.get(target_type)
    if not model_cls:
        raise ValueError(f"Invalid target_type: {target_type}")

    contact = db.query(model_cls).filter(model_cls.id == target_id).first()
    if not contact:
        raise ValueError(f"{target_type} {target_id} not found")

    compiler = _PROFILE_COMPILERS[target_type]
    contact_profile_str = compiler(contact)

    company_data = {
        "name": company.name,
        "description": company.description,
        "genre": company.genre,
        "platforms": company.platforms,
        "release_stage": company.release_stage,
        "funding_stage": company.funding_stage,
        "funding_target_k": company.funding_target_k,
        "marketing_budget_k": company.marketing_budget_k,
        "team_size": company.team_size,
        "revenue_model": company.revenue_model,
        "target_audience": company.target_audience,
        "trailer_url": company.trailer_url,
        "pitch_deck_url": company.pitch_deck_url,
        "media_kit_url": company.media_kit_url,
    }
    company_profile_str = json.dumps(company_data, indent=2, default=str)

    # Create the pitch record
    pitch = GeneratedPitch(
        company_id=company_id,
        target_type=target_type,
        target_id=target_id,
        target_name=getattr(contact, "name", "Unknown"),
        pitch_type=pitch_type,
        tone=tone,
        user_instructions=user_instructions or None,
        company_snapshot=company_data,
        contact_snapshot=json.loads(contact_profile_str) if contact_profile_str else None,
        status="generating",
        claude_model_used=PITCH_MODEL,
    )
    db.add(pitch)
    db.flush()

    # Call Claude
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = _build_pitch_prompt(
            company_profile_str, contact_profile_str,
            pitch_type, user_instructions, tone,
        )
        response = client.messages.create(
            model=PITCH_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        output = response.content[0].text
        pitch.generation_tokens = response.usage.output_tokens

        # Parse SUBJECT: / BODY:
        subject = ""
        body = output
        if "SUBJECT:" in output:
            parts = output.split("BODY:", 1)
            subject_part = parts[0]
            subject = subject_part.replace("SUBJECT:", "").strip()
            if len(parts) > 1:
                body = parts[1].strip()

        pitch.subject_line = subject
        pitch.body = body
        pitch.status = "completed"

    except Exception as e:
        logger.error("Pitch generation failed: %s", e)
        pitch.status = "failed"
        pitch.error_message = str(e)

    db.commit()
    db.refresh(pitch)
    return pitch


def generate_bulk_pitches(
    db: Session,
    company_id: int,
    target_type: str,
    target_ids: list[int],
    pitch_type: str,
    user_instructions: str = "",
    tone: str = "professional",
) -> list[GeneratedPitch]:
    """Generate pitches for multiple targets."""
    results = []
    for tid in target_ids:
        try:
            p = generate_pitch(db, company_id, target_type, tid, pitch_type, user_instructions, tone)
            results.append(p)
        except Exception as e:
            logger.error("Bulk pitch failed for %s %d: %s", target_type, tid, e)
    return results


def approve_pitch(
    db: Session,
    pitch_id: int,
    edited_subject: Optional[str] = None,
    edited_body: Optional[str] = None,
) -> GeneratedPitch:
    """Approve a pitch, optionally editing content."""
    from datetime import datetime, timezone

    pitch = db.query(GeneratedPitch).filter(GeneratedPitch.id == pitch_id).first()
    if not pitch:
        raise ValueError(f"Pitch {pitch_id} not found")
    if pitch.status not in ("completed", "approved"):
        raise ValueError(f"Cannot approve pitch in status: {pitch.status}")

    if edited_subject is not None:
        pitch.subject_line = edited_subject
    if edited_body is not None:
        pitch.body = edited_body

    pitch.status = "approved"
    pitch.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pitch)
    return pitch


def list_pitches(
    db: Session,
    company_id: Optional[int] = None,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[GeneratedPitch]:
    """List pitches with optional filters."""
    q = db.query(GeneratedPitch)
    if company_id:
        q = q.filter(GeneratedPitch.company_id == company_id)
    if target_type:
        q = q.filter(GeneratedPitch.target_type == target_type)
    if status:
        q = q.filter(GeneratedPitch.status == status)
    return q.order_by(GeneratedPitch.created_at.desc()).offset(offset).limit(limit).all()
