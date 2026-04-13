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

def _rewrite_description(desc: str, title: str) -> str:
    """Rewrite a raw game description into a polished elevator pitch sentence."""
    if not desc:
        return ""
    d = desc.strip().rstrip(".")
    # If it's already a full sentence (starts with capital, has a verb-like pattern), frame it
    if len(d) > 80:
        return f"In short, {title} is {d[0].lower()}{d[1:]}."
    return f"{title} is {d[0].lower()}{d[1:]}."


def _weave_points_narrative(points: list[str], style: str = "flow") -> str:
    """Transform raw selling points into polished narrative paragraphs.
    style='flow' = woven prose, style='build' = escalating structure."""
    if not points:
        return ""
    escaped = [html.escape(p) for p in points]

    if style == "build":
        # Escalating structure: each point gets its own punchy line
        lines = []
        intros = [
            "First, there's", "On top of that,", "And perhaps most importantly,",
            "It also features", "Add to that", "Plus,",
        ]
        for i, pt in enumerate(escaped):
            intro = intros[i] if i < len(intros) else "There's also"
            lines.append(f"{intro} {pt[0].lower()}{pt[1:]}.")
        return " ".join(lines)

    # Flowing prose
    if len(escaped) == 1:
        return f"At its core, {escaped[0][0].lower()}{escaped[0][1:]} is what sets this apart."
    if len(escaped) == 2:
        return (
            f"Two things make this stand out: {escaped[0][0].lower()}{escaped[0][1:]}, "
            f"and {escaped[1][0].lower()}{escaped[1][1:]}."
        )
    # 3+
    highlights = ", ".join(f"{p[0].lower()}{p[1:]}" for p in escaped[:-1])
    return (
        f"What makes this genuinely different: {highlights} "
        f"— and {escaped[-1][0].lower()}{escaped[-1][1:]}."
    )


def _rewrite_context(ctx: str) -> str:
    """Turn raw custom context into a polished paragraph."""
    if not ctx:
        return ""
    c = ctx.strip()
    if not c.endswith(".") and not c.endswith("!") and not c.endswith("?"):
        c += "."
    return c


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
    The user's raw input (description, selling points, context) is completely
    rewritten and reframed into polished PR copy — not inserted verbatim.
    """
    title = html.escape(game_title or "Our Game")
    raw_desc = game_description or ""
    points = key_selling_points or []
    raw_ctx = custom_context or ""

    desc_pitch = _rewrite_description(raw_desc, title)
    points_flow = _weave_points_narrative(points, "flow")
    points_build = _weave_points_narrative(points, "build")
    ctx_clean = _rewrite_context(raw_ctx)

    # Tone-adaptive elements
    if tone == "casual":
        g1, g2 = "Hey Editor,", "Hi Editor,"
        c1, c2 = "Talk soon!", "Looking forward to it!"
    elif tone == "enthusiastic":
        g1, g2 = "Hi Editor!", "Hey Editor!"
        c1, c2 = "Can't wait to hear your thoughts!", "Really excited to connect on this!"
    elif tone == "formal":
        g1, g2 = "Dear Editor,", "Dear Editor,"
        c1, c2 = "Respectfully,", "With kind regards,"
    else:
        g1, g2 = "Hi Editor,", "Hello Editor,"
        c1, c2 = "Best regards,", "Looking forward to hearing from you,"

    if message_type == "coverage_request":

        # ═══ COVERAGE A: "The Newsroom Pitch" ═══
        # Strategy: Frame it as a ready-to-publish story. Do all the work for them.
        a_subject = f"{title} — Ready-Made Story for Your Outlet"

        ctx_para_a = f"\nHere's some additional context that could strengthen the piece: {ctx_clean}\n" if ctx_clean else ""
        a_body = f"""{g1}

I have a story that I believe writes itself — and I think your outlet is the right home for it.

We're about to launch {title}, and the narrative behind this game is one your readers will connect with. {desc_pitch} {points_flow}
{ctx_para_a}
I've already done the legwork to make this as easy as possible for your team. Here's what's ready to go right now:

- A complete press kit with key art, screenshots, and a gameplay trailer
- A polished fact sheet with everything you'd need for a news piece
- Developer quotes ready for attribution
- Exclusive early access if your team wants a hands-on preview

