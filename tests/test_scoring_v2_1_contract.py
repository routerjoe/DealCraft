"""
Contract tests for Scoring Model v2.1 constants and structure.

Sprint 14: ML Refinement
Validates that v2.1 constants are defined and model version is updated.
"""

import pytest

from mcp.core.scoring import OpportunityScorer


class TestScoringV21Constants:
    """Test that v2.1 constants are defined."""

    def test_model_version_identifier_exists(self):
        """Test scoring model version can be identified."""
        scorer = OpportunityScorer()

        # Test scoring with any opportunity
        opp = {"oems": ["Cisco"], "amount": 100000}
        scores = scorer.calculate_composite_score(opp)

        # Should have scoring_model field
        assert "scoring_model" in scores
        # Current version is v2_enhanced, v2.1 will be multi_factor_v2.1_audited
        assert "v2" in scores["scoring_model"]

    @pytest.mark.skip(reason="TODO: Define REGION_BONUS_AUDITED constants in Sprint 14 dev")
    def test_region_bonus_audited_constants(self):
        """Test that audited region bonus constants are defined."""
        # TODO: Implement in scoring.py
        from mcp.core.scoring import REGION_BONUS_AUDITED

        assert REGION_BONUS_AUDITED["East"] == 2.5
        assert REGION_BONUS_AUDITED["West"] == 2.0
        assert REGION_BONUS_AUDITED["Central"] == 1.5

    @pytest.mark.skip(reason="TODO: Define CUSTOMER_ORG_BONUS_AUDITED in Sprint 14 dev")
    def test_customer_org_bonus_audited_constants(self):
        """Test that audited customer org bonus constants are defined."""
        # TODO: Implement in scoring.py
        from mcp.core.scoring import CUSTOMER_ORG_BONUS_AUDITED

        assert CUSTOMER_ORG_BONUS_AUDITED["DOD"] == 4.0
        assert CUSTOMER_ORG_BONUS_AUDITED["Civilian"] == 3.0
        assert CUSTOMER_ORG_BONUS_AUDITED["Default"] == 2.0

    @pytest.mark.skip(reason="TODO: Define CV_RECOMMENDATION_BONUS_AUDITED in Sprint 14 dev")
    def test_cv_bonus_audited_constants(self):
        """Test that audited CV bonus constants are defined."""
        # TODO: Implement in scoring.py
        from mcp.core.scoring import CV_RECOMMENDATION_BONUS_AUDITED

        assert CV_RECOMMENDATION_BONUS_AUDITED["single"] == 5.0
        assert CV_RECOMMENDATION_BONUS_AUDITED["multiple"] == 7.0


class TestScoringV21Guardrails:
    """Test that v2.1 guardrails are in place."""

    @pytest.mark.skip(reason="TODO: Implement guardrail constants in Sprint 14 dev")
    def test_score_bounds_constants(self):
        """Test that score bound constants are defined."""
        # TODO: Implement in scoring.py
        from mcp.core.scoring import MAX_SCORE, MAX_WIN_PROB, MIN_SCORE, MIN_WIN_PROB

        assert MIN_SCORE == 0.0
        assert MAX_SCORE == 100.0
        assert MIN_WIN_PROB == 0.0
        assert MAX_WIN_PROB == 1.0

    @pytest.mark.skip(reason="TODO: Implement MAX_TOTAL_BONUS in Sprint 14 dev")
    def test_max_total_bonus_constant(self):
        """Test that maximum total bonus is defined."""
        # TODO: Implement in scoring.py
        from mcp.core.scoring import MAX_TOTAL_BONUS

        assert MAX_TOTAL_BONUS == 15.0

    def test_score_never_exceeds_100(self):
        """Test that composite scores are capped at 100."""
        scorer = OpportunityScorer()

        # Create opportunity with max scores
        opp = {
            "oems": ["Microsoft"],  # 95 points
            "partners": ["Microsoft Partner 1", "Microsoft Partner 2"],
            "contract_vehicle": "SEWP V",  # 95 points
            "amount": 100000000,  # 100 points
            "stage": "Negotiation",
            "close_date": "2025-11-01",
            "region": "East",
            "customer_org": "DOD",
            "contracts_recommended": ["SEWP V", "GSA Schedule"],
        }

        scores = scorer.calculate_composite_score(opp)

        # Should never exceed 100
        assert scores["score_scaled"] <= 100.0
        assert scores["score_raw"] <= 100.0

    def test_win_probability_never_exceeds_1(self):
        """Test that win probability is capped at 1.0 (100%)."""
        scorer = OpportunityScorer()

        opp = {
            "oems": ["Microsoft"],
            "amount": 100000000,
            "stage": "Closed Won",  # 1.0 multiplier
            "close_date": "2025-11-01",
        }

        scores = scorer.calculate_composite_score(opp)

        # Win prob should be between 0-100 (percentage scale)
        assert 0 <= scores["win_prob"] <= 100


