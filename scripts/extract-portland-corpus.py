#!/usr/bin/env python3

import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq


SECTION_FIELDS = [
    "ipfs_cid",
    "identifier",
    "title",
    "name",
    "text",
    "source_url",
    "official_cite",
    "bluebook_citation",
    "chapter",
    "jsonld",
]


def read_rows(path, columns=None):
    return pq.read_table(path, columns=columns).to_pylist()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_properties(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"raw": value}


def normalize_title_number(identifier):
    if not identifier:
        return ""
    marker = "Portland City Code "
    if identifier.startswith(marker):
        code = identifier[len(marker) :]
        return code.split(".", 1)[0]
    return ""


def extract_sections(corpus_root):
    rows = read_rows(corpus_root / "canonical" / "STATE-OR.parquet", SECTION_FIELDS)
    sections = []
    section_index = {}

    for index, row in enumerate(rows):
        cid = row["ipfs_cid"]
        section_index[cid] = index
        sections.append(
            {
                "ipfs_cid": cid,
                "identifier": row.get("identifier") or "",
                "title": row.get("title") or row.get("name") or "",
                "text": row.get("text") or "",
                "source_url": row.get("source_url") or "",
                "official_cite": row.get("official_cite") or "",
                "bluebook_citation": row.get("bluebook_citation") or "",
                "chapter": row.get("chapter") or "",
                "title_number": normalize_title_number(row.get("identifier") or ""),
                "jsonld": row.get("jsonld") or "",
            }
        )

    write_json(corpus_root / "generated" / "sections.json", sections)
    write_json(corpus_root / "generated" / "section-index.json", section_index)
    return sections


def extract_embeddings(corpus_root):
    rows = read_rows(
        corpus_root / "canonical" / "STATE-OR_embeddings.parquet",
        ["ipfs_cid", "embedding", "embedding_model", "embedding_backend"],
    )
    if not rows:
        raise ValueError("No embedding rows found")

    dimension = len(rows[0]["embedding"])
    cids = []
    vector_path = corpus_root / "generated" / "embeddings.f32"
    vector_path.parent.mkdir(parents=True, exist_ok=True)

    with vector_path.open("wb") as handle:
        for row in rows:
            embedding = row["embedding"]
            if len(embedding) != dimension:
                raise ValueError(f"Embedding dimension mismatch for {row['ipfs_cid']}")
            cids.append(row["ipfs_cid"])
            handle.write(struct.pack(f"<{dimension}f", *[float(value) for value in embedding]))

    write_json(
        corpus_root / "generated" / "embedding-index.json",
        {
            "schemaVersion": 1,
            "count": len(rows),
            "dimension": dimension,
            "embeddingModel": rows[0].get("embedding_model") or "thenlper/gte-small",
            "browserEmbeddingModel": "Xenova/gte-small",
            "binary": "embeddings.f32",
            "ipfs_cids": cids,
        },
    )


def extract_bm25(corpus_root):
    rows = read_rows(
        corpus_root / "canonical" / "STATE-OR_bm25.parquet",
        [
            "id",
            "document_id",
            "title",
            "document_length",
            "term_frequencies",
            "bm25_k1",
            "bm25_b",
            "bm25_avgdl",
            "bm25_document_count",
        ],
    )

    docs = []
    document_frequency = defaultdict(int)
    for row in rows:
        term_frequency_pairs = row.get("term_frequencies") or []
        terms = {}
        for pair in term_frequency_pairs:
            term = pair.get("term")
            if not term:
                continue
            terms[term] = int(pair.get("tf") or 0)
            document_frequency[term] += 1
        docs.append(
            {
                "id": row["id"],
                "document_id": row.get("document_id") or row["id"],
                "title": row.get("title") or "",
                "document_length": int(row.get("document_length") or 0),
                "terms": terms,
            }
        )

    first = rows[0] if rows else {}
    write_json(
        corpus_root / "generated" / "bm25-documents.json",
        {
            "schemaVersion": 1,
            "documents": docs,
            "documentFrequency": dict(document_frequency),
            "k1": float(first.get("bm25_k1") or 1.5),
            "b": float(first.get("bm25_b") or 0.75),
            "avgdl": float(first.get("bm25_avgdl") or 0),
            "documentCount": int(first.get("bm25_document_count") or len(docs)),
        },
    )


