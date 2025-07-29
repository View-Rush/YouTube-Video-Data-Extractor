import logging
import re
from typing import Dict, Any, List, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentAnalysisService:
    """Service for analyzing and scoring YouTube video content for Sri Lankan relevance."""
    
    def __init__(self):
        self.sri_lanka_indicators = self._initialize_sri_lanka_indicators()
        self.quality_indicators = self._initialize_quality_indicators()
        self.spam_patterns = self._initialize_spam_patterns()
    
    def _initialize_sri_lanka_indicators(self) -> Dict[str, Any]:
        """Initialize Sri Lankan content indicators."""
        return {
            'locations': {
                # Major cities and towns
                'colombo', 'kandy', 'galle', 'jaffna', 'negombo', 'anuradhapura', 'polonnaruwa',
                'trincomalee', 'batticaloa', 'ratnapura', 'kurunegala', 'puttalam', 'badulla',
                'bandarawela', 'ella', 'nuwara eliya', 'matara', 'hambantota', 'chilaw', 'kegalle',
                'monaragala', 'vavuniya', 'mannar', 'ampara', 'kalutara', 'gampaha', 'matale',
                'sigiriya', 'dambulla', 'bentota', 'hikkaduwa', 'unawatuna', 'mirissa', 'arugam bay',
                'yala', 'udawalawe', 'sinharaja', 'horton plains', 'adams peak', 'pidurangala',
                'temple of tooth', 'gangaramaya', 'kelaniya', 'kataragama', 'sri pada'
            },
            'languages': {
                'sinhala', 'tamil', 'sinhalese', 'sri lankan', 'lk', 'ceylon'
            },
            'cultural_terms': {
                'ayubowan', 'vanakkam', 'poya', 'vesak', 'poson', 'esala', 'kathina', 'avurudu',
                'sinhala new year', 'tamil new year', 'deepavali', 'christmas', 'eid',
                'kiribath', 'kottu', 'hoppers', 'string hoppers', 'pol sambol', 'parippu',
                'rice and curry', 'watalappan', 'kokis', 'achcharu', 'pittu', 'roti',
                'thala guli', 'aggala', 'halapa', 'kevum', 'athirasa'
            },
            'institutions': {
                'university of colombo', 'university of peradeniya', 'university of moratuwa',
                'university of kelaniya', 'university of sri jayewardenepura', 'university of ruhuna',
                'university of jaffna', 'open university of sri lanka', 'sliit', 'nsbm',
                'royal college', 'st thomas college', 'ladies college', 'visakha vidyalaya',
                'nalanda college', 'ananda college', 'dharmaraja college', 'trinity college',
                'st josephs college', 'wesley college'
            },
            'media_outlets': {
                'daily mirror', 'sunday times', 'daily news', 'island', 'lankadeepa', 'divaina',
                'ada derana', 'tv derana', 'itv', 'rupavahini', 'charana tv', 'sirasa tv',
                'hiru tv', 'swarnavahini', 'art tv', 'shakthi tv', 'capital tv'
            },
            'sports_teams': {
                'sri lanka cricket', 'sri lankan lions', 'colombo fc', 'police fc', 'army fc',
                'navy fc', 'air force fc', 'ratnam fc', 'renown sc', 'saunders sc'
            },
            'politicians': {
                'ranil wickremesinghe', 'mahinda rajapaksa', 'gotabaya rajapaksa', 'sajith premadasa',
                'maithripala sirisena', 'chandrika kumaratunga', 'anura kumara dissanayake'
            },
            'celebrities': {
                'jackson anthony', 'ranjan ramanayake', 'sanath jayasuriya', 'kumar sangakkara',
                'mahela jayawardene', 'lasith malinga', 'chaminda vaas', 'muttiah muralitharan'
            }
        }
    
    def _initialize_quality_indicators(self) -> Dict[str, Any]:
        """Initialize quality indicators for content scoring."""
        return {
            'positive_indicators': {
                'hd', 'high definition', '1080p', '4k', 'uhd', 'official', 'verified',
                'original', 'exclusive', 'interview', 'documentary', 'educational',
                'tutorial', 'guide', 'review', 'analysis', 'behind the scenes'
            },
            'negative_indicators': {
                'clickbait', 'fake', 'scam', 'spam', 'bot', 'automated', 'duplicate',
                'stolen', 'copied', 'repost', 'mirror', 'leaked', 'pirated'
            },
            'engagement_keywords': {
                'like', 'subscribe', 'comment', 'share', 'bell', 'notification',
                'follow', 'join', 'community', 'discussion', 'feedback'
            }
        }
    
    def _initialize_spam_patterns(self) -> List[str]:
        """Initialize spam detection patterns."""
        return [
            r'\b(100%|guaranteed|instant|immediate|urgent|limited time)\b',
            r'\b(click here|download now|act now|order now)\b',
            r'\$[\d,]+\s*(dollars?|usd|earn|make|profit)',
            r'\b(miracle|secret|revealed|exposed|shocking)\b',
            r'(!!!|!!!)|\?{3,}|\.{4,}',
            r'\b(watch.*before.*deleted|removed|banned)\b'
        ]
    
    def analyze_content(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze video content for Sri Lankan relevance and quality."""
        title = video_data.get('title', '').lower()
        description = video_data.get('description', '').lower()
        channel_title = video_data.get('channel_title', '').lower()
        tags = [tag.lower() for tag in video_data.get('tags', [])]
        
        # Combine all text for analysis
        combined_text = f"{title} {description} {channel_title} {' '.join(tags)}"
        
        # Calculate scores
        sri_lanka_score = self._calculate_sri_lanka_score(combined_text, video_data)
        quality_score = self._calculate_quality_score(combined_text, video_data)
        engagement_score = self._calculate_engagement_score(video_data)
        spam_score = self._calculate_spam_score(combined_text)
        
        # Determine if content is Sri Lankan
        is_sri_lankan = sri_lanka_score >= 0.3  # Threshold can be adjusted
        
        # Calculate overall content score
        content_score = (sri_lanka_score * 0.4 + quality_score * 0.3 + 
                        engagement_score * 0.2 + (1 - spam_score) * 0.1)
        
        return {
            'is_sri_lankan_content': is_sri_lankan,
            'content_score': round(content_score, 3),
            'sri_lanka_score': round(sri_lanka_score, 3),
            'quality_score': round(quality_score, 3),
            'engagement_score': round(engagement_score, 3),
            'spam_score': round(spam_score, 3),
            'analysis_metadata': {
                'matched_locations': self._find_matched_terms(combined_text, self.sri_lanka_indicators['locations']),
                'matched_cultural_terms': self._find_matched_terms(combined_text, self.sri_lanka_indicators['cultural_terms']),
                'detected_language': self._detect_language(combined_text),
                'content_category': self._categorize_content(combined_text),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    def _calculate_sri_lanka_score(self, text: str, video_data: Dict[str, Any]) -> float:
        """Calculate Sri Lankan relevance score."""
        score = 0.0
        max_score = 0.0
        
        # Location mentions (high weight)
        location_matches = self._count_matches(text, self.sri_lanka_indicators['locations'])
        location_score = min(location_matches * 0.2, 0.4)
        score += location_score
        max_score += 0.4
        
        # Language indicators (medium weight)
        language_matches = self._count_matches(text, self.sri_lanka_indicators['languages'])
        language_score = min(language_matches * 0.15, 0.3)
        score += language_score
        max_score += 0.3
        
        # Cultural terms (medium weight)
        cultural_matches = self._count_matches(text, self.sri_lanka_indicators['cultural_terms'])
        cultural_score = min(cultural_matches * 0.1, 0.2)
        score += cultural_score
        max_score += 0.2
        
        # Institutions and media (low weight)
        institution_matches = self._count_matches(text, self.sri_lanka_indicators['institutions'])
        media_matches = self._count_matches(text, self.sri_lanka_indicators['media_outlets'])
        institutional_score = min((institution_matches + media_matches) * 0.05, 0.1)
        score += institutional_score
        max_score += 0.1
        
        # Channel location (if available)
        channel_country = video_data.get('channel_country', '').lower()
        if channel_country in ['lk', 'sri lanka', 'sri_lanka']:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, text: str, video_data: Dict[str, Any]) -> float:
        """Calculate content quality score."""
        score = 0.5  # Base score
        
        # Positive indicators
        positive_matches = self._count_matches(text, self.quality_indicators['positive_indicators'])
        score += min(positive_matches * 0.1, 0.3)
        
        # Negative indicators
        negative_matches = self._count_matches(text, self.quality_indicators['negative_indicators'])
        score -= min(negative_matches * 0.1, 0.3)
        
        # Video metadata quality
        if video_data.get('definition') == 'hd':
            score += 0.1
        
        if video_data.get('caption') == 'true':
            score += 0.1
        
        # Duration (prefer videos with reasonable length)
        duration = video_data.get('duration', '')
        if duration:
            duration_seconds = self._parse_duration(duration)
            if 30 <= duration_seconds <= 3600:  # 30 seconds to 1 hour
                score += 0.1
            elif duration_seconds > 3600:  # Very long videos
                score -= 0.05
        
        return max(0.0, min(score, 1.0))
    
    def _calculate_engagement_score(self, video_data: Dict[str, Any]) -> float:
        """Calculate engagement score based on metrics."""
        view_count = video_data.get('view_count', 0)
        like_count = video_data.get('like_count', 0)
        comment_count = video_data.get('comment_count', 0)
        
        # Calculate engagement rate
        if view_count > 0:
            like_rate = like_count / view_count
            comment_rate = comment_count / view_count
            engagement_rate = like_rate + comment_rate * 2  # Comments weighted higher
        else:
            engagement_rate = 0.0
        
        # Normalize engagement rate (typical good engagement is 2-10%)
        normalized_engagement = min(engagement_rate * 10, 1.0)  # Scale to 0-1
        
        # Minimum view threshold
        view_score = min(view_count / 1000, 1.0) if view_count > 0 else 0.0
        
        return (normalized_engagement * 0.7 + view_score * 0.3)
    
    def _calculate_spam_score(self, text: str) -> float:
        """Calculate spam likelihood score."""
        spam_indicators = 0
        
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                spam_indicators += 1
        
        # Check for excessive capitalization
        if len(text) > 50:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.3:
                spam_indicators += 1
        
        # Check for excessive punctuation
        punct_count = sum(1 for c in text if c in '!?.')
        if len(text) > 0 and punct_count / len(text) > 0.1:
            spam_indicators += 1
        
        return min(spam_indicators * 0.2, 1.0)
    
    def _count_matches(self, text: str, keywords: Set[str]) -> int:
        """Count keyword matches in text."""
        matches = 0
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        for keyword in keywords:
            if keyword in text.lower():
                matches += 1
        
        return matches
    
    def _find_matched_terms(self, text: str, keywords: Set[str]) -> List[str]:
        """Find which specific terms matched."""
        matched = []
        for keyword in keywords:
            if keyword in text.lower():
                matched.append(keyword)
        return matched
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Sri Lankan languages."""
        # Simple heuristics for language detection
        sinhala_chars = re.findall(r'[\u0D80-\u0DFF]', text)
        tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
        
        if sinhala_chars:
            return 'sinhala'
        elif tamil_chars:
            return 'tamil'
        elif any(word in text.lower() for word in ['sri lanka', 'colombo', 'kandy']):
            return 'english_sri_lankan'
        else:
            return 'english'
    
    def _categorize_content(self, text: str) -> str:
        """Categorize content type."""
        categories = {
            'news': ['news', 'breaking', 'update', 'report', 'announcement'],
            'entertainment': ['music', 'dance', 'comedy', 'movie', 'film', 'song'],
            'sports': ['cricket', 'football', 'rugby', 'sports', 'match', 'game'],
            'travel': ['travel', 'visit', 'tour', 'destination', 'hotel', 'beach'],
            'food': ['food', 'recipe', 'cooking', 'restaurant', 'curry', 'rice'],
            'education': ['education', 'tutorial', 'learn', 'how to', 'guide', 'university'],
            'politics': ['politics', 'election', 'government', 'minister', 'parliament'],
            'culture': ['culture', 'festival', 'tradition', 'temple', 'religious', 'ceremony']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text.lower() for keyword in keywords):
                return category
        
        return 'general'
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        try:
            # Simple parser for PT format (PT1H2M3S)
            if not duration.startswith('PT'):
                return 0
            
            duration = duration[2:]  # Remove PT
            seconds = 0
            
            # Hours
            if 'H' in duration:
                hours, duration = duration.split('H', 1)
                seconds += int(hours) * 3600
            
            # Minutes
            if 'M' in duration:
                minutes, duration = duration.split('M', 1)
                seconds += int(minutes) * 60
            
            # Seconds
            if 'S' in duration:
                secs = duration.split('S')[0]
                seconds += int(secs)
            
            return seconds
        except:
            return 0
    
    def get_content_insights(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get insights from a collection of analyzed videos."""
        if not videos:
            return {}
        
        sri_lankan_count = sum(1 for v in videos if v.get('is_sri_lankan_content', False))
        total_count = len(videos)
        
        avg_content_score = sum(v.get('content_score', 0) for v in videos) / total_count
        avg_quality_score = sum(v.get('quality_score', 0) for v in videos) / total_count
        
        # Category distribution
        categories = {}
        languages = {}
        
        for video in videos:
            metadata = video.get('analysis_metadata', {})
            category = metadata.get('content_category', 'unknown')
            language = metadata.get('detected_language', 'unknown')
            
            categories[category] = categories.get(category, 0) + 1
            languages[language] = languages.get(language, 0) + 1
        
        return {
            'total_videos': total_count,
            'sri_lankan_videos': sri_lankan_count,
            'sri_lankan_percentage': (sri_lankan_count / total_count) * 100 if total_count > 0 else 0,
            'average_content_score': round(avg_content_score, 3),
            'average_quality_score': round(avg_quality_score, 3),
            'category_distribution': categories,
            'language_distribution': languages,
            'analysis_timestamp': datetime.now().isoformat()
        }
