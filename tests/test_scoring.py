"""Tests for intelligent opportunity scoring engine - Phase 5."""

from datetime import datetime, timezone

import pytest

from mcp.core.scoring import OpportunityScorer


@pytest.fixture
def scorer():
    """Create a scorer instance for testing."""
    return OpportunityScorer()


@pytest.fixture
def sample_opportunity():
    """Create a sample opportunity for testing."""
    return {
        "id": "test_opp_1",
        "name": "Test Opportunity",
        "oems": ["Microsoft"],
        "partners": ["Partner A", "Partner B"],
        "tags": ["federal", "opportunity"],
        "amount": 500000,
        "stage": "Proposal",
        "close_date": "2025-06-30T00:00:00Z",
        "source": "Govly",
        "contract_vehicle": "SEWP V",
    }


class TestOEMAlignmentScoring:
    """Test OEM alignment scoring logic."""

    def test_high_priority_oem(self, scorer):
        """Test scoring for high-priority OEMs."""
        score = scorer.calculate_oem_alignment_score(["Microsoft"])
        assert score == 95

    def test_medium_priority_oem(self, scorer):
        """Test scoring for medium-priority OEMs."""
        score = scorer.calculate_oem_alignment_score(["AWS"])
        assert score == 80

    def test_unknown_oem(self, scorer):
        """Test scoring for unknown OEMs."""
        score = scorer.calculate_oem_alignment_score(["UnknownVendor"])
        assert score == 50  # Default score

    def test_multiple_oems_returns_highest(self, scorer):
        """Test that multiple OEMs return the highest score."""
        score = scorer.calculate_oem_alignment_score(["UnknownVendor", "Microsoft", "AWS"])
        assert score == 95  # Should return Microsoft's score

    def test_empty_oem_list(self, scorer):
        """Test scoring with empty OEM list."""
        score = scorer.calculate_oem_alignment_score([])
        assert score == 50  # Default score

    def test_case_insensitive_matching(self, scorer):
        """Test that OEM matching is case-insensitive."""
        score1 = scorer.calculate_oem_alignment_score(["microsoft"])
        score2 = scorer.calculate_oem_alignment_score(["MICROSOFT"])
        score3 = scorer.calculate_oem_alignment_score(["Microsoft"])
        assert score1 == score2 == score3


class TestContractVehicleScoring:
    """Test contract vehicle scoring logic."""

    def test_high_priority_vehicle(self, scorer):
        """Test scoring for high-priority contract vehicles."""
        score = scorer.calculate_contract_vehicle_score("SEWP V")
        assert score == 95

    def test_medium_priority_vehicle(self, scorer):
        """Test scoring for medium-priority contract vehicles."""
        score = scorer.calculate_contract_vehicle_score("GSA Schedule")
        assert score == 90

    def test_unknown_vehicle(self, scorer):
        """Test scoring for unknown contract vehicles."""
        score = scorer.calculate_contract_vehicle_score("Unknown Contract")
        assert score == 50  # Default

    def test_empty_vehicle(self, scorer):
        """Test scoring with empty vehicle."""
        score = scorer.calculate_contract_vehicle_score("")
        assert score == 50  # Default

    def test_partial_match(self, scorer):
        """Test partial matching of contract vehicle names."""
        score = scorer.calculate_contract_vehicle_score("NASA SOLUTIONS 2")
        assert score == 92  # Should match "NASA SOLUTIONS"


class TestPartnerFitScoring:
    """Test partner fit scoring logic."""

    def test_no_partners(self, scorer):
        """Test scoring with no partners."""
        score = scorer.calculate_partner_fit_score([], ["Microsoft"])
        assert score == 50.0  # Neutral score

    def test_single_partner(self, scorer):
        """Test scoring with single partner."""
        score = scorer.calculate_partner_fit_score(["Partner A"], ["Microsoft"])
        assert score == 60.0  # Base score for having partners

    def test_multiple_partners_bonus(self, scorer):
        """Test bonus for multiple partners."""
        score = scorer.calculate_partner_fit_score(["Partner A", "Partner B", "Partner C"], ["Microsoft"])
        assert score >= 60.0  # Should have bonus for multiple partners
        assert score <= 100.0

    def test_partner_oem_alignment(self, scorer):
        """Test bonus for partner-OEM alignment."""
        score = scorer.calculate_partner_fit_score(["Microsoft Partner"], ["Microsoft"])
        assert score >= 70.0  # Should have alignment bonus


