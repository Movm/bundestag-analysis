"""API route handlers for analysis endpoints."""

from collections import Counter
from fastapi import APIRouter, HTTPException

from ..analyzer import WordAnalyzer, AnalysisResult
from ..parser import parse_speeches_from_protocol
from ..categorizer import WordCategorizer
from .schemas import (
    ExtractSpeechesRequest,
    ExtractSpeechesResponse,
    SpeechInfo,
    AnalyzeTextRequest,
    AnalyzeTextResponse,
    AnalyzeToneRequest,
    AnalyzeToneResponse,
    ClassifyTopicsRequest,
    ClassifyTopicsResponse,
    WordCount,
    ToneScores,
    TopicScores,
    HealthResponse,
    # New schemas for speaker profile and party comparison
    SpeakerProfileRequest,
    SpeakerProfileResponse,
    SignatureWord,
    PartyComparisonRequest,
    PartyComparisonResponse,
    PartyProfile,
)

router = APIRouter()

# Global analyzer instance (expensive to create, reuse across requests)
_analyzer: WordAnalyzer | None = None


def get_analyzer() -> WordAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = WordAnalyzer(model="de_core_news_lg")
    return _analyzer


def _convert_tone_scores(tone_scores) -> ToneScores:
    """Convert internal ToneScores to API schema."""
    d = tone_scores.to_dict()
    return ToneScores(
        affirmative=d["affirmative"],
        aggression=d["aggression"],
        labeling=d["labeling"],
        solution_focus=d["solution_focus"],
        collaboration=d["collaboration"],
        demand_intensity=d["demand_intensity"],
        acknowledgment=d["acknowledgment"],
        authority=d["authority"],
        future_orientation=d["future_orientation"],
        emotional_intensity=d["emotional_intensity"],
        inclusivity=d["inclusivity"],
        discriminatory=d["discriminatory"],
    )


def _convert_topic_scores(topic_scores) -> TopicScores:
    """Convert internal TopicScores to API schema."""
    d = topic_scores.to_dict()
    return TopicScores(
        migration=d.get("migration", 0),
        klima=d.get("klima", 0),
        wirtschaft=d.get("wirtschaft", 0),
        soziales=d.get("soziales", 0),
        sicherheit=d.get("sicherheit", 0),
        gesundheit=d.get("gesundheit", 0),
        europa=d.get("europa", 0),
        digital=d.get("digital", 0),
        bildung=d.get("bildung", 0),
        finanzen=d.get("finanzen", 0),
        justiz=d.get("justiz", 0),
        arbeit=d.get("arbeit", 0),
        mobilitaet=d.get("mobilitaet", 0),
    )


def _make_word_counts(
    counter, total_words: int, top_n: int = 50
) -> list[WordCount]:
    """Convert Counter to list of WordCount with frequencies."""
    return [
        WordCount(
            word=word,
            count=count,
            frequency_per_1000=round((count / total_words) * 1000, 2)
            if total_words > 0
            else 0,
        )
        for word, count in counter.most_common(top_n)
    ]


# =============================================================================
# Health Check
# =============================================================================


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health and spaCy model status."""
    analyzer = get_analyzer()
    return HealthResponse(
        status="healthy",
        spacy_model="de_core_news_lg",
        spacy_model_loaded=analyzer.nlp is not None,
    )


# =============================================================================
# Speech Extraction
# =============================================================================


@router.post("/extract/speeches", response_model=ExtractSpeechesResponse)
async def extract_speeches(request: ExtractSpeechesRequest):
    """Extract individual speeches from protocol text.

    Parses a full Plenarprotokoll text and extracts individual speeches
    with speaker name, party affiliation, speech type, and word count.
    """
    if not request.text or len(request.text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Text too short - expected full protocol text",
        )

    speeches = parse_speeches_from_protocol(request.text)

    return ExtractSpeechesResponse(
        speech_count=len(speeches),
        speeches=[
            SpeechInfo(
                speaker=s.get("speaker", ""),
                party=s.get("party"),
                text=s.get("text", ""),
                type=s.get("type", "unknown"),
                category=s.get("category", "unknown"),
                words=s.get("words", 0),
                first_name=s.get("first_name"),
                last_name=s.get("last_name"),
                acad_title=s.get("acad_title"),
                is_government=s.get("is_government", False),
            )
            for s in speeches
        ],
    )


# =============================================================================
# Text Analysis
# =============================================================================


@router.post("/analyze/text", response_model=AnalyzeTextResponse)
async def analyze_text(request: AnalyzeTextRequest):
    """Analyze text for word frequencies, tone, and topics.

    Uses spaCy NLP to extract and lemmatize nouns, adjectives, and verbs.
    Optionally includes semantic categorization (Scheme D/E) and topic
    classification (Scheme F).
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Text too short for analysis",
        )

    analyzer = get_analyzer()

    # Create a synthetic speech dict for the analyzer
    speeches = [{"text": request.text}]
    result = analyzer.analyze_speeches(speeches, party="analysis")

    response = AnalyzeTextResponse(
        total_words=result.total_words,
        total_nouns=result.total_nouns,
        total_adjectives=result.total_adjectives,
        total_verbs=result.total_verbs,
        top_nouns=_make_word_counts(
            result.noun_counts, result.total_words, request.top_n
        ),
        top_adjectives=_make_word_counts(
            result.adjective_counts, result.total_words, request.top_n
        ),
        top_verbs=_make_word_counts(
            result.verb_counts, result.total_words, request.top_n
        ),
    )

    if request.include_tone and result.tone_scores:
        response.tone_scores = _convert_tone_scores(result.tone_scores)

    if request.include_topics and result.topic_scores:
        response.topic_scores = _convert_topic_scores(result.topic_scores)

    return response


