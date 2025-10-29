"""Extended regression tests for CV recommender - Phase 8."""

import pytest

from mcp.core.cv_recommender import CVRecommender


@pytest.fixture
def recommender():
    """Create CV recommender instance."""
    return CVRecommender()


class TestCVRankingEnforcement:
    """Test that CV rankings are enforced correctly."""

    def test_sewp_v_ranks_highest(self, recommender):
        """Test SEWP V ranks higher than NASA SOLUTIONS."""
        opp = {"oems": ["Dell"], "amount": 1000000}

        recommendations = recommender.recommend_vehicles(opp, top_n=5)

        sewp_rank = next((i for i, r in enumerate(recommendations) if r["contract_vehicle"] == "SEWP V"), None)
        nasa_rank = next((i for i, r in enumerate(recommendations) if r["contract_vehicle"] == "NASA SOLUTIONS"), None)

        assert sewp_rank is not None
        assert nasa_rank is not None
        assert sewp_rank < nasa_rank  # SEWP V should rank higher

    def test_nasa_ranks_higher_than_gsa(self, recommender):
        """Test NASA SOLUTIONS ranks higher than GSA Schedule."""
        opp = {"oems": ["HPE"], "amount": 500000}

        recommendations = recommender.recommend_vehicles(opp, top_n=5)

        nasa_rank = next((i for i, r in enumerate(recommendations) if r["contract_vehicle"] == "NASA SOLUTIONS"), None)
        gsa_rank = next((i for i, r in enumerate(recommendations) if r["contract_vehicle"] == "GSA Schedule"), None)

        assert nasa_rank is not None
        assert gsa_rank is not None
        assert nasa_rank < gsa_rank

    def test_priority_scores_descending(self, recommender):
        """Test that recommendations are in descending score order."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        recommendations = recommender.recommend_vehicles(opp, top_n=7)

        for i in range(len(recommendations) - 1):
            assert recommendations[i]["cv_score"] >= recommendations[i + 1]["cv_score"]


class TestBPAScoring:
    """Test BPA availability scoring."""

    def test_bpa_increases_score(self, recommender):
        """Test that active BPAs increase CV score."""
        opp = {"oems": ["Cisco"], "amount": 500000}

        # SEWP V has BPA
        sewp_score, _ = recommender.calculate_cv_score("SEWP V", opp)

        # CIO-SP3 has no BPA
        cio_score, _ = recommender.calculate_cv_score("CIO-SP3", opp)

        # SEWP V should have higher score due to BPA
        assert sewp_score > cio_score

    def test_bpa_in_reasoning(self, recommender):
        """Test that BPA status appears in reasoning."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        _, reasons = recommender.calculate_cv_score("SEWP V", opp)

        # Should mention BPA
        assert any("BPA" in r for r in reasons)