def extract_graph(corpus_root):
    entity_rows = read_rows(
        corpus_root / "canonical" / "STATE-OR_knowledge_graph_entities.parquet",
        ["id", "type", "label", "properties_json"],
    )
    relationship_rows = read_rows(
        corpus_root / "canonical" / "STATE-OR_knowledge_graph_relationships.parquet",
        ["id", "source", "target", "type", "properties_json"],
    )

    entities = [
        {
            "id": row["id"],
            "type": row.get("type") or "",
            "label": row.get("label") or "",
            "properties": parse_properties(row.get("properties_json")),
        }
        for row in entity_rows
    ]
    relationships = [
        {
            "id": row["id"],
            "source": row.get("source") or "",
            "target": row.get("target") or "",
            "type": row.get("type") or "",
            "properties": parse_properties(row.get("properties_json")),
        }
        for row in relationship_rows
    ]

    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for rel in relationships:
        compact = {"id": rel["id"], "type": rel["type"], "source": rel["source"], "target": rel["target"]}
        outgoing[rel["source"]].append(compact)
        incoming[rel["target"]].append(compact)

    write_json(corpus_root / "generated" / "entities.json", entities)
    write_json(corpus_root / "generated" / "relationships.json", relationships)
    write_json(
        corpus_root / "generated" / "graph-adjacency.json",
        {"schemaVersion": 1, "outgoing": dict(outgoing), "incoming": dict(incoming)},
    )


def extract_logic_summary(corpus_root):
    path = corpus_root / "logic_proofs" / "STATE-OR_logic_proof_artifacts.parquet"
    if not path.exists():
        return

    rows = read_rows(
        path,
        [
            "ipfs_cid",
            "identifier",
            "title",
            "formalization_scope",
            "fol_status",
            "deontic_status",
            "deontic_temporal_fol",
            "deontic_cognitive_event_calculus",
            "frame_logic_ergo",
            "norm_operator",
            "norm_type",
            "zkp_backend",
            "zkp_security_note",
            "zkp_verified",
        ],
    )
    summaries = []
    for row in rows:
        summaries.append(
            {
                "ipfs_cid": row["ipfs_cid"],
                "identifier": row.get("identifier") or "",
                "title": row.get("title") or "",
                "formalization_scope": row.get("formalization_scope") or "",
                "fol_status": row.get("fol_status") or "",
                "deontic_status": row.get("deontic_status") or "",
                "deontic_temporal_fol": row.get("deontic_temporal_fol") or "",
                "deontic_cognitive_event_calculus": row.get("deontic_cognitive_event_calculus") or "",
                "frame_logic_ergo": row.get("frame_logic_ergo") or "",
                "norm_operator": row.get("norm_operator") or "",
                "norm_type": row.get("norm_type") or "",
                "zkp_backend": row.get("zkp_backend") or "",
                "zkp_security_note": row.get("zkp_security_note") or "",
                "zkp_verified": bool(row.get("zkp_verified")),
            }
        )

    write_json(corpus_root / "generated" / "logic-proof-summaries.json", summaries)


def write_generated_manifest(corpus_root, sections):
    generated_root = corpus_root / "generated"
    files = sorted(
        {
            path.relative_to(corpus_root).as_posix(): path.stat().st_size
            for path in generated_root.glob("**/*")
            if path.is_file()
        }.items()
    )
    write_json(
        generated_root / "generated-manifest.json",
        {
            "schemaVersion": 1,
            "sectionCount": len(sections),
            "embeddingDimension": 384,
            "joinField": "ipfs_cid",
            "files": [{"path": file_path, "bytes": size} for file_path, size in files],
        },
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: extract-portland-corpus.py <corpus-root>")

    corpus_root = Path(sys.argv[1]).resolve()
    sections = extract_sections(corpus_root)
    extract_embeddings(corpus_root)
    extract_bm25(corpus_root)
    extract_graph(corpus_root)
    extract_logic_summary(corpus_root)
    write_generated_manifest(corpus_root, sections)
    print(f"Generated browser corpus assets in {corpus_root / 'generated'}")


if __name__ == "__main__":
    main()
