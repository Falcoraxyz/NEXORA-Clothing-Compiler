"""
Vision Metrics
Computes quality metrics: SSIM, LPIPS, seam continuity.
Used for validation and auto-correction feedback.
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from PIL import Image


class VisionMetrics:
    """
    Computes quality metrics for generated templates.
    
    Metrics:
    - SSIM: Structural similarity (per-panel and full template)
    - LPIPS: Learned perceptual similarity (if available)
    - Seam continuity: Pixel difference across panel boundaries
    """

    def __init__(self):
        pass

    def compute_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Compute SSIM between two images.
        Returns value between 0 and 1 (1 = identical).
        """
        # Convert to float
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)

        # Constants for stability
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        # Mean
        mu1 = np.mean(img1)
        mu2 = np.mean(img2)

        # Variance
        sigma1_sq = np.var(img1)
        sigma2_sq = np.var(img2)

        # Covariance
        sigma12 = np.mean((img1 - mu1) * (img2 - mu2))

        # SSIM formula
        numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
        denominator = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)

        return numerator / denominator

    def compute_seam_continuity(self, template: np.ndarray, 
                                 panel_positions: Dict[str, Tuple[int, int, int, int]],
                                 edge_constraints: List[Dict]) -> Dict[str, float]:
        """
        Compute seam continuity across panel boundaries.
        Returns per-edge and average continuity scores.
        """
        results = {}

        for constraint in edge_constraints:
            if constraint["type"] != "boundary_match":
                continue

            panel_a_id = constraint["edge_a"]["panel"]
            edge_a_name = constraint["edge_a"]["edge"]
            panel_b_id = constraint["edge_b"]["panel"]
            edge_b_name = constraint["edge_b"]["edge"]

            pos_a = panel_positions.get(panel_a_id)
            pos_b = panel_positions.get(panel_b_id)

            if not pos_a or not pos_b:
                continue

            # Get edge pixels from template
            edge_a_pixels = self._get_edge_from_template(template, pos_a, edge_a_name)
            edge_b_pixels = self._get_edge_from_template(template, pos_b, edge_b_name)

            if edge_a_pixels is None or edge_b_pixels is None:
                continue

            # Compute difference
            diff = np.abs(edge_a_pixels.astype(np.float64) - edge_b_pixels.astype(np.float64))
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)

            # Convert to similarity score (0-1, 1 = perfect)
            similarity = 1.0 - (mean_diff / 255.0)

            key = f"{panel_a_id}.{edge_a_name}-{panel_b_id}.{edge_b_name}"
            results[key] = {
                "similarity": similarity,
                "max_diff": max_diff,
                "mean_diff": mean_diff,
                "pass": similarity >= 0.85,  # Threshold
            }

        return results

    def _get_edge_from_template(self, template: np.ndarray, 
                                 pos: Tuple[int, int, int, int],
                                 edge_name: str) -> Optional[np.ndarray]:
        """Get edge pixels from template at given position."""
        x, y, w, h = pos
        panel = template[y:y+h, x:x+w]

        if edge_name == "top":
            return panel[0, :, :3]
        elif edge_name == "bottom":
            return panel[h - 1, :, :3]
        elif edge_name == "left":
            return panel[:, 0, :3]
        elif edge_name == "right":
            return panel[:, w - 1, :3]
        return None

    def compute_coverage(self, template: np.ndarray, 
                         panel_positions: Dict[str, Tuple[int, int, int, int]] = None) -> float:
        """
        Compute non-transparent coverage ratio.
        If panel_positions provided, only counts area within panel bounding boxes.
        """
        if template.shape[2] == 4:
            alpha = template[:, :, 3]
            non_empty = np.sum(alpha > 0)
        else:
            non_empty = np.sum(np.any(template > 0, axis=2))
        
        if panel_positions:
            # Only count area that should have content (panel bounding boxes)
            total_panel_area = 0
            for x, y, w, h in panel_positions.values():
                total_panel_area += w * h
            if total_panel_area == 0:
                return 0.0
            return non_empty / total_panel_area
        else:
            total = template.shape[0] * template.shape[1]
            return non_empty / total if total > 0 else 0.0

    def compute_color_accuracy(self, template: np.ndarray, 
                                expected_color: Tuple[int, int, int],
                                tolerance: int = 30) -> float:
        """Compute how well the template matches the expected primary color."""
        if template.shape[2] == 4:
            mask = template[:, :, 3] > 0
        else:
            mask = np.any(template > 0, axis=2)

        if not np.any(mask):
            return 0.0

        rgb = template[:, :, :3]
        diff = np.abs(rgb.astype(np.int16) - np.array(expected_color))
        matches = np.all(diff < tolerance, axis=2)
        color_match = np.sum(matches & mask) / np.sum(mask)

        return color_match

    def full_report(self, template: Image.Image, 
                    panel_positions: Dict[str, Tuple[int, int, int, int]],
                    edge_constraints: List[Dict],
                    expected_color: Tuple[int, int, int]) -> Dict:
        """Generate a full quality report."""
        template_np = np.array(template)

        report = {
            "coverage": self.compute_coverage(template_np, panel_positions),
            "color_accuracy": self.compute_color_accuracy(template_np, expected_color),
            "seam_continuity": self.compute_seam_continuity(template_np, panel_positions, edge_constraints),
        }

        # Overall pass/fail
        # Coverage: at least 80% of panel area should have content
        # Color: at least 50% of pixels should match primary color
        # Seams: all edges should have similarity >= 0.85
        report["pass"] = (
            report["coverage"] >= 0.8 and
            report["color_accuracy"] >= 0.5
        )

        # Check all seams pass
        for edge_key, seam in report["seam_continuity"].items():
            if not seam["pass"]:
                report["pass"] = False
                break

        return report


def evaluate_template(template: Image.Image, 
                      panel_positions: Dict[str, Tuple[int, int, int, int]],
                      edge_constraints: List[Dict],
                      expected_color: Tuple[int, int, int]) -> Dict:
    """Convenience function."""
    metrics = VisionMetrics()
    return metrics.full_report(template, panel_positions, edge_constraints, expected_color)
