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

def _build_selling_points_prose(points: list[str]) -> str:
    """Turn selling points into natural flowing prose, not bullet points."""
    if not points:
        return ""
    if len(points) == 1:
        return html.escape(points[0])
    last = html.escape(points[-1])
    rest = ", ".join(html.escape(p) for p in points[:-1])
    return f"{rest}, and {last}"


def generate_message_variants(
    message_type: str = "pitch",
    tone: str = "professional",
    game_title: Optional[str] = None,
    game_description: Optional[str] = None,
    key_selling_points: Optional[list[str]] = None,
    custom_context: Optional[str] = None,
) -> dict:
    """
    Generate two genuinely distinct, publication-ready message variants.
    Each uses a completely different structure, persuasion strategy, and voice.
    The user's game info is woven in naturally — not dumped as lists.
    Returns dict with variant_a and variant_b.
    """
    title = html.escape(game_title or "Our Game")
    desc = html.escape(game_description or "")
    points = key_selling_points or []
    ctx = html.escape(custom_context or "")
    sp_prose = _build_selling_points_prose(points)
    sp_bullets = _format_selling_points(points) if points else ""

    # Tone-adaptive elements
    if tone == "casual":
        g1, g2 = "Hey Editor,", "Hi Editor,"
        c1, c2 = "Talk soon!", "Looking forward to it!"
        opener_warm = "Hope you're having a great week."
    elif tone == "enthusiastic":
        g1, g2 = "Hi Editor!", "Hey Editor!"
        c1, c2 = "Can't wait to hear your thoughts!", "Really looking forward to connecting!"
        opener_warm = "I'm thrilled to be reaching out to you today."
    elif tone == "formal":
        g1, g2 = "Dear Editor,", "Dear Editor,"
        c1, c2 = "Respectfully,", "With kind regards,"
        opener_warm = "I trust this message finds you well."
    else:
        g1, g2 = "Hi Editor,", "Hello Editor,"
        c1, c2 = "Best regards,", "Looking forward to hearing from you,"
        opener_warm = "I hope this finds you well."

    if message_type == "coverage_request":
        # ═══════════════════════════════════════════════════
        # COVERAGE REQUEST — Variant A: "The Newsroom Pitch"
        # Strategy: Lead with the story, make it easy to say yes
        # ═══════════════════════════════════════════════════
        a_subject = f"{title} — Ready-Made Story for Your Outlet"
        a_body = f"""{g1}

{opener_warm}

I have a story I think is a natural fit for your outlet.

{title}{f" — {desc}" if desc else ""} is launching soon, and there's a real narrative here that I think your readers would connect with.{f" What sets it apart: {sp_prose}." if sp_prose else ""}

{f"{ctx}" + chr(10) + chr(10) if ctx else ""}Rather than just sending a press release, I wanted to reach out personally because I genuinely think this aligns with what your outlet covers. I've put together a complete press kit — key art, screenshots, gameplay trailer, fact sheet — so if this catches your eye, you can hit the ground running.

I can also set up a developer interview, provide early access for a hands-on preview, or tailor assets to whatever format works best for your editorial calendar.

Would this be something your outlet would be interested in covering? Happy to send everything over immediately.

{c1}"""

        # ═══════════════════════════════════════════════════
        # COVERAGE REQUEST — Variant B: "The Story Angle"
        # Strategy: Propose specific editorial angles, show you know their work
        # ═══════════════════════════════════════════════════
        b_subject = f"Three Story Angles on {title} — Pick the One That Fits"
        b_body = f"""{g2}

I've been following your outlet's coverage and wanted to pitch something a bit different — not just "here's a game, please cover it," but three specific angles I think would genuinely resonate with your audience.

{title}{f" — {desc}" if desc else ""}.{f" The standout elements: {sp_prose}." if sp_prose else ""}

{f"{ctx}" + chr(10) + chr(10) if ctx else ""}Here are the angles I had in mind:

1. The Behind-the-Scenes Story — How {title} went from concept to reality. I can arrange an in-depth interview with the creative leads about the decisions that shaped the game.

2. The First-Look Preview — An exclusive hands-on experience with the build, including assets your outlet would be the first to publish.

3. The Industry Angle — What {title} represents in the current gaming landscape and why it matters right now. Great for a feature or opinion piece.

You're welcome to pick one, combine them, or suggest something entirely different. I'll make it happen.

Which angle interests you most?

{c2}"""

    else:
        # ═══════════════════════════════════════════════════
        # PITCH — Variant A: "The Exclusive Offer"
        # Strategy: Create urgency and exclusivity, make them feel chosen
        # ═══════════════════════════════════════════════════
        a_subject = f"For Your Eyes First: {title}"
        a_body = f"""{g1}

I'm reaching out to a very small group of outlets before we go wide with this announcement — and your outlet is one of them.

{title}{f" — {desc}" if desc else ""} is something we've been working on quietly, and we're now ready to show it to the world.{f" What makes it special: {sp_prose}." if sp_prose else ""}

{f"{ctx}" + chr(10) + chr(10) if ctx else ""}Before we send this to the broader press list, I wanted to give your outlet the chance to break this story. Here's what I can offer exclusively:

- A review copy or early access build, available immediately
- First-to-publish gameplay footage and screenshots
- A sit-down interview with our lead developer or creative director
- Any custom assets your team needs for the piece

This window won't last long — once we go public, the exclusivity is gone. But I'd rather your outlet gets first crack at this than anyone else.

Interested? I can have everything in your inbox within the hour.

{c1}"""

        # ═══════════════════════════════════════════════════
        # PITCH — Variant B: "The Relationship Builder"
        # Strategy: No pressure, focus on mutual value, open a conversation
        # ═══════════════════════════════════════════════════
        b_subject = f"{title} — I Think Your Audience Will Love This"
        b_body = f"""{g2}

I'll keep this short because I know your inbox is packed.

We're launching {title}{f" — {desc}" if desc else ""}, and I genuinely believe it's the kind of game your audience gets excited about.{f" A few reasons why: {sp_prose}." if sp_prose else ""}

{f"{ctx}" + chr(10) + chr(10) if ctx else ""}I'm not looking for a favor — I think covering this would be genuinely valuable for your readers. The response from early testers has been overwhelmingly positive, and I'd love for your outlet to see why.

No strings attached. I can send over:
- A press kit with everything you need to decide if it's a fit
- A review copy so your team can experience it firsthand
- Developer access if you want quotes or an interview

If it's not the right fit, no hard feelings at all. But if it is, I'd love to make it as easy as possible for your team to cover it.

Worth a look?

{c2}"""

    return {
        "variant_a": {
            "label": "The Newsroom Pitch" if message_type == "coverage_request" else "The Exclusive Offer",
            "subject": a_subject,
            "body_text": BeautifulSoup_to_text(a_body) if "<" in a_body else a_body.strip(),
        },
        "variant_b": {
            "label": "The Story Angle" if message_type == "coverage_request" else "The Relationship Builder",
            "subject": b_subject,
            "body_text": BeautifulSoup_to_text(b_body) if "<" in b_body else b_body.strip(),
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
