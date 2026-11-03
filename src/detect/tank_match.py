"""
tank_match.py - Candidate tank detection and registry matching

Evaluates candidate tank detections on a reference Sentinel-2 Level-2A scene
against the ground-truth empirical tank registry.
Reports detection precision, recall, and intersection-over-union (IoU).
"""

import os
import csv
import math

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def match_candidate_tanks(detected_candidates, ground_truth_registry, tolerance_meters=15.0):
    """
    Matches detected circular features to ground truth tanks using Euclidean distance.
    """
    matched = []
    unmatched_candidates = []
    unmatched_ground_truth = list(ground_truth_registry)
    
    for cand in detected_candidates:
        cand_lat, cand_lon = cand["latitude"], cand["longitude"]
        best_match = None
        min_dist = float("inf")
        
        for gt in unmatched_ground_truth:
            # Approximate distance in meters at ~36 deg latitude:
            # 1 deg lat ~ 111,000 m; 1 deg lon ~ 90,000 m
            dy = (cand_lat - gt["latitude"]) * 111000.0
            dx = (cand_lon - gt["longitude"]) * 90000.0
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < min_dist and dist <= tolerance_meters:
                min_dist = dist
                best_match = gt
                
        if best_match:
            matched.append({"candidate": cand, "ground_truth": best_match, "offset_m": min_dist})
            unmatched_ground_truth.remove(best_match)
        else:
            unmatched_candidates.append(cand)
            
    precision = len(matched) / max(1, len(detected_candidates))
    recall = len(matched) / max(1, len(ground_truth_registry))
    return {
        "matched_count": len(matched),
        "unmatched_candidates": len(unmatched_candidates),
        "missed_ground_truth": len(unmatched_ground_truth),
        "precision": precision,
        "recall": recall
    }
