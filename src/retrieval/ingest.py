"""
Ingest Script
Loads syllabuses.json and mock CS drive files into ChromaDB.

Run from project root:
    python src/retrieval/ingest.py
"""
import json
import os
import sys
from pathlib import Path

# Ensure project root is on the path so src.* imports work
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.vector_store import VectorStoreManager

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SYLLABUS_PATH = PROJECT_ROOT / "data" / "raw" / "syllabuses.json"
MOCK_DRIVE_DIR = PROJECT_ROOT / "data" / "mock_cs_drive"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(PROJECT_ROOT / "data" / "chroma_db"))

# ---------------------------------------------------------------------------
# Mock CS Drive documents (inline, supplemented by text files)
# ---------------------------------------------------------------------------
INLINE_MOCK_DOCS = [
    {
        "id": "mock_intro_cs_loops",
        "content": (
            "Introduction to CS - Loops and Iteration\n"
            "A loop allows repeated execution of code blocks. "
            "For loops iterate over sequences using range() or direct iteration. "
            "While loops run while a condition is true. "
            "break exits a loop early; continue skips to the next iteration. "
            "Nested loops multiply complexity. Common use cases: array traversal, "
            "counting, accumulation patterns."
        ),
        "metadata": {"type": "mock_doc", "topic": "loops", "source": "mock_cs_drive"},
    },
    {
        "id": "mock_intro_cs_recursion",
        "content": (
            "Introduction to CS - Recursion and Recursive Functions\n"
            "Recursion is when a function calls itself to solve a smaller subproblem. "
            "Requires a base case (termination condition) and a recursive case. "
            "Classic examples: factorial, Fibonacci, binary search, tree traversal. "
            "Each call adds a frame to the call stack. Deep recursion can cause stack overflow. "
            "Memoization caches results to avoid recomputation."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "recursion",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_data_structures",
        "content": (
            "Data Structures - Arrays, Stacks, Queues\n"
            "Arrays store elements in contiguous memory with O(1) random access. "
            "Stacks follow LIFO order (push/pop from top). Used in function call management, "
            "expression evaluation, undo operations. "
            "Queues follow FIFO order (enqueue at rear, dequeue from front). "
            "Used in BFS, scheduling, buffering. "
            "Python: list as stack; collections.deque as efficient queue."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "data_structures",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_algorithms_sorting",
        "content": (
            "Algorithms - Sorting\n"
            "Bubble sort: O(n²) — repeatedly swap adjacent out-of-order elements. "
            "Merge sort: O(n log n) stable divide-and-conquer. Split, sort halves, merge. "
            "Quick sort: O(n log n) average; partition around pivot. "
            "Selection sort: O(n²) — find minimum and place it. "
            "Insertion sort: O(n²) worst case but O(n) on nearly sorted data. "
            "Heap sort: O(n log n) in-place using a max-heap."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "sorting",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_oop",
        "content": (
            "Object-Oriented Programming - Classes and Objects\n"
            "OOP organises code around objects that bundle data (attributes) and behaviour (methods). "
            "Key principles: Encapsulation hides internal state. "
            "Inheritance allows a subclass to reuse and extend a superclass. "
            "Polymorphism lets different classes implement the same interface differently. "
            "Abstraction exposes only relevant details. "
            "Python syntax: class, __init__, self, super(). "
            "Special methods (__str__, __repr__, __eq__) enable operator overloading."
        ),
        "metadata": {"type": "mock_doc", "topic": "oop", "source": "mock_cs_drive"},
    },
    {
        "id": "mock_trees",
        "content": (
            "Data Structures - Trees\n"
            "A tree is a hierarchical data structure with a root node and subtrees of children. "
            "Binary trees have at most two children per node. "
            "Binary Search Trees (BST): left subtree < node < right subtree. "
            "Search, insert, delete: O(log n) average, O(n) worst (unbalanced). "
            "AVL trees and Red-Black trees maintain balance automatically. "
            "Traversals: in-order (sorted output for BST), pre-order, post-order, level-order (BFS)."
        ),
        "metadata": {"type": "mock_doc", "topic": "trees", "source": "mock_cs_drive"},
    },
    {
        "id": "mock_graphs",
        "content": (
            "Data Structures - Graphs\n"
            "A graph G=(V,E) consists of vertices V and edges E. "
            "Directed vs undirected; weighted vs unweighted. "
            "Representations: adjacency matrix O(V²) space; adjacency list O(V+E). "
            "BFS explores level by level using a queue — shortest path in unweighted graphs. "
            "DFS explores depth-first using a stack or recursion — cycle detection, topological sort. "
            "Dijkstra's algorithm finds shortest paths in weighted graphs with non-negative edges. "
            "Applications: networks, maps, dependency resolution."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "graphs",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_complexity",
        "content": (
            "Algorithm Analysis - Time and Space Complexity\n"
            "Big-O notation describes the upper bound on an algorithm's growth rate. "
            "Common classes: O(1) constant, O(log n) logarithmic, O(n) linear, "
            "O(n log n) linearithmic, O(n²) quadratic, O(2ⁿ) exponential. "
            "Analyse by counting the dominant operation as a function of input size n. "
            "Drop constants and lower-order terms. "
            "Space complexity measures auxiliary memory usage. "
            "Recursive algorithms have O(depth) call-stack space. "
            "Theta Θ gives a tight bound; Omega Ω gives a lower bound."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "complexity",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_functions_scope",
        "content": (
            "Introduction to CS - Functions and Scope\n"
            "Functions are named, reusable blocks of code defined with def. "
            "Parameters pass data in; return sends data out. "
            "Default parameters allow optional arguments. "
            "*args and **kwargs accept variable numbers of positional/keyword arguments. "
            "Scope rules (LEGB): Local → Enclosing → Global → Built-in. "
            "global and nonlocal keywords modify enclosing scope variables. "
            "Lambda expressions create anonymous one-line functions."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "functions",
            "source": "mock_cs_drive",
        },
    },
    {
        "id": "mock_pointers_memory",
        "content": (
            "Systems Programming - Pointers and Memory Management\n"
            "A pointer stores the memory address of another variable. "
            "Dereferencing a pointer accesses the value at that address. "
            "Dynamic memory allocation (malloc/free in C, new/delete in C++) places objects on the heap. "
            "Stack memory is automatically managed; heap memory is manually managed. "
            "Common bugs: dangling pointers (use after free), memory leaks (missing free), "
            "buffer overflows (writing past array bounds), null pointer dereference. "
            "Python manages memory automatically via reference counting and garbage collection."
        ),
        "metadata": {
            "type": "mock_doc",
            "topic": "pointers_memory",
            "source": "mock_cs_drive",
        },
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_mock_drive_files() -> list:
    """Load .txt files from data/mock_cs_drive/ as additional documents."""
    docs = []
    if not MOCK_DRIVE_DIR.exists():
        print(f"  [WARN] Mock CS drive directory not found: {MOCK_DRIVE_DIR}")
        return docs

    for txt_file in sorted(MOCK_DRIVE_DIR.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8")
        doc_id = f"file_{txt_file.stem}"
        docs.append(
            {
                "id": doc_id,
                "content": content,
                "metadata": {
                    "type": "mock_doc_file",
                    "topic": txt_file.stem,
                    "source": str(txt_file.name),
                },
            }
        )
        print(f"  Loaded mock file: {txt_file.name} ({len(content)} chars)")
    return docs


def ingest_syllabuses(store: VectorStoreManager) -> dict:
    """Load syllabuses.json and add course-level + topic-level documents."""
    with open(SYLLABUS_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    course_docs = []
    topic_docs = []
    skipped = 0

    for record in records:
        if not record.get("found") or not record.get("syllabus_text", "").strip():
            skipped += 1
            continue

        course_num = record.get("course_num", "unknown")
        course_name = record.get("course_name", "") or ""
        semester = record.get("semester", "") or ""
        lecturer = record.get("lecturer", "") or ""
        topics = record.get("topics", []) or []

        # Course-level document
        course_docs.append(
            {
                "id": f"course_{course_num}",
                "content": f"{course_name}\n\n{record['syllabus_text']}",
                "metadata": {
                    "type": "syllabus",
                    "course_num": course_num,
                    "course_name": course_name,
                    "semester": semester,
                    "lecturer": lecturer,
                    "topics_count": len(topics),
                    "source": f"BIU Syllabus - {course_name}",
                },
            }
        )

        # Topic-level chunks
        for idx, t in enumerate(topics):
            week = str(t.get("week", "?"))
            topic_text = t.get("topic", "").strip()
            if not topic_text:
                continue
            # Use idx to guarantee uniqueness even when week values repeat
            doc_id = f"{course_num}_w{week}_i{idx}"
            topic_docs.append(
                {
                    "id": doc_id,
                    "content": (
                        f"Course: {course_name}, Week {week}: {topic_text}"
                    ),
                    "metadata": {
                        "type": "syllabus_topic",
                        "course_num": course_num,
                        "course_name": course_name,
                        "week": week,
                        "semester": semester,
                        "source": f"{course_name} - Week {week} Syllabus",
                    },
                }
            )

    print(f"  Course docs: {len(course_docs)}")
    print(f"  Topic docs:  {len(topic_docs)}")
    print(f"  Skipped (no syllabus): {skipped}")

    store.add_documents(course_docs)
    store.add_documents(topic_docs)

    return {
        "course_docs": len(course_docs),
        "topic_docs": len(topic_docs),
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("ArmorAgent — Ingestion Pipeline")
    print("=" * 60)
    print(f"ChromaDB path : {CHROMA_DB_PATH}")
    print(f"Syllabus JSON : {SYLLABUS_PATH}")
    print()

    store = VectorStoreManager(db_path=CHROMA_DB_PATH)
    print(f"Collection count before ingest: {store.get_collection_count()}")
    print()

    # 1. Syllabuses
    print("[1/3] Ingesting syllabuses.json …")
    syllabus_stats = ingest_syllabuses(store)

    # 2. Inline mock docs
    print("\n[2/3] Ingesting inline mock CS drive documents …")
    store.add_documents(INLINE_MOCK_DOCS)
    print(f"  Inline mock docs: {len(INLINE_MOCK_DOCS)}")

    # 3. Mock drive text files
    print("\n[3/3] Loading mock CS drive text files …")
    file_docs = load_mock_drive_files()
    if file_docs:
        store.add_documents(file_docs)

    total = store.get_collection_count()
    print()
    print("=" * 60)
    print("Ingestion complete!")
    print(f"  Syllabus course docs : {syllabus_stats['course_docs']}")
    print(f"  Syllabus topic docs  : {syllabus_stats['topic_docs']}")
    print(f"  Inline mock docs     : {len(INLINE_MOCK_DOCS)}")
    print(f"  File mock docs       : {len(file_docs)}")
    print(f"  Total in collection  : {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
