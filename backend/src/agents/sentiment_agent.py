from __future__ import annotations

import re
import os
from typing import Any, Dict, List, Optional
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
    - Fallback: Keyword-based sentiment scoring
    """
    name = "sentiment_agent"

    def __init__(self) -> None:
        self.hf_client = HuggingFaceClient()
        self.positive_words = {
            'good', 'great', 'excellent', 'happy', 'pleased', 'satisfied',
            'success', 'successful', 'agree', 'perfect', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'appreciate', 'thank', 'thanks'
        }
        self.negative_words = {
            'bad', 'poor', 'terrible', 'unhappy', 'disappointed', 'unsatisfied',
            'failure', 'failed', 'disagree', 'problem', 'issue', 'concern',
            'hate', 'dislike', 'worry', 'worried', 'unfortunately', 'sadly'
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
        Simple sentiment analysis using keyword matching.
        Fallback method.
        """
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        pos_count = sum(1 for w in words if w in self.positive_words)
        neg_count = sum(1 for w in words if w in self.negative_words)
        
        total = pos_count + neg_count
        if total == 0:
            return {"sentiment": "Neutral", "score": 0.5}
        
        pos_ratio = pos_count / total
        
        if pos_ratio > 0.6:
            return {"sentiment": "Positive", "score": pos_ratio}
        elif pos_ratio < 0.4:
            return {"sentiment": "Negative", "score": 1 - pos_ratio}
        else:
            return {"sentiment": "Neutral", "score": 0.5}

    def _analyze_sentiment(self, text: str, segments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sentiment with HuggingFace API and fallback.
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
