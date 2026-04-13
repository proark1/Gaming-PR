"""
Message Generation Service
Generates personalized outreach messages for outlets, streamers, and gaming VCs
based on their scraped data and profile information.
"""
import html
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer
from app.models.gaming_vc import GamingVC
from app.models.outreach import OutreachMessage

logger = logging.getLogger(__name__)


# ─── Template Helpers ───

def _personalize_greeting(name: str, tone: str) -> str:
    """Generate a personalized greeting based on tone."""
    if tone == "casual":
        return f"Hey {name},"
    elif tone == "enthusiastic":
        return f"Hi {name}!"
    elif tone == "formal":
        return f"Dear {name},"
    return f"Hi {name},"


def _format_list_html(items: list[str], max_items: int = 5) -> str:
    """Format a list as HTML bullet points."""
    if not items:
        return ""
    display = items[:max_items]
    lines = "".join(f"<li>{html.escape(item)}</li>" for item in display)
    return f"<ul>{lines}</ul>"


def _format_selling_points(points: list[str]) -> str:
    """Format key selling points as HTML."""
    if not points:
        return ""
    lines = "".join(f"<li><strong>{html.escape(p)}</strong></li>" for p in points)
    return f"<ul>{lines}</ul>"


def _closing(tone: str) -> str:
    """Generate a closing based on tone."""
    if tone == "casual":
        return "Cheers,"
    elif tone == "enthusiastic":
        return "Can't wait to hear from you!"
    elif tone == "formal":
        return "Respectfully,"
    return "Best regards,"


# ─── Outlet Message Generation ───

def _generate_outlet_pitch(outlet: GamingOutlet, game_title: str, game_description: str,
                           selling_points: list[str], tone: str, custom_context: str) -> tuple[str, str, dict]:
    """Generate a pitch email for a gaming news outlet."""
    recipient_name = outlet.editor_in_chief or outlet.name
    personalization = {}

    # Build personalized opening based on outlet data
    opening_lines = []
    if outlet.editorial_focus:
        focus = ", ".join(outlet.editorial_focus[:3])
        opening_lines.append(f"I'm reaching out because {outlet.name}'s focus on {focus} makes you an ideal outlet for this announcement.")
        personalization["editorial_focus"] = outlet.editorial_focus
    elif outlet.category:
        cat_display = outlet.category.replace("_", " ").title()
        opening_lines.append(f"Given {outlet.name}'s excellent coverage of {cat_display}, I wanted to share an exciting new title with you.")
        personalization["category"] = outlet.category

    if outlet.language != "en":
        opening_lines.append(f"We're particularly excited to reach your {outlet.country or outlet.region} audience.")
        personalization["language"] = outlet.language
        personalization["region"] = outlet.country or outlet.region

    if outlet.monthly_visitors:
        personalization["monthly_visitors"] = outlet.monthly_visitors

    if outlet.platforms_covered:
        personalization["platforms_covered"] = outlet.platforms_covered
    if outlet.genres_covered:
        personalization["genres_covered"] = outlet.genres_covered

    opening = " ".join(opening_lines) if opening_lines else f"I'm reaching out to share an exciting new game with the {outlet.name} team."

    # Build subject
    subject = f"Exclusive: {game_title} - Press Coverage Opportunity for {outlet.name}"

    # Build body
    sp_html = _format_selling_points(selling_points) if selling_points else ""
    review_line = ""
    if outlet.publishes_reviews:
        review_line = "<p>We'd love to provide your team with a review copy if you're interested in covering the game.</p>"
    elif outlet.content_types_accepted:
        accepted = ", ".join(outlet.content_types_accepted[:3])
        review_line = f"<p>We're happy to provide {accepted} materials for your coverage.</p>"

    submission_line = ""
    if outlet.submission_email:
        submission_line = f"<p><em>I noticed you accept pitches at {outlet.submission_email} - happy to follow up there as well.</em></p>"
    elif outlet.preferred_contact_method:
        submission_line = f"<p><em>I understand your preferred contact method is {outlet.preferred_contact_method}.</em></p>"

    body_html = f"""
<p>{_personalize_greeting(recipient_name, tone)}</p>
<p>{opening}</p>
<p>I'm excited to introduce <strong>{html.escape(game_title)}</strong>{f" - {html.escape(game_description)}" if game_description else ""}.</p>
{f"<p><strong>Key highlights:</strong></p>{sp_html}" if sp_html else ""}
{review_line}
{submission_line}
{f"<p>{html.escape(custom_context)}</p>" if custom_context else ""}
<p>I'd be happy to provide press assets, arrange an interview with the development team, or set up an exclusive preview. Please let me know what would work best for {outlet.name}.</p>
<p>{_closing(tone)}</p>
""".strip()

    body_text = BeautifulSoup_to_text(body_html)
    return subject, body_html, personalization


