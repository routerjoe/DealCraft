"""DealCraft light theme for Textual TUI."""

from textual.design import ColorSystem

# DealCraft brand colors - light theme
DEALCRAFT_LIGHT = ColorSystem(
    primary="#CC0000",  # DealCraft red
    secondary="#2C5F8D",  # Professional blue
    warning="#FF9800",  # Orange for warnings
    error="#D32F2F",  # Deep red for errors
    success="#388E3C",  # Green for success
    accent="#0277BD",  # Bright blue accent
    background="#FFFFFF",  # White background
    surface="#F5F5F5",  # Light gray surface
    panel="#FAFAFA",  # Very light gray panel
    dark=False,  # Light theme
)
