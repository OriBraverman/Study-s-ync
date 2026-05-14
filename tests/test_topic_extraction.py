import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'scraper'))

from syllabus_scraper import extract_weekly_topics


def test_extract_893311_table_format():
    """89-3311 uses a table format: number, date, multi-line topic."""
    text = """Abacus outline Lessons plan (Including active learning):

Lesson No.

Topic

Active learning

Required reading

Assessment

1

26.10.25

Introduction

About the class
Paradigms of programming languages

 

Logic Programming in Prolog 1:

Basic Prolog (Horn Clauses)
Backtracking
Unification

 

 

Chapter 4.4 of "Concepts in programming languages" by Mitchell

 

Chapters 1+2+3 Of "Programming in Prolog" by Clocksin and Mellish

 

2

2.11.25

Logic Programming in Prolog 2:

Resolution
Cut
Negation/closed world assumption

 

Chapter 4 Of "Programming in Prolog" by Clocksin and Mellish

 

Home assignment about Prolog

3

9.11.25

Functional Programming in ML 1:

Expressions
Types
Functions
Polymorphism
Currying

 

Chapters 1-5 Of "ML for the working programmar" by Paulson.

 

4

16.11.25

Fucntional Programming in ML 2:

Loops
Data Structures
Sums and Products
Variants
Lists
Tail recursion

 

Chapters 6+8 Of "ML for the working programmar" by Paulson.

 

 

 

5

23.11.25

Type Inference

The type inference problem
The Hindley–Milner Algorithm
Unification
Most general unifier
Extensions

 

Chapters 5.3 and 13 of "The Functional Approach to Programming"
Cornell CS3110 notes on type inference
Home assignment about ML

6

30.11.25

Closures

Semantics of ML
Evaluation rules
Dynamic Scoping
Static Scoping

 

Chapters 3 and 11 of "The Functional Approach to Programming"
 

7

7.12.25

Rust

Mutability
Datatypes, functions
Ownership
Pattern matching

 

 

Chapters 1 – 6 of

The Rust Programming Language

 

8

14.12.25

Operational Semantics

The While programming language
Semantics of expressions
Semantics of Statements
Properties

 

Chapters 1 and 2.1 of "Semantics with applications" by Nielson and Nielson

Home assignment about Rust and Semantics

9

28.12.25

Untyped Lamda calculus

Lambda terms
Booleans
Church numerals
Recursion
Substitutions
Evaluation order and strategies
Connection to ML

 

Chapter  5 of "Types and Programming Languages" by Pierce

 

10

4.1.26

Simply typed lambda calculus 1

Simple types
Type system
Derivations
Well-typed terms

 

Chapter  5,9 of "Types and Programming Languages" by Pierce

Home assignment about  Lambda calculus

11

11.1.26

Simply typed lambda calculus 2

Type safety
Normalization
Connection to major programming languages

 

Chapters  9,12 of "Types and Programming Languages" by Pierce

 

12

18.1.26

Linear Types

Extending the lambda calculus
Linear terms
Linear type system
Properties
Connection to rust

 

Chapter 1 of "Advanced Topics in Types and Programming Languages" by Walker (edited by Pierce)

 

13

25.1.26

Summary

Putting it all together
Verification

 

 

 

 

Additional Topics

If time permits

Correctness of functional programs
Axiomatic semantics
Formal verification
Primitive recursive functions

 

 

 

* There may be changes in the syllabus depending on learning progress and effectiveness

מטרות הקורס / תוצרי הלמידה
ידע
1.
2.
3.

מיומנויות
1.
2.

ערכים (במידה ולא רלוונטי ניתן למחוק)
1.
2.

למידה פעילה - תכנון מהלך השיעורים
מס'
השיעור	נושא השיעור	למידה פעילה	קריאה/צפיה נדרשת	הערכה תהליכית/מעצבת
1	 	למידה בקבוצות/ מרצה אורח.ת	 	 
2	 	 	 	 
3	 	 	 	 
"""

    topics = extract_weekly_topics(text)
    assert len(topics) == 13, f"Expected 13 topics, got {len(topics)}"
    assert topics[0]["week"] == "1"
    assert "Introduction" in topics[0]["topic"]
    assert "Paradigms of programming languages" in topics[0]["topic"]
    assert topics[4]["week"] == "5"
    assert "Type Inference" in topics[4]["topic"]
    assert topics[12]["week"] == "13"
    assert "Summary" in topics[12]["topic"]


def test_extract_89110_list_format():
    """89-110 uses a simple numbered list format."""
    text = """תכנית הוראה מפורטת:
מהלך השיעורים: (שיטות ההוראה ,שימוש בטכנולוגיה ,מרצים אורחים) הרצאות עם שקפים, תרגילי תכנות. זה קורס מבוא שמטרתו להקנות את המושגים הבסיסים והבנת שיטת החשיבה בעולם מדעי המחשב בכלל והתכנות בפרט, ולכן מהווה קורס יסוד להמשך התואר.
תכנית הוראה מפורטת לכל השיעורים:
הנושאים לא בהכרח יילמדו לפי הסדר המופיע ברשימה להלן, ויתכן (לפי התקדמות במהלך הסמסטר) שיתווספו נושאים לרשימה.
1 .ייצוג בבסיסים שונים, המרות בין בסיסים
2 .פעולות אריטמטיות ולוגיות בעולם הבינארי, ייצוג מספרים שליליים וFloating point
3.אופרטורים, תנאים וללואות
4 .פונקציות ומבחנים
5 .מערכים ומחרוזות, מבנה הזיכרון של התכנית
6 .מצביעים
7 .הקצאות זכרון דינאמיות
8 .פייתון, ושפות לא/מקומפלות בהכללה
9 .תכנות מודולרי, קבצים ותהליך הקומילציה
10 .מבני -נתונים בסיסיים
11 .ניתוח זמן ריצה של תוכנית
12 .אלגוריתמי מיון וסריקה בסיסיים
    מטרות הקורס / תוצרי הלמידה
"""

    topics = extract_weekly_topics(text)
    assert len(topics) == 12, f"Expected 12 topics, got {len(topics)}"
    assert topics[0]["week"] == "1"
    assert "ייצוג בבסיסים" in topics[0]["topic"]
    assert topics[11]["week"] == "12"
    assert "אלגוריתמי מיון" in topics[11]["topic"]


def test_does_not_extract_dates_as_topics():
    """Dates like 26.10.25 should not appear as topics."""
    text = """Lessons plan:
1
26.10.25
Introduction
2
2.11.25
Logic Programming
"""
    topics = extract_weekly_topics(text)
    assert len(topics) == 2
    assert topics[0]["topic"] == "Introduction"
    assert topics[1]["topic"] == "Logic Programming"
    for t in topics:
        assert "10.25" not in t["topic"]
        assert "11.25" not in t["topic"]