def _generate_outlet_coverage_request(outlet: GamingOutlet, game_title: str, game_description: str,
                                       selling_points: list[str], tone: str, custom_context: str) -> tuple[str, str, dict]:
    """Generate a coverage request for an outlet."""
    recipient_name = outlet.editor_in_chief or outlet.name
    personalization = {"type": "coverage_request"}

    subject = f"{game_title} - Coverage Request for {outlet.name}"

    games_line = ""
    if outlet.genres_covered:
        genres = ", ".join(outlet.genres_covered[:3])
        games_line = f"<p>Given your coverage of {genres} titles, we believe {html.escape(game_title)} would be a great fit for your audience.</p>"
        personalization["genres_covered"] = outlet.genres_covered

    body_html = f"""
<p>{_personalize_greeting(recipient_name, tone)}</p>
<p>I hope this message finds you well. I'm writing to request coverage of <strong>{html.escape(game_title)}</strong> on {outlet.name}.</p>
{f"<p>{html.escape(game_description)}</p>" if game_description else ""}
{games_line}
{_format_selling_points(selling_points) if selling_points else ""}
{f"<p>{html.escape(custom_context)}</p>" if custom_context else ""}
<p>We have press kits, screenshots, trailers, and dev interviews available. Would any of these be useful for your coverage?</p>
<p>{_closing(tone)}</p>
""".strip()

    return subject, body_html, personalization


# ─── Streamer Message Generation ───

def _generate_streamer_pitch(streamer: Streamer, game_title: str, game_description: str,
                              selling_points: list[str], tone: str, custom_context: str) -> tuple[str, str, dict]:
    """Generate a pitch for a gaming streamer."""
    personalization = {}

    # Personalize based on streamer's content
    opening_lines = []

    if streamer.primary_game and streamer.primary_game != "Variety":
        opening_lines.append(f"I've been watching your {streamer.primary_game} content and thought you'd love this new title.")
        personalization["primary_game"] = streamer.primary_game
    elif streamer.is_variety_streamer:
        opening_lines.append(f"As one of the best variety streamers out there, I think this game is right up your alley.")
        personalization["is_variety"] = True

    if streamer.content_style == "competitive":
        opening_lines.append("Given your competitive nature, I think you'll appreciate the skill-based mechanics.")
        personalization["content_style"] = "competitive"
    elif streamer.content_style == "educational":
        opening_lines.append("Your thorough, educational approach to games would be perfect for showcasing what makes this title special.")
        personalization["content_style"] = "educational"

    if streamer.games_played:
        personalization["games_played"] = streamer.games_played[:5]

    if streamer.follower_count:
        personalization["follower_count"] = streamer.follower_count
    if streamer.avg_viewers:
        personalization["avg_viewers"] = streamer.avg_viewers

    if streamer.tier:
        personalization["tier"] = streamer.tier

    opening = " ".join(opening_lines) if opening_lines else f"I'm a big fan of your content and wanted to reach out about an exciting opportunity."

    subject = f"{game_title} - Streaming Partnership Opportunity"

    # Customize offer based on what they accept
    offer_lines = []
    if streamer.accepts_game_codes:
        offer_lines.append("a complimentary game code")
    if streamer.accepts_sponsored_streams:
        offer_lines.append("a sponsored stream opportunity")
    offer = " and ".join(offer_lines) if offer_lines else "early access to the game"

    sponsor_line = ""
    if streamer.past_sponsors:
        sponsors = ", ".join(streamer.past_sponsors[:3])
        sponsor_line = f"<p>We've seen your fantastic partnerships with {sponsors} and believe our collaboration could be equally impactful.</p>"
        personalization["past_sponsors"] = streamer.past_sponsors

    achievements_line = ""
    if streamer.notable_achievements:
        achievement = streamer.notable_achievements[0]
        achievements_line = f"<p>Congrats on {html.escape(achievement)}, by the way - truly impressive!</p>"
        personalization["notable_achievement"] = achievement

    agency_line = ""
    if streamer.agency:
        agency_line = f"<p><em>Happy to coordinate through {html.escape(streamer.agency)} if that's easier.</em></p>"
        personalization["agency"] = streamer.agency

    body_html = f"""
<p>{_personalize_greeting(streamer.name, tone)}</p>
<p>{opening}</p>
{achievements_line}
<p>I'm reaching out to offer you {offer} for <strong>{html.escape(game_title)}</strong>{f" - {html.escape(game_description)}" if game_description else ""}.</p>
{_format_selling_points(selling_points) if selling_points else ""}
{sponsor_line}
{f"<p>{html.escape(custom_context)}</p>" if custom_context else ""}
<p>We think your {streamer.follower_count and f"{streamer.follower_count:,}+ followers" or "audience"} would absolutely love this game. Let us know if you're interested and we'll get everything set up!</p>
{agency_line}
<p>{_closing(tone)}</p>
""".strip()

    return subject, body_html, personalization


