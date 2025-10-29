"""Test MCP tools discovery and registration - Phase 5-9."""

from pathlib import Path


class TestMCPToolsFilesExist:
    """Test that MCP tool files exist (TypeScript)."""

    def test_forecast_tools_file_exists(self):
        """Test forecast tools file exists."""
        forecast_path = Path("src/tools/forecast/index.ts")
        assert forecast_path.exists()

        content = forecast_path.read_text()
        assert "forecastTools" in content
        assert "handleForecastTool" in content

    def test_crm_tools_file_exists(self):
        """Test CRM tools file exists."""
        crm_path = Path("src/tools/crm/index.ts")
        assert crm_path.exists()

        content = crm_path.read_text()
        assert "crmTools" in content
        assert "handleCrmTool" in content

    def test_cv_tools_file_exists(self):
        """Test CV tools file exists."""
        cv_path = Path("src/tools/cv/index.ts")
        assert cv_path.exists()

        content = cv_path.read_text()
        assert "cvTools" in content
        assert "handleCvTool" in content


class TestMCPToolDefinitions:
    """Test MCP tool definitions in TypeScript source."""

    def test_forecast_tool_definitions(self):
        """Test forecast tools are defined."""
        content = Path("src/tools/forecast/index.ts").read_text()

        # Check for tool names
        assert "forecast_run" in content
        assert "forecast_all" in content
        assert "forecast_top" in content
        assert "forecast_export_csv" in content
        assert "forecast_export_obsidian" in content

    def test_crm_tool_definitions(self):
        """Test CRM tools are defined."""
        content = Path("src/tools/crm/index.ts").read_text()

        # Check for tool names
        assert "crm_export" in content
        assert "crm_attribution" in content
        assert "crm_validate" in content

    def test_cv_tool_definitions(self):
        """Test CV tools are defined."""
        content = Path("src/tools/cv/index.ts").read_text()

        # Check for tool names
        assert "cv_recommend" in content
        assert "cv_list" in content
        assert "cv_details" in content


class TestMCPServerIntegration:
    """Test tools are registered in main MCP server."""

    def test_tools_imported_in_main_index(self):
        """Test tools are imported in src/index.ts."""
        index_path = Path("src/index.ts")
        assert index_path.exists()

        content = index_path.read_text()

        # Check imports
        assert "forecastTools" in content
        assert "handleForecastTool" in content
        assert "cvTools" in content
        assert "handleCvTool" in content
        assert "crmTools" in content
        assert "handleCrmTool" in content

    def test_tools_registered_in_array(self):
        """Test tools are added to tools array."""
        index_path = Path("src/index.ts")
        content = index_path.read_text()

        # Tools should be spread into this.tools
        assert "...forecastTools" in content
        assert "...cvTools" in content

    def test_handlers_registered(self):
        """Test tool handlers are registered in routing."""
        index_path = Path("src/index.ts")
        content = index_path.read_text()

        # Check handler routing
        assert "handleForecastTool" in content
        assert "handleCvTool" in content


class TestAPIEndpointIntegration:
    """Test that tools call the correct API endpoints."""

    def test_forecast_tools_reference_api(self):
        """Test forecast tools reference /v1/forecast endpoints."""
        content = Path("src/tools/forecast/index.ts").read_text()

        assert "/v1/forecast/run" in content
        assert "/v1/forecast/all" in content
        assert "/v1/forecast/top" in content
        assert "/v1/forecast/export/csv" in content
        assert "/v1/forecast/export/obsidian" in content

    def test_crm_tools_reference_api(self):
        """Test CRM tools reference /v1/crm endpoints."""
        content = Path("src/tools/crm/index.ts").read_text()

        assert "/v1/crm/export" in content
        assert "/v1/crm/attribution" in content
        assert "/v1/crm/validate" in content

    def test_cv_tools_reference_api(self):
        """Test CV tools reference /v1/cv endpoints."""
        content = Path("src/tools/cv/index.ts").read_text()

        assert "/v1/cv/recommend" in content
        assert "/v1/cv/vehicles" in content
