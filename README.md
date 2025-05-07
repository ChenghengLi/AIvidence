<div align="center">

# 🛡️ AIvidence: Fighting Misinformation 🔍
  
![AIvidence Logo](https://img.shields.io/badge/✓-AIVIDENCE-cc8800?style=for-the-badge&labelColor=800000)

<p>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-2E64FE.svg?style=flat-square&logo=python&logoColor=white" alt="Python Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-32CD32.svg?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License"></a>
  <a href="https://www.upc.edu/en"><img src="https://img.shields.io/badge/🏆_MERIThON-Winner-FFD700.svg?style=flat-square" alt="Award"></a>
  <img src="https://img.shields.io/badge/Version-1.0.0-2f4f4f.svg?style=flat-square" alt="Version">
</p>

<br>

***When control +c/v spreads misinformation, we fight back with control + AIvidence***

<br>

**🏆 Winner of the 3rd MERIThON Competition at UPC Manresa 🏆**

</div>

---

## 🔍 Overview

AIvidence is an advanced fact-checking platform that analyzes digital content for accuracy using a powerful combination of web scraping, search engine integration, and language models. Developed for the 3rd MERIThON Competition at UPC Manresa, this tool provides automated verification of factual claims, helping users navigate today's complex information ecosystem.

<details open>
<summary><b>✨ Key Features</b></summary>
<br>

- 🕸️ **Advanced Content Extraction** - Reliable scraping from websites and HTML files
- 🧠 **Domain Intelligence** - Analysis of expertise requirements and information patterns
- 🔎 **Claim Detection** - Automatic identification of verifiable factual statements
- 🌐 **Multi-source Verification** - Cross-reference claims with web search results
- 📊 **Comprehensive Reports** - Detailed analysis with truthfulness scores and evidence
- 🤖 **Multi-LLM Support** - Works with OpenAI, Anthropic, and Ollama models
- ⚙️ **Configurable** - Adjustable verification depth and claim thresholds

</details>

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- API keys for:
  - [OpenAI API](https://platform.openai.com/account/api-keys) (for GPT models)
  - [Anthropic API](https://console.anthropic.com/account/keys) (for Claude models)
  - [Brave Search API](https://brave.com/search/api/) (for web search functionality)

### Quick Setup

```bash
# Clone and enter repository
git clone https://github.com/ChenghengLi/AIvidence
cd AIvidence/aividence

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Configure API keys
cp .env.template .env
# Edit .env with your API keys
```

### Getting API Keys

<details>
<summary><b>📋 How to get an OpenAI API Key</b></summary>
<br>

1. Go to [OpenAI's platform website](https://platform.openai.com/)
2. Create an account or log in to your existing account
3. Click on your profile icon in the top-right corner
4. Select "View API keys"
5. Click "Create new secret key"
6. Save your API key securely (you won't be able to view it again)
7. Set up billing information under "Billing" in the left menu

New accounts receive free credits that expire after three months.

</details>

<details>
<summary><b>📋 How to get an Anthropic API Key</b></summary>
<br>

1. Go to [Anthropic's console](https://console.anthropic.com/)
2. Create an account or log in to your existing account
3. Click on your profile icon in the top-right corner
4. Select "API Keys"
5. Click "Create Key" and enter a name for your key
6. Copy your key and store it securely (you won't be able to view it again)
7. Set up billing under "Plans & Billing" in the left navigation

</details>

<details>
<summary><b>📋 How to get a Brave Search API Key</b></summary>
<br>

1. Go to [Brave Search API](https://brave.com/search/api/)
2. Click "Get started for FREE"
3. Create an account or log in to your existing account
4. After signing up, you'll be taken to your dashboard
5. Navigate to the API Keys section
6. Create a new API key
7. Copy and save your API key securely

The free tier allows up to 1 query/second and 2,000 queries/month.

</details>

## 🚀 Usage

AIvidence provides flexible options for analyzing content, from simple command-line operations to advanced programmatic integration. Below are detailed examples to help you get started.

### Command Line Interface


Our intuitive command-line interface makes it easy to analyze web content or local HTML files with just a few commands.

#### Basic Website Analysis

```bash
python -m aividence.run --url https://example.com
```

This command analyzes the content at `example.com`, extracts claims, verifies them against online sources, and generates a comprehensive report in the default `reports` directory.

#### Local HTML File Analysis

```bash
python -m aividence.run --file path/to/file.html
```

Perfect for analyzing offline content or pre-downloaded web pages. AIvidence processes the HTML file and generates the same detailed analysis as with online content.

#### Advanced Options

<table>
  <tr>
    <th>Option</th>
    <th>Description</th>
    <th>Example</th>
  </tr>
  <tr>
    <td><code>--model</code></td>
    <td>Select LLM model</td>
    <td><code>--model gpt-4o-mini</code></td>
  </tr>
  <tr>
    <td><code>--max-claims</code></td>
    <td>Number of claims to verify</td>
    <td><code>--max-claims 10</code></td>
  </tr>
  <tr>
    <td><code>--verbose</code></td>
    <td>Enable detailed logging</td>
    <td><code>--verbose</code></td>
  </tr>
  <tr>
    <td><code>--output</code></td>
    <td>Custom output filename</td>
    <td><code>--output report.md</code></td>
  </tr>
  <tr>
    <td><code>--output-dir</code></td>
    <td>Custom output directory</td>
    <td><code>--output-dir results</code></td>
  </tr>
</table>

You can combine these options to tailor the analysis to your specific needs:

```bash
python -m aividence.run --url https://news-site.com/article --model gpt-4o-mini --max-claims 15 --verbose --output-dir important-analyses
```

### Python API

For developers looking to integrate AIvidence into their applications, our Python API provides programmatic access to all features.

#### Basic Integration

```python
from aividence.core.fact_check_engine import FactCheckEngine

# Initialize the engine with the powerful gpt-4o-mini model
engine = FactCheckEngine(model_name="gpt-4o-mini")

# Analyze a website
result = engine.analyze_content(
    source="https://example.com",
    source_type="url",
    max_claims=5
)

# Generate and save a report
report = result.to_markdown_report()
with open("report.md", "w", encoding="utf-8") as f:
    f.write(report)
```

#### Working with Analysis Results

The analysis results object provides rich access to verification data:

```python
# Get overall assessment
print(f"Overall trustworthiness score: {result.overall_score}/5")
print(f"Topic identified: {result.topic}")
print(f"Analysis summary: {result.summary}")

# Process individual verified claims
for claim_result in result.verification_results:
    print(f"\nClaim: {claim_result.claim}")
    print(f"Truthfulness score: {claim_result.score}/5")
    print(f"Confidence: {claim_result.confidence}")
    
    # List supporting evidence
    if claim_result.evidence:
        print("Supporting evidence:")
        for evidence in claim_result.evidence:
            print(f"- {evidence}")
    
    # List contradicting evidence
    if claim_result.contradictions:
        print("Contradicting evidence:")
        for contradiction in claim_result.contradictions:
            print(f"- {contradiction}")
            
    print(f"Explanation: {claim_result.explanation}")
```

### Integration Example: Web Application

AIvidence can be easily integrated into web applications to provide real-time fact checking:

```python
from flask import Flask, request, jsonify
from aividence.core.fact_check_engine import FactCheckEngine

app = Flask(__name__)
engine = FactCheckEngine(model_name="gpt-4o-mini")

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        result = engine.analyze_content(source=url)
        return jsonify({
            "overall_score": result.overall_score,
            "topic": result.topic,
            "summary": result.summary,
            "claims": [
                {
                    "text": r.claim,
                    "score": r.score,
                    "confidence": r.confidence,
                    "explanation": r.explanation
                } for r in result.verification_results
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## 📊 How It Works


![Imagen de WhatsApp 2025-05-06 a las 22 26 06_dc0fd611](https://github.com/user-attachments/assets/9323a383-8a87-4d96-ab00-f3b882a5a4d6)


## 📝 Report Format

<div align="center">


</div>

AIvidence generates comprehensive markdown reports featuring:

<table>
  <tr>
    <th width="30%">Section</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>Summary</b></td>
    <td>Overall assessment of content trustworthiness with key observations</td>
  </tr>
  <tr>
    <td><b>Claims Analysis</b></td>
    <td>Detailed verification of key factual claims extracted from the content</td>
  </tr>
  <tr>
    <td><b>Evidence</b></td>
    <td>Supporting and contradicting information found during verification</td>
  </tr>
  <tr>
    <td><b>Sources</b></td>
    <td>References and links to sources used for verification</td>
  </tr>
  <tr>
    <td><b>Recommendations</b></td>
    <td>Practical advice for readers on how to approach the analyzed content</td>
  </tr>
</table>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

Special thanks to UPC Manresa for hosting the 3rd MERIThON Competition, and to all the mentors and judges who recognized this project's potential for combating misinformation.

## 👥 The Minds Behind AIvidence

<div align="center">
  
<!-- Team Members -->
<p>
  <a href="https://www.linkedin.com/in/chengheng-li-8b14641ba/">
    <img src="https://img.shields.io/badge/⭐_Chengheng_Li_Chen-LinkedIn-%23D4AF37?style=for-the-badge&logo=linkedin&logoColor=white" alt="Chengheng Li Chen (Team Leader)"/>
  </a>
</p>

<p>
  <a href="https://www.linkedin.com/in/xu-yao-140059231/">
    <img src="https://img.shields.io/badge/Xu_Yao_Chen-LinkedIn-%2300a0dc?style=for-the-badge&logo=linkedin&logoColor=white" alt="Xu Yao Chen"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://www.linkedin.com/in/zhiqian-zhou-196350300/">
    <img src="https://img.shields.io/badge/Zhiqian_Zhou-LinkedIn-%2300a0dc?style=for-the-badge&logo=linkedin&logoColor=white" alt="Zhiqian Zhou"/>
  </a>
</p>

<p>
  <a href="https://www.linkedin.com/in/zhihao-chen-584aa52b5/">
    <img src="https://img.shields.io/badge/Zhihao_Chen-LinkedIn-%2300a0dc?style=for-the-badge&logo=linkedin&logoColor=white" alt="Zhihao Chen"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://www.linkedin.com/in/pengcheng-chen-153612317/">
    <img src="https://img.shields.io/badge/Pengcheng_Chen-LinkedIn-%2300a0dc?style=for-the-badge&logo=linkedin&logoColor=white" alt="Pengcheng Chen"/>
  </a>
</p>

</div>