# ─── Gaming VC Message Generation ───

def _generate_vc_pitch(vc: GamingVC, game_title: str, game_description: str,
                        selling_points: list[str], tone: str, custom_context: str) -> tuple[str, str, dict]:
    """Generate an investment pitch for a gaming VC."""
    personalization = {}

    recipient_name = vc.name
    if vc.partners:
        # Address the most relevant partner
        gaming_partners = [p for p in vc.partners if "gaming" in (p.get("focus", "") or "").lower()]
        if gaming_partners:
            recipient_name = gaming_partners[0]["name"]
            personalization["addressed_partner"] = gaming_partners[0]
        else:
            recipient_name = vc.partners[0]["name"]
            personalization["addressed_partner"] = vc.partners[0]

    # Personalize based on VC's focus
    opening_lines = []

    if vc.investment_focus:
        focus = ", ".join(vc.investment_focus[:3])
        opening_lines.append(f"Given {vc.name}'s focus on {focus}, I believe we're a strong fit for your portfolio.")
        personalization["investment_focus"] = vc.investment_focus

    if vc.gaming_subsectors:
        personalization["gaming_subsectors"] = vc.gaming_subsectors

    if vc.thesis:
        opening_lines.append(f"Your thesis on the future of interactive entertainment resonates deeply with our vision.")
        personalization["thesis_aligned"] = True

    if vc.investment_stage:
        personalization["investment_stage"] = vc.investment_stage

    opening = " ".join(opening_lines) if opening_lines else f"I'm reaching out because {vc.name} has an impressive track record in gaming investment."

    subject = f"{game_title} - Investment Opportunity | Gaming Studio Pitch"

    portfolio_line = ""
    if vc.notable_portfolio:
        companies = ", ".join(p["name"] for p in vc.notable_portfolio[:3])
        portfolio_line = f"<p>Your portfolio including {companies} shows exactly the kind of visionary investments we admire.</p>"
        personalization["notable_portfolio"] = [p["name"] for p in vc.notable_portfolio[:3]]

    check_line = ""
    if vc.typical_check_size:
        check_line = f"<p>We're raising a round that aligns with your typical check size of {html.escape(vc.typical_check_size)}.</p>"
        personalization["check_size"] = vc.typical_check_size

    pitch_line = ""
    if vc.pitch_email:
        pitch_line = f"<p><em>Happy to send our full deck to {html.escape(vc.pitch_email)} if you'd prefer.</em></p>"
    elif vc.pitch_form_url:
        pitch_line = f"<p><em>I've also submitted through your pitch form for formal tracking.</em></p>"

    body_html = f"""
<p>{_personalize_greeting(recipient_name, "formal" if tone == "professional" else tone)}</p>
<p>{opening}</p>
{portfolio_line}
<p>I'm the founder of the studio behind <strong>{html.escape(game_title)}</strong>{f" - {html.escape(game_description)}" if game_description else ""}.</p>
{_format_selling_points(selling_points) if selling_points else ""}
{check_line}
{f"<p>{html.escape(custom_context)}</p>" if custom_context else ""}
<p>I'd love to schedule a call to walk you through our deck, traction metrics, and roadmap. Would you have 30 minutes this week or next?</p>
{pitch_line}
<p>{_closing("formal" if tone == "professional" else tone)}</p>
""".strip()

    return subject, body_html, personalization


