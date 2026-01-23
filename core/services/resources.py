from core.models import LearningTrack, Subject, Topic, Resource


def seed_dsa_resources():
    """
    Safely seeds DSA learning structure.
    Will never violate foreign keys.
    Can be called multiple times.
    """

    # 1. Track
    track, _ = LearningTrack.objects.get_or_create(
        name="Computer Science",
        defaults={"description": "Core computer science fundamentals"}
    )

    # 2. Subject
    subject, _ = Subject.objects.get_or_create(
        track=track,
        name="Data Structures and Algorithms"
    )

    # 3. Topics
    topics = {
        "Arrays": "Linear data structure storing elements in contiguous memory",
        "Linked Lists": "Dynamic linear data structure with nodes",
        "Stacks & Queues": "LIFO and FIFO based structures",
        "Trees": "Hierarchical data structures",
        "Graphs": "Network-based data structures",
        "Sorting Algorithms": "Bubble, Merge, Quick, Heap sorting",
        "Searching Algorithms": "Linear and Binary search",
        "Dynamic Programming": "Optimization-based problem solving",
    }

    topic_objects = {}
    for name, desc in topics.items():
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            name=name,
            defaults={"description": desc}
        )
        topic_objects[name] = topic

    # 4. Resources
    resources = [
        ("Arrays", "Arrays in DSA – GeeksforGeeks", "https://www.geeksforgeeks.org/array-data-structure/", "article"),
        ("Linked Lists", "Linked List Full Course – freeCodeCamp", "https://www.youtube.com/watch?v=Hj_rA0dhr2I", "video"),
        ("Stacks & Queues", "Stacks & Queues – GeeksforGeeks", "https://www.geeksforgeeks.org/stack-data-structure/", "article"),
        ("Trees", "Trees in DSA – freeCodeCamp", "https://www.youtube.com/watch?v=oSWTXtMglKE", "video"),
        ("Graphs", "Graph Theory – Abdul Bari", "https://www.youtube.com/watch?v=pcKY4hjDrxk", "video"),
        ("Sorting Algorithms", "Sorting Algorithms Visualized", "https://visualgo.net/en/sorting", "article"),
        ("Searching Algorithms", "Binary Search – CS Dojo", "https://www.youtube.com/watch?v=P3YID7liBug", "video"),
        ("Dynamic Programming", "Dynamic Programming – Aditya Verma", "https://www.youtube.com/watch?v=nqowUJzG-iM", "video"),
    ]

    for topic_name, title, url, rtype in resources:
        Resource.objects.get_or_create(
            topic=topic_objects[topic_name],
            title=title,
            defaults={
                "url": url,
                "type": rtype,
                "is_best": True
            }
        )