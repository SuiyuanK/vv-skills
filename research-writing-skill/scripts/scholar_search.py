#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scholar Search - Multi-database academic literature search tool.

Supported databases:
  - pubmed: PubMed (biomedical)
  - crossref: CrossRef (all disciplines)
  - semanticscholar: Semantic Scholar (AI-enhanced)
  - arxiv: arXiv (preprints, CS/physics/math)

Supported output formats:
  - json: JSON format (default)
  - bibtex: BibTeX format for LaTeX
  - ris: RIS format for EndNote/Zotero
  - apa: APA citation style
  - mla: MLA citation style
  - chicago: Chicago citation style
  - vancouver: Vancouver citation style

Usage:
  python scholar_search.py "deep learning" --sources crossref --year 2020-2024 --limit 20
  python scholar_search.py "transformer attention" --format bibtex --output refs.bib
  python scholar_search.py "quantum computing" --format apa --limit 5
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# Citation Formatting Functions
# ═══════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Remove characters that break citation formats."""
    if not text:
        return ""
    text = re.sub(r"[{}\[\]\\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def generate_cite_key(paper: dict) -> str:
    """Generate a BibTeX citation key from paper data."""
    authors = paper.get("authors", [])
    if authors:
        first_author = authors[0] if isinstance(authors[0], str) else str(authors[0])
        # Extract last name
        parts = first_author.split()
        last_name = parts[-1] if parts else "unknown"
        last_name = re.sub(r"[^a-zA-Z]", "", last_name).lower()
    else:
        last_name = "unknown"
    year = str(paper.get("year") or "XXXX")
    return f"{last_name}{year}"


def normalize_paper(data: dict) -> dict:
    """Normalize paper dict for citation formatting."""
    authors = data.get("authors", [])
    if isinstance(authors, list):
        authors_str = " and ".join(authors)
    else:
        authors_str = str(authors)

    return {
        "title": data.get("title") or "Unknown",
        "authors_str": authors_str,
        "journal": data.get("journal") or "",
        "year": str(data.get("year") or ""),
        "doi": data.get("doi") or "",
        "pmid": data.get("pmid") or "",
        "arxiv_id": data.get("arxiv") or data.get("arxiv_id") or "",
        "url": data.get("url") or data.get("pdf_url") or "",
        "abstract": data.get("abstract") or "",
        "document_type": "article",
        "citation_count": data.get("citations") or 0,
    }


def to_bibtex(paper: dict) -> str:
    """Format paper as BibTeX entry."""
    p = normalize_paper(paper)
    key = generate_cite_key(paper)

    lines = [f"@article{{{key},"]

    title = clean_text(p["title"])
    if title:
        lines.append(f"  title = {{{title}}},")

    authors = p["authors_str"]
    lines.append(f"  author = {{{authors or 'Unknown'}}},")

    journal = clean_text(p["journal"])
    if journal:
        lines.append(f"  journal = {{{journal}}},")
    if p["year"]:
        lines.append(f"  year = {{{p['year']}}},")
    if p["doi"]:
        lines.append(f"  doi = {{{p['doi']}}},")
    if p["pmid"]:
        lines.append(f"  pmid = {{{p['pmid']}}},")
    if p["arxiv_id"]:
        lines.append(f"  eprint = {{{p['arxiv_id']}}},")
        lines.append("  archivePrefix = {arXiv},")
    if p["url"]:
        lines.append(f"  url = {{{p['url']}}},")

    # Remove trailing comma
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]
    lines.append("}")

    return "\n".join(lines)