def _generate_vc_intro(vc: GamingVC, game_title: str, game_description: str,
                        selling_points: list[str], tone: str, custom_context: str) -> tuple[str, str, dict]:
    """Generate an introductory email for a gaming VC."""
    personalization = {"type": "intro"}
    recipient_name = vc.partners[0]["name"] if vc.partners else vc.name

    subject = f"Introduction: {game_title} Studio x {vc.name}"

    events_line = ""
    if vc.events_attended:
        events = ", ".join(vc.events_attended[:3])
        events_line = f"<p>If you're attending {events} this year, we'd love to meet in person.</p>"
        personalization["events"] = vc.events_attended

    body_html = f"""
<p>{_personalize_greeting(recipient_name, tone)}</p>
<p>I wanted to introduce myself and our studio. We're building <strong>{html.escape(game_title)}</strong>{f", {html.escape(game_description)}" if game_description else ""}.</p>
{_format_selling_points(selling_points) if selling_points else ""}
<p>We're early but already showing strong signals, and {vc.name}'s expertise in gaming would be invaluable as we scale.</p>
{events_line}
{f"<p>{html.escape(custom_context)}</p>" if custom_context else ""}
<p>Would you be open to a brief intro call? I'd love to share more about what we're building.</p>
<p>{_closing(tone)}</p>
""".strip()

    return subject, body_html, personalization


# ─── Utility ───

def BeautifulSoup_to_text(html_content: str) -> str:
    """Convert HTML to plain text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


# ─── Base Message Variants (for edit-before-bulk flow) ───

def generate_message_variants(
    message_type: str = "pitch",
    tone: str = "professional",
    game_title: Optional[str] = None,
    game_description: Optional[str] = None,
    key_selling_points: Optional[list[str]] = None,
    custom_context: Optional[str] = None,
) -> dict:
    """
    Generate two distinct best-practice message variants for the user to
    choose from before bulk-sending. Each variant has a different angle.
    Returns dict with variant_a and variant_b, each having subject + body_text.
    """
    game_title = game_title or "Our Game"
    game_description = game_description or ""
    key_selling_points = key_selling_points or []
    custom_context = custom_context or ""

    greeting = _personalize_greeting("Editor", tone)
    sp_html = _format_selling_points(key_selling_points) if key_selling_points else ""
    closing = _closing(tone)
    desc_line = f" — {html.escape(game_description)}" if game_description else ""
    ctx_line = f"<p>{html.escape(custom_context)}</p>" if custom_context else ""

    if message_type == "coverage_request":
        # ── Variant A: Direct & Resource-Led ──
        a_subject = f"{game_title} — Coverage Opportunity + Press Kit Ready"
        a_html = f"""
<p>{greeting}</p>
<p>I'm reaching out because <strong>{html.escape(game_title)}</strong>{desc_line} is launching soon, and I'd love for your outlet to be among the first to cover it.</p>
{f"<p><strong>Why this stands out:</strong></p>{sp_html}" if sp_html else ""}
{ctx_line}
<p>We have a full press kit ready for you — including screenshots, key art, a gameplay trailer, and a fact sheet. I can also arrange an exclusive developer interview or early hands-on access if that would be helpful for your coverage.</p>
<p>Would any of these work for your editorial calendar? Happy to tailor the assets to what your outlet needs most.</p>
<p>{closing}</p>
""".strip()

        # ── Variant B: Story-Angle & Audience-Focused ──
        b_subject = f"Story Angle: {game_title} — A Fresh Take Your Readers Will Love"
        b_html = f"""
<p>{greeting}</p>
<p>I wanted to share a story angle I think would resonate with your audience.</p>
<p><strong>{html.escape(game_title)}</strong>{desc_line} brings something genuinely new to the table, and I believe your outlet is the perfect home for this story.</p>
{f"<p><strong>What makes it noteworthy:</strong></p>{sp_html}" if sp_html else ""}
{ctx_line}
<p>I can offer several coverage angles — a behind-the-scenes feature on the development journey, an interview with the creative director, or a first-look preview with exclusive assets. Whatever fits your editorial style best.</p>
<p>What angle would be most interesting for your outlet? I'll have everything ready to go.</p>
<p>{closing}</p>
""".strip()
    else:
        # ── Variant A: Exclusive Preview Pitch ──
        a_subject = f"Exclusive First Look: {game_title}"
        a_html = f"""
<p>{greeting}</p>
<p>I'm excited to offer your outlet an exclusive first look at <strong>{html.escape(game_title)}</strong>{desc_line}.</p>
{f"<p><strong>Key highlights:</strong></p>{sp_html}" if sp_html else ""}
{ctx_line}
<p>We're selectively reaching out to a small number of outlets we genuinely respect, and your team is at the top of that list. I can provide early access, a review copy, press assets, or arrange a hands-on session with the development team — whatever works best for you.</p>
<p>Would your outlet be interested in covering this? I'd love to set something up.</p>
<p>{closing}</p>
""".strip()

        # ── Variant B: Value Proposition & Partnership Pitch ──
        b_subject = f"{game_title} — Let's Get Your Audience Excited"
        b_html = f"""
