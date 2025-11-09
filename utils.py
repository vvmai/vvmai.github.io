"""
Shared utility functions for brainvomit Streamlit application.
"""
import streamlit as st


def configure_page(layout="wide", title=None):
    """
    Configure Streamlit page with common settings.

    Args:
        layout: Page layout mode ('wide' or 'centered')
        title: Optional page title
    """
    config = {"layout": layout}
    if title:
        config["page_title"] = title
    st.set_page_config(**config)


def get_plotly_config(scroll_zoom=True):
    """
    Get standard Plotly configuration.

    Args:
        scroll_zoom: Whether to enable scroll zoom

    Returns:
        dict: Plotly configuration
    """
    return {'scrollZoom': scroll_zoom}