I can also tailor the angle — whether that's a news piece, a feature, a preview, or an interview format. Whatever serves your editorial calendar best.

The launch window is approaching, so priority access is available now for outlets that want to be among the first to cover this.

Shall I send the full kit over?

{c1}"""

        # ═══ COVERAGE B: "The Story Angle" ═══
        # Strategy: Pitch specific editorial angles. Show editorial thinking.
        b_subject = f"Three Story Angles on {title} — Take Your Pick"

        ctx_para_b = f"\nOne more thing worth noting: {ctx_clean}\n" if ctx_clean else ""
        b_body = f"""{g2}

I'd like to pitch you something more specific than "please cover our game." I've put together three editorial angles that I think would genuinely work for your audience — and I'd love your take on which one resonates.

The game is {title}. {desc_pitch} {points_build}
{ctx_para_b}
Here are the angles:

1. The Making-Of Feature
The story of how {title} came to life — the creative risks, the pivots, the breakthroughs. I can set up a long-form interview with the team leads, plus behind-the-scenes assets nobody else has seen.

2. The Exclusive First Look
A hands-on preview with the latest build, paired with assets your outlet publishes first. Ideal for a news piece or preview feature that drives traffic on announcement day.

3. The Bigger Picture
What {title} signals about where the industry is heading. This works as a thought piece or feature — I can provide data points, developer perspective, and context to build the argument.

Feel free to pick one, mash them together, or pitch me something completely different. I'll make whatever you need happen.

Which direction interests you?

{c2}"""

    else:

        # ═══ PITCH A: "The Exclusive Offer" ═══
        # Strategy: Scarcity, urgency, make them feel hand-picked.
        a_subject = f"For Your Eyes First: {title}"

        ctx_para_a = f"\n{ctx_clean}\n" if ctx_clean else ""
        a_body = f"""{g1}

I'm writing to you before we announce this publicly — because I want your outlet to have first access.

{title} is the game we've been building behind closed doors, and we're now ready to show it. {desc_pitch} {points_flow}
{ctx_para_a}
We're being deliberate about who sees this first. Your outlet is on a very short list, and here's what that means:

- You get a review copy or hands-on access before anyone else
- Your outlet can publish gameplay footage, screenshots, and key art first
- I'll arrange a dedicated interview with our creative lead — on your schedule
- If you need custom assets, B-roll, or anything else, I'll have it turned around fast

Once we open this up to the wider press list, the exclusivity window closes. I'd much rather your team gets the head start.

If this sounds like a fit, I can have everything in your hands today.

{c1}"""

        # ═══ PITCH B: "The Relationship Builder" ═══
        # Strategy: Zero pressure. Lead with genuine value. Open a door.
        b_subject = f"{title} — Built for the Kind of Audience You Reach"

        ctx_para_b = f"\n{ctx_clean}\n" if ctx_clean else ""
        b_body = f"""{g2}

I'll be honest — I'm not here to add another pitch to your pile. I'm reaching out because I genuinely think this game and your audience are a perfect match, and I wanted to start a conversation about it.

The game is {title}. {desc_pitch} {points_build}
{ctx_para_b}
The early reception has been strong. Players and testers keep telling us the same thing — this is the kind of game they wish they'd heard about sooner. That's exactly why I thought of your outlet.

I don't want to assume what format works best for you, so here's what I can offer — take whatever's useful, ignore the rest:

- A press kit so you can see if it's editorially relevant
- A review copy for your team to try firsthand — no obligation
- Access to our developers for quotes, interviews, or a Q&A feature

If it clicks, amazing — I'll make the process seamless. If it's not the right fit, genuinely no pressure. I'd rather build a relationship with your outlet for the long run than push something that doesn't land.

Either way — would it be worth a quick look?

{c2}"""

    return {
        "variant_a": {
            "label": "The Newsroom Pitch" if message_type == "coverage_request" else "The Exclusive Offer",
            "subject": a_subject,
            "body_text": a_body.strip(),
        },
        "variant_b": {
            "label": "The Story Angle" if message_type == "coverage_request" else "The Relationship Builder",
            "subject": b_subject,
            "body_text": b_body.strip(),
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
