"""
Common plotting utilities for matplotlib visualizations.
"""
import matplotlib.pyplot as plt
from typing import Optional, Tuple


def setup_plot(
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Optional[Tuple[float, float]] = None,
    grid: bool = True
) -> plt.Figure:
    """
    Set up a matplotlib plot with common styling.

    Args:
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Optional figure size (width, height)
        grid: Whether to show grid

    Returns:
        Matplotlib figure object
    """
    if figsize:
        fig = plt.figure(figsize=figsize)
    else:
        fig = plt.figure()

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()

    return fig


def finalize_plot(legend: bool = True) -> plt.Figure:
    """
    Finalize a matplotlib plot with legend and get current figure.

    Args:
        legend: Whether to show legend

    Returns:
        Current matplotlib figure
    """
    if legend:
        plt.legend()
    return plt.gcf()
