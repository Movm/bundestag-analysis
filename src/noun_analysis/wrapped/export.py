"""Web/JSON export methods for wrapped analysis (mixin class)."""

import random


class ExportMixin:
    """Mixin providing export functionality for WrappedData."""

    def _generate_quiz_questions(self) -> list[dict]:
        """Generate quiz questions from the data."""
        questions = []
        parties = self.metadata.get("parties", [])

        # Get signature words for word-guessing quizzes
        party_signatures = {}
        for party in parties:
            sigs = self.get_distinctive_words(party, "nouns", 5)
            if sigs:
                party_signatures[party] = sigs

        # Quiz 0: Rank the top word from a party
        # Show 4 signature words from one party, user guesses which is #1
        # Tie-breaker: party with more speeches wins if ratios are equal
        best_party = None
        best_ratio = 0
        best_speeches = 0
        for party, sigs in party_signatures.items():
            if len(sigs) >= 4:
                party_speeches = self.party_stats.get(party, {}).get("real_speeches", 0)
                if sigs[0][1] > best_ratio or (sigs[0][1] == best_ratio and party_speeches > best_speeches):
                    best_party = party
                    best_ratio = sigs[0][1]
                    best_speeches = party_speeches

        if best_party and len(party_signatures[best_party]) >= 4:
            sigs = party_signatures[best_party]
            correct_word, ratio = sigs[0]  # #1 word
            options = [w for w, r in sigs[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-signature",
                "type": "prediction",
                "question": f"Welches Wort nutzt {best_party} am meisten im Vergleich zu anderen?",
                "options": options,
                "correctAnswer": correct_word,
                "explanation": f"\"{correct_word}\" ist {best_party}s Lieblingswort ({ratio:.1f}x häufiger als andere Parteien).",
            })

        # Quiz 1: Rank the top key topic from a different party
        # Show 4 key topics from one party, user guesses which is #1
        party_topics = {}
        for party in parties:
            topics = self.get_key_topics(party, "nouns", 5)
            if topics and len(topics) >= 4:
                party_topics[party] = topics

        # Pick a different party than Quiz 0 for variety
        # Tie-breaker: party with more speeches wins if ratios are equal
        quiz1_party = None
        quiz1_ratio = 0
        quiz1_speeches = 0
        for party, topics in party_topics.items():
            if party != best_party:
                party_speeches = self.party_stats.get(party, {}).get("real_speeches", 0)
                if topics[0][2] > quiz1_ratio or (topics[0][2] == quiz1_ratio and party_speeches > quiz1_speeches):
                    quiz1_party = party
                    quiz1_ratio = topics[0][2]
                    quiz1_speeches = party_speeches

        if quiz1_party and len(party_topics[quiz1_party]) >= 4:
            topics = party_topics[quiz1_party]
            correct_word, count, ratio = topics[0]  # #1 topic
            options = [w for w, c, r in topics[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-party-topic",
                "type": "prediction",
                "question": f"Welches Wort nutzt {quiz1_party} am meisten im Vergleich zu anderen?",
                "options": options,
                "correctAnswer": correct_word,
                "explanation": f"\"{correct_word}\" - {quiz1_party} verwendet es {count:,}× ({ratio:.1f}x häufiger als andere).",
            })

        # Quiz: Most speeches
        party_speeches = [(p, self.party_stats.get(p, {}).get("real_speeches", 0)) for p in parties]
        party_speeches.sort(key=lambda x: x[1], reverse=True)
        if party_speeches:
            top_party = party_speeches[0][0]
            top_count = party_speeches[0][1]
            options = [p for p, _ in party_speeches[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-speeches",
                "type": "prediction",
                "question": "Welche Partei hat die meisten Reden gehalten?",
                "options": options,
                "correctAnswer": top_party,
                "explanation": f"{top_party} mit {top_count} Reden!",
            })

        # Quiz: Top interrupter
        interrupters = self.get_top_interrupters(4)
        if interrupters:
            top_name, top_party, top_count = interrupters[0]
            options = [f"{n} ({p})" for n, p, _ in interrupters]
            random.shuffle(options)
            questions.append({
                "id": "quiz-interrupter",
                "type": "prediction",
                "question": "Wer hat am meisten unterbrochen?",
                "options": options,
                "correctAnswer": f"{top_name} ({top_party})",
                "explanation": f"{top_name} ({top_party}) mit {top_count} Unterbrechungen!",
            })

        # Quiz: Applause champion
        applause = self.get_applause_ranking(4)
        if applause:
            top_party, top_count = applause[0]
            options = [p for p, _ in applause]
            random.shuffle(options)
            questions.append({
                "id": "quiz-applause",
                "type": "prediction",
                "question": "Welche Partei applaudiert am meisten?",
                "options": options,
                "correctAnswer": top_party,
                "explanation": f"{top_party} mit {top_count:,} Beifallsbekundungen!",
            })

        # Quiz: Loudest heckler
        heckles = self.get_heckle_ranking(4)
        if heckles:
            top_party, top_count = heckles[0]
            options = [p for p, _ in heckles]
            random.shuffle(options)
            questions.append({
                "id": "quiz-heckler",
                "type": "prediction",
                "question": "Welche Partei ruft am lautesten dazwischen?",
                "options": options,
                "correctAnswer": top_party,
                "explanation": f"{top_party} mit {top_count:,} Zwischenrufen!",
            })

        # Quiz: Top speaker
        speakers = self.get_top_speakers(4)
        if speakers:
            top_name, top_party, top_count = speakers[0]
            options = [f"{n} ({p})" for n, p, _ in speakers]
            random.shuffle(options)
            questions.append({
                "id": "quiz-speakers",
                "type": "prediction",
                "question": "Wer hat die meisten Reden gehalten?",
                "options": options,
                "correctAnswer": f"{top_name} ({top_party})",
                "explanation": f"{top_name} ({top_party}) mit {top_count} Reden!",
            })

        # Quiz: Most words total
        wordiest = self.get_wordiest_speakers(4)
        if wordiest:
            top_name, top_party, total_words, speech_count = wordiest[0]
            options = [f"{n} ({p})" for n, p, _, _ in wordiest]
            random.shuffle(options)
            questions.append({
                "id": "quiz-words-total",
                "type": "prediction",
                "question": "Wer hat insgesamt die meisten Wörter gesprochen?",
                "options": options,
                "correctAnswer": f"{top_name} ({top_party})",
                "explanation": f"{top_name} mit {total_words:,} Wörtern aus {speech_count} Reden!",
            })

        # Quiz: Hot topic
        hot = self.get_hot_topics(4)
        if hot:
            questions.append({
                "id": "quiz-hot-topic",
                "type": "prediction",
                "question": "Welches Wort ist bei den meisten Parteien unter den Top-Themen?",
                "options": hot[:4],
                "correctAnswer": hot[0],
                "explanation": f'"{hot[0]}" ist bei allen Fraktionen in der Top-50!',
            })

        # Quiz: Which individual person says Moin the most?
        from collections import Counter
        moin_person_counts = Counter()
        for speech in self.all_speeches:
            text = speech.get('text', '').lower()
            count = text.count('moin')
            if count > 0:
                speaker = speech['speaker']
                party = speech['party']
                moin_person_counts[(speaker, party)] += count

        if moin_person_counts:
            top_moin_people = moin_person_counts.most_common(4)
            top_speaker, top_party = top_moin_people[0][0]
            top_count = top_moin_people[0][1]
            options = [f"{s} ({p})" for (s, p), _ in top_moin_people]
            # Add more options if needed
            if len(options) < 4:
                for speech in self.all_speeches[:20]:
                    opt = f"{speech['speaker']} ({speech['party']})"
                    if opt not in options:
                        options.append(opt)
                    if len(options) >= 4:
                        break
            random.shuffle(options)
            questions.append({
                "id": "quiz-moin-person",
                "type": "prediction",
                "question": 'Welche Person sagt am häufigsten "Moin"?',
                "options": options[:4],
                "correctAnswer": f"{top_speaker} ({top_party})",
                "explanation": f'{top_speaker} grüßt mit {top_count}x "Moin"!',
            })

        # Quiz: Most unique speakers (spread of speakers)
        speaker_spread = [
            (p, len(self.speaker_stats.get(p, {})))
            for p in parties
        ]
        speaker_spread.sort(key=lambda x: x[1], reverse=True)
        if speaker_spread:
            top_party = speaker_spread[0][0]
            top_count = speaker_spread[0][1]
            options = [p for p, _ in speaker_spread[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-speaker-spread",
                "type": "prediction",
                "question": "Welche Fraktion hat die meisten verschiedenen Redner?",
                "options": options,
                "correctAnswer": top_party,
                "explanation": f"{top_party} mit {top_count} verschiedenen Rednern!",
            })

        # Quiz: Top question asker (Fragestunde/Regierungsbefragung)
        all_questioners = []
        for party, counts in self.question_speaker_stats.items():
            for speaker, count in counts.items():
                all_questioners.append((speaker, party, count))
        all_questioners.sort(key=lambda x: x[2], reverse=True)
        if all_questioners:
            top_name, top_party, top_count = all_questioners[0]
            options = [f"{n} ({p})" for n, p, _ in all_questioners[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-zwischenfragen",
                "type": "prediction",
                "question": "Wer stellt die meisten Fragen in der Fragestunde?",
                "options": options,
                "correctAnswer": f"{top_name} ({top_party})",
                "explanation": f"{top_name} ({top_party}) mit {top_count} Fragen!",
            })

        # =====================================================================
        # TONE ANALYSIS QUIZ QUESTIONS (Scheme D) - indices 12+
        # =====================================================================

        if self.has_tone_data():
            # Quiz 12: Most aggressive party
            agg_ranking = self.get_aggression_ranking()
            if agg_ranking and len(agg_ranking) >= 4:
                top_party, top_score = agg_ranking[0]
                options = [p for p, _ in agg_ranking[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-aggressive",
                    "type": "prediction",
                    "question": "Welche Partei nutzt die aggressivste Sprache?",
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f"{top_party} mit {top_score:.0f}% aggressiven Adjektiven!",
                })

            # Quiz 13: Most labeling party
            label_ranking = self.get_labeling_ranking()
            if label_ranking and len(label_ranking) >= 4:
                top_party, top_score = label_ranking[0]
                options = [p for p, _ in label_ranking[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-labeling",
                    "type": "prediction",
                    "question": 'Wer nutzt am meisten "ideologische Labels"?',
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f'{top_party} mit {top_score:.0f}% Etikettierungen wie "ideologisch", "radikal"!',
                })

            # Quiz 14: Most collaborative party
            collab_ranking = self.get_collaboration_ranking()
            if collab_ranking and len(collab_ranking) >= 4:
                top_party, top_score = collab_ranking[0]
                options = [p for p, _ in collab_ranking[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-collaborative",
                    "type": "prediction",
                    "question": "Welche Fraktion nutzt die kooperativste Sprache?",
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f"{top_party} mit {top_score:.0f}% kooperativen Verben!",
                })

            # Quiz 15: Most solution-oriented party
            solution_ranking = self.get_solution_focus_ranking()
            if solution_ranking and len(solution_ranking) >= 4:
                top_party, top_score = solution_ranking[0]
                options = [p for p, _ in solution_ranking[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-solution",
                    "type": "prediction",
                    "question": "Welche Partei spricht am lösungsorientiertesten?",
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f"{top_party} mit {top_score:.0f}% lösungsorientierten Verben!",
                })

            # Quiz 16: Most demanding party
            demand_ranking = self.get_demand_ranking()
            if demand_ranking and len(demand_ranking) >= 4:
                top_party, top_score = demand_ranking[0]
                options = [p for p, _ in demand_ranking[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-demanding",
                    "type": "prediction",
                    "question": "Welche Partei fordert am meisten?",
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f'{top_party} mit {top_score:.0f}% fordernden Verben wie "fordern", "verlangen"!',
                })

        # =====================================================================
        # GENDER ANALYSIS QUIZ QUESTIONS - indices 18+
        # =====================================================================

        if self.has_gender_data():
            # Quiz 18: Highest female ratio party
            gender_ratios = self.get_gender_ratio_by_party()
            if gender_ratios and len(gender_ratios) >= 4:
                top_party, top_ratio = gender_ratios[0]
                options = [p for p, _ in gender_ratios[:4]]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-gender-ratio",
                    "type": "prediction",
                    "question": "Welche Fraktion hat den höchsten Frauenanteil?",
                    "options": options,
                    "correctAnswer": top_party,
                    "explanation": f"{top_party} mit {top_ratio*100:.0f}% Rednerinnen!",
                })

            # Quiz 19: Top female speaker
            top_female = self.get_top_female_speakers(4)
            if top_female:
                top_name, top_party, top_count = top_female[0]
                options = [f"{n} ({p})" for n, p, _ in top_female]
                random.shuffle(options)
                questions.append({
                    "id": "quiz-top-female",
                    "type": "prediction",
                    "question": "Welche Frau hielt die meisten Reden?",
                    "options": options,
                    "correctAnswer": f"{top_name} ({top_party})",
                    "explanation": f"{top_name} ({top_party}) mit {top_count} Reden!",
                })

            # Quiz 20: Who interrupts more - men or women?
            patterns = self.get_interruption_patterns_by_gender()
            male_interrupts = patterns["interruptions_made"]["male"]
            female_interrupts = patterns["interruptions_made"]["female"]
            if male_interrupts > 0 or female_interrupts > 0:
                if male_interrupts > female_interrupts:
                    correct = "Männer"
                    ratio = male_interrupts / female_interrupts if female_interrupts > 0 else male_interrupts
                    explanation = f"Männer unterbrechen {ratio:.1f}x häufiger ({male_interrupts:,} vs {female_interrupts:,})!"
                else:
                    correct = "Frauen"
                    ratio = female_interrupts / male_interrupts if male_interrupts > 0 else female_interrupts
                    explanation = f"Frauen unterbrechen {ratio:.1f}x häufiger ({female_interrupts:,} vs {male_interrupts:,})!"
                questions.append({
                    "id": "quiz-gender-interrupts",
                    "type": "prediction",
                    "question": "Wer unterbricht häufiger?",
                    "options": ["Männer", "Frauen"],
                    "correctAnswer": correct,
                    "explanation": explanation,
                })

            # Quiz 21: Academic titles by gender
            academic = self.get_academic_titles_by_gender()
            male_dr = academic.get("male", 0)
            female_dr = academic.get("female", 0)
            if male_dr > 0 or female_dr > 0:
                if male_dr > female_dr:
                    correct = "Männer"
                    explanation = f"Männer: {male_dr*100:.0f}% Dr., Frauen: {female_dr*100:.0f}%"
                else:
                    correct = "Frauen"
                    explanation = f"Frauen: {female_dr*100:.0f}% Dr., Männer: {male_dr*100:.0f}%"
                questions.append({
                    "id": "quiz-academic-titles",
                    "type": "prediction",
                    "question": "Wer hat häufiger einen Doktortitel?",
                    "options": ["Männer", "Frauen"],
                    "correctAnswer": correct,
                    "explanation": explanation,
                })

        # =====================================================================
        # SENTIMENT ANALYSIS QUIZ - Biggest Critic (volume-weighted)
        # =====================================================================
        # Formula: score = negative_count × √(total_count)
        # This rewards both high negative count AND high volume
        import math
        interrupters = self.drama_stats.get("interrupters", {})
        negative = self.drama_stats.get("negative_interjections", {})

        # Calculate volume-weighted scores for people with ≥50 total interjections
        critic_scores = []
        for (name, party), total in interrupters.items():
            if total >= 50:
                neg_count = negative.get((name, party), 0)
                score = neg_count * math.sqrt(total)
                if neg_count > 0:
                    critic_scores.append((name, party, neg_count, total, score))

        critic_scores.sort(key=lambda x: x[4], reverse=True)

        if critic_scores and len(critic_scores) >= 4:
            top_name, top_party, top_neg, top_total, top_score = critic_scores[0]
            # Get rate leader for explanation
            rate_leader = max(critic_scores, key=lambda x: x[2] / x[3])
            rate_name, rate_party, rate_neg, rate_total = rate_leader[:4]
            rate_pct = round(rate_neg / rate_total * 100)

            options = [f"{n} ({p})" for n, p, _, _, _ in critic_scores[:4]]
            random.shuffle(options)
            questions.append({
                "id": "quiz-biggest-critic",
                "type": "prediction",
                "question": "Wer ruft am meisten kritisch dazwischen (absolut)?",
                "options": options,
                "correctAnswer": f"{top_name} ({top_party})",
                "explanation": f"{top_neg} kritische von {top_total} Zwischenrufen! ({rate_name} hat höhere Rate: {rate_pct}%)",
            })

        return questions

    def to_web_json(self) -> dict:
        """Export data in format expected by web app."""
        parties_data = []
        for party in self.metadata.get("parties", []):
            stats = self.party_stats.get(party, {})
            style = self.get_communication_style(party)
            champion = self.get_party_champion(party)

            # Count unique speakers for this party
            unique_speakers = len(self.speaker_stats.get(party, {}))

            # Calculate wortbeitraege (all speeches minus formal speeches)
            party_total_speeches = len([s for s in self.all_speeches if s.get('party') == party])
            party_formal_speeches = stats.get("real_speeches", stats.get("speeches", 0))
            party_wortbeitraege = party_total_speeches - party_formal_speeches

            parties_data.append({
                "party": party,
                "speeches": party_formal_speeches,
                "wortbeitraege": party_wortbeitraege,
                "totalWords": stats.get("total_words", 0),
                "uniqueSpeakers": unique_speakers,
                "topWords": [
                    {"word": w, "count": c}
                    for w, c in self.top_words.get(party, {}).get("nouns", [])[:7]
                ],
                "signatureWords": [
                    {"word": w, "ratio": round(r, 1)}
                    for w, r in self.get_distinctive_words(party, "nouns", 5)
                ],
                "keyTopics": [
                    {"word": w, "count": c, "ratio": round(r, 1)}
                    for w, c, r in self.get_key_topics(party, "nouns", 5)
                ],
                "avgSpeechLength": int(style.get("avg_speech_length", 0)),
                "descriptiveness": round(style.get("descriptiveness", 0) * 100, 1),
                "topSpeaker": {
                    "name": champion[0],
                    "speeches": champion[1]
                } if champion else {"name": "", "speeches": 0},
            })

        # Calculate total reden and wortbeitraege
        total_reden = sum(1 for s in self.all_speeches if s.get('category', 'rede' if s.get('type') == 'rede' else 'wortbeitrag') == 'rede')
        total_wortbeitraege = len(self.all_speeches) - total_reden

        return {
            "metadata": {
                "totalSpeeches": self.metadata.get("total_speeches", 0),
                "redenCount": total_reden,
                "wortbeitraegeCount": total_wortbeitraege,
                "totalWords": self.metadata.get("total_words", 0),
                "partyCount": len(self.metadata.get("parties", [])),
                "speakerCount": self.get_unique_speaker_count(),
                "wahlperiode": self.metadata.get("wahlperiode", 0),
                "sitzungen": self.metadata.get("sitzungen", 50),
            },
            "parties": parties_data,
            "drama": {
                "topZwischenrufer": [
                    {"name": n, "party": p, "count": c}
                    for n, p, c in self.get_top_interrupters(5)
                ],
                "mostInterrupted": [
                    {"name": n, "party": p, "count": c}
                    for n, p, c in self.get_most_interrupted(5)
                ],
                "applauseChampions": [
                    {"party": p, "count": c}
                    for p, c in self.get_applause_ranking(5)
                ],
                "loudestHecklers": [
                    {"party": p, "count": c}
                    for p, c in self.get_heckle_ranking(5)
                ],
                "zwischenrufStats": self._build_zwischenruf_stats(),
            },
            "topSpeakers": [
                {"name": n, "party": p, "speeches": c}
                for n, p, c in self.get_top_speakers(20)
            ],
            "topBefragungResponders": [
                {"name": n, "party": p, "responses": c}
                for n, p, c in self.get_top_befragung_responders(20)
            ],
            "topSpeakersByWords": [
                {"name": n, "party": p, "totalWords": w, "speeches": c}
                for n, p, w, c in self.get_wordiest_speakers(20)
            ],
            "topSpeakersByAvgWords": [
                {"name": n, "party": p, "avgWords": avg, "totalWords": w, "speeches": c}
                for n, p, avg, w, c in self.get_speakers_by_avg_words(20, min_speeches=5)
            ],
            "hotTopics": self.get_hot_topics(15),
            "toneAnalysis": self._build_tone_analysis_json() if self.has_tone_data() else None,
            "topicAnalysis": self._build_topic_analysis_json(),
            "funFacts": self._generate_fun_facts(),
            "genderAnalysis": self._build_gender_analysis_json() if self.has_gender_data() else None,
            # Raw data for frontend quiz generation
            "moinSpeakers": self._get_moin_speakers(10),
            "topQuestionAskers": self._get_top_question_askers(10),
        }

    def _get_moin_speakers(self, limit: int) -> list[dict]:
        """Get speakers who say 'Moin' most often."""
        from collections import Counter
        moin_counts: Counter[tuple[str, str]] = Counter()
        for speech in self.all_speeches:
            text = speech.get("text", "").lower()
            count = text.count("moin")
            if count > 0:
                moin_counts[(speech["speaker"], speech["party"])] += count
        return [
            {"name": n, "party": p, "count": c}
            for (n, p), c in moin_counts.most_common(limit)
        ]

    def _get_top_question_askers(self, limit: int) -> list[dict]:
        """Get top question askers from Fragestunde/Regierungsbefragung."""
        all_questioners = []
        for party, counts in self.question_speaker_stats.items():
            for speaker, count in counts.items():
                all_questioners.append((speaker, party, count))
        all_questioners.sort(key=lambda x: x[2], reverse=True)
        return [
            {"name": n, "party": p, "count": c}
            for n, p, c in all_questioners[:limit]
        ]

    def _build_zwischenruf_stats(self) -> dict:
        """Build sentiment classification stats for Zwischenrufe."""
        positive = self.drama_stats.get("positive_interjections", {})
        negative = self.drama_stats.get("negative_interjections", {})
        neutral = self.drama_stats.get("neutral_interjections", {})

        total_positive = sum(positive.values())
        total_negative = sum(negative.values())
        total_neutral = sum(neutral.values())
        total_all = total_positive + total_negative + total_neutral

        return {
            "total": total_all,
            "positive": total_positive,
            "negative": total_negative,
            "neutral": total_neutral,
            "positivePercent": round(total_positive / total_all * 100, 1) if total_all > 0 else 0,
            "negativePercent": round(total_negative / total_all * 100, 1) if total_all > 0 else 0,
            "neutralPercent": round(total_neutral / total_all * 100, 1) if total_all > 0 else 0,
            "classification": {
                "positive": "Zustimmung (genau, richtig, bravo, stimmt, ...)",
                "negative": "Kritik (unsinn, quatsch, falsch, lüge, ...)",
                "neutral": "Nicht klar zuordnenbar (Fragen, Kommentare, ...)",
            },
        }

    def _generate_fun_facts(self) -> list[dict]:
        """Generate fun facts including tone analysis insights."""
        facts = []
        meta = self.metadata

        # Basic stats facts
        total_words = meta.get("total_words", 0)
        total_speeches = meta.get("total_speeches", 0)
        sitzungen = meta.get("sitzungen", 50)

        if total_words and sitzungen:
            words_per_day = total_words // sitzungen
            facts.append({
                "emoji": "📅",
                "value": f"{words_per_day:,}",
                "label": "Wörter pro Sitzungstag",
                "category": "general",
            })

        if total_words and total_speeches:
            avg_words = total_words // total_speeches
            facts.append({
                "emoji": "🎤",
                "value": f"{avg_words:,}",
                "label": "Wörter pro Rede",
                "category": "general",
            })

        books = total_words // 50000 if total_words else 0
        if books:
            facts.append({
                "emoji": "📚",
                "value": str(books),
                "label": "Bücher-Äquivalent",
                "category": "general",
            })

        # Tone analysis facts (Scheme D)
        if self.has_tone_data():
            # Most aggressive party
            agg_ranking = self.get_aggression_ranking()
            if agg_ranking:
                top_party, top_score = agg_ranking[0]
                facts.append({
                    "emoji": "💢",
                    "value": f"{top_score:.0f}%",
                    "label": f"Aggression ({top_party})",
                    "sublabel": "aggressivste Sprache",
                    "category": "tone",
                })

            # Most labeling party (key Scheme D insight)
            label_ranking = self.get_labeling_ranking()
            if label_ranking:
                top_party, top_score = label_ranking[0]
                if top_score > 1:  # Only show if significant
                    facts.append({
                        "emoji": "🏷️",
                        "value": f"{top_score:.0f}%",
                        "label": f"Etikettierung ({top_party})",
                        "sublabel": '"ideologisch", "radikal"...',
                        "category": "tone",
                    })

            # Most collaborative party
            collab_ranking = self.get_collaboration_ranking()
            if collab_ranking:
                top_party, top_score = collab_ranking[0]
                facts.append({
                    "emoji": "🤝",
                    "value": f"{top_score:.0f}%",
                    "label": f"Kooperation ({top_party})",
                    "sublabel": "kooperativste Sprache",
                    "category": "tone",
                })

            # Top labeling word (key insight)
            best_label = None
            for party in self.metadata.get("parties", []):
                words = self.get_top_words_by_category(party, "adjectives", "labeling", 1)
                if words:
                    word, count = words[0]
                    if best_label is None or count > best_label[1]:
                        best_label = (word, count, party)

            if best_label:
                word, count, party = best_label
                facts.append({
                    "emoji": "🎯",
                    "value": f'"{word}"',
                    "label": f"{count}× ({party})",
                    "sublabel": "häufigstes Label",
                    "category": "tone",
                })

            # Top aggressive word
            best_word = None
            for party in self.metadata.get("parties", []):
                words = self.get_top_words_by_category(party, "adjectives", "aggressive", 1)
                if words:
                    word, count = words[0]
                    if best_word is None or count > best_word[1]:
                        best_word = (word, count, party)

            if best_word:
                word, count, party = best_word
                facts.append({
                    "emoji": "🔥",
                    "value": f'"{word}"',
                    "label": f"{count}× ({party})",
                    "sublabel": "häufigstes Kampfwort",
                    "category": "tone",
                })

            # Affirmative spread (difference between most and least affirmative)
            aff_ranking = self.get_affirmative_ranking()
            if aff_ranking and len(aff_ranking) >= 2:
                most_aff = aff_ranking[0]
                least_aff = aff_ranking[-1]
                spread = most_aff[1] - least_aff[1]
                if spread > 10:
                    facts.append({
                        "emoji": "📊",
                        "value": f"{spread:.0f}%",
                        "label": "Positivitäts-Spread",
                        "sublabel": f"{most_aff[0]} vs {least_aff[0]}",
                        "category": "tone",
                    })

        # Gender analysis facts
        if self.has_gender_data():
            distribution = self.get_gender_distribution()
            total_known = distribution["male"] + distribution["female"]

            if total_known > 0:
                female_pct = (distribution["female"] / total_known) * 100
                facts.append({
                    "emoji": "👩",
                    "value": f"{female_pct:.0f}%",
                    "label": "Rednerinnen",
                    "sublabel": f"{distribution['female']} von {total_known}",
                    "category": "gender",
                })

            # Top party by female ratio
            gender_ratios = self.get_gender_ratio_by_party()
            if gender_ratios:
                top_party, top_ratio = gender_ratios[0]
                facts.append({
                    "emoji": "🏆",
                    "value": f"{top_ratio*100:.0f}%",
                    "label": f"Frauenanteil ({top_party})",
                    "sublabel": "höchster Frauenanteil",
                    "category": "gender",
                })

            # Top female speaker
            top_female = self.get_top_female_speakers(1)
            if top_female:
                name, party, speeches = top_female[0]
                facts.append({
                    "emoji": "🎤",
                    "value": name.split()[-1],  # Last name only
                    "label": f"{speeches} Reden",
                    "sublabel": "Top-Rednerin",
                    "category": "gender",
                })

            # Interruption ratio
            patterns = self.get_interruption_patterns_by_gender()
            male_int = patterns["interruptions_made"]["male"]
            female_int = patterns["interruptions_made"]["female"]
            if male_int > 0 and female_int > 0:
                ratio = male_int / female_int
                facts.append({
                    "emoji": "🗣️",
                    "value": f"{ratio:.1f}x",
                    "label": "Männer unterbrechen mehr",
                    "sublabel": f"{male_int:,} vs {female_int:,}",
                    "category": "gender",
                })

        return facts

    def _build_tone_analysis_json(self) -> dict:
        """Build tone analysis section for web JSON export (Scheme D + E)."""
        from .party_profiles import build_party_profile
        from ..categorizer import ToneScores

        parties_tone = []
        party_profiles = {}

        # First pass: collect all ToneScores for rank-based comparison
        all_party_scores: dict[str, ToneScores] = {}
        for party in self.metadata.get("parties", []):
            if party not in self.tone_data:
                continue
            scores_dict = self.tone_data[party]
            all_party_scores[party] = ToneScores(
                affirmative_score=scores_dict.get("affirmative", 50.0),
                aggression_index=scores_dict.get("aggression", 0.0),
                labeling_index=scores_dict.get("labeling", 0.0),
                solution_focus=scores_dict.get("solution_focus", 50.0),
                collaboration_score=scores_dict.get("collaboration", 50.0),
                demand_intensity=scores_dict.get("demand_intensity", 0.0),
                acknowledgment_rate=scores_dict.get("acknowledgment", 0.0),
                # Extended scores (Scheme E)
                authority_index=scores_dict.get("authority", 50.0),
                future_orientation=scores_dict.get("future_orientation", 50.0),
                emotional_intensity=scores_dict.get("emotional_intensity", 50.0),
                inclusivity_index=scores_dict.get("inclusivity", 50.0),
                discriminatory_index=scores_dict.get("discriminatory", 0.0),
            )

        # Second pass: build profiles with rank-based classification
        for party, scores in all_party_scores.items():
            profile = build_party_profile(party, scores, all_party_scores)
            party_profiles[party] = profile.to_dict()

            parties_tone.append({
                "party": party,
                "scores": self.tone_data[party],
                # Adjective categories (Scheme D)
                "topAffirmative": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "adjectives", "affirmative", 5)
                ],
                "topCritical": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "adjectives", "critical", 5)
                ],
                "topAggressive": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "adjectives", "aggressive", 5)
                ],
                "topLabeling": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "adjectives", "labeling", 5)
                ],
                # Verb categories (Scheme D)
                "topSolution": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "solution", 5)
                ],
                "topProblem": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "problem", 5)
                ],
                "topCollaborative": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "collaborative", 5)
                ],
                "topConfrontational": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "confrontational", 5)
                ],
                "topDemanding": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "demanding", 5)
                ],
                "topAcknowledging": [
                    {"word": w, "count": c}
                    for w, c in self.get_top_words_by_category(party, "verbs", "acknowledging", 5)
                ],
            })

        return {
            "parties": parties_tone,
            "partyProfiles": party_profiles,
            "rankings": {
                # Adjective-based scores (Scheme D)
                "affirmative": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_affirmative_ranking()
                ],
                "aggression": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_aggression_ranking()
                ],
                "labeling": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_labeling_ranking()
                ],
                # Verb-based scores (Scheme D)
                "solutionFocus": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_solution_focus_ranking()
                ],
                "collaboration": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_collaboration_ranking()
                ],
                "demandIntensity": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_demand_ranking()
                ],
                "acknowledgment": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_acknowledgment_ranking()
                ],
                # Extended scores (Scheme E)
                "authority": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_authority_ranking()
                ],
                "futureOrientation": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_future_orientation_ranking()
                ],
                "emotionalIntensity": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_emotional_intensity_ranking()
                ],
                "inclusivity": [
                    {"party": p, "score": round(s, 1)}
                    for p, s in self.get_inclusivity_ranking()
                ],
                "discriminatory": [
                    {"party": p, "score": round(s, 2)}
                    for p, s in self.get_discriminatory_ranking()
                ],
                "discriminatoryCounts": [
                    {"party": p, "count": c}
                    for p, c in self.get_discriminatory_counts()
                    if p != "fraktionslos"
                ],
            },
        }

    def _build_gender_analysis_json(self) -> dict:
        """Build gender analysis section for web JSON export.

        Provides two metrics transparently:
        - "Reden" (formal speeches): Main podium speeches only
        - "Wortmeldungen" (all activity): Including questions, interventions, etc.
        """
        distribution = self.get_gender_distribution()
        total_known = distribution["male"] + distribution["female"]

        # Per-party gender stats
        parties_gender = []
        for party in self.metadata.get("parties", []):
            by_party = self.get_gender_distribution_by_party().get(party, {})
            male = by_party.get("male", 0)
            female = by_party.get("female", 0)
            total = male + female
            parties_gender.append({
                "party": party,
                "male": male,
                "female": female,
                "femaleRatio": round((female / total) * 100, 1) if total > 0 else 0,
            })

        # Sort by female ratio
        parties_gender.sort(key=lambda x: x["femaleRatio"], reverse=True)

        # Interruption patterns
        interruption_patterns = self.get_interruption_patterns_by_gender()

        return {
            "distribution": {
                "male": distribution["male"],
                "female": distribution["female"],
                "unknown": distribution["unknown"],
                "femalePercent": round((distribution["female"] / total_known) * 100, 1) if total_known > 0 else 0,
            },
            "byParty": parties_gender,
            # Formal speeches only (Reden) - comparable to existing wrapped stats
            "topFemaleSpeakersReden": [
                {"name": n, "party": p, "count": s}
                for n, p, s in self.get_top_female_speakers(10, formal_only=True)
            ],
            "topMaleSpeakersReden": [
                {"name": n, "party": p, "count": s}
                for n, p, s in self.get_top_male_speakers(10, formal_only=True)
            ],
            # All activity (Wortmeldungen) - includes questions, interventions, etc.
            "topFemaleSpeakersAll": [
                {"name": n, "party": p, "count": s}
                for n, p, s in self.get_top_female_speakers(10, formal_only=False)
            ],
            "topMaleSpeakersAll": [
                {"name": n, "party": p, "count": s}
                for n, p, s in self.get_top_male_speakers(10, formal_only=False)
            ],
            "interruptionPatterns": {
                "maleInterruptions": interruption_patterns["interruptions_made"]["male"],
                "femaleInterruptions": interruption_patterns["interruptions_made"]["female"],
                "maleInterrupted": interruption_patterns["interruptions_received"]["male"],
                "femaleInterrupted": interruption_patterns["interruptions_received"]["female"],
            },
            "speechLength": self.get_speech_length_by_gender(),
            "academicTitles": self.get_academic_titles_by_gender(),
            # Metadata about metrics
            "_metrics": {
                "reden": "Formal podium speeches only",
                "wortmeldungen": "All activity including questions, interventions",
            },
        }

    def _build_topic_analysis_json(self) -> dict:
        """Build topic analysis section for web JSON export (Scheme F).

        Aggregates topic noun counts from all speeches by party.
        Returns per-1000 word frequencies for each policy topic.
        """
        import re
        from collections import Counter
        from noun_analysis.lexicons import TOPIC_LEXICONS, TopicCategory

        # Build word-to-topic lookup
        word_to_topic: dict[str, str] = {}
        for topic, words in TOPIC_LEXICONS.items():
            for word in words:
                word_to_topic[word] = topic.value

        topic_set = set(word_to_topic.keys())
        word_pattern = re.compile(r'\b[a-zäöüß]{4,}\b')
        topic_names = [t.value for t in TopicCategory]

        # Count topics per party
        party_topic_counts: dict[str, dict[str, int]] = {}
        party_word_counts: dict[str, int] = {}

        for speech in self.all_speeches:
            party = speech.get("party", "")
            text = speech.get("text", "").lower()
            if not party or not text:
                continue

            if party not in party_topic_counts:
                party_topic_counts[party] = {t: 0 for t in topic_names}
                party_word_counts[party] = 0

            words = word_pattern.findall(text)
            party_word_counts[party] += len(words)

            for word in words:
                if word in topic_set:
                    topic = word_to_topic[word]
                    party_topic_counts[party][topic] += 1

        # Calculate per-1000 frequencies
        party_scores: dict[str, dict[str, float]] = {}
        for party in party_topic_counts:
            total_words = party_word_counts.get(party, 0)
            if total_words == 0:
                continue
            party_scores[party] = {
                topic: round((count / total_words) * 1000, 2)
                for topic, count in party_topic_counts[party].items()
            }

        # Find top topics overall (across all parties)
        bundestag_totals: dict[str, int] = {t: 0 for t in topic_names}
        for counts in party_topic_counts.values():
            for topic, count in counts.items():
                bundestag_totals[topic] += count

        total_all_words = sum(party_word_counts.values())
        bundestag_scores = {
            topic: round((count / total_all_words) * 1000, 2) if total_all_words > 0 else 0
            for topic, count in bundestag_totals.items()
        }

        # Rank topics
        sorted_topics = sorted(
            bundestag_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "byParty": party_scores,
            "overall": bundestag_scores,
            "topTopics": [
                {"topic": topic, "score": score, "rank": i + 1}
                for i, (topic, score) in enumerate(sorted_topics[:6])
            ],
        }
