"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================


class ExtractSpeechesRequest(BaseModel):
    """Request to extract speeches from protocol text."""

    text: str = Field(..., description="Full protocol text to parse")


class AnalyzeTextRequest(BaseModel):
    """Request to analyze text for word frequencies."""

    text: str = Field(..., description="Text to analyze")
    include_categories: bool = Field(
        default=True,
        description="Include semantic category counts (Scheme D/E/F)",
    )
    include_tone: bool = Field(
        default=True,
        description="Include tone analysis scores",
    )
    include_topics: bool = Field(
        default=True,
        description="Include topic classification scores",
    )
    top_n: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of top words to return per type",
    )


class AnalyzeToneRequest(BaseModel):
    """Request for tone-only analysis."""

    text: str = Field(..., description="Text to analyze for tone")


class ClassifyTopicsRequest(BaseModel):
    """Request for topic classification."""

    text: str = Field(..., description="Text to classify by topic")


class AnalyzeProtocolRequest(BaseModel):
    """Request to analyze a full protocol by ID."""

    protocol_id: int = Field(..., description="Protocol ID to fetch and analyze")
    wahlperiode: int = Field(default=21, description="Electoral period")


# =============================================================================
# Response Models
# =============================================================================


class SpeechInfo(BaseModel):
    """Individual speech extracted from protocol."""

    speaker: str
    party: str | None
    text: str
    type: str
    category: str
    words: int
    first_name: str | None = None
    last_name: str | None = None
    acad_title: str | None = None
    is_government: bool = False


class ExtractSpeechesResponse(BaseModel):
    """Response with extracted speeches."""

    success: bool = True
    speech_count: int
    speeches: list[SpeechInfo]


class WordCount(BaseModel):
    """Word with its count."""

    word: str
    count: int
    frequency_per_1000: float | None = None


class ToneScores(BaseModel):
    """Communication style tone scores (0-100 scale)."""

    affirmative: float = Field(description="Affirmative vs critical adjectives")
    aggression: float = Field(description="Aggressive adjective usage")
    labeling: float = Field(description="Labeling/othering language")
    solution_focus: float = Field(description="Solution vs problem verbs")
    collaboration: float = Field(description="Collaborative vs confrontational")
    demand_intensity: float = Field(description="Demanding verb usage")
    acknowledgment: float = Field(description="Acknowledging verb usage")
    authority: float = Field(description="Obligation vs possibility modals")
    future_orientation: float = Field(description="Prospective vs retrospective")
    emotional_intensity: float = Field(description="Intensifier vs moderator usage")
    inclusivity: float = Field(description="Inclusive vs exclusive pronouns")
    discriminatory: float = Field(description="Discriminatory language (per-mille)")


class TopicScores(BaseModel):
    """Topic classification scores (per-1000 words)."""

    migration: float = 0
    klima: float = 0
    wirtschaft: float = 0
    soziales: float = 0
    sicherheit: float = 0
    gesundheit: float = 0
    europa: float = 0
    digital: float = 0
    bildung: float = 0
    finanzen: float = 0
    justiz: float = 0
    arbeit: float = 0
    mobilitaet: float = 0


class AnalyzeTextResponse(BaseModel):
    """Response with text analysis results."""

    success: bool = True
    total_words: int
    total_nouns: int
    total_adjectives: int
    total_verbs: int
    top_nouns: list[WordCount]
    top_adjectives: list[WordCount]
    top_verbs: list[WordCount]
    tone_scores: ToneScores | None = None
    topic_scores: TopicScores | None = None


class AnalyzeToneResponse(BaseModel):
    """Response with tone analysis only."""

    success: bool = True
    total_words: int
    tone_scores: ToneScores


class ClassifyTopicsResponse(BaseModel):
    """Response with topic classification only."""

    success: bool = True
    total_words: int
    topic_scores: TopicScores


class PartyAnalysis(BaseModel):
    """Analysis results for a single party."""

    party: str
    speech_count: int
    total_words: int
    top_nouns: list[WordCount]
    top_adjectives: list[WordCount]
    top_verbs: list[WordCount]
    tone_scores: ToneScores | None = None
    topic_scores: TopicScores | None = None


