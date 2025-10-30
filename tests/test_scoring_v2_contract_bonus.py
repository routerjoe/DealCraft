"""Extended tests for scoring v2 context bonuses - Phase 9, updated for v2.1 audited values."""

import pytest

from mcp.core.scoring import OpportunityScorer


@pytest.fixture
def scorer():
    """Create scorer instance."""
    return OpportunityScorer()


class TestCVRecommendationBonus:
    """Test CV recommendation bonus (v2.1: single=5%, multiple=7%)."""

    def test_cv_bonus_applied(self, scorer):
        """Test that CV recommendations add bonus (v2.1: multiple CVs = 7%)."""
        opp_with_cv = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "contracts_recommended": ["SEWP V", "GSA Schedule"],  # 2 CVs = multiple
        }

        opp_without_cv = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "contracts_recommended": [],
        }

        scores_with = scorer.calculate_composite_score(opp_with_cv)
        scores_without = scorer.calculate_composite_score(opp_without_cv)

        # v2.1: Multiple CVs should be 7 points higher
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 6.9

    def test_cv_bonus_in_results(self, scorer):
        """Test CV bonus is recorded in results (v2.1: single CV = 5%)."""
        opp = {
            "oems": ["Cisco"],
            "amount": 500000,
            "contracts_recommended": ["DHS FirstSource II"],  # 1 CV = single
        }

        scores = scorer.calculate_composite_score(opp)

        assert "cv_recommendation_bonus" in scores
        assert scores["cv_recommendation_bonus"] == 5.0  # Single CV


class TestRegionBonus:
    """Test region bonus (v2.1: East=2.5%, West=2.0%, Central=1.5%)."""

    def test_region_bonus_applied(self, scorer):
        """Test that strategic regions add bonus (v2.1: East = 2.5%)."""
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

        # v2.1: East should be 2.5 points higher
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 2.4

    def test_strategic_regions_get_bonus(self, scorer):
        """Test East, West, Central regions get differentiated bonuses (v2.1 audited)."""
        expected_bonuses = {"East": 2.5, "West": 2.0, "Central": 1.5}

        for region, expected_bonus in expected_bonuses.items():
            opp = {
                "oems": ["Microsoft"],
                "amount": 1000000,
                "region": region,
            }

            scores = scorer.calculate_composite_score(opp)
            assert scores["region_bonus"] == expected_bonus

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
    """Test customer org bonus (v2.1: DOD=4%, Civilian=3%, Default=2%)."""

    def test_org_bonus_applied(self, scorer):
        """Test that known orgs add bonus (v2.1: DOD = 4%)."""
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

        # v2.1: DOD should be 4 points higher
        assert scores_with["score_scaled"] >= scores_without["score_scaled"] + 3.9

    def test_org_bonus_in_results(self, scorer):
        """Test org bonus is recorded in results (v2.1: Default tier = 2%)."""
        opp = {
            "oems": ["Cisco"],
            "amount": 500000,
            "customer_org": "Agency X",  # Not DOD/Civilian, so Default tier
        }

        scores = scorer.calculate_composite_score(opp)

        assert "customer_org_bonus" in scores
        assert scores["customer_org_bonus"] == 2.0  # v2.1 Default tier


class TestCombinedBonuses:
    """Test that bonuses combine correctly (v2.1)."""

    def test_all_bonuses_stack(self, scorer):
        """Test all bonuses stack correctly (v2.1: 5+2.5+4 = 11.5%)."""
        opp_all = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
            "region": "East",  # v2.1: 2.5%
            "customer_org": "DOD",  # v2.1: 4.0%
            "contracts_recommended": ["SEWP V"],  # Single CV: 5.0%
        }

        opp_none = {
            "oems": ["Microsoft"],
            "amount": 1000000,
            "stage": "Proposal",
        }

        scores_all = scorer.calculate_composite_score(opp_all)
        scores_none = scorer.calculate_composite_score(opp_none)

        # v2.1: Should have +11.5% total bonus (5.0 + 2.5 + 4.0)
        expected_diff = 11.5
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

    def test_scoring_model_v2_1(self, scorer):
        """Test scoring model version is v2.1_audited."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        scores = scorer.calculate_composite_score(opp)

        assert "scoring_model" in scores
        assert scores["scoring_model"] == "multi_factor_v2.1_audited"


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