# =============================================================================
# Tone Analysis (Lightweight)
# =============================================================================


@router.post("/analyze/tone", response_model=AnalyzeToneResponse)
async def analyze_tone(request: AnalyzeToneRequest):
    """Analyze text for communication style tone scores only.

    Returns tone metrics like aggression, collaboration, solution-focus,
    without full word frequency breakdown. Faster for tone-only analysis.
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Text too short for analysis",
        )

    analyzer = get_analyzer()
    speeches = [{"text": request.text}]
    result = analyzer.analyze_speeches(speeches, party="analysis")

    if not result.tone_scores:
        raise HTTPException(
            status_code=500,
            detail="Tone analysis failed - no scores generated",
        )

    return AnalyzeToneResponse(
        total_words=result.total_words,
        tone_scores=_convert_tone_scores(result.tone_scores),
    )


# =============================================================================
# Topic Classification
# =============================================================================


@router.post("/analyze/topics", response_model=ClassifyTopicsResponse)
async def classify_topics(request: ClassifyTopicsRequest):
    """Classify text by political topics.

    Returns per-1000-word frequency scores for 13 topic categories:
    migration, climate, economy, social, security, health, Europe,
    digital, education, finance, justice, labor, mobility.
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Text too short for analysis",
        )

    analyzer = get_analyzer()
    speeches = [{"text": request.text}]
    result = analyzer.analyze_speeches(speeches, party="analysis")

    if not result.topic_scores:
        raise HTTPException(
            status_code=500,
            detail="Topic classification failed - no scores generated",
        )

    return ClassifyTopicsResponse(
        total_words=result.total_words,
        topic_scores=_convert_topic_scores(result.topic_scores),
    )


# =============================================================================
# Speaker Profile Analysis
# =============================================================================


from pydantic import BaseModel, Field as PydanticField


class SpeechesInput(BaseModel):
    """Input model for speeches-based analysis."""

    speeches: list[dict] = PydanticField(
        ...,
        description="List of speech dicts with 'text', 'speaker', 'party' fields",
    )