def to_ris(paper: dict) -> str:
    """Format paper as RIS entry."""
    p = normalize_paper(paper)
    lines = ["TY  - JOUR"]

    title = clean_text(p["title"])
    if title:
        lines.append(f"TI  - {title}")

    for author in p["authors_str"].split(" and "):
        author = author.strip()
        if author:
            lines.append(f"AU  - {author}")

    if p["journal"]:
        lines.append(f"JO  - {clean_text(p['journal'])}")
    if p["year"]:
        lines.append(f"PY  - {p['year']}")
    if p["doi"]:
        lines.append(f"DO  - {p['doi']}")
    if p["url"]:
        lines.append(f"UR  - {p['url']}")

    lines.append("ER  - ")
    return "\n".join(lines)


def to_text_citation(paper: dict, style: str = "apa") -> str:
    """Format paper as text citation in specified style."""
    p = normalize_paper(paper)
    authors = p["authors_str"] or "Unknown"
    year = p["year"] or "n.d."
    title = clean_text(p["title"])
    journal = clean_text(p["journal"])
    doi = p["doi"] or p["url"] or ""

    if style == "apa":
        return f"{authors} ({year}). {title}. {journal}. {doi}"
    elif style == "mla":
        return f'{authors}. "{title}." {journal}, {year}. {doi}.'
    elif style == "chicago":
        return f'{authors}. "{title}." {journal} ({year}). {doi}.'
    elif style == "vancouver":
        return f"{authors}. {title}. {journal}. {year}. Available from: {doi}"
    else:
        return f"{authors} ({year}). {title}. {journal}."


def format_papers(papers: List[dict], fmt: str) -> str:
    """Format list of papers to specified format."""
    if fmt == "json":
        return json.dumps(papers, indent=2, ensure_ascii=False)
    elif fmt == "bibtex":
        return "\n\n".join(to_bibtex(p) for p in papers)
    elif fmt == "ris":
        return "\n\n".join(to_ris(p) for p in papers)
    elif fmt in ["apa", "mla", "chicago", "vancouver"]:
        return "\n\n".join(to_text_citation(p, fmt) for p in papers)
    else:
        raise ValueError(f"Unknown format: {fmt}")


# ═══════════════════════════════════════════════════════════════════════
# Search Engine Classes
# ═══════════════════════════════════════════════════════════════════════


