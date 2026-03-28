import os
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import Question

def cleanup_questions():
    print("Starting cleanup of existing questions...")
    questions = Question.objects.all()
    count = 0
    
    for q in questions:
        raw = q.correct_answer
        # Clean common prefixes like "wer: ", "Ans: ", etc.
        cleaned = re.sub(r'^(?:wer|answ|ans|answer|correct)\b\s*[:.\-]?\s*', '', raw, flags=re.IGNORECASE)
        
        if cleaned != raw:
            q.correct_answer = cleaned
            q.save()
            print(f"Fixed Q {q.id}: '{raw}' -> '{cleaned}'")
            count += 1
            
    print(f"Cleanup complete! Fixed {count} questions.")

if __name__ == "__main__":
    cleanup_questions()
