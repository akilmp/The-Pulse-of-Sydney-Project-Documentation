"""Streamlit entrypoint for the Sydney Pulse dashboard."""

import streamlit as st


def main() -> None:
    """Render the landing page for the dashboard."""
    st.set_page_config(page_title="Sydney Pulse Dashboard", page_icon="🌀", layout="wide")
    st.title("Sydney Pulse Dashboard")
    st.markdown(
        """
        This is a placeholder Streamlit app. Add interactive components once data
        pipelines are in place and cleaned datasets are available.
        """
    )


if __name__ == "__main__":
    main()