class TestScoringV21Features:
    """Test v2.1 feature tracking."""

    @pytest.mark.skip(reason="TODO: Implement feature store in Sprint 14 dev")
    def test_feature_store_schema_defined(self):
        """Test that feature store schema is defined."""
        # TODO: Implement feature store
        from mcp.core.scoring import FEATURE_SCHEMA

        required_fields = [
            "opportunity_id",
            "oem_alignment",
            "partner_fit",
            "vehicle_score",
            "region_bonus",
            "org_bonus",
            "cv_bonus",
        ]

        for field in required_fields:
            assert field in FEATURE_SCHEMA

    @pytest.mark.skip(reason="TODO: Implement feature store persistence in Sprint 14 dev")
    def test_feature_store_persistence(self):
        """Test that features are persisted to feature store."""
        # TODO: Implement persistence
        from mcp.core.scoring import save_features

        opp_id = "test_123"
        features = {"oem_alignment": 92.0}

        save_features(opp_id, features)

        # Verify saved
        from pathlib import Path

        feature_store = Path("data/feature_store.jsonl")
        assert feature_store.exists()


class TestScoringV21Compatibility:
    """Test v2.1 maintains compatibility with v2.0."""

    def test_v2_0_scores_still_valid(self):
        """Test that v2.0 opportunities can still be scored."""
        scorer = OpportunityScorer()

        # v2.0 style opportunity
        opp = {
            "oems": ["Cisco"],
            "amount": 500000,
            "stage": "Discovery",
            "region": "East",
            "customer_org": "DOD",
            "contracts_recommended": ["GSA Schedule"],
        }

        scores = scorer.calculate_composite_score(opp)

        # Should still have all v2.0 fields
        assert "region_bonus" in scores
        assert "customer_org_bonus" in scores
        assert "cv_recommendation_bonus" in scores

    def test_bonus_fields_always_present(self):
        """Test that bonus fields are always in results."""
        scorer = OpportunityScorer()

        # Minimal opportunity
        opp = {"oems": ["Dell"], "amount": 100000}

        scores = scorer.calculate_composite_score(opp)

        # Bonus fields should exist (may be 0)
        assert "region_bonus" in scores
        assert "customer_org_bonus" in scores
        assert "cv_recommendation_bonus" in scores


class TestScoringV21Reasoning:
    """Test v2.1 reasoning output."""

    def test_reasoning_includes_all_bonuses(self):
        """Test that reasoning explains all bonuses."""
        scorer = OpportunityScorer()

        opp = {
            "oems": ["Cisco"],
            "amount": 1000000,
            "region": "East",
            "customer_org": "DOD",
            "contracts_recommended": ["SEWP V", "DHS FirstSource II"],
        }

        scores = scorer.calculate_composite_score(opp, include_reasoning=True)

        assert "score_reasoning" in scores
        reasoning = scores["score_reasoning"]
        assert isinstance(reasoning, list)

        # Should mention bonuses
        reasoning_text = " ".join(reasoning).lower()
        # At least some bonus should be mentioned
        assert any(word in reasoning_text for word in ["bonus", "region", "customer", "cv"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