<p>{greeting}</p>
<p>I have a game I think your audience will genuinely love, and I'd like to explore how we can work together to bring it to them.</p>
<p><strong>{html.escape(game_title)}</strong>{desc_line} is generating real buzz, and I believe a feature on your outlet would be a win for both sides.</p>
{f"<p><strong>Here's why:</strong></p>{sp_html}" if sp_html else ""}
{ctx_line}
<p>I'm flexible on format — whether that's a review copy, an exclusive trailer premiere, a developer Q&A, or a sponsored feature. I want to make this as easy as possible for your team.</p>
<p>What would be the best way to collaborate? Happy to jump on a quick call or send over a press kit right away.</p>
<p>{closing}</p>
""".strip()

    return {
        "variant_a": {
            "label": "Direct & Resource-Led" if message_type == "coverage_request" else "Exclusive Preview",
            "subject": a_subject,
            "body_text": BeautifulSoup_to_text(a_html),
        },
        "variant_b": {
            "label": "Story-Angle & Audience" if message_type == "coverage_request" else "Partnership & Value",
            "subject": b_subject,
            "body_text": BeautifulSoup_to_text(b_html),
        },
    }


# ─── Main Generation Function ───

def generate_message(
    db: Session,
    target_type: str,
    target_id: int,
    message_type: str = "pitch",
    tone: str = "professional",
    game_title: Optional[str] = None,
    game_description: Optional[str] = None,
    key_selling_points: Optional[list[str]] = None,
    custom_context: Optional[str] = None,
) -> OutreachMessage:
    """
    Generate a personalized outreach message for an outlet, streamer, or gaming VC.
    Uses all available data about the target to personalize the message.
    """
    game_title = game_title or "Our Game"
    game_description = game_description or ""
    key_selling_points = key_selling_points or []
    custom_context = custom_context or ""

    if target_type == "outlet":
        outlet = db.query(GamingOutlet).filter(GamingOutlet.id == target_id).first()
        if not outlet:
            raise ValueError(f"Outlet {target_id} not found")
        if message_type == "coverage_request":
            subject, body_html, personalization = _generate_outlet_coverage_request(
                outlet, game_title, game_description, key_selling_points, tone, custom_context)
        else:
            subject, body_html, personalization = _generate_outlet_pitch(
                outlet, game_title, game_description, key_selling_points, tone, custom_context)
        msg = OutreachMessage(
            target_type="outlet", outlet_id=target_id,
            recipient_name=outlet.editor_in_chief or outlet.name,
            recipient_email=outlet.submission_email or outlet.contact_email,
        )

    elif target_type == "streamer":
        streamer = db.query(Streamer).filter(Streamer.id == target_id).first()
        if not streamer:
            raise ValueError(f"Streamer {target_id} not found")
        subject, body_html, personalization = _generate_streamer_pitch(
            streamer, game_title, game_description, key_selling_points, tone, custom_context)
        msg = OutreachMessage(
            target_type="streamer", streamer_id=target_id,
            recipient_name=streamer.name,
            recipient_email=streamer.business_email or streamer.contact_email,
        )

    elif target_type == "gaming_vc":
        vc = db.query(GamingVC).filter(GamingVC.id == target_id).first()
        if not vc:
            raise ValueError(f"Gaming VC {target_id} not found")
        if message_type == "intro":
            subject, body_html, personalization = _generate_vc_intro(
                vc, game_title, game_description, key_selling_points, tone, custom_context)
        else:
            subject, body_html, personalization = _generate_vc_pitch(
                vc, game_title, game_description, key_selling_points, tone, custom_context)
        recipient_name = vc.partners[0]["name"] if vc.partners else vc.name
        msg = OutreachMessage(
            target_type="gaming_vc", gaming_vc_id=target_id,
            recipient_name=recipient_name,
            recipient_email=vc.pitch_email or vc.contact_email,
        )
    else:
        raise ValueError(f"Unknown target type: {target_type}")

    msg.subject = subject
    msg.body_html = body_html
    msg.body_text = BeautifulSoup_to_text(body_html)
    msg.message_type = message_type
    msg.tone = tone
    msg.personalization_data = personalization
    msg.game_title = game_title
    msg.game_description = game_description
    msg.key_selling_points = key_selling_points
    msg.status = "draft"

    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