@router.post("/analysis/speaker-profile", response_model=SpeakerProfileResponse)
async def get_speaker_profile(
    speaker_name: str,
    speeches_input: SpeechesInput,
):
    """Get a comprehensive profile for a speaker based on their speeches.

    Requires a list of speeches (pre-filtered by speaker from bundestag-mcp).
    Returns speech statistics, top words, signature words, tone, and topics.
    """
    speeches = speeches_input.speeches

    if not speeches:
        raise HTTPException(
            status_code=400,
            detail=f"No speeches provided for speaker: {speaker_name}",
        )

    analyzer = get_analyzer()

    # Aggregate speech statistics
    total_speeches = len(speeches)
    formal_speeches = sum(1 for s in speeches if s.get("category") == "rede")
    wortbeitraege = sum(1 for s in speeches if s.get("category") == "wortbeitrag")
    befragung = sum(
        1 for s in speeches if s.get("type") in ("befragung", "fragestunde_antwort")
    )

    # Get party from first speech
    party = speeches[0].get("party", "unknown") if speeches else "unknown"
    first_name = speeches[0].get("first_name") if speeches else None
    last_name = speeches[0].get("last_name") if speeches else None
    acad_title = speeches[0].get("acad_title") if speeches else None

    # Analyze all speeches together
    result = analyzer.analyze_speeches(speeches, party=party)

    # Build response
    response = SpeakerProfileResponse(
        name=speaker_name,
        first_name=first_name,
        last_name=last_name,
        party=party,
        acad_title=acad_title,
        total_speeches=total_speeches,
        formal_speeches=formal_speeches,
        wortbeitraege=wortbeitraege,
        befragung_responses=befragung,
        total_words=result.total_words,
        avg_words_per_speech=round(result.total_words / total_speeches, 1)
        if total_speeches > 0
        else 0,
        top_nouns=_make_word_counts(result.noun_counts, result.total_words, 20),
        top_adjectives=_make_word_counts(
            result.adjective_counts, result.total_words, 20
        ),
        top_verbs=_make_word_counts(result.verb_counts, result.total_words, 20),
    )

    if result.tone_scores:
        response.tone_scores = _convert_tone_scores(result.tone_scores)

    if result.topic_scores:
        response.topic_scores = _convert_topic_scores(result.topic_scores)

    return response


# =============================================================================
# Party Comparison Analysis
# =============================================================================


@router.post("/analysis/party-comparison", response_model=PartyComparisonResponse)
async def compare_parties(
    speeches_input: SpeechesInput,
    parties: list[str] | None = None,
    wahlperiode: int = 21,
    top_n: int = 20,
):
    """Compare parties based on their speeches.

    Requires a list of speeches (from bundestag-mcp semantic search).
    Groups speeches by party and compares tone, topics, and vocabulary.
    """
    speeches = speeches_input.speeches

    if not speeches:
        raise HTTPException(
            status_code=400,
            detail="No speeches provided for comparison",
        )

    analyzer = get_analyzer()

    # Group speeches by party
    speeches_by_party: dict[str, list] = {}
    for speech in speeches:
        party = speech.get("party")
        if party:
            if parties and party not in parties:
                continue
            if party not in speeches_by_party:
                speeches_by_party[party] = []
            speeches_by_party[party].append(speech)

    if not speeches_by_party:
        raise HTTPException(
            status_code=400,
            detail="No speeches found for the specified parties",
        )

    # Analyze each party
    party_profiles = []
    tone_scores_by_party = {}

    for party, party_speeches in speeches_by_party.items():
        result = analyzer.analyze_speeches(party_speeches, party=party)

        # Count unique speakers
        speakers = set(s.get("speaker") for s in party_speeches if s.get("speaker"))

        profile = PartyProfile(
            party=party,
            speaker_count=len(speakers),
            speech_count=len(party_speeches),
            total_words=result.total_words,
            avg_words_per_speech=round(result.total_words / len(party_speeches), 1)
            if party_speeches
            else 0,
            top_nouns=_make_word_counts(result.noun_counts, result.total_words, top_n),
            top_adjectives=_make_word_counts(
                result.adjective_counts, result.total_words, top_n
            ),
            top_verbs=_make_word_counts(result.verb_counts, result.total_words, top_n),
        )

        if result.tone_scores:
            profile.tone_scores = _convert_tone_scores(result.tone_scores)
            tone_scores_by_party[party] = result.tone_scores

        if result.topic_scores:
            profile.topic_scores = _convert_topic_scores(result.topic_scores)

        party_profiles.append(profile)

    # Build rankings based on tone scores
    aggression_ranking = sorted(
        tone_scores_by_party.keys(),
        key=lambda p: tone_scores_by_party[p].aggression,
        reverse=True,
    )
    collaboration_ranking = sorted(
        tone_scores_by_party.keys(),
        key=lambda p: tone_scores_by_party[p].collaboration,
        reverse=True,
    )
    solution_ranking = sorted(
        tone_scores_by_party.keys(),
        key=lambda p: tone_scores_by_party[p].solution_focus,
        reverse=True,
    )

    return PartyComparisonResponse(
        wahlperiode=wahlperiode,
        parties_compared=list(speeches_by_party.keys()),
        party_profiles=party_profiles,
        aggression_ranking=aggression_ranking,
        collaboration_ranking=collaboration_ranking,
        solution_focus_ranking=solution_ranking,
    )
