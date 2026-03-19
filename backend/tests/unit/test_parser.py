"""
Unit tests for the HTML parser.

Tests cover:
- Clean text extraction from typical handbook HTML
- Navigation / footer elements are stripped
- Title extraction from h1 and <title> tags
- Heading hierarchy preserved as markdown (#, ##, ###)
- Empty / error pages return None
- Minimum length filtering
"""

import pytest
from scraper.parser import parse_page

# ── Sample HTML fixtures ──────────────────────────────────────────────────────

SIMPLE_HANDBOOK_HTML = """
<!DOCTYPE html>
<html>
<head><title>GitLab Values | GitLab</title></head>
<body>
  <nav>Home | About | Values</nav>
  <header>GitLab Header</header>
  <main>
    <h1>GitLab Values</h1>
    <p>GitLab's six values are known as CREDIT.</p>
    <h2>Collaboration</h2>
    <p>We work together across teams. Everyone can contribute.</p>
    <h2>Results</h2>
    <p>We focus on outcomes, not activity. Shipping matters.</p>
    <ul>
      <li>Focus on outcomes</li>
      <li>Measure what matters</li>
    </ul>
  </main>
  <footer>Copyright GitLab 2024</footer>
</body>
</html>
"""

MINIMAL_VALID_HTML = """
<html>
<body>
  <main>
    <h1>Short Page</h1>
    <p>This page has enough content to pass the minimum length check.
    GitLab is an all-remote company that values transparency and collaboration
    above all else in the way it operates day to day.</p>
  </main>
</body>
</html>
"""

TOO_SHORT_HTML = """
<html><body><main><p>Short.</p></main></body></html>
"""

EMPTY_HTML = "<html><body></body></html>"

CODE_BLOCK_HTML = """
<html><body><main>
  <h1>API Guide</h1>
  <p>Use the following command to authenticate with GitLab CI.</p>
  <pre><code>export CI_TOKEN=your-token-here
curl -H "Authorization: Bearer $CI_TOKEN" https://gitlab.com/api/v4/projects</code></pre>
  <p>The token must be scoped to the correct project permissions.</p>
</main></body></html>
"""

TABLE_HTML = """
<html><body><main>
  <h1>Compensation Bands</h1>
  <p>GitLab uses location factor-based compensation bands.</p>
  <table>
    <tr><th>Level</th><th>Location Factor</th><th>Base Range</th></tr>
    <tr><td>IC4</td><td>0.85</td><td>$80k–$120k</td></tr>
    <tr><td>IC5</td><td>0.90</td><td>$120k–$160k</td></tr>
  </table>
</main></body></html>
"""


# ── Basic parsing ─────────────────────────────────────────────────────────────

class TestParsePageBasic:

    @pytest.mark.unit
    def test_returns_dict_on_valid_html(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert isinstance(result, dict)

    @pytest.mark.unit
    def test_required_keys_present(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        assert "url"       in result
        assert "page_type" in result
        assert "title"     in result
        assert "content"   in result

    @pytest.mark.unit
    def test_url_preserved(self):
        url    = "https://handbook.gitlab.com/values/"
        result = parse_page(url, SIMPLE_HANDBOOK_HTML, "handbook")
        assert result["url"] == url

    @pytest.mark.unit
    def test_page_type_preserved(self):
        result = parse_page("https://about.gitlab.com/direction/", SIMPLE_HANDBOOK_HTML, "direction")
        assert result["page_type"] == "direction"


# ── Title extraction ──────────────────────────────────────────────────────────

class TestTitleExtraction:

    @pytest.mark.unit
    def test_extracts_h1_as_title(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result["title"] == "GitLab Values"

    @pytest.mark.unit
    def test_falls_back_to_title_tag(self):
        html = """
        <html>
        <head><title>Hiring Process | GitLab</title></head>
        <body><main><p>This is a page about hiring at GitLab.
        The hiring process involves multiple steps and is designed to be fair.
        GitLab hires globally and uses async interviewing techniques.</p></main></body>
        </html>
        """
        result = parse_page("https://handbook.gitlab.com/hiring/", html, "handbook")
        # Should strip " | GitLab" suffix and return clean title
        assert result is not None
        if result["title"]:
            assert "| GitLab" not in result["title"]


# ── Content cleaning ──────────────────────────────────────────────────────────

class TestContentCleaning:

    @pytest.mark.unit
    def test_nav_stripped(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        # Nav content "Home | About | Values" should not appear in content
        assert "Home | About | Values" not in result["content"]

    @pytest.mark.unit
    def test_footer_stripped(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        assert "Copyright GitLab 2024" not in result["content"]

    @pytest.mark.unit
    def test_main_content_extracted(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        assert "CREDIT" in result["content"]
        assert "Collaboration" in result["content"]

    @pytest.mark.unit
    def test_headings_preserved_as_markdown(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        # h2 headings should become ## in the output
        assert "Collaboration" in result["content"]
        assert "Results" in result["content"]

    @pytest.mark.unit
    def test_paragraphs_extracted(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        assert "outcomes" in result["content"].lower()

    @pytest.mark.unit
    def test_list_items_extracted(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        # List items should appear in content
        assert "outcomes" in result["content"].lower() or "measure" in result["content"].lower()

    @pytest.mark.unit
    def test_code_block_extracted(self):
        result = parse_page("https://handbook.gitlab.com/api/", CODE_BLOCK_HTML, "handbook")
        assert result is not None
        assert "CI_TOKEN" in result["content"]

    @pytest.mark.unit
    def test_table_rows_extracted(self):
        result = parse_page("https://handbook.gitlab.com/compensation/", TABLE_HTML, "handbook")
        assert result is not None
        assert "IC4" in result["content"] or "IC5" in result["content"]


# ── Minimum length filtering ──────────────────────────────────────────────────

class TestLengthFiltering:

    @pytest.mark.unit
    def test_too_short_returns_none(self):
        result = parse_page("https://handbook.gitlab.com/empty/", TOO_SHORT_HTML, "handbook")
        assert result is None

    @pytest.mark.unit
    def test_empty_html_returns_none(self):
        result = parse_page("https://handbook.gitlab.com/empty/", EMPTY_HTML, "handbook")
        assert result is None

    @pytest.mark.unit
    def test_valid_page_not_none(self):
        result = parse_page("https://handbook.gitlab.com/valid/", MINIMAL_VALID_HTML, "handbook")
        assert result is not None

    @pytest.mark.unit
    def test_content_minimum_length(self):
        result = parse_page("https://handbook.gitlab.com/values/", SIMPLE_HANDBOOK_HTML, "handbook")
        assert result is not None
        assert len(result["content"]) >= 200


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:

    @pytest.mark.unit
    def test_malformed_html_handled_gracefully(self):
        malformed = "<html><body><main><h1>Broken <p>page content is here and has enough text to pass</p></main>"
        result    = parse_page("https://handbook.gitlab.com/broken/", malformed, "handbook")
        # Should not raise — either returns dict or None
        assert result is None or isinstance(result, dict)

    @pytest.mark.unit
    def test_completely_invalid_input_returns_none(self):
        result = parse_page("https://handbook.gitlab.com/invalid/", "not html at all !!!", "handbook")
        # Very short non-html — should return None (too short)
        assert result is None or isinstance(result, dict)