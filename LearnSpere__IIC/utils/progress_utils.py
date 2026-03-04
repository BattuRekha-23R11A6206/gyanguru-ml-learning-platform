"""
Progress Tracking Utilities
Handles user progress tracking for the ML learning course
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# File paths
COURSE_STRUCTURE_FILE = 'data/course_structure.json'
USER_PROGRESS_FILE = 'data/user_progress.json'

def _now_iso() -> str:
    return datetime.now().isoformat()

def ensure_progress_file():
    """Ensure user progress file exists"""
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(USER_PROGRESS_FILE):
        with open(USER_PROGRESS_FILE, 'w') as f:
            json.dump({"user_progress": {}}, f, indent=2)

def load_course_structure():
    """Load course structure from JSON file"""
    try:
        with open(COURSE_STRUCTURE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def load_user_progress():
    """Load user progress from JSON file"""
    ensure_progress_file()
    try:
        with open(USER_PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"user_progress": {}}

def save_user_progress(progress_data):
    """Save user progress to JSON file"""
    ensure_progress_file()
    with open(USER_PROGRESS_FILE, 'w') as f:
        json.dump(progress_data, f, indent=2)

def get_user_progress(username: str) -> Dict:
    """Get progress for a specific user"""
    progress_data = load_user_progress()
    user_progress = progress_data.get("user_progress", {}).get(username, {})

    # Initialize progress if user doesn't exist
    if not user_progress:
        user_progress = {
            "username": username,
            "started_at": _now_iso(),
            "modules_completed": [],
            "topics_completed": [],
            "quiz_scores": {},
            "current_module": None,
            "current_topic": None,
            "total_time_spent": 0,
            "last_activity": _now_iso(),
            # Modality + interaction analytics
            "modality_usage": {  # counts of interactions by modality
                "text": 0,
                "code": 0,
                "audio": 0,
                "image": 0
            },
            "interaction_history": []  # append-only list of events (kept reasonably small elsewhere)
        }
        progress_data["user_progress"][username] = user_progress
        save_user_progress(progress_data)

    # Backfill new fields for existing users
    if "modality_usage" not in user_progress:
        user_progress["modality_usage"] = {"text": 0, "code": 0, "audio": 0, "image": 0}
    if "interaction_history" not in user_progress:
        user_progress["interaction_history"] = []

    return user_progress

def update_topic_progress(
    username: str,
    topic_id: str,
    completed: bool = True,
    time_spent: int = 0,
    modality: Optional[str] = None,
    event: str = "completed",
):
    """Update progress for a specific topic + log interaction metadata."""
    progress_data = load_user_progress()
    user_progress = get_user_progress(username)

    # Normalize modality to one of our known buckets
    modality_bucket = None
    if modality:
        modality_lower = str(modality).lower().strip()
        if modality_lower in ("text", "code", "audio", "image"):
            modality_bucket = modality_lower

    # Always accumulate time spent (non-negative) even if the topic was completed earlier
    try:
        time_spent_int = int(time_spent or 0)
    except (TypeError, ValueError):
        time_spent_int = 0
    if time_spent_int < 0:
        time_spent_int = 0

    user_progress["total_time_spent"] += time_spent_int

    if completed and topic_id not in user_progress["topics_completed"]:
        user_progress["topics_completed"].append(topic_id)

    user_progress["last_activity"] = _now_iso()

    # Update current topic
    user_progress["current_topic"] = topic_id

    # Track modality usage counts
    if modality_bucket:
        user_progress["modality_usage"][modality_bucket] = user_progress["modality_usage"].get(modality_bucket, 0) + 1

    # Log interaction event (cap list size to avoid unbounded growth)
    user_progress["interaction_history"].append({
        "ts": _now_iso(),
        "topic_id": topic_id,
        "event": event,
        "completed": bool(completed),
        "time_spent": time_spent_int,
        "modality": modality_bucket,
    })
    if len(user_progress["interaction_history"]) > 500:
        user_progress["interaction_history"] = user_progress["interaction_history"][-500:]

    # Check if module is completed
    course_structure = load_course_structure()
    if course_structure:
        for module in course_structure["course"]["modules"]:
            module_topics = [topic["id"] for topic in module["topics"]]
            if all(topic_id in user_progress["topics_completed"] for topic_id in module_topics):
                if module["id"] not in user_progress["modules_completed"]:
                    user_progress["modules_completed"].append(module["id"])

    # Update current module
    if user_progress["modules_completed"]:
        user_progress["current_module"] = user_progress["modules_completed"][-1]
    else:
        user_progress["current_module"] = course_structure["course"]["modules"][0]["id"] if course_structure else None

    progress_data["user_progress"][username] = user_progress
    save_user_progress(progress_data)

    return user_progress

def update_quiz_score(username: str, topic: str, score: float):
    """Update quiz score for a specific topic (and log errors if provided)."""
    progress_data = load_user_progress()
    user_progress = get_user_progress(username)

    user_progress["quiz_scores"][topic] = score
    user_progress["last_activity"] = _now_iso()

    # Track quiz analytics / error patterns
    if "error_patterns" not in user_progress:
        user_progress["error_patterns"] = {}
    topic_key = str(topic)
    topic_pattern = user_progress["error_patterns"].get(topic_key, {"attempts": 0, "failures": 0, "last_score": None})
    topic_pattern["attempts"] = int(topic_pattern.get("attempts", 0)) + 1
    topic_pattern["last_score"] = score
    if score < 70:
        topic_pattern["failures"] = int(topic_pattern.get("failures", 0)) + 1
    user_progress["error_patterns"][topic_key] = topic_pattern

    # Interaction history
    user_progress["interaction_history"].append({
        "ts": _now_iso(),
        "topic_id": topic_key,
        "event": "quiz_submitted",
        "score": score,
        "passed": score >= 70,
    })
    if len(user_progress["interaction_history"]) > 500:
        user_progress["interaction_history"] = user_progress["interaction_history"][-500:]

    progress_data["user_progress"][username] = user_progress
    save_user_progress(progress_data)

    return user_progress

def get_course_progress(username: str) -> Dict:
    """Get comprehensive course progress for a user"""
    user_progress = get_user_progress(username)
    course_structure = load_course_structure()

    if not course_structure:
        return {"error": "Course structure not found"}

    course = course_structure["course"]
    progress_summary = {
        "username": username,
        "course_title": course["title"],
        "total_modules": len(course["modules"]),
        "completed_modules": len(user_progress["modules_completed"]),
        "total_topics": sum(len(module["topics"]) for module in course["modules"]),
        "completed_topics": len(user_progress["topics_completed"]),
        "progress_percentage": 0,
        "current_module": user_progress["current_module"],
        "current_topic": user_progress["current_topic"],
        "total_time_spent": user_progress["total_time_spent"],
        "started_at": user_progress["started_at"],
        "last_activity": user_progress["last_activity"],
        "quiz_scores": user_progress["quiz_scores"],
        "modality_usage": user_progress.get("modality_usage", {}),
        "modules": []
    }

    # Calculate progress percentage
    if progress_summary["total_topics"] > 0:
        progress_summary["progress_percentage"] = round(
            (progress_summary["completed_topics"] / progress_summary["total_topics"]) * 100, 2
        )

    # Build module details
    for module in course["modules"]:
        module_progress = {
            "id": module["id"],
            "title": module["title"],
            "description": module["description"],
            "order": module["order"],
            "completed": module["id"] in user_progress["modules_completed"],
            "total_topics": len(module["topics"]),
            "completed_topics": 0,
            "topics": []
        }

        for topic in module["topics"]:
            topic_completed = topic["id"] in user_progress["topics_completed"]
            if topic_completed:
                module_progress["completed_topics"] += 1

            module_progress["topics"].append({
                "id": topic["id"],
                "title": topic["title"],
                "description": topic["description"],
                "content_type": topic["content_type"],
                "estimated_time": topic["estimated_time"],
                "completed": topic_completed,
                "prerequisites": topic["prerequisites"]
            })

        progress_summary["modules"].append(module_progress)

    return progress_summary

def get_next_topic(username: str) -> Optional[Dict]:
    """Get the next recommended topic for the user"""
    user_progress = get_user_progress(username)
    course_structure = load_course_structure()

    if not course_structure:
        return None

    # Adaptive rule: if the user failed the last quiz for the current topic,
    # recommend revisiting that topic before moving forward.
    try:
        current_topic_id = user_progress.get("current_topic")
        error_patterns = user_progress.get("error_patterns", {}) or {}
        if current_topic_id and current_topic_id in error_patterns:
            last_score = error_patterns.get(current_topic_id, {}).get("last_score")
            if last_score is not None and float(last_score) < 70:
                for module in course_structure["course"]["modules"]:
                    for topic in module["topics"]:
                        if topic.get("id") == current_topic_id:
                            return {
                                "topic": topic,
                                "module": {
                                    "id": module["id"],
                                    "title": module["title"],
                                },
                                "reason": "review_failed_quiz",
                            }
    except Exception:
        pass

    # Find the first incomplete topic in order
    for module in course_structure["course"]["modules"]:
        for topic in module["topics"]:
            if topic["id"] not in user_progress["topics_completed"]:
                # Check prerequisites
                prerequisites_met = all(
                    prereq in user_progress["topics_completed"]
                    for prereq in topic["prerequisites"]
                )
                if prerequisites_met:
                    return {
                        "topic": topic,
                        "module": {
                            "id": module["id"],
                            "title": module["title"]
                        }
                    }

    return None

def get_available_topics(username: str) -> List[Dict]:
    """Get all topics available for the user (completed prerequisites)"""
    user_progress = get_user_progress(username)
    course_structure = load_course_structure()

    if not course_structure:
        return []

    available_topics = []

    for module in course_structure["course"]["modules"]:
        for topic in module["topics"]:
            if topic["id"] not in user_progress["topics_completed"]:
                # Check prerequisites
                prerequisites_met = all(
                    prereq in user_progress["topics_completed"]
                    for prereq in topic["prerequisites"]
                )
                if prerequisites_met:
                    available_topics.append({
                        "topic": topic,
                        "module": {
                            "id": module["id"],
                            "title": module["title"]
                        }
                    })

    return available_topics

def reset_user_progress(username: str):
    """Reset all progress for a user"""
    progress_data = load_user_progress()
    if username in progress_data["user_progress"]:
        progress_data["user_progress"][username] = {
            "username": username,
            "started_at": datetime.now().isoformat(),
            "modules_completed": [],
            "topics_completed": [],
            "current_module": None,
            "current_topic": None,
            "total_time_spent": 0,
            "last_activity": datetime.now().isoformat()
        }
        save_user_progress(progress_data)

def get_module_for_topic(topic_id: str) -> str:
    """Get the module id that contains the given topic id"""
    course_structure = load_course_structure()
    for module in course_structure["course"]["modules"]:
        for topic in module["topics"]:
            if topic["id"] == topic_id:
                return module["id"]
    return None

def get_course_statistics() -> Dict:
    """Get overall course statistics"""
    progress_data = load_user_progress()
    course_structure = load_course_structure()

    if not course_structure:
        return {"error": "Course structure not found"}

    total_users = len(progress_data["user_progress"])
    total_topics = sum(len(module["topics"]) for module in course_structure["course"]["modules"])

    completed_topics = 0
    total_time_spent = 0
    completed_modules = 0

    for user_progress in progress_data["user_progress"].values():
        completed_topics += len(user_progress["topics_completed"])
        total_time_spent += user_progress["total_time_spent"]
        completed_modules += len(user_progress["modules_completed"])

    return {
        "total_users": total_users,
        "total_topics": total_topics,
        "total_modules": len(course_structure["course"]["modules"]),
        "completed_topics": completed_topics,
        "completed_modules": completed_modules,
        "total_time_spent": total_time_spent,
        "average_completion_rate": round((completed_topics / (total_users * total_topics)) * 100, 2) if total_users > 0 else 0
    }