class TestGovlyRelevanceScoring:
    """Test Govly relevance scoring logic."""

    def test_govly_source(self, scorer):
        """Test high score for Govly source."""
        score = scorer.calculate_govly_relevance_score([], "Govly")
        assert score == 85.0

    def test_non_govly_source(self, scorer):
        """Test base score for non-Govly source."""
        score = scorer.calculate_govly_relevance_score([], "Direct")
        assert score == 50.0

    def test_federal_tags_bonus(self, scorer):
        """Test bonus for federal/government tags."""
        score = scorer.calculate_govly_relevance_score(["federal", "government"], "Direct")
        assert score > 50.0  # Should have bonus

    def test_multiple_gov_tags(self, scorer):
        """Test multiple government-related tags."""
        score = scorer.calculate_govly_relevance_score(["federal", "agency", "dod"], "Direct")
        assert score >= 70.0  # Should accumulate bonuses


class TestAmountScoring:
    """Test deal amount scoring logic."""

    def test_zero_amount(self, scorer):
        """Test scoring for zero amount."""
        score = scorer.calculate_amount_score(0)
        assert score == 0.0

    def test_small_deal(self, scorer):
        """Test scoring for small deals."""
        score = scorer.calculate_amount_score(50000)
        assert score == 50.0  # $50K falls in < $100K bracket

    def test_medium_deal(self, scorer):
        """Test scoring for medium deals."""
        score = scorer.calculate_amount_score(500000)
        assert score == 80.0  # $500K falls in < $1M bracket

    def test_large_deal(self, scorer):
        """Test scoring for large deals."""
        score = scorer.calculate_amount_score(5000000)
        assert score == 95.0  # $5M falls in < $10M bracket

    def test_very_large_deal(self, scorer):
        """Test scoring for very large deals."""
        score = scorer.calculate_amount_score(50000000)
        assert score == 100.0


class TestStageProbability:
    """Test stage probability calculations."""

    def test_qualification_stage(self, scorer):
        """Test probability for Qualification stage."""
        prob = scorer.calculate_stage_probability("Qualification")
        assert prob == 0.15

    def test_proposal_stage(self, scorer):
        """Test probability for Proposal stage."""
        prob = scorer.calculate_stage_probability("Proposal")
        assert prob == 0.45

    def test_negotiation_stage(self, scorer):
        """Test probability for Negotiation stage."""
        prob = scorer.calculate_stage_probability("Negotiation")
        assert prob == 0.75

    def test_closed_won_stage(self, scorer):
        """Test probability for Closed Won stage."""
        prob = scorer.calculate_stage_probability("Closed Won")
        assert prob == 1.0

    def test_closed_lost_stage(self, scorer):
        """Test probability for Closed Lost stage."""
        prob = scorer.calculate_stage_probability("Closed Lost")
        assert prob == 0.0

    def test_unknown_stage(self, scorer):
        """Test default probability for unknown stage."""
        prob = scorer.calculate_stage_probability("Unknown Stage")
        assert prob == 0.20


class TestTimeDecayFactor:
    """Test time decay factor calculations."""

    def test_past_due_date(self, scorer):
        """Test decay for past due dates."""
        past_date = "2020-01-01T00:00:00Z"
        factor = scorer.calculate_time_decay_factor(past_date)
        assert factor == 0.5

    def test_urgent_close_30_days(self, scorer):
        """Test high urgency for deals closing within 30 days."""
        # Create a date 15 days from now
        from datetime import timedelta

        close_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        factor = scorer.calculate_time_decay_factor(close_date)
        assert factor == 1.0

    def test_medium_urgency_90_days(self, scorer):
        """Test medium urgency for deals closing within 90 days."""
        from datetime import timedelta

        close_date = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
        factor = scorer.calculate_time_decay_factor(close_date)
        assert factor == 0.95

    def test_far_future_date(self, scorer):
        """Test lower urgency for far future dates."""
        from datetime import timedelta

        close_date = (datetime.now(timezone.utc) + timedelta(days=400)).isoformat()
        factor = scorer.calculate_time_decay_factor(close_date)
        assert factor == 0.6

    def test_invalid_date(self, scorer):
        """Test default factor for invalid dates."""
        factor = scorer.calculate_time_decay_factor("invalid-date")
        assert factor == 0.75  # Default


