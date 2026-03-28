import json
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Team, Student, Question, AdminUser
from .serializers import TeamSerializer, StudentSerializer, QuestionSerializer
import qrcode
import os
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

from django.shortcuts import render

def admin_dashboard(request):
    if not request.session.get('admin_logged_in'):
        from django.shortcuts import redirect
        return redirect('/api/auth/login/')
    return render(request, 'quiz/admin_dashboard.html')

def presentation_view(request):
    return render(request, 'quiz/presentation.html')


def admin_register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '').strip()
        if not name or not password:
            return render(request, 'quiz/admin_register.html', {'error': 'Name and password are required'})
        if AdminUser.objects.filter(name=name).exists():
            return render(request, 'quiz/admin_register.html', {'error': 'Admin name already taken'})
        AdminUser.objects.create(name=name, password=password)
        from django.shortcuts import redirect
        return redirect('/api/auth/login/')
    return render(request, 'quiz/admin_register.html')

def admin_login(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            admin = AdminUser.objects.get(name=name, password=password)
            request.session['admin_logged_in'] = True
            request.session['admin_name'] = admin.name
            from django.shortcuts import redirect
            return redirect('/api/dashboard/')
        except AdminUser.DoesNotExist:
            return render(request, 'quiz/admin_login.html', {'error': 'Invalid name or password'})
    return render(request, 'quiz/admin_login.html')

def admin_logout(request):
    request.session.flush()
    from django.shortcuts import redirect
    return redirect('/api/auth/login/')

def register_view(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        team = None
    return render(request, 'quiz/register.html', {'team': team})

@api_view(['POST', 'GET'])
def teams_api(request):
    if request.method == 'GET':
        teams = Team.objects.all().order_by('-score')
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        name = request.data.get('name')
        password = request.data.get('password', '1234')
        if not name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = Team.objects.create(name=name, password=password)
        
        # Generate QR Code dynamically using the host so mobile phones can connect
        qr_link = f"{request.scheme}://{request.get_host()}/api/register/{team.id}/"
        qr = qrcode.make(qr_link)
        
        # Save QR Image
        qr_filename = f"team_{team.id}_qr.png"
        qr_path = os.path.join(settings.MEDIA_ROOT, qr_filename)
        
        # Ensure media directory exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        qr.save(qr_path)
        
        return Response({
            "message": "Team created successfully",
            "team": TeamSerializer(team).data,
            "qr_url": f"http://localhost:8000/media/{qr_filename}"
        }, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
def team_detail(request, pk):
    try:
        team = Team.objects.get(pk=pk)
        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Team.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def team_detail(request, pk):
    try:
        team = Team.objects.get(pk=pk)
        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Team.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def join_team(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if team.students.count() >= team.max_members:
        return Response({"error": "Team is Full"}, status=status.HTTP_400_BAD_REQUEST)
        
    name = request.data.get('name')
    section = request.data.get('section')
    register_no = request.data.get('register_no')
    
    if not all([name, section, register_no]):
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
    student = Student.objects.create(
        name=name,
        section=section,
        register_no=register_no,
        team=team
    )
    
    return Response({
        "message": "Successfully joined the team",
        "student": StudentSerializer(student).data
    })

@api_view(['POST'])
def upload_pdf(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    # 🤖 DYNAMIC AI SETTINGS
    # We now fetch the API key from the frontend request!
    # Users can paste their OpenAI/Gemini Key in the HTML dashboard.
    api_key = request.data.get('api_key', '')
    ai_mode = request.data.get('ai_mode', 'auto')

    if not api_key:
        # Fallback if empty, though local will take over if empty.
        pass

    pdf_file = request.FILES['file']

    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        if not text.strip():
            return Response({"error": "PDF is empty or just images (No text found). Try a different PDF."}, status=status.HTTP_400_BAD_REQUEST)

        # DEBUG: Log a snippet of the text to terminal
        print(f"\n[SCANNER] AI Mode: {ai_mode} | Key Length: {len(api_key)}")
        print(f"--- PDF TEXT START (300 chars) ---\n{text[:300]}\n-----------------------------------\n")

        questions_created = []
        
        # ── AUTO-SELECT AI MODE ──────────────────────────────────────────────
        used_ai = False
        ai_error = None
        detected_mode = ai_mode

        # Try GEMINI (Default if key doesn't start with sk-)
        if api_key and not api_key.startswith('sk-') and (ai_mode == 'auto' or ai_mode == 'gemini'):
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                prompt = (
                    "Extract all MCQs from this text. Return ONLY a JSON list of objects. "
                    "Each object MUST have: 'question', 'option1', 'option2', 'option3', 'option4', 'correct_answer' (full text). "
                    "Text: " + text
                )
                
                response = None
                last_err = "No models available"
                
                # Iterate through various model versions because API keys may differ in supported versions
                for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro-latest', 'gemini-pro']:
                    try:
                        model = genai.GenerativeModel(model_name)
                        # Some older models don't support response_mime_type, so fallback safely
                        try:
                            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                        except Exception:
                            response = model.generate_content(prompt)
                        break  # Stop trying if we successfully got a response
                    except Exception as e:
                        last_err = str(e)
                        response = None
                        continue
                        
                if not response:
                    raise Exception(f"All models failed. Last error: {last_err}")
                    
                import json as _json
                # Clean up markdown code blocks if gemini-pro returns them instead of raw json
                resp_text = response.text.strip()
                if resp_text.startswith("```json"):
                    resp_text = resp_text[7:-3].strip()
                elif resp_text.startswith("```"):
                    resp_text = resp_text[3:-3].strip()

                data = _json.loads(resp_text)
                q_list = data if isinstance(data, list) else data.get('questions', [])
                if q_list:
                    for q in q_list:
                        Question.objects.create(
                            question=q.get('question', ''),
                            option1=q.get('option1', ''),
                            option2=q.get('option2', ''),
                            option3=q.get('option3', ''),
                            option4=q.get('option4', ''),
                            correct_answer=q.get('correct_answer', '')
                        )
                        questions_created.append(1)
                    used_ai = True
                    detected_mode = "Gemini"
            except Exception as e:
                ai_error = f"Gemini Error: {str(e)}"
                logger.error(ai_error)

        # Try OPENAI (If explicitly chosen OR auto with sk- key)
        if not used_ai and api_key and (ai_mode == 'openai' or (ai_mode == 'auto' and api_key.startswith('sk-'))):
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                system_msg = "Extract MCQs to JSON. Keys: question, option1, option2, option3, option4, correct_answer (full text)."
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user",   "content": text}
                    ],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                import json as _json
                data = _json.loads(response.choices[0].message.content)
                q_list = data if isinstance(data, list) else data.get('questions', [])
                if q_list:
                    for q in q_list:
                        Question.objects.create(
                            question=q.get('question', ''),
                            option1=q.get('option1', ''),
                            option2=q.get('option2', ''),
                            option3=q.get('option3', ''),
                            option4=q.get('option4', ''),
                            correct_answer=q.get('correct_answer', '')
                        )
                        questions_created.append(1)
                    used_ai = True
                    detected_mode = "OpenAI"
            except Exception as e:
                ai_error = f"OpenAI Error: {str(e)}"
                logger.error(ai_error)

        # ── ADVANCED LOCAL HEURISTIC PARSER (No API Needed) ────────────────────
        if not used_ai:
            import re
            
            # Clean up text layout issues common in PDFs
            text = re.sub(r'(?<!\n)\n(?=[a-z])', ' ', text) # Merge broken lines
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            cur_q = ""
            cur_opts = {}
            cur_ans = ""
            
            def flush():
                nonlocal cur_q, cur_opts, cur_ans
                if cur_q and len(cur_opts) >= 2:
                    ans_val = cur_opts.get(cur_ans, cur_ans) if cur_ans else ""
                    # If answer wasn't matched but we have options, just pick option 1 for safety
                    if not ans_val and "A" in cur_opts: ans_val = cur_opts["A"]
                    
                    Question.objects.create(
                        question=cur_q.strip(),
                        option1=cur_opts.get("A", cur_opts.get("1", "")),
                        option2=cur_opts.get("B", cur_opts.get("2", "")),
                        option3=cur_opts.get("C", cur_opts.get("3", "")),
                        option4=cur_opts.get("D", cur_opts.get("4", "")),
                        correct_answer=ans_val.strip()
                    )
                    questions_created.append(1)
                cur_q = ""
                cur_opts = {}
                cur_ans = ""

            q_pattern = re.compile(r'^(?:Q\d+|Question\s*\d+|\d+)\b\s*[:.\-)]\s*(.*)', re.IGNORECASE)
            opt_pattern = re.compile(r'^[\(\[]?([A-E1-5])[\)\]]?[\s.:\-]+\s*(.*)', re.IGNORECASE)
            ans_pattern = re.compile(r'^(?:Ans|Answer|Correct(?: Answer)?)\b\s*[:.\-]?\s*(.*)', re.IGNORECASE)

            # Some PDFs have options inline like: A) Apple B) Banana C) Cat D) Dog
            inline_opt_pattern = re.compile(r'[\(\[]?([A-D])[\)\]][\s.:\-]+([^A-D\(\[]+)')

            # State tracking
            mode = 'search'  # search, question, options
            
            for line in lines:
                # Is it an Answer?
                am = ans_pattern.match(line)
                if am:
                    raw_ans = am.group(1).strip()
                    # Final cleanup of any trailing garbage or nested prefixes like "wer: A"
                    raw_ans = re.sub(r'^(?:wer|answ|ans|answer|correct)\b\s*[:.\-]?\s*', '', raw_ans, flags=re.IGNORECASE)
                    
                    if len(raw_ans) == 1 and raw_ans.upper() in "ABCDE12345":
                        cur_ans = raw_ans.upper()
                    else:
                        cur_ans = raw_ans
                    flush()
                    mode = 'search'
                    continue

                # Is it a new Question?
                qm = q_pattern.match(line)
                if qm and len(qm.group(1)) > 2:
                    flush() # save previous
                    cur_q = qm.group(1).strip()
                    mode = 'question'
                    continue
                
                # Is it an Option?
                om = opt_pattern.match(line)
                if om and mode in ['question', 'options']:
                    letter = str(om.group(1)).upper()
                    cur_opts[letter] = om.group(2).strip()
                    mode = 'options'
                    
                    # Check if the line has multiple inline options (e.g. A. cat B. dog)
                    inline_matches = inline_opt_pattern.findall(line)
                    if len(inline_matches) > 1:
                        for match in inline_matches:
                            cur_opts[match[0].upper()] = match[1].strip()
                    
                    # Sometimes answer is on the same line as the last option
                    am_inline = re.search(r'(?:Ans|Answer|Correct)\s*[:.\-]?\s*([A-D1-4])\b', line, re.IGNORECASE)
                    if am_inline:
                        cur_ans = am_inline.group(1).upper()
                        flush()
                        mode = 'search'
                    continue

                # Continuation of question or option
                if mode == 'question':
                    cur_q += " " + line
                elif mode == 'options' and cur_opts:
                    # Append to the most recently added option
                    last_opt = list(cur_opts.keys())[-1]
                    cur_opts[last_opt] += " " + line

            flush() # save the last one

            detected_mode = "Advanced Universal Local Parser (NO API)"

        method = detected_mode.upper() if used_ai else "Super-Aggressive Local Parser"
        msg = f"Successfully parsed {len(questions_created)} questions using {method}!"
        if not used_ai and api_key and ai_error:
            msg += f" (Note: AI failed with {ai_error})"
            
        return Response({"message": msg})

    except Exception as e:
        logger.error(f"Critical parsing error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_questions(request):
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)

@api_view(['PATCH', 'DELETE'])
def question_detail(request, pk):
    try:
        q = Question.objects.get(pk=pk)
    except Question.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        q.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH – update correct_answer
    correct = request.data.get('correct_answer')
    if correct is not None:
        q.correct_answer = correct
        q.save()
    return Response(QuestionSerializer(q).data)

@api_view(['DELETE'])
def delete_all_questions(request):
    count, _ = Question.objects.all().delete()
    return Response({"message": f"Deleted {count} questions."})


@api_view(['POST'])
def check_answer(request):
    question_id = request.data.get('question_id')
    selected_option = request.data.get('selected_option')
    team_id = request.data.get('team_id')
    
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        
    is_correct = False
    # If AI logic was needed here, we would make OpenAI call.
    # We stick to fast DB checking.
    if selected_option == question.correct_answer:
        is_correct = True
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                team.score += 1
                team.save()
            except Team.DoesNotExist:
                pass
                
    return Response({
        "result": "Correct" if is_correct else "Wrong",
        "correct_answer": question.correct_answer,
        "is_correct": is_correct
    })

@api_view(['POST'])
def add_point(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
        team.score += 1
        team.save()
        return Response({"message": "Point added", "score": team.score})
    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def reset_all_scores(request):
    count = Team.objects.all().update(score=0)
    return Response({"message": f"Scores reset for {count} teams."})

@api_view(['POST'])
def subtract_point(request, team_id):
    try:
        team = Team.objects.get(id=team_id)
        team.score -= 1
        team.save()
        return Response({"message": "Point subtracted", "score": team.score})
    except Team.DoesNotExist:
        return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
