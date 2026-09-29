from src.parse.parser import PARSED_COLUMNS, infer_level, parse_html

HTML="""<!doctype html><html><head><title>Fallback Title at Fallback Co | ITviec</title>
<script type='application/ld+json'>{
  "@context":"https://schema.org","@type":"JobPosting",
  "title":"Senior Data Engineer","datePosted":"2026-09-09",
  "hiringOrganization":{"@type":"Organization","name":"Example Co"},
  "baseSalary":{"@type":"MonetaryAmount","currency":"USD","value":{"@type":"QuantitativeValue","unitText":"MONTH","value":"1,000 - 2,000 USD"}},
  "jobLocation":[
    {"@type":"Place","address":{"@type":"PostalAddress","addressRegion":"Hồ Chí Minh"}},
    {"@type":"Place","address":{"@type":"PostalAddress","addressRegion":"Hà Nội"}}
  ]
}</script></head><body>
<div class='imb-4 d-flex'><div>Job Expertise:</div><div><a>Data Engineer</a></div></div>
<section class='job-content' data-jobs--jd-scroll-target='jobContent'>
  <div class='paragraph'><h2>Top 3 reasons to join us</h2><p>Do not keep me</p></div>
  <div class='paragraph'><h2>Job description</h2><p>Build pipelines.</p></div>
  <div class='paragraph'><h2>Your skills and experience</h2><p>Python and SQL.</p></div>
  <div class='paragraph'><h2>Why You'll Love Working Here</h2><p>Do not keep me either</p></div>
</section>
<h2>More jobs for you</h2><div><h3>Fake Other Job</h3><span>9,999 USD</span></div>
</body></html>"""

def test_real_itviec_shape_and_boundaries():
    r=parse_html(HTML,job_id="senior-data-engineer-example-1234",url="https://itviec.com/it-jobs/senior-data-engineer-example-1234",crawled_at="2026-09-29T16:42:00+07:00")
    assert list(r)==PARSED_COLUMNS
    assert r["title"]=="Senior Data Engineer"
    assert r["company"]=="Example Co"
    assert r["level"]=="Senior"
    assert r["location"]=="Hồ Chí Minh; Hà Nội"
    assert r["posted_date"]=="2026-09-09"
    assert r["category"]=="Data Engineer"
    assert r["salary_raw"]=="1,000 - 2,000 USD"
    assert "Build pipelines." in r["jd_text"]
    assert "Python and SQL." in r["jd_text"]
    assert "Top 3 reasons" not in r["jd_text"]
    assert "More jobs for you" not in r["jd_text"]
    assert "Fake Other Job" not in r["jd_text"]

def test_level_examples():
    assert infer_level("Technical Leader Java Expert")=="Lead"
    assert infer_level("Business Analyst Middle")=="Middle"
    assert infer_level("Mid-Senior Fullstack Developer")=="Senior"
    assert infer_level("Tập sự tiềm năng AIOps/DevOps Engineer")=="Intern"
    assert infer_level("System Administrator") is None
