import json
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
LECTURES_DB_PATH = PROJECT_ROOT / "data" / "lectures_database.json"
MOCK_DRIVE_DIR = PROJECT_ROOT / "data" / "mock_cs_drive"

# Ensure output dir exists
os.makedirs(MOCK_DRIVE_DIR, exist_ok=True)

# 7 Real Lectures Data
real_lectures = [
    {
        "lecture_number": 1,
        "lecture_date": "2025-10-16",
        "topic": "מבני נתונים לינאריים וערימות",
        "json_source": "1 Elementary Data Structures.json",
        "hebrew_summary": (
            "הרצאה זו מציגה מבני נתונים בסיסיים ולינאריים לניהול קבוצות דינמיות. "
            "1. מערכים (Arrays): אחסון רציף בזיכרון, גישה אקראית בזמן $O(1)$ אך הכנסה/מחיקה בזמן $O(n)$ [שקופית 2]. "
            "2. מחסנית (Stack): מבנה נתונים בשיטת LIFO (Last-In, First-Out). פעולת הכנסה PUSH ומחיקה POP מבוצעות בראש המחסנית בזמן $O(1)$ [שקופית 7]. "
            "3. תור (Queue): מבנה נתונים בשיטת FIFO (First-In, First-Out). הכנסה ENQUEUE מבוצעת בזנב ומחיקה DEQUEUE מבוצעת בראש התור בזמן $O(1)$ [שקופית 9]. "
            "4. רשימה מקושרת (Linked List): איברים המקושרים באמצעות מצביעים, המאפשרים שינוי גודל דינמי בזמן $O(1)$ להכנסה/מחיקה וגישה בזמן $O(n)$ [שקופית 10]. "
            "5. ייצוג עצים מושרשים (Rooted Trees): ייצוג באמצעות שלושה מצביעים לכל צומת (אב, בן שמאלי, ואח ימני הבא) מאפשר להגיע לכל הבנים בזמן לינארי במספר הבנים [שקופית 12]. "
            "6. ערימה בינארית (Binary Heap): עץ בינארי כמעט מלא המקיים את תכונת הערימה (ערימת מקסימום: מפתח האב גדול או שווה למפתחות בניו). "
            "7. מיון ערימה (Heap Sort): בניית ערימה בזמן $O(n)$ וביצוע מחיקות חוזרות של איבר המקסימום למיון המערך בזמן של $O(n \\log n)$ במקרה הגרוע ביותר [שקופית 21]."
        ),
        "ai_questions": "שאל את הסטודנט מהו ההבדל המרכזי בין מחסנית לתור במונחים של סדר הכנסה והוצאה, וכיצד מיוצג עץ כללי באמצעות שני מצביעים בלבד לכל צומת.",
        "english_rag_text": (
            "Lecture 1: Elementary Data Structures & Heaps\n\n"
            "Key Concepts:\n"
            "1. Arrays: Contiguous memory allocation, O(1) random access, O(n) insert/delete.\n"
            "2. Stacks (LIFO): Last-In, First-Out dynamic set. INSERT is called PUSH, DELETE is called POP. "
            "Both operate on the top of the stack in O(1) time.\n"
            "3. Queues (FIFO): First-In, First-Out dynamic set. INSERT is ENQUEUE (at the tail), DELETE is DEQUEUE (at the head) in O(1) time.\n"
            "4. Linked Lists: Linearly ordered objects linked dynamically via pointers (memory addresses). Supports dynamic sizing.\n"
            "5. Rooted Tree Representation: Generalized linked list representation. Three pointers per node (parent, left-child, right-sibling) are sufficient to traverse all children in linear time.\n"
            "6. Binary Heaps: An array object visualized as a nearly complete binary tree. Max-Heap Property: parent key is >= children keys. Min-Heap Property: parent key is <= children keys.\n"
            "7. Heap Sort: Algorithm that builds a max-heap in O(n) time, then repeatedly extracts the maximum element and restores the heap property. Runs in O(n log n) time in-place."
        )
    },
    {
        "lecture_number": 2,
        "lecture_date": "2025-10-23",
        "topic": "רקורסיה, סיבוכיות ומשפט המאסטר",
        "json_source": "2 Functions and Recursions.json",
        "hebrew_summary": (
            "הרצאה זו מוקדשת לניתוח אסימפטוטי של פונקציות ופתרון משוואות נסיגה (Recurrences) הנובעות מאלגוריתמי רקורסיה והפרד ומשול. "
            "1. קצב גידול של פונקציות: הגדרת חסמים אסימפטוטיים: $O(g(n))$ חסם עליון, $\\Omega(g(n))$ חסם תחתון, ו-$\\Theta(g(n))$ חסם הדוק אסימפטוטית [שקופית 2]. "
            "2. גישת הפרד ומשול (Divide-and-Conquer): חלוקת הבעיה לתת-בעיות קטנות יותר מאותו סוג, פתרון רקורסיבי שלהן, ומיזוג הפתרונות לפתרון הבעיה המקורית [שקופית 10]. "
            "3. בעיית תת-המערך המקסימלי (Maximum Subarray): פתרון בשיטת הפרד ומשול בזמן $O(n \\log n)$ בהשוואה לפתרון נאיבי של $O(n^2)$ [שקופית 11]. "
            "4. פתרון משוואות נסיגה: "
            "א. שיטת ההצבה (Substitution Method): ניחוש חסם והוכחתו באמצעות אינדוקציה מתמטית [שקופית 18]. "
            "ב. משפט המאסטר (Master Theorem): כלי שימושי לפתרון משוואות מהצורה $T(n) = aT(n/b) + f(n)$ עבור קבועים $a \\ge 1, b > 1$. המשפט מציג 3 מקרים בהתאם להשוואה בין $f(n)$ לבין $n^{\\log_b a}$ [שקופית 21]. "
            "ג. משוואות רקורסיה לינאריות (Linear Recurrences): שיטות לפתרון משוואות לינאריות הומוגניות ולא-הומוגניות עם מקדמים קבועים באמצעות פולינום אופייני [שקופית 31]."
        ),
        "ai_questions": "שאל את הסטודנט מהם שלושת המקרים של משפט המאסטר, וכיצד הוא ינתח בעזרתם את סיבוכיות זמן הריצה של מיון מיזוג.",
        "english_rag_text": (
            "Lecture 2: Functions, Complexity, and Recurrences\n\n"
            "Key Concepts:\n"
            "1. Asymptotic Notations: O (Upper bound), Omega (Lower bound), and Theta (Tight asymptotic bound).\n"
            "2. Divide-and-Conquer: Split the problem into smaller subproblems of the same type, conquer recursively, and combine solutions. Example: Maximum Subarray Problem solved in O(n log n).\n"
            "3. Substitution Method for Recurrences: Guess the mathematical form of the solution, then use mathematical induction to find constants and prove the bound.\n"
            "4. Master Theorem: Solves recurrences of the form T(n) = aT(n/b) + f(n) where a >= 1 and b > 1.\n"
            "   - Case 1: If f(n) = O(n^(log_b(a) - epsilon)), then T(n) = Theta(n^(log_b a)).\n"
            "   - Case 2: If f(n) = Theta(n^(log_b a)), then T(n) = Theta(n^(log_b a) log n).\n"
            "   - Case 3: If f(n) = Omega(n^(log_b(a) + epsilon)) and satisfies the regularity condition (a*f(n/b) <= c*f(n) for c < 1), then T(n) = Theta(f(n)).\n"
            "5. Linear Recurrence Equations: Solution to homogeneous and nonhomogeneous linear recurrences with constant coefficients using characteristic polynomials."
        )
    },
    {
        "lecture_number": 3,
        "lecture_date": "2025-10-30",
        "topic": "עצי חיפוש בינאריים ועצי AVL",
        "json_source": "3 Search Trees.json",
        "hebrew_summary": (
            "הרצאה זו מציגה את מבנה הנתונים עץ חיפוש בינארי (BST) ומרחיבה לעצי חיפוש מאוזנים עצמאית (AVL). "
            "1. תכונת עץ החיפוש הבינארי (BST Property): לכל צומת $x$, המפתחות בתת-העץ השמאלי של $x$ קטנים או שווים ל-$x.key$, והמפתחות בתת-העץ הימני גדולים או שווים ל-$x.key$ [שקופית 3]. "
            "2. סריקה בסדר תוכי (Inorder Traversal): מאפשרת לדווח ולבקר בכל מפתחות העץ בצורה ממוינת בזמן לינארי $\\Theta(n)$ [שקופית 4]. "
            "3. שאילתות על BST: חיפוש (Search), מציאת מינימום/מקסימום, ומציאת עוקב (Successor) וקודם (Predecessor) בזיכרון, כולן רצות בזמן $O(h)$ כאשר $h$ הוא גובה העץ [שקופית 7]. "
            "4. עדכונים: פעולות הכנסה (Insertion) ומחיקה (Deletion) השומרות על תכונת ה-BST בזמן $O(h)$ [שקופית 21]. "
            "5. עצי AVL: עץ חיפוש בינארי המאזן את עצמו. לכל צומת, הפרש הגבהים בין תת-העץ הימני לשמאלי (גורם האיזון Balance Factor) הוא לכל היותר $1$. "
            "גובה עץ AVL עם $n$ צמתים חסום על ידי $h = O(\\log n)$ [שקופית 33]. "
            "6. איזון העץ: פעולות סיבוב יחיד (Single Rotation) וסיבוב כפול (Double Rotation) מתבצעות בזמן $O(1)$ לשיקום איזון ה-AVL לאחר הכנסה או מחיקה [שקופית 35]."
        ),
        "ai_questions": "בקש מהסטודנט להסביר מהו 'עוקב' (successor) של צומת בעץ חיפוש בינארי, וכיצד משרתים איזוני ה-AVL (סיבובים) לשמירה על גובה אופטימלי.",
        "english_rag_text": (
            "Lecture 3: Binary Search Trees & AVL Trees\n\n"
            "Key Concepts:\n"
            "1. Binary Search Tree (BST) Property: For any node x, keys in its left subtree are <= x.key, and keys in its right subtree are >= x.key.\n"
            "2. Inorder Tree Walk: Prints BST keys in sorted order. Time complexity is Theta(n).\n"
            "3. BST Queries (Search, Min, Max, Successor, Predecessor): All query operations run in O(h) time, where h is the height of the tree.\n"
            "   - Successor: The node with the smallest key greater than x.key. If right subtree exists, it's the minimum of that subtree. Otherwise, it's the lowest ancestor whose left child is also an ancestor.\n"
            "4. BST Insert/Delete: Operates in O(h) time. Deletion has three cases: node has no children, node has one child, or node has two children (replaced by its successor).\n"
            "5. AVL Trees: Height-balanced BST. For every node, the height difference between left and right subtrees is at most 1. Height is strictly bounded at h < 1.44 log2(n) = O(log n).\n"
            "6. Rotations: O(1) operations (Left Rotate, Right Rotate) used to restore AVL balance after insertion or deletion."
        )
    },
    {
        "lecture_number": 4,
        "lecture_date": "2025-11-06",
        "topic": "אלגוריתמי מיון וחסמים",
        "json_source": "4 Sorting.json",
        "hebrew_summary": (
            "הרצאה זו מנתחת את מגבלות התיאורטיות של מיונים מבוססי השוואה ומציגה מיונים מהירים בזמן לינארי. "
            "1. חסם תחתון למיונים מבוססי השוואה: שימוש במודל עץ החלטות (Decision Trees) מוכיח כי כל אלגוריתם מיון המבוסס על השוואות בלבד דורש לפחות $\\Omega(n \\log n)$ השוואות במקרה הגרוע ביותר [שקופית 3]. "
            "2. מיון מיזוג (Merge Sort): אלגוריתם יציב בשיטת הפרד ומשול הרץ בזמן אופטימלי של $\\Theta(n \\log n)$ [שקופית 6]. "
            "3. מיונים בזמן לינארי: אלגוריתמים שאינם מבוססים על השוואות ועוקפים את החסם התחתון תחת הנחות ספציפיות על הקלט: "
            "א. מיון מנייה (Counting Sort): מניח ש-$n$ איברי הקלט הם שלמים בטווח $[0..k]$. רץ בזמן $O(n+k)$ ויציב אסימפטוטית [שקופית 8]. "
            "ב. מיון בסיס (Radix Sort): ממיין מספרים בעלי $d$ ספרות מהספרה הפחות משמעותית למשמעותית ביותר באמצעות מיון יציב (כמו Counting Sort). רץ בזמן $O(d(n+k))$ [שקופית 9]. "
            "ג. מיון דליים (Bucket Sort): מניח התפלגות אחידה של הקלט בקטע $[0..1)$. מחלק את האיברים ל-$n$ דליים, ממיין כל דלי בנפרד וממזג. רץ בזמן ממוצע של $\\Theta(n)$ [שקופית 10]."
        ),
        "ai_questions": "שאל את הסטודנט מדוע לא ניתן למיין בשיטת השוואות בזמן טוב יותר מ-$\Omega(n \\log n)$ במקרה הגרוע, ובאילו תנאים Counting Sort מאפשר מיון בזמן לינארי.",
        "english_rag_text": (
            "Lecture 4: Sorting Lower Bounds & Linear-Time Sorting\n\n"
            "Key Concepts:\n"
            "1. Comparison-based Sorting Lower Bound: In the decision-tree model, any comparison-based sort requires Omega(n log n) comparisons in the worst case because a binary tree with >= n! leaves must have height >= log(n!) = Omega(n log n).\n"
            "2. Linear-Time Non-Comparison Sorting:\n"
            "   - Counting Sort: Assumes keys are integers in the range [0..k]. Uses temporary and output arrays to place elements directly in sorted order. Stable, runs in O(n+k) time.\n"
            "   - Radix Sort: Sorts multi-digit numbers digit-by-digit starting from Least Significant Digit (LSD) to Most Significant Digit (MSD). Requires a stable sorting helper (like Counting Sort). Runs in O(d(n+k)) time.\n"
            "   - Bucket Sort: Assumes input is uniformly distributed in the interval [0, 1). Divides the interval into n equal-sized buckets, distributes keys, sorts each bucket, and concatenates. Runs in linear average-case time Theta(n)."
        )
    },
    {
        "lecture_number": 5,
        "lecture_date": "2025-11-13",
        "topic": "תכנות דינמי ובעיית חיתוך המוט",
        "json_source": "5 Dynamic Programming.json",
        "hebrew_summary": (
            "הרצאה זו מציגה את פרדיגמת תכנות דינמי (Dynamic Programming) לפתרון בעיות אופטימיזציה בעלות תת-בעיות חופפות. "
            "1. בעיית חיתוך המוט (Rod Cutting): מציאת הדרך הרווחית ביותר לחתוך מוט באורך $n$ בהינתן מחירון לכל אורך. פתרון רקורסיבי נאיבי רץ בזמן אקספוננציאלי $O(2^n)$ בשל חישובים חוזרים ונשנים [שקופית 2]. "
            "2. עקרונות התכנות הדינמי: א. תת-בעיות חופפות (Overlapping Subproblems). ב. תשתית אופטימלית (Optimal Substructure) - פתרון אופטימלי לבעיה מורכב מפתרונות אופטימליים לתת-בעיותיה. "
            "3. פתרונות תכנות דינמי: "
            "א. גישת מלמעלה-למטה עם זיכרון (Top-down with Memoization): פתרון רקורסיבי תוך שמירת תוצאות במערך למניעת חישוב כפול בזמן $O(n^2)$ [שקופית 6]. "
            "ב. גישת מלמטה-למעלה (Bottom-up Solution): פתרון איטרטיבי מהתת-בעיות הקטנות לגדולות ביותר בזמן $O(n^2)$ תוך חיסכון בתקורה של רקורסיה [שקופית 8]. "
            "4. שחזור הפתרון האופטימלי (Solution Reconstruction): שמירת טבלה נוספת של החלטות החיתוך האופטימליות מאפשרת לשחזר את אורכי החיתוך עצמם ולא רק את הרווח המרבי [שקופית 9]."
        ),
        "ai_questions": "בקש מהסטודנט להסביר מהו ההבדל בין גישת Bottom-up לגישת Top-down עם Memoization בתכנות דינמי, וכיצד משחזרים את הפתרון האופטימלי עצמו ולא רק את ערכו.",
        "english_rag_text": (
            "Lecture 5: Dynamic Programming & Rod Cutting\n\n"
            "Key Concepts:\n"
            "1. Dynamic Programming (DP) Paradigm: Applied to optimization problems with overlapping subproblems and optimal substructure.\n"
            "2. Rod Cutting Problem: Given a rod of length n and a price table p_i for pieces of length i, find the maximum revenue r_n obtainable by cutting the rod.\n"
            "   - Naive Recursive Solution: T(n) = O(2^n) because it repeatedly recalculates the same subproblems.\n"
            "3. DP Approaches:\n"
            "   - Top-down with Memoization: Solves recursively but saves each subproblem's result in a lookup table. Runs in O(n^2) time.\n"
            "   - Bottom-up: Solves subproblems in size order (smallest first), avoiding recursion overhead. Runs in O(n^2) time.\n"
            "4. Reconstruction of Optimal Solution: By keeping a choice array s[i] representing the optimal size of the first piece cut from a rod of length i, we can reconstruct the exact cuts in O(n) time."
        )
    },
    {
        "lecture_number": 6,
        "lecture_date": "2025-11-20",
        "topic": "אלגוריתמים חמדניים ובעיית בחירת הפעילויות",
        "json_source": "6 Greedy Algorithms.json",
        "hebrew_summary": (
            "הרצאה זו מציגה את שיטת העיצוב של אלגוריתמים חמדניים (Greedy Algorithms) הבוחרת בכל שלב את האפשרות הטובה ביותר באותו רגע. "
            "1. בעיית בחירת הפעילויות (Activity Selection): תזמון מספר מקסימלי של פעילויות שאינן חופפות בחדר הרצאות יחיד. אסטרטגיה חמדנית של בחירת הפעילות שמסתיימת ראשונה מוכחת כמניבה פתרון אופטימלי גלובלי בזמן $O(n \\log n)$ [שקופית 3]. "
            "2. רכיבי האסטרטגיה החמדנית: "
            "א. תכונת הבחירה החמדנית (Greedy Choice Property): ניתן להגיע לפתרון אופטימלי גלובלי על ידי בחירות מקומיות אופטימליות. "
            "ב. תת-מבנה אופטימלי (Optimal Substructure): פתרון אופטימלי לבעיה מכיל בתוכו פתרונות אופטימליים לתת-הבעיות [שקופית 8]. "
            "3. תכנות דינמי לעומת חמדנות: השוואה באמצעות בעיית התרמיל (Knapsack Problem). "
            "א. בעיית התרמיל השביר (Fractional Knapsack): ניתן לקחת חלקי מוצרים, ולכן פתרון חמדני לפי יחס ערך/משקל מניב פתרון אופטימלי. "
            "ב. בעיית התרמיל השלם (0-1 Knapsack): לא ניתן לקחת חלקי מוצרים. פתרון חמדני נכשל ויש לפתור באמצעות תכנות דינמי [שקופית 9]."
        ),
        "ai_questions": "שאל את הסטודנט מהו ההבדל המרכזי בין בעיית התרמיל השלם (0-1 Knapsack) לבעיית התרמיל השביר (Fractional Knapsack) ומדוע רק אחת מהן ניתנת לפתרון חמדני.",
        "english_rag_text": (
            "Lecture 6: Greedy Algorithms & Activity Selection\n\n"
            "Key Concepts:\n"
            "1. Greedy Choice Property: A globally optimal solution can be arrived at by making locally optimal (greedy) choices without looking ahead or recalculating past decisions.\n"
            "2. Activity Selection Problem: Select the maximum number of mutually compatible activities in a single shared resource. Greedy strategy: sort activities by finish time, always choose the earliest finishing compatible activity. Runs in O(n log n) time and is proven optimal.\n"
            "3. Optimal Substructure: Required for both DP and Greedy algorithms. The optimal solution contains optimal solutions to subproblems.\n"
            "4. Knapsack Problems Comparison:\n"
            "   - Fractional Knapsack: Can take fractions of items. Greedy strategy based on highest value-per-weight ratio yields optimal solution in O(n log n).\n"
            "   - 0-1 Knapsack: Items must be taken whole. Greedy strategy fails. Requires Dynamic Programming with running time O(n W)."
        )
    },
    {
        "lecture_number": 7,
        "lecture_date": "2025-11-27",
        "topic": "סריקת גרפים ואלגוריתמי מסלול קצר ביותר",
        "json_source": "7 Exploring Graphs.json",
        "hebrew_summary": (
            "הרצאה זו מציגה ייצוגי גרפים בזיכרון, שיטות סריקה ואלגוריתמים למציאת מסלולים קצרים ביותר. "
            "1. ייצוג גרפים: רשימת סמיכויות (Adjacency List) חסכונית במקום $O(V+E)$ לעומת מטריצת סמיכויות (Adjacency Matrix) עם גישה מהירה של $O(1)$ במחיר $O(V^2)$ מקום [שקופית 2]. "
            "2. אלגוריתמי סריקה: "
            "א. חיפוש לרוחב (BFS): סורק שכבה אחר שכבה בעזרת תור (Queue) ומחשב מסלולים קצרים ביותר בגרף לא משוקלל בזמן $O(V+E)$ [שקופית 3]. "
            "ב. חיפוש לעומק (DFS): חוקר לאורך הענפים בעזרת רקורסיה/מחסנית, שימושי למיונים טופולוגיים וזיהוי רכיבים קשירים [שקופית 4]. "
            "3. מסלול קצר ביותר ממקור יחיד (Single-Source Shortest Paths): "
            "א. אלגוריתם דייקסטרה (Dijkstra's Algorithm): מניח משקלים אי-שליליים בלבד. משתמש בתור קדימויות ומשיג זמן ריצה של $O(E \\log V)$ בעזרת ערימה [שקופית 5]. "
            "ב. אלגוריתם בלמן-פורד (Bellman-Ford): מתאים למשקלים שליליים, מבצע הקלה (Relaxation) של כל הקשתות $V-1$ פעמים, ומזהה מעגלים שליליים בזמן $O(VE)$ [שקופית 6]. "
            "4. מסלולים קצרים בין כל הזוגות (All-Pairs Shortest Paths): "
            "אלגוריתם פלויד-וורשל (Floyd-Warshall) העובד בשיטת תכנות דינמי ומחשב מרחקים בין כל הזוגות בגרף בזמן הדוק של $\\Theta(V^3)$ [שקופית 7]."
        ),
        "ai_questions": "שאל את הסטודנט מתי נעדיף להשתמש באלגוריתם בלמן-פורד על פני דייקסטרה למציאת מסלולים קצרים ביותר, וכיצד בלמן-פורד מזהה מעגלים שליליים.",
        "english_rag_text": (
            "Lecture 7: Graph Exploration & Shortest Paths\n\n"
            "Key Concepts:\n"
            "1. Graph Representations: Adjacency List (space O(V+E), efficient for sparse graphs) vs Adjacency Matrix (space O(V^2), O(1) edge check).\n"
            "2. Search Algorithms:\n"
            "   - Breadth-First Search (BFS): Explores nodes level-by-level using a Queue. Computes single-source shortest paths on unweighted graphs in O(V+E).\n"
            "   - Depth-First Search (DFS): Explores recursively along branches, records discovery/finish times. Used for topological sort and cycle detection.\n"
            "3. Single-Source Shortest Paths:\n"
            "   - Dijkstra's Algorithm: Requires non-negative edge weights. Greedy strategy using a Min-Priority Queue. Runs in O(E log V) time with binary heaps.\n"
            "   - Bellman-Ford Algorithm: Handles negative weights, detects negative weight cycles. Runs in O(V E) time by relaxing all edges V-1 times.\n"
            "4. All-Pairs Shortest Paths:\n"
            "   - Floyd-Warshall Algorithm: Dynamic programming bottom-up algorithm. Runs in Theta(V^3) time using three nested loops."
        )
    }
]

