from setuptools import setup, find_packages

setup(
    name="aividence",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-core",
        "langchain-anthropic",
        "langchain-openai",
        "langchain-community",
        "pydantic",
        "beautifulsoup4",
        "selenium",
        "requests",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "fact-check=aividence.run:main",  
        ],
    },
    python_requires=">=3.8",
    description="A tool for analyzing content for factual accuracy",
    author="AIvideance Team",
)