class TestCeilingEnforcement:
    """Test ceiling validation reduces viability."""

    def test_amount_within_ceiling_passes(self, recommender):
        """Test that deals within ceiling get no penalty."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}  # Well within SEWP V ceiling

        score, reasons = recommender.calculate_cv_score("SEWP V", opp)

        # Should have positive mentions about ceiling
        assert any("ceiling" in r.lower() for r in reasons)
        assert score >= 90  # Should maintain high score

    def test_amount_exceeds_ceiling_penalized(self, recommender):
        """Test that deals exceeding ceiling get penalized."""
        # SEWP V ceiling is $50B, let's test with amount beyond
        opp = {"oems": ["Microsoft"], "amount": 60000000000}  # $60B

        score, reasons = recommender.calculate_cv_score("SEWP V", opp)

        # Should have penalty in score
        assert score < 90  # Reduced from base priority of 95

        # Should mention ceiling issue
        assert any("exceed" in r.lower() for r in reasons)


class TestOEMCategoryAlignment:
    """Test OEM alignment scoring."""

    def test_oem_match_increases_score(self, recommender):
        """Test that OEM alignment increases score."""
        opp_microsoft = {"oems": ["Microsoft"], "amount": 500000}
        opp_unknown = {"oems": ["UnknownVendor"], "amount": 500000}

        score_ms, _ = recommender.calculate_cv_score("SEWP V", opp_microsoft)
        score_unk, _ = recommender.calculate_cv_score("SEWP V", opp_unknown)

        # Microsoft is supported, should have higher score
        assert score_ms > score_unk

    def test_oem_match_in_reasoning(self, recommender):
        """Test that OEM match appears in reasoning."""
        opp = {"oems": ["Cisco", "Microsoft"], "amount": 1000000}

        _, reasons = recommender.calculate_cv_score("SEWP V", opp)

        # Should mention OEM support
        assert any("supports" in r.lower() or "cisco" in r.lower() or "microsoft" in r.lower() for r in reasons)

    def test_all_oems_supported_bonus(self, recommender):
        """Test that 'All OEMs' vehicles get bonus for any OEM."""
        opp = {"oems": ["RareVendor"], "amount": 500000}

        score, reasons = recommender.calculate_cv_score("GSA Schedule", opp)  # Supports All OEMs

        # Should mention all OEMs support
        assert any("all oems" in r.lower() for r in reasons)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_vehicle_graceful_failure(self, recommender):
        """Test unknown vehicle returns default score with message."""
        opp = {"oems": ["Microsoft"], "amount": 100000}

        score, reasons = recommender.calculate_cv_score("NonExistent Vehicle", opp)

        assert score == 50.0  # Default score
        assert len(reasons) > 0
        assert "Unknown" in reasons[0]

    def test_malformed_opportunity_returns_empty(self, recommender):
        """Test malformed opportunity returns valid recommendations."""
        opp = {}  # Empty opportunity

        recommendations = recommender.recommend_vehicles(opp, top_n=3)

        # Should still return recommendations (with default scoring)
        assert len(recommendations) == 3
        assert all("contract_vehicle" in r for r in recommendations)

    def test_negative_amount_handled(self, recommender):
        """Test negative amounts don't break scoring."""
        opp = {"oems": ["Microsoft"], "amount": -1000}

        score, reasons = recommender.calculate_cv_score("SEWP V", opp)

        # Should not crash
        assert isinstance(score, (int, float))
        assert score >= 0

    def test_missing_oems_field(self, recommender):
        """Test missing OEMs field handled gracefully."""
        opp = {"amount": 500000}  # No OEMs

        recommendations = recommender.recommend_vehicles(opp, top_n=3)

        assert len(recommendations) == 3
        # Should still return valid recommendations


class TestRecommendationStructure:
    """Test recommendation record structure."""

    def test_recommendation_has_required_fields(self, recommender):
        """Test each recommendation has all required fields."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        recommendations = recommender.recommend_vehicles(opp, top_n=3)

        for rec in recommendations:
            assert "contract_vehicle" in rec
            assert "cv_score" in rec
            assert "priority" in rec
            assert "reasoning" in rec
            assert "has_bpa" in rec

    def test_reasoning_is_list(self, recommender):
        """Test reasoning is always a list of strings."""
        opp = {"oems": ["Cisco"], "amount": 500000}

        recommendations = recommender.recommend_vehicles(opp, top_n=3)

        for rec in recommendations:
            assert isinstance(rec["reasoning"], list)
            assert all(isinstance(r, str) for r in rec["reasoning"])

    def test_cv_score_in_range(self, recommender):
        """Test CV score is always 0-100."""
        opp = {"oems": ["Dell"], "amount": 2000000}

        recommendations = recommender.recommend_vehicles(opp, top_n=7)

        for rec in recommendations:
            assert 0 <= rec["cv_score"] <= 100


class TestTopNLimiting:
    """Test top_n parameter works correctly."""

    def test_top_n_limits_results(self, recommender):
        """Test top_n limits number of recommendations."""
        opp = {"oems": ["Microsoft"], "amount": 1000000}

        for n in [1, 3, 5]:
            recommendations = recommender.recommend_vehicles(opp, top_n=n)
            assert len(recommendations) == n

    def test_top_n_beyond_available(self, recommender):
        """Test requesting more than available returns all."""
        opp = {"oems": ["Cisco"], "amount": 500000}

        # Request 100 (only 7 vehicles available)
        recommendations = recommender.recommend_vehicles(opp, top_n=100)

        assert len(recommendations) == 7  # All available vehicles