class ScholarSearch:
    """Multi-database academic literature search."""

    def __init__(self, email: str = "research@example.com"):
        self.email = email
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"ScholarSearch/1.0 (mailto:{email})"})

    def search(
        self,
        query: str,
        sources: List[str] = None,
        year_start: int = None,
        year_end: int = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search multiple databases and aggregate results."""
        sources = sources or ["pubmed", "crossref", "semanticscholar", "arxiv"]
        all_results = []

        for source in sources:
            try:
                if source == "pubmed":
                    results = self._search_pubmed(query, year_start, year_end, limit)
                elif source == "crossref":
                    results = self._search_crossref(query, year_start, year_end, limit)
                elif source == "semanticscholar":
                    results = self._search_semanticscholar(query, year_start, year_end, limit)
                elif source == "arxiv":
                    results = self._search_arxiv(query, year_start, year_end, limit)
                else:
                    print(f"Warning: Unknown source '{source}'", file=sys.stderr)
                    continue

                for r in results:
                    r["_source"] = source
                all_results.extend(results)

            except Exception as e:
                print(f"Error searching {source}: {e}", file=sys.stderr)

        # Deduplicate by DOI
        seen_dois = set()
        unique_results = []
        for paper in all_results:
            doi = paper.get("doi")
            if doi:
                if doi in seen_dois:
                    continue
                seen_dois.add(doi)
            unique_results.append(paper)

        # Sort by citation count (descending), handle None values
        unique_results.sort(key=lambda x: x.get("citations") or 0, reverse=True)

        return unique_results[:limit * len(sources)]

    def _search_pubmed(
        self, query: str, year_start: int, year_end: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Search PubMed via E-utilities API."""
        # Build query
        pubmed_query = f"({query})[Title/Abstract]"
        if year_start and year_end:
            pubmed_query += f" AND {year_start}:{year_end}[pdat]"
        elif year_start:
            pubmed_query += f" AND {year_start}:{datetime.now().year}[pdat]"

        # Search for PMIDs
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": pubmed_query,
            "retmode": "json",
            "retmax": min(limit, 100),
        }

        response = self.session.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        pmids = response.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        # Fetch metadata
        results = []
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

        for i, pmid in enumerate(pmids[:limit]):
            if i > 0:
                time.sleep(0.34)  # Rate limit: 3 requests/second

            try:
                params = {"db": "pubmed", "id": pmid, "retmode": "json"}
                response = self.session.get(fetch_url, params=params, timeout=30)
                data = response.json()

                result = data.get("result", {}).get(pmid, {})
                if result and not result.get("error"):
                    authors = [
                        a.get("name", "")
                        for a in result.get("authors", [])
                    ]

                    results.append({
                        "title": result.get("title", ""),
                        "authors": authors,
                        "year": result.get("pubdate", "")[:4] if result.get("pubdate") else None,
                        "journal": result.get("fulljournalname", ""),
                        "pmid": pmid,
                        "doi": result.get("elocationid", "").replace("doi: ", "") if "doi" in result.get("elocationid", "").lower() else None,
                        "abstract": None,  # Requires efetch
                        "citations": None,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    })
            except Exception as e:
                print(f"Error fetching PMID {pmid}: {e}", file=sys.stderr)

        return results

    def _search_crossref(
        self, query: str, year_start: int, year_end: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Search CrossRef API."""
        url = "https://api.crossref.org/works"

        filter_parts = ["type:journal-article"]
        if year_start:
            filter_parts.append(f"from-pub-date:{year_start}")
        if year_end:
            filter_parts.append(f"until-pub-date:{year_end}")

        params = {
            "query.bibliographic": query,
            "rows": min(limit, 1000),
            "filter": ",".join(filter_parts),
            "mailto": self.email,
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        items = response.json().get("message", {}).get("items", [])
        results = []

        for item in items:
            authors = []
            for author in item.get("author", []):
                if "given" in author and "family" in author:
                    authors.append(f"{author['given']} {author['family']}")

            year = None
            if "published-print" in item:
                date_parts = item["published-print"].get("date-parts", [[]])[0]
                if date_parts:
                    year = date_parts[0]
            elif "published-online" in item:
                date_parts = item["published-online"].get("date-parts", [[]])[0]
                if date_parts:
                    year = date_parts[0]

            results.append({
                "title": item.get("title", [""])[0] if item.get("title") else "",
                "authors": authors,
                "year": year,
                "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "doi": item.get("DOI"),
                "abstract": item.get("abstract"),
                "citations": item.get("is-referenced-by-count", 0),
                "url": f"https://doi.org/{item['DOI']}" if item.get("DOI") else None,
            })

        return results

    def _search_semanticscholar(
        self, query: str, year_start: int, year_end: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Search Semantic Scholar API."""
        url = "https://api.semanticscholar.org/graph/v1/paper/search"

        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": "paperId,title,authors,year,abstract,citationCount,openAccessPdf,externalIds,venue",
        }

        if year_start and year_end:
            params["year"] = f"{year_start}-{year_end}"
        elif year_start:
            params["year"] = f"{year_start}-"
        elif year_end:
            params["year"] = f"-{year_end}"

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        papers = response.json().get("data", [])
        results = []

        for paper in papers:
            authors = [a.get("name", "") for a in paper.get("authors", [])]
            external_ids = paper.get("externalIds", {})
            oa_pdf = paper.get("openAccessPdf", {})

            results.append({
                "title": paper.get("title", ""),
                "authors": authors,
                "year": paper.get("year"),
                "journal": paper.get("venue", ""),
                "doi": external_ids.get("DOI"),
                "pmid": external_ids.get("PubMed"),
                "arxiv": external_ids.get("ArXiv"),
                "abstract": paper.get("abstract"),
                "citations": paper.get("citationCount", 0),
                "pdf_url": oa_pdf.get("url") if oa_pdf else None,
                "url": f"https://www.semanticscholar.org/paper/{paper.get('paperId')}" if paper.get("paperId") else None,
            })

        return results

    def _search_arxiv(
        self, query: str, year_start: int, year_end: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Search arXiv API."""
        search_query = f"all:{query}"
        url = f"http://export.arxiv.org/api/query?search_query={quote(search_query)}&start=0&max_results={limit}"

        time.sleep(3)  # Rate limit: 1 request per 3 seconds

        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        entries = root.findall("atom:entry", ns)
        results = []

        for entry in entries:
            arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]

            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""

            authors = []
            for author_elem in entry.findall("atom:author", ns):
                name_elem = author_elem.find("atom:name", ns)
                if name_elem is not None:
                    authors.append(name_elem.text)

            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""

            published_elem = entry.find("atom:published", ns)
            year = int(published_elem.text[:4]) if published_elem is not None else None

            # Apply year filter
            if year_start and year and year < year_start:
                continue
            if year_end and year and year > year_end:
                continue

            doi_elem = entry.find("arxiv:doi", ns)
            doi = doi_elem.text if doi_elem is not None else None

            results.append({
                "title": title,
                "authors": authors,
                "year": year,
                "journal": "arXiv",
                "arxiv": arxiv_id,
                "doi": doi,
                "abstract": abstract,
                "citations": None,
                "pdf_url": f"http://arxiv.org/pdf/{arxiv_id}.pdf",
                "url": f"http://arxiv.org/abs/{arxiv_id}",
            })

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Search academic literature across multiple databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search and show results
  python scholar_search.py "deep learning transformer"

  # Output as BibTeX for LaTeX
  python scholar_search.py "landslide detection" --format bibtex -o refs.bib

  # Output as APA citation style
  python scholar_search.py "neural network" --format apa --year 2022-2025

  # Filter by year and save JSON
  python scholar_search.py "machine learning" --year 2022-2025 -o results.json

Supported formats:
  json      - JSON format (default)
  bibtex    - BibTeX format for LaTeX
  ris       - RIS format for EndNote/Zotero
  apa       - APA citation style
  mla       - MLA citation style
  chicago   - Chicago citation style
  vancouver - Vancouver citation style
        """
    )

    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--sources",
        default="crossref",
        help="Comma-separated list of sources: pubmed,crossref,semanticscholar,arxiv (default: crossref)"
    )
    parser.add_argument(
        "--year",
        help="Year range (e.g., 2022-2025 or 2023-)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum results (default: 20)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "bibtex", "ris", "apa", "mla", "chicago", "vancouver"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (use '-' for stdout, default: stdout)"
    )
    parser.add_argument(
        "--email",
        default="research@example.com",
        help="Email for API polite pool"
    )

    args = parser.parse_args()

    # Parse year range
    year_start, year_end = None, None
    if args.year:
        parts = args.year.split("-")
        if len(parts) == 2:
            year_start = int(parts[0]) if parts[0] else None
            year_end = int(parts[1]) if parts[1] else None
        else:
            year_start = int(args.year)

    # Parse sources
    sources = [s.strip().lower() for s in args.sources.split(",")]

    # Search
    print(f"Searching: {args.query}", file=sys.stderr)
    print(f"Sources: {', '.join(sources)}", file=sys.stderr)
    if year_start or year_end:
        print(f"Year: {year_start or ''}-{year_end or ''}", file=sys.stderr)

    searcher = ScholarSearch(email=args.email)
    results = searcher.search(
        query=args.query,
        sources=sources,
        year_start=year_start,
        year_end=year_end,
        limit=args.limit,
    )

    print(f"Found {len(results)} papers", file=sys.stderr)

    # Format output
    try:
        output = format_papers(results, args.format)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    if args.output == "-" or args.output is None:
        print(output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