class AnalyzeProtocolResponse(BaseModel):
    """Response with full protocol analysis."""

    success: bool = True
    protocol_id: int
    speech_count: int
    parties: list[str]
    party_analyses: list[PartyAnalysis]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    spacy_model: str
    spacy_model_loaded: bool


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: str
    detail: str | None = None


# =============================================================================
# Speaker Profile Models
# =============================================================================


class SpeakerProfileRequest(BaseModel):
    """Request for speaker profile analysis."""

    speaker_name: str = Field(..., description="Full name of the speaker")
    wahlperiode: int = Field(default=21, description="Electoral period")
    include_signature_words: bool = Field(
        default=True,
        description="Include signature words (distinctive vocabulary)",
    )
    include_tone: bool = Field(
        default=True,
        description="Include tone analysis scores",
    )
    include_topics: bool = Field(
        default=True,
        description="Include topic focus areas",
    )


class SignatureWord(BaseModel):
    """A signature word that is distinctive for a speaker."""

    word: str
    speaker_frequency: float = Field(description="Per-1000 frequency for speaker")
    baseline_frequency: float = Field(description="Per-1000 frequency for baseline")
    ratio: float = Field(description="How many times more frequent than baseline")


class SpeakerProfileResponse(BaseModel):
    """Response with comprehensive speaker profile."""

    success: bool = True
    name: str
    first_name: str | None = None
    last_name: str | None = None
    party: str
    acad_title: str | None = None
    gender: str | None = None

    # Speech statistics
    total_speeches: int = 0
    formal_speeches: int = 0  # category='rede'
    wortbeitraege: int = 0  # category='wortbeitrag'
    befragung_responses: int = 0  # Government Q&A
    total_words: int = 0
    avg_words_per_speech: float = 0.0

    # Interaction statistics
    interruptions_made: int = 0
    interruptions_received: int = 0

    # Top words
    top_nouns: list[WordCount] = []
    top_adjectives: list[WordCount] = []
    top_verbs: list[WordCount] = []

    # Signature words (distinctive vocabulary)
    signature_nouns: list[SignatureWord] = []
    signature_adjectives: list[SignatureWord] = []

    # Analysis scores
    tone_scores: ToneScores | None = None
    topic_scores: TopicScores | None = None

    # Comparison to party average
    words_vs_party_avg: float | None = Field(
        default=None,
        description="Percentage difference from party average words per speech",
    )


# =============================================================================
# Party Comparison Models
# =============================================================================


class PartyComparisonRequest(BaseModel):
    """Request for party comparison analysis."""

    parties: list[str] | None = Field(
        default=None,
        description="List of parties to compare. If None, compare all.",
    )
    wahlperiode: int = Field(default=21, description="Electoral period")
    include_tone: bool = Field(
        default=True,
        description="Include tone analysis comparison",
    )
    include_topics: bool = Field(
        default=True,
        description="Include topic focus comparison",
    )
    include_distinctive_words: bool = Field(
        default=True,
        description="Include distinctive vocabulary per party",
    )
    top_n: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of top words/distinctive words to return",
    )


class PartyProfile(BaseModel):
    """Profile for a single party in comparison."""

    party: str
    speaker_count: int = 0
    speech_count: int = 0
    total_words: int = 0
    avg_words_per_speech: float = 0.0

    # Top words
    top_nouns: list[WordCount] = []
    top_adjectives: list[WordCount] = []
    top_verbs: list[WordCount] = []

    # Distinctive words (used more than other parties)
    distinctive_nouns: list[SignatureWord] = []
    distinctive_adjectives: list[SignatureWord] = []

    # Analysis scores
    tone_scores: ToneScores | None = None
    topic_scores: TopicScores | None = None


class PartyComparisonResponse(BaseModel):
    """Response with party comparison analysis."""

    success: bool = True
    wahlperiode: int
    parties_compared: list[str]
    party_profiles: list[PartyProfile]

    # Rankings (party names ordered by metric)
    aggression_ranking: list[str] = Field(
        default=[],
        description="Parties ranked by aggression score (highest first)",
    )
    collaboration_ranking: list[str] = Field(
        default=[],
        description="Parties ranked by collaboration score (highest first)",
    )
    solution_focus_ranking: list[str] = Field(
        default=[],
        description="Parties ranked by solution focus (highest first)",
    )
