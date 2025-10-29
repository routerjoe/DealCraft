"""Extended tests for scoring v2 context bonuses - Phase 9."""

import pytest

from mcp.core.scoring import OpportunityScorer


@pytest.fixture
def scorer():
    """Create scorer instance."""
    return OpportunityScorer()


class TestCVRecommendationBonus:
    """Test CV recommendation bonus (+5%)."""

    def test_cv_bonus_applied(self, scorer):
        """Test that CV recommendations add 5% bonus."""
        opp_with_cv = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "contracts_recommended": ["SEWP V", "GSA Schedule"],
        }

        opp_without_cv = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "contracts_recommended": [],
        }

        scores_with = scorer.calculate_composite_score(opp_with_cv)
        scores_without = scorer.calculate_composite_score(opp_without_cv)

        # score_scaled should be 5 points higher with CV
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 4.9

    def test_cv_bonus_in_results(self, scorer):
        """Test CV bonus is recorded in results."""
        opp = {
            "oems": ["Cisco"],
            "amount": 500000,
            "contracts_recommended": ["DHS FirstSource II"],
        }

        scores = scorer.calculate_composite_score(opp)

        assert "cv_recommendation_bonus" in scores
        assert scores["cv_recommendation_bonus"] == 5.0


class TestRegionBonus:
    """Test region bonus (+2%)."""

    def test_region_bonus_applied(self, scorer):
        """Test that strategic regions add 2% bonus."""
        opp_with_region = {
            "oems": ["Dell"],
            "amount": 500000,
            "region": "East",
        }

        opp_without_region = {
            "oems": ["Dell"],
            "amount": 500000,
            "region": "",
        }

        scores_with = scorer.calculate_composite_score(opp_with_region)
        scores_without = scorer.calculate_composite_score(opp_without_region)

        # score_scaled should be 2 points higher
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 1.9

    def test_strategic_regions_get_bonus(self, scorer):
        """Test East, West, Central regions get bonus."""
        for region in ["East", "West", "Central"]:
            opp = {
                "oems": ["Microsoft"],
                "amount": 1000000,
                "region": region,
            }

            scores = scorer.calculate_composite_score(opp)
            assert scores["region_bonus"] == 2.0

    def test_non_strategic_region_no_bonus(self, scorer):
        """Test non-strategic regions get no bonus."""
        opp = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "region": "Unknown Region",
        }

        scores = scorer.calculate_composite_score(opp)
        assert scores["region_bonus"] == 0.0


class TestCustomerOrgBonus:
    """Test customer org bonus (+3%)."""

    def test_org_bonus_applied(self, scorer):
        """Test that known orgs add 3% bonus."""
        opp_with_org = {
            "oems": ["HPE"],
            "amount": 750000,
            "customer_org": "Department of Defense",
        }

        opp_without_org = {
            "oems": ["HPE"],
            "amount": 750000,
            "customer_org": "",
        }

        scores_with = scorer.calculate_composite_score(opp_with_org)
        scores_without = scorer.calculate_composite_score(opp_without_org)

        # score_scaled should be 3 points higher
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 2.9

    def test_org_bonus_in_results(self, scorer):
        """Test org bonus is recorded in results."""
        opp = {
            "oems": ["Cisco"],
            "amount": 500000,
            "customer_org": "Agency X",
        }

        scores = scorer.calculate_composite_score(opp)

        assert "customer_org_bonus" in scores
        assert scores["customer_org_bonus"] == 3.0


class TestCombinedBonuses:
    """Test that bonuses combine correctly."""

    def test_all_bonuses_stack(self, scorer):
        """Test all bonuses (CV+Region+Org) stack correctly."""
        opp_all = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "region": "East",
            "customer_org": "DOD",
            "contracts_recommended": ["SEWP V"],
        }

        opp_none = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
        }

        scores_all = scorer.calculate_composite_score(opp_all)
        scores_none = scorer.calculate_composite_score(opp_none)

        # Should have +10% total bonus (5+2+3)
        expected_diff = 10.0
        actual_diff = scores_all["score_scaled"] - scores_none["score_scaled"]

        assert abs(actual_diff - expected_diff) < 0.5  # Allow small rounding

    def test_bonus_fields_present(self, scorer):
        """Test all bonus fields are present in results."""
        opp = {
            "oems": ["Dell"],
            "amount": 500000,
            "region": "West",
            "customer_org": "Agency",
            "contracts_recommended": ["NASA SOLUTIONS"],
        }

        scores = scorer.calculate_composite_score(opp)

        assert "region_bonus" in scores
        assert "customer_org_bonus" in scores
        assert "cv_recommendation_bonus" in scores

    def test_scoring_model_v2(self, scorer):
        """Test scoring model version is v2_enhanced."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        scores = scorer.calculate_composite_score(opp)

        assert "scoring_model" in scores
        assert scores["scoring_model"] == "multi_factor_v2_enhanced"


class TestReasoningOutput:
    """Test detailed reasoning output."""

    def test_reasoning_includes_bonuses(self, scorer):
        """Test reasoning output includes bonus explanations."""
        opp = {
            "oems": ["Cisco"],
            "amount": 1000000,
            "region": "East",
            "customer_org": "DOD",
            "contracts_recommended": ["DHS FirstSource II"],
        }

        scores = scorer.calculate_composite_score(opp, include_reasoning=True)

        assert "score_reasoning" in scores
        reasoning = scores["score_reasoning"]

        assert isinstance(reasoning, list)
        assert len(reasoning) > 0

        # Should mention bonuses
        reasoning_text = " ".join(reasoning).lower()
        assert "bonus" in reasoning_text or "region" in reasoning_text

    def test_reasoning_omitted_when_not_requested(self, scorer):
        """Test reasoning is not included when not requested."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        scores = scorer.calculate_composite_score(opp, include_reasoning=False)

        assert "score_reasoning" not in scores
