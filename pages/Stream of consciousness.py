import streamlit as st
from utils import configure_page
from datetime import datetime
from pathlib import Path
import re
import html

configure_page(layout="wide", title="Stream of Consciousness")


def parse_markdown_file(file_path):
    """
    Parse a markdown file with YAML frontmatter.

    Args:
        file_path: Path to the markdown file

    Returns:
        dict with 'title', 'date', and 'body'
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        frontmatter = match.group(1)
        body = match.group(2).strip()

        # Parse date from frontmatter
        date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', frontmatter)
        if date_match:
            date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
        else:
            # Fallback to file modification time
            date = datetime.fromtimestamp(file_path.stat().st_mtime)
    else:
        # No frontmatter, use entire content as body
        body = content.strip()
        date = datetime.fromtimestamp(file_path.stat().st_mtime)

    # Extract title from filename (remove .md extension)
    title = file_path.stem

    return {
        'title': title,
        'date': date,
        'body': body
    }


@st.cache_data
def load_all_posts():
    """
    Load all blog posts from the text_posts directory.

    Returns:
        List of post dictionaries, sorted by date (newest first)
    """
    posts_dir = Path('text_posts')

    if not posts_dir.exists():
        return []

    posts = []
    for md_file in posts_dir.glob('*.md'):
        # Skip README
        if md_file.name.lower() == 'readme.md':
            continue

        try:
            post = parse_markdown_file(md_file)
            posts.append(post)
        except Exception as e:
            st.warning(f"Error loading {md_file.name}: {str(e)}")
            continue

    # Sort by date, newest first
    posts.sort(key=lambda x: x['date'], reverse=True)

    return posts


# Custom CSS for blog styling
st.markdown("""
    <style>
    .blog-container {
        background-color: white;
        padding: 1.5rem;
        border: 1px solid;
        margin-bottom: 1.5rem;
    }

    .blog-title {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .blog-date {
        font-size: 0.85rem;
        margin-bottom: 1rem;
        font-style: italic;
    }

    .blog-body {
        font-size: 1rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    .post-list-container {
        background-color: white;
        padding: 1rem;
        border: 1px solid #c52077;
        margin-bottom: 1.5rem;
    }

    .post-list-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #c52077;
        margin-bottom: 0.8rem;
    }

    /* Condense button spacing and set green background */
    [data-testid="column"]:first-child button {
        margin-bottom: 0.2rem !important;
        padding: 0.3rem 0.5rem !important;
        font-size: 0.85rem !important;
    }

    [data-testid="column"]:first-child button[kind="secondary"] {
        background-color: #93cb81 !important;
        border: 1px solid #93cb81 !important;
        color: #463037 !important;
    }

    /* Active/primary button styling */
    [data-testid="column"]:first-child button[kind="primary"] {
        background-color: #7ab560 !important;
        border: 1px solid #7ab560 !important;
        color: #463037 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load all posts
BLOG_POSTS = load_all_posts()

if not BLOG_POSTS:
    st.error("No blog posts found in text_posts/ directory")
    st.stop()

# Initialize session state for current page
if 'blog_page' not in st.session_state:
    st.session_state.blog_page = 0

# Handle URL parameter for post selection
try:
    query_params = st.query_params
    if 'post' in query_params:
        post_idx = int(query_params['post'])
        if 0 <= post_idx < len(BLOG_POSTS):
            st.session_state.blog_page = post_idx
except:
    pass

# Get current post
current_post = BLOG_POSTS[st.session_state.blog_page]

# Create two-column layout
col_left, col_right = st.columns([1, 3])

with col_left:
    # Post list in left column
    for idx, post in enumerate(BLOG_POSTS):
        button_type = "primary" if idx == st.session_state.blog_page else "secondary"
        if st.button(
            post['title'],
            key=f"post_{idx}",
            type=button_type,
            use_container_width=True
        ):
            st.session_state.blog_page = idx
            st.query_params.update({"post": idx})
            st.rerun()

with col_right:
    # Display blog post in single container
    st.markdown(f"""
    <div class="blog-container">
        <div class="blog-title">{html.escape(current_post['title'])}</div>
        <div class="blog-date">{current_post['date'].strftime('%B %d, %Y')}</div>
        <div class="blog-body">{html.escape(current_post['body'])}</div>
    </div>
    """, unsafe_allow_html=True)
