from core.services.groq import generate_goal_solution

def generate_task_reply(task, history, user_message):
    context = f"""
You are a helpful study assistant.

TASK:
Title: {task.title}
Subject: {task.custom_subject or task.subject}
Type: {task.task_type}

CHAT HISTORY:
{history}

USER QUESTION:
{user_message}

Respond clearly, step-by-step if needed.
If assignment: guide more, don't just dump final answers unless asked.
"""

    return generate_goal_solution(context)
