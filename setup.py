from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="streamlit-theta",
    version="1.0.0",
    author="Arcana Team",
    author_email="team@arcana.dev",
    description="A PowerPoint/Keynote-style visual slide editor for Streamlit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arcana/streamlit-theta",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Streamlit",
    ],
    python_requires=">=3.7",
    install_requires=[
        "streamlit>=1.0.0",
    ],
    keywords="streamlit, powerpoint, keynote, presentation, visual editor, slides",
    project_urls={
        "Bug Reports": "https://github.com/arcana/streamlit-theta/issues",
        "Source": "https://github.com/arcana/streamlit-theta",
    },
) 