def get_slide_text(json_source_name) -> str:
    """קריאת תוכן השקופיות מקובץ ה-JSON המקביל וסידורו כטקסט קריא."""
    json_path = PROJECT_ROOT / "json_outputs" / json_source_name
    if not json_path.exists():
        print(f"  [WARN] Slide JSON not found: {json_path}")
        return ""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            slides = json.load(f)
        
        lines = []
        for slide in slides:
            # מפתח מספר עמוד או שקופית
            page = slide.get("slide_number") or slide.get("page_number") or "?"
            content = slide.get("content", "").strip()
            if content:
                # ניקוי רווחים מיותרים
                clean_lines = [l.strip() for l in content.split("\n") if l.strip()]
                lines.append(f"[שקופית {page}]\n" + "\n".join(clean_lines))
        return "\n\n".join(lines)
    except Exception as e:
        print(f"  [ERROR] Failed to load slide content from {json_source_name}: {e}")
        return ""

def main():
    print("=" * 60)
    print("Study[S]ync - Lecture Integration Script")
    print("=" * 60)
    
    # 1. Update lectures_database.json
    if not LECTURES_DB_PATH.exists():
        print(f"[ERROR] Lectures database not found at {LECTURES_DB_PATH}")
        return

    print("Loading lectures_database.json ...")
    with open(LECTURES_DB_PATH, "r", encoding="utf-8") as f:
        lectures = json.load(f)

    print(f"Original database contains {len(lectures)} entries.")
    
    # Remove existing "אלגוריתמים ומבני נתונים 1" entries to prevent duplication
    original_count = len(lectures)
    lectures = [l for l in lectures if l.get("course_name") != "אלגוריתמים ומבני נתונים 1"]
    print(f"Removed {original_count - len(lectures)} old entries for Algorithms & Data Structures 1.")

    # Add the 7 new real lectures with actual slide contents
    rag_file_mappings = []
    
    for rl in real_lectures:
        actual_slides = get_slide_text(rl["json_source"])
        
        # Combine Hebrew summary with actual slide content for display in the UI
        db_content = rl["hebrew_summary"]
        if actual_slides:
            db_content += "\n\n--- תוכן המצגת (שקופיות) ---\n\n" + actual_slides
            
        new_entry = {
            "course_name": "אלגוריתמים ומבני נתונים 1",
            "lecture_number": rl["lecture_number"],
            "lecture_date": rl["lecture_date"],
            "topic": rl["topic"],
            "content": db_content,
            "ai_questions": rl["ai_questions"]
        }
        lectures.append(new_entry)
        # Safe ASCII prints
        print(f"Added Lecture {rl['lecture_number']} ({rl['lecture_date']}) with slide text ({len(actual_slides)} chars)")

        # Prepare RAG text content (English summary + full slide content)
        rag_text = rl["english_rag_text"]
        if actual_slides:
            rag_text += "\n\n--- FULL SLIDE PRESENTATION CONTENT ---\n\n" + actual_slides
            
        # Map to filename based on lecture index
        filename_map = {
            1: "data_structures_elementary.txt",
            2: "algorithms_recursion.txt",
            3: "algorithms_search_trees.txt",
            4: "algorithms_sorting_bounds.txt",
            5: "algorithms_dynamic_programming.txt",
            6: "algorithms_greedy.txt",
            7: "algorithms_graphs.txt",
        }
        filename = filename_map[rl["lecture_number"]]
        rag_file_mappings.append((filename, rag_text))

    # Save back LECTURES_DB_PATH
    print(f"Saving {len(lectures)} entries back to {LECTURES_DB_PATH} ...")
    with open(LECTURES_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(lectures, f, ensure_ascii=False, indent=2)
    print("[OK] data/lectures_database.json updated successfully!")

    # 2. Write RAG text files to data/mock_cs_drive/
    print("\nWriting RAG text files to data/mock_cs_drive/ ...")
    
    for filename, content in rag_file_mappings:
        file_path = MOCK_DRIVE_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Written {filename} ({len(content)} chars)")

    print("\nIntegration script completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
