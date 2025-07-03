from services.resume_pipeline.scraper import parse_requirements

sample_html = """
<html><body>
<h2>Job Requirements</h2>
<ul><li>Python</li><li>SQL</li></ul>
</body></html>
"""

def test_parse_requirements():
    text = parse_requirements(sample_html)
    assert "Python" in text
    assert "SQL" in text
