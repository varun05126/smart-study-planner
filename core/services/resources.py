from django.db import transaction
from core.models import LearningTrack, Subject, Topic, Resource


# ==================================================
# CORE SAFE CREATOR
# ==================================================

def safe_get_or_create(model, **kwargs):
    obj, _ = model.objects.get_or_create(**kwargs)
    return obj


# ==================================================
# UNIVERSAL SUBJECT SEEDER ENGINE
# ==================================================

@transaction.atomic
def seed_subject_resources(track_name, subject_name, topics_dict, resources_list):
    """
    UNIVERSAL SEEDER ENGINE

    track_name     -> "Computer Science", "Chemistry", "Electronics"
    subject_name   -> "Web Development", "Organic Chemistry"
    topics_dict    -> { "HTML": "desc", "CSS": "desc" }
    resources_list -> [
        ("HTML", "HTML Full Course", "url", "video", "short desc"),
        ...
    ]
    """

    # 1. Track
    track = safe_get_or_create(
        LearningTrack,
        name=track_name,
        defaults={"description": f"{track_name} academic track"}
    )

    # 2. Subject
    subject = safe_get_or_create(
        Subject,
        track=track,
        name=subject_name
    )

    # 3. Topics
    topic_objects = {}
    for name, desc in topics_dict.items():
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            name=name,
            defaults={"description": desc}
        )
        topic_objects[name] = topic

    # 4. Resources
    for topic_name, title, url, rtype, short_desc in resources_list:
        Resource.objects.get_or_create(
            topic=topic_objects[topic_name],
            title=title,
            defaults={
                "url": url,
                "type": rtype,
                "short_description": short_desc,
                "is_best": True
            }
        )

    return subject


# ==================================================
# DSA
# ==================================================

def seed_dsa_resources():

    topics = {
        "Arrays": "Linear data structure storing elements",
        "Linked Lists": "Dynamic node-based structure",
        "Stacks": "LIFO structure",
        "Queues": "FIFO structure",
        "Trees": "Hierarchical structure",
        "Graphs": "Network structure",
        "Sorting Algorithms": "Sorting techniques",
        "Searching Algorithms": "Searching techniques",
        "Dynamic Programming": "Optimization techniques",
        "Recursion & Backtracking": "Divide and conquer problems"
    }

    resources = [
        ("Arrays", "Arrays – GeeksforGeeks", "https://www.geeksforgeeks.org/array-data-structure/", "article",
         "Learn fundamentals of arrays and operations."),
        ("Arrays", "Arrays – freeCodeCamp", "https://www.youtube.com/watch?v=QJNwK2uJyGs", "video",
         "Full beginner friendly array course."),

        ("Linked Lists", "Linked List – freeCodeCamp", "https://www.youtube.com/watch?v=Hj_rA0dhr2I", "video",
         "Complete linked list mastery."),

        ("Trees", "Trees – freeCodeCamp", "https://www.youtube.com/watch?v=oSWTXtMglKE", "video",
         "Binary trees, BSTs, traversals explained."),

        ("Graphs", "Graph Theory – Abdul Bari", "https://www.youtube.com/watch?v=pcKY4hjDrxk", "video",
         "Deep conceptual understanding of graphs."),

        ("Dynamic Programming", "DP – Aditya Verma", "https://www.youtube.com/watch?v=nqowUJzG-iM", "video",
         "Master problem solving patterns."),

        ("Arrays", "DSA Notes PDF", "https://www.vssut.ac.in/lecture_notes/lecture1423904941.pdf", "book",
         "Printable structured DSA notes."),
    ]

    return seed_subject_resources(
        "Computer Science",
        "Data Structures and Algorithms",
        topics,
        resources
    )


# ==================================================
# WEB DEVELOPMENT
# ==================================================

def seed_web_resources():

    topics = {
        "HTML": "Structure of web pages",
        "CSS": "Styling and layouts",
        "JavaScript": "Web interactivity",
        "Git & GitHub": "Version control",
        "React": "Frontend framework",
        "Backend Basics": "Server-side development",
        "Databases": "Data storage systems"
    }

    resources = [
        ("HTML", "HTML Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=pQN-pnXPaVg", "video",
         "Learn to build website structure."),
        ("CSS", "CSS Crash Course – Traversy", "https://www.youtube.com/watch?v=yfoY53QXEnI", "video",
         "Modern styling techniques."),
        ("JavaScript", "JavaScript Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=jS4aFq5-91M", "video",
         "Make websites interactive."),

        ("Git & GitHub", "Git & GitHub – freeCodeCamp", "https://www.youtube.com/watch?v=RGOj5yH7evk", "video",
         "Professional version control skills."),

        ("React", "React Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=bMknfKXIFA8", "video",
         "Frontend development with React."),

        ("Databases", "SQL Tutorial – freeCodeCamp", "https://www.youtube.com/watch?v=HXV3zeQKqGY", "video",
         "Databases for web applications."),

        ("HTML", "MDN Web Docs", "https://developer.mozilla.org/", "docs",
         "Official web development documentation."),
    ]

    return seed_subject_resources(
        "Computer Science",
        "Web Development",
        topics,
        resources
    )


# ==================================================
# SQL / DATABASES
# ==================================================

def seed_sql_resources():

    topics = {
        "SQL Basics": "Foundations of SQL",
        "Queries": "Filtering and aggregations",
        "Joins": "Multi-table operations",
        "Indexes": "Performance optimization",
        "Practice": "Hands-on problem solving"
    }

    resources = [
        ("SQL Basics", "SQL Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=HXV3zeQKqGY", "video",
         "Complete beginner SQL guide."),
        ("Queries", "W3Schools SQL", "https://www.w3schools.com/sql/", "docs",
         "Interactive SQL reference."),
        ("Practice", "LeetCode SQL", "https://leetcode.com/studyplan/top-sql-50/", "practice",
         "Interview level SQL problems."),
        ("Practice", "HackerRank SQL", "https://www.hackerrank.com/domains/sql", "practice",
         "Structured SQL practice path."),
    ]

    return seed_subject_resources(
        "Computer Science",
        "SQL & Databases",
        topics,
        resources
    )


# ==================================================
# AUTO SEEDER (BASED ON USER GOAL)
# ==================================================

def seed_resources_by_goal(goal_title):

    title = goal_title.lower()

    if "dsa" in title or "data structure" in title:
        return seed_dsa_resources()

    if "web" in title or "frontend" in title or "website" in title:
        return seed_web_resources()

    if "sql" in title or "database" in title:
        return seed_sql_resources()

    # Future plug-and-play
    # if "chem" in title:
    #     return seed_chemistry_resources()

    return None
