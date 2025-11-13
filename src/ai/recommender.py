"""
Recommendation engine that learns from user feedback
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

from ..core.config import RECOMMENDATION_CONFIG, FEEDBACK_DIR

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Learns from user feedback to improve recommendations"""
    
    def __init__(self):
        self.feedback_file = FEEDBACK_DIR / 'user_feedback.json'
        self.user_choices = []
        self.extension_stats = defaultdict(lambda: {'kept': 0, 'deleted': 0})
        self.category_stats = defaultdict(lambda: {'kept': 0, 'deleted': 0})
        self.load_feedback()
        self._update_statistics()
    
    def load_feedback(self):
        """Load user feedback from file"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    self.user_choices = json.load(f)
                logger.info(f"Loaded {len(self.user_choices)} feedback entries")
            except Exception as e:
                logger.error(f"Error loading feedback: {e}")
                self.user_choices = []
        else:
            logger.debug("No existing feedback file")
            self.user_choices = []
    
    def save_feedback(self):
        """Save user feedback to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.user_choices, f, indent=2)
            logger.debug(f"Saved {len(self.user_choices)} feedback entries")
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
    
    def record_choice(self, file_metadata: Dict, user_kept: bool):
        """
        Record a user's decision
        
        Args:
            file_metadata: File metadata dictionary
            user_kept: True if user kept the file, False if deleted
        """
        choice = {
            'extension': file_metadata.get('extension', 'unknown'),
            'category': file_metadata.get('category', 'other'),
            'size_mb': file_metadata.get('size_mb', 0),
            'accessed_days_ago': file_metadata.get('accessed_days_ago', 0),
            'is_disposable_ext': file_metadata.get('is_disposable_ext', False),
            'user_kept': user_kept,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_choices.append(choice)
        
        # Update statistics
        extension = choice['extension']
        category = choice['category']
        
        if user_kept:
            self.extension_stats[extension]['kept'] += 1
            self.category_stats[category]['kept'] += 1
        else:
            self.extension_stats[extension]['deleted'] += 1
            self.category_stats[category]['deleted'] += 1
        
        # Keep only recent history
        max_history = RECOMMENDATION_CONFIG['history_limit']
        if len(self.user_choices) > max_history * 2:
            self.user_choices = self.user_choices[-max_history:]
            self._update_statistics()
        
        self.save_feedback()
    
    def record_batch_choices(self, files_metadata: List[Dict], kept_indices: List[int]):
        """
        Record multiple choices at once
        
        Args:
            files_metadata: List of file metadata dictionaries
            kept_indices: Indices of files that were kept
        """
        kept_set = set(kept_indices)
        
        for i, file_meta in enumerate(files_metadata):
            user_kept = i in kept_set
            self.record_choice(file_meta, user_kept)
    
    def _update_statistics(self):
        """Update statistics from feedback history"""
        self.extension_stats.clear()
        self.category_stats.clear()
        
        for choice in self.user_choices:
            extension = choice['extension']
            category = choice['category']
            
            if choice['user_kept']:
                self.extension_stats[extension]['kept'] += 1
                self.category_stats[category]['kept'] += 1
            else:
                self.extension_stats[extension]['deleted'] += 1
                self.category_stats[category]['deleted'] += 1
    
    def get_extension_preference(self, extension: str) -> float:
        """
        Get user's preference for an extension
        
        Args:
            extension: File extension
            
        Returns:
            Score from 0 (always delete) to 1 (always keep)
        """
        stats = self.extension_stats.get(extension)
        
        if not stats or (stats['kept'] + stats['deleted']) == 0:
            return 0.5  # Neutral if no data
        
        total = stats['kept'] + stats['deleted']
        kept_ratio = stats['kept'] / total
        
        return kept_ratio
    
    def get_category_preference(self, category: str) -> float:
        """
        Get user's preference for a file category
        
        Args:
            category: File category
            
        Returns:
            Score from 0 (always delete) to 1 (always keep)
        """
        stats = self.category_stats.get(category)
        
        if not stats or (stats['kept'] + stats['deleted']) == 0:
            return 0.5  # Neutral if no data
        
        total = stats['kept'] + stats['deleted']
        kept_ratio = stats['kept'] / total
        
        return kept_ratio
    
    def adjust_score(self, file_metadata: Dict, base_score: float) -> float:
        """
        Adjust a base recommendation score based on user preferences
        
        Args:
            file_metadata: File metadata dictionary
            base_score: Base score from ML model (0=delete, 1=keep)
            
        Returns:
            Adjusted score (0=delete, 1=keep)
        """
        if len(self.user_choices) < RECOMMENDATION_CONFIG['min_similar_count']:
            return base_score  # Not enough data yet
        
        # Get preferences
        extension = file_metadata.get('extension', 'unknown')
        category = file_metadata.get('category', 'other')
        
        ext_pref = self.get_extension_preference(extension)
        cat_pref = self.get_category_preference(category)
        
        # Calculate adjustment
        # If user usually keeps this type: push score toward 1 (keep)
        # If user usually deletes this type: push score toward 0 (delete)
        
        adjustment_factor = RECOMMENDATION_CONFIG['adjustment_factor']
        
        # Weight extension more heavily than category
        ext_adjustment = (ext_pref - 0.5) * adjustment_factor
        cat_adjustment = (cat_pref - 0.5) * (adjustment_factor * 0.5)
        
        adjusted_score = base_score + ext_adjustment + cat_adjustment
        
        # Clamp to [0, 1]
        adjusted_score = max(0.0, min(1.0, adjusted_score))
        
        logger.debug(f"Adjusted score for {extension}: {base_score:.2f} -> {adjusted_score:.2f}")
        
        return adjusted_score
    
    def get_recommendations(
        self,
        files_metadata: List[Dict],
        ml_predictions: List[int],
        ml_probabilities: List[List[float]]
    ) -> List[Dict]:
        """
        Generate final recommendations combining ML and user preferences
        
        Args:
            files_metadata: List of file metadata
            ml_predictions: ML model predictions (1=keep, 0=delete)
            ml_probabilities: ML model probabilities [[p_delete, p_keep], ...]
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        for file_meta, prediction, probs in zip(files_metadata, ml_predictions, ml_probabilities):
            # Base score (probability of keeping)
            base_keep_score = float(probs[1])
            
            # Adjust based on user preferences
            adjusted_keep_score = self.adjust_score(file_meta, base_keep_score)
            
            # Final recommendation
            recommend_delete = adjusted_keep_score < 0.5
            confidence = adjusted_keep_score if not recommend_delete else (1 - adjusted_keep_score)
            
            recommendation = {
                'recommend_delete': recommend_delete,
                'confidence': confidence,
                'ml_prediction': int(prediction),
                'ml_confidence': float(probs[prediction]),
                'adjusted_score': adjusted_keep_score,
                'user_influenced': abs(adjusted_keep_score - base_keep_score) > 0.05
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """Get recommendation engine statistics"""
        total_feedback = len(self.user_choices)
        
        if total_feedback > 0:
            kept_count = sum(1 for c in self.user_choices if c['user_kept'])
            deleted_count = total_feedback - kept_count
        else:
            kept_count = deleted_count = 0
        
        return {
            'total_feedback': total_feedback,
            'files_kept': kept_count,
            'files_deleted': deleted_count,
            'extensions_learned': len(self.extension_stats),
            'categories_learned': len(self.category_stats),
        }
    
    def get_top_preferences(self, n: int = 10) -> Dict:
        """
        Get top extension preferences
        
        Args:
            n: Number of top extensions to return
            
        Returns:
            Dictionary with top kept and deleted extensions
        """
        # Calculate keep ratios
        ext_ratios = {}
        for ext, stats in self.extension_stats.items():
            total = stats['kept'] + stats['deleted']
            if total >= RECOMMENDATION_CONFIG['min_similar_count']:
                ext_ratios[ext] = {
                    'keep_ratio': stats['kept'] / total,
                    'total': total
                }
        
        # Sort by keep ratio
        sorted_exts = sorted(ext_ratios.items(), key=lambda x: x[1]['keep_ratio'], reverse=True)
        
        return {
            'most_kept': sorted_exts[:n],
            'most_deleted': sorted_exts[-n:][::-1] if len(sorted_exts) > n else []
        }
    
    def reset_feedback(self):
        """Clear all feedback (use with caution!)"""
        self.user_choices = []
        self.extension_stats.clear()
        self.category_stats.clear()
        self.save_feedback()
        logger.info("All feedback has been reset")