class TestCompositeScore:
    """Test composite score calculation."""

    def test_composite_score_structure(self, scorer, sample_opportunity):
        """Test that composite score returns all required fields."""
        scores = scorer.calculate_composite_score(sample_opportunity)

        # Check all required fields are present
        assert "score_raw" in scores
        assert "score_scaled" in scores
        assert "win_prob" in scores
        assert "oem_alignment_score" in scores
        assert "partner_fit_score" in scores
        assert "contract_vehicle_score" in scores
        assert "govly_relevance_score" in scores
        assert "amount_score" in scores
        assert "stage_probability" in scores
        assert "time_decay_factor" in scores
        assert "weights_used" in scores
        assert "scoring_model" in scores
        assert "scored_at" in scores

    def test_score_ranges(self, scorer, sample_opportunity):
        """Test that all scores are within valid ranges."""
        scores = scorer.calculate_composite_score(sample_opportunity)

        # All scores should be 0-100
        assert 0 <= scores["score_raw"] <= 100
        assert 0 <= scores["score_scaled"] <= 100
        assert 0 <= scores["win_prob"] <= 100
        assert 0 <= scores["oem_alignment_score"] <= 100
        assert 0 <= scores["partner_fit_score"] <= 100
        assert 0 <= scores["contract_vehicle_score"] <= 100
        assert 0 <= scores["govly_relevance_score"] <= 100

    def test_high_quality_opportunity(self, scorer):
        """Test scoring for a high-quality opportunity."""
        from datetime import timedelta

        # Use a date 15 days in the future for high urgency
        future_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        high_quality_opp = {
            "oems": ["Microsoft"],
            "partners": ["Microsoft Partner", "Cisco Partner"],
            "tags": ["federal", "agency"],
            "amount": 5000000,
            "stage": "Negotiation",
            "close_date": future_date,
            "source": "Govly",
            "contract_vehicle": "SEWP V",
        }

        scores = scorer.calculate_composite_score(high_quality_opp)

        # Should have high scores across the board
        assert scores["win_prob"] >= 50.0  # Adjusted for realistic expectations
        assert scores["oem_alignment_score"] >= 90.0
        assert scores["contract_vehicle_score"] >= 90.0

    def test_low_quality_opportunity(self, scorer):
        """Test scoring for a low-quality opportunity."""
        low_quality_opp = {
            "oems": ["UnknownVendor"],
            "partners": [],
            "tags": [],
            "amount": 10000,
            "stage": "Qualification",
            "close_date": "2027-12-31T00:00:00Z",
            "source": "Cold Call",
            "contract_vehicle": "",
        }

        scores = scorer.calculate_composite_score(low_quality_opp)

        # Should have lower scores
        assert scores["win_prob"] < 50.0


class TestConfidenceInterval:
    """Test confidence interval calculations."""

    def test_confidence_interval_structure(self, scorer):
        """Test that confidence interval returns required fields."""
        ci = scorer.calculate_confidence_interval(75.0, 1000000, "Proposal")

        assert "lower_bound" in ci
        assert "upper_bound" in ci
        assert "interval_width" in ci
        assert "confidence_level" in ci

    def test_bounds_valid_range(self, scorer):
        """Test that confidence bounds are within 0-100."""
        ci = scorer.calculate_confidence_interval(75.0, 1000000, "Proposal")

        assert 0 <= ci["lower_bound"] <= 100
        assert 0 <= ci["upper_bound"] <= 100
        assert ci["lower_bound"] <= ci["upper_bound"]

    def test_qualification_wider_interval(self, scorer):
        """Test that Qualification stage has wider interval."""
        ci_qual = scorer.calculate_confidence_interval(75.0, 1000000, "Qualification")
        ci_nego = scorer.calculate_confidence_interval(75.0, 1000000, "Negotiation")

        assert ci_qual["interval_width"] > ci_nego["interval_width"]

    def test_large_deal_wider_interval(self, scorer):
        """Test that larger deals have wider intervals."""
        ci_small = scorer.calculate_confidence_interval(75.0, 100000, "Proposal")
        ci_large = scorer.calculate_confidence_interval(75.0, 10000000, "Proposal")

        assert ci_large["interval_width"] > ci_small["interval_width"]

    def test_edge_case_zero_prob(self, scorer):
        """Test confidence interval at 0% probability."""
        ci = scorer.calculate_confidence_interval(0.0, 1000000, "Proposal")

        assert ci["lower_bound"] == 0.0
        assert ci["upper_bound"] >= 0.0

    def test_edge_case_full_prob(self, scorer):
        """Test confidence interval at 100% probability."""
        ci = scorer.calculate_confidence_interval(100.0, 1000000, "Closed Won")

        assert ci["upper_bound"] == 100.0
        assert ci["lower_bound"] <= 100.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_fields(self, scorer):
        """Test scoring with missing fields."""
        minimal_opp = {"id": "test"}
        scores = scorer.calculate_composite_score(minimal_opp)

        # Should not raise an error and return valid scores
        assert "win_prob" in scores
        assert scores["win_prob"] >= 0

    def test_non_list_oems(self, scorer):
        """Test when OEMs is a string instead of list."""
        opp = {"oems": "Microsoft", "amount": 100000}
        scores = scorer.calculate_composite_score(opp)

        # Should handle gracefully
        assert "oem_alignment_score" in scores

    def test_negative_amount(self, scorer):
        """Test handling of negative amounts."""
        score = scorer.calculate_amount_score(-1000)
        assert score == 0.0

    def test_null_values(self, scorer):
        """Test handling of null/None values."""
        opp = {
            "oems": None,
            "partners": None,
            "tags": None,
            "amount": None,
        }
        scores = scorer.calculate_composite_score(opp)

        # Should not crash
        assert "win_prob" in scores
