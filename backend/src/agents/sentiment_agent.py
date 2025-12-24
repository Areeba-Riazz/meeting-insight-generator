from __future__ import annotations

import re
import os
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from .base_agent import BaseAgent


class HuggingFaceClient:
    """Client for HuggingFace Inference API with error handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def query(self, model: str, inputs: Dict[str, Any], timeout: int = 30) -> Optional[Dict]:
        """Query HuggingFace model with error handling."""
        if not self.token:
            return None
        
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/{model}",
                headers=self.headers,
                json=inputs,
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[HuggingFace API Error] {e}")
            return None


class SentimentAgent(BaseAgent):
    """
    Analyze sentiment of meeting using HuggingFace RoBERTa model.
    - Primary: HuggingFace sentiment analysis model
    - Fallback: Enhanced NLP-based sentiment scoring with negation, intensity, n-grams
    """
    name = "sentiment_agent"

    def __init__(self) -> None:
        self.hf_client = HuggingFaceClient()
        
        # Core sentiment words with business/meeting context
        self.positive_words = {
            'good', 'great', 'excellent', 'happy', 'pleased', 'satisfied',
            'success', 'successful', 'agree', 'perfect', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'appreciate', 'thank', 'thanks',
            # Business-specific
            'approved', 'accomplished', 'achieved', 'productive', 'efficient',
            'innovative', 'breakthrough', 'milestone', 'profitable', 'growth',
            'improved', 'optimized', 'streamlined', 'exceeded', 'outperformed',
            'collaboration', 'synergy', 'aligned', 'consensus', 'resolution',
            'positive', 'strong', 'solid', 'promising', 'impressive'
        }
        
        self.negative_words = {
            'bad', 'poor', 'terrible', 'unhappy', 'disappointed', 'unsatisfied',
            'failure', 'failed', 'disagree', 'problem', 'issue', 'concern',
            'hate', 'dislike', 'worry', 'worried', 'unfortunately', 'sadly',
            # Business-specific
            'delayed', 'blocked', 'bottleneck', 'risk', 'threat', 'declined',
            'underperformed', 'missed', 'overbudget', 'escalate', 'critical',
            'blocker', 'impediment', 'setback', 'regression', 'conflict',
            'negative', 'weak', 'concerning', 'problematic', 'difficult'
        }
        
        # Bigrams and trigrams
        self.positive_bigrams = {
            'very good', 'really great', 'went well', 'looks good',
            'sounds great', 'makes sense', 'well done', 'good job',
            'great work', 'nice work', 'looks promising', 'going well',
            'on track', 'positive feedback', 'good progress', 'really appreciate'
        }
        
        self.negative_bigrams = {
            'not good', 'not great', 'went wrong', 'doesnt work',
            'big problem', 'major issue', 'bad news', 'gone wrong',
            'not working', 'behind schedule', 'over budget', 'serious concern',
            'not happy', 'not satisfied', 'fell short', 'needs improvement'
        }
        
        # Intensity modifiers
        self.amplifiers = {
            'very', 'extremely', 'incredibly', 'absolutely', 'completely',
            'totally', 'really', 'so', 'quite', 'highly', 'particularly',
            'especially', 'exceptionally', 'remarkably', 'significantly'
        }
        
        self.diminishers = {
            'somewhat', 'slightly', 'barely', 'hardly', 'little',
            'a bit', 'kind of', 'sort of', 'rather', 'fairly',
            'moderately', 'relatively', 'marginally'
        }
        
        # Negation terms
        self.negation_terms = {
            'not', 'no', 'never', 'neither', 'nobody', 'nothing',
            'nowhere', 'hardly', 'barely', 'scarcely', "n't", 'without',
            'none', 'noone'
        }
        
        # Contrast words (second clause carries more weight)
        self.contrast_words = {
            'but', 'however', 'although', 'though', 'yet',
            'nevertheless', 'nonetheless', 'still', 'despite'
        }
        
        # Punctuation that ends negation scope
        self.negation_enders = {',', '.', '!', '?', ';', ':', 'but', 'however', 'and'}

    def _extract_ngrams(self, words: List[str], n: int = 2) -> List[str]:
        """Extract n-grams from word list."""
        if len(words) < n:
            return []
        return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

    def _handle_negations(self, words: List[str]) -> Tuple[List[str], List[bool]]:
        """
        Mark words that are negated.
        Returns: (words, is_negated_flags)
        """
        is_negated = [False] * len(words)
        negate = False
        
        for i, word in enumerate(words):
            if word in self.negation_terms or word.endswith("n't"):
                negate = True
            elif word in self.negation_enders:
                negate = False
            elif negate:
                is_negated[i] = True
                # Don't reset negate immediately - allow for phrases like "not very good"
                if word in self.positive_words or word in self.negative_words:
                    negate = False
        
        return words, is_negated

    def _get_word_context(self, words: List[str], index: int) -> str:
        """Determine rough POS context for weighting."""
        word = words[index]
        
        # Adverbs often end in -ly
        if word.endswith('ly'):
            return 'adverb'
        
        # Check if it follows a copula (linking verb)
        if index > 0:
            prev_word = words[index-1]
            if prev_word in {'is', 'was', 'are', 'were', 'been', 'be', 'being', 'am'}:
                return 'adjective'
        
        return 'other'

    def _calculate_weighted_sentiment(self, words: List[str]) -> float:
        """
        Calculate sentiment with intensity modifiers, negation, and POS weighting.
        """
        words, is_negated = self._handle_negations(words)
        score = 0.0
        
        for i, word in enumerate(words):
            # Skip if not a sentiment word
            if word not in self.positive_words and word not in self.negative_words:
                continue
            
            # Base sentiment
            base_score = 1.0 if word in self.positive_words else -1.0
            
            # Apply negation (flip sentiment)
            if is_negated[i]:
                base_score *= -0.8  # Negation doesn't completely flip (e.g., "not good" ≠ "bad")
            
            # Check for intensity modifier in previous word
            weight = 1.0
            if i > 0:
                prev_word = words[i-1]
                if prev_word in self.amplifiers:
                    weight = 1.5
                elif prev_word in self.diminishers:
                    weight = 0.5
            
            # Apply POS-based weighting
            context = self._get_word_context(words, i)
            if context in ['adjective', 'adverb']:
                weight *= 1.2
            else:
                weight *= 0.8
            
            score += base_score * weight
        
        return score

    def _analyze_punctuation(self, text: str) -> float:
        """Analyze punctuation for sentiment cues."""
        exclamation_count = text.count('!')
        question_count = text.count('?')
        ellipsis_count = text.count('...')
        
        # Multiple exclamations often indicate strong positive emotion
        exclamation_weight = min(exclamation_count * 0.1, 0.5)
        
        # Many questions might indicate uncertainty/concern
        question_weight = min(question_count * 0.05, 0.2) * -1
        
        # Ellipsis often indicates hesitation/concern
        ellipsis_weight = ellipsis_count * -0.1
        
        return exclamation_weight + question_weight + ellipsis_weight

    def _handle_contrast(self, text: str) -> Optional[float]:
        """
        Handle contrastive conjunctions - second part carries more weight.
        Returns None if no contrast detected.
        """
        text_lower = text.lower()
        
        for contrast in self.contrast_words:
            pattern = rf'\b{contrast}\b'
            if re.search(pattern, text_lower):
                parts = re.split(pattern, text_lower, maxsplit=1)
                if len(parts) == 2:
                    # First part gets 30% weight, second part gets 70%
                    words1 = re.findall(r'\b[a-z]+\b', parts[0])
                    words2 = re.findall(r'\b[a-z]+\b', parts[1])
                    
                    score1 = self._calculate_weighted_sentiment(words1) * 0.3
                    score2 = self._calculate_weighted_sentiment(words2) * 0.7
                    return score1 + score2
        
        return None

    def _score_ngrams(self, text: str) -> float:
        """Score bigrams and trigrams."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        bigrams = self._extract_ngrams(words, 2)
        bigrams_text = [' '.join(bg) for bg in [words[i:i+2] for i in range(len(words)-1)]]
        
        score = 0.0
        matched_indices = set()
        
        # Score bigrams (these override individual word scores)
        for i, bigram in enumerate(bigrams_text):
            if bigram in self.positive_bigrams:
                score += 1.5  # Bigrams are more reliable
                matched_indices.add(i)
                matched_indices.add(i+1)
            elif bigram in self.negative_bigrams:
                score -= 1.5
                matched_indices.add(i)
                matched_indices.add(i+1)
        
        return score

    def _analyze_by_sentences(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment sentence by sentence for better accuracy."""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        if not sentences:
            return {"sentiment": "Neutral", "score": 0.5, "consistency": 0.0}
        
        sentence_scores = []
        
        for sentence in sentences:
            if len(sentence) < 5:
                continue
            
            # Check for contrast patterns first
            contrast_score = self._handle_contrast(sentence)
            if contrast_score is not None:
                sentence_scores.append(contrast_score)
                continue
            
            # Score n-grams
            ngram_score = self._score_ngrams(sentence)
            
            # Score individual words with weighting
            words = re.findall(r'\b[a-z]+\b', sentence.lower())
            word_score = self._calculate_weighted_sentiment(words)
            
            # Analyze punctuation
            punct_score = self._analyze_punctuation(sentence)
            
            # Combine scores
            total_score = ngram_score + word_score + punct_score
            sentence_scores.append(total_score)
        
        if not sentence_scores:
            return {"sentiment": "Neutral", "score": 0.5, "consistency": 0.0}
        
        # Use median to reduce outlier impact
        sorted_scores = sorted(sentence_scores)
        median_score = sorted_scores[len(sorted_scores)//2]
        
        # Calculate consistency (agreement between sentences)
        positive_count = sum(1 for s in sentence_scores if s > 0.2)
        negative_count = sum(1 for s in sentence_scores if s < -0.2)
        neutral_count = len(sentence_scores) - positive_count - negative_count
        
        max_agreement = max(positive_count, negative_count, neutral_count)
        consistency = max_agreement / len(sentence_scores) if sentence_scores else 0.0
        
        # Convert score to sentiment label and normalize score
        if median_score > 0.3:
            sentiment = "Positive"
            normalized_score = min(0.5 + (median_score / 10.0), 1.0)
        elif median_score < -0.3:
            sentiment = "Negative"
            normalized_score = min(0.5 + (abs(median_score) / 10.0), 1.0)
        else:
            sentiment = "Neutral"
            normalized_score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": normalized_score,
            "consistency": consistency
        }

    def _analyze_sentiment_hf(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment using HuggingFace RoBERTa model.
        Returns None if API fails.
        """
        result = self.hf_client.query(
            "cardiffnlp/twitter-roberta-base-sentiment-latest",
            {"inputs": text}
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            scores = result[0]
            # Find highest scoring sentiment
            max_score = max(scores, key=lambda x: x['score'])
            return {
                "sentiment": max_score['label'],
                "score": max_score['score']
            }
        return None

    def _analyze_sentiment_fallback(self, text: str) -> Dict[str, Any]:
        """
        Enhanced sentiment analysis using multiple NLP techniques.
        """
        return self._analyze_by_sentences(text)

    def _analyze_sentiment(self, text: str, segments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sentiment with HuggingFace API and enhanced fallback.
        """
        # Analyze overall sentiment
        overall_hf = self._analyze_sentiment_hf(text[:512])  # Limit text length
        overall = overall_hf if overall_hf else self._analyze_sentiment_fallback(text)
        
        # Analyze per segment
        segment_sentiments = []
        for seg in segments[:20]:  # Limit to first 20 segments to avoid rate limits
            seg_text = seg.get('text', '')
            if len(seg_text) < 10:
                continue
            
            # Try HuggingFace first
            seg_sentiment = self._analyze_sentiment_hf(seg_text)
            if not seg_sentiment:
                seg_sentiment = self._analyze_sentiment_fallback(seg_text)
            
            segment_sentiments.append({
                "start": seg.get('start', 0),
                "end": seg.get('end', 0),
                "sentiment": seg_sentiment['sentiment'],
                "score": seg_sentiment['score'],
                "text": seg_text[:100]
            })
        
        return {
            "overall": overall['sentiment'],
            "score": overall['score'],
            "segments": segment_sentiments
        }

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment overall and per segment.
        
        Returns:
            {
                "sentiment": {
                    "overall": "Positive",
                    "score": 0.75,
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 30.5,
                            "sentiment": "Neutral",
                            "score": 0.5,
                            "text": "Welcome everyone..."
                        }
                    ]
                }
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        sentiment_result = self._analyze_sentiment(text, segments)
        
        return {"sentiment": sentiment_result}