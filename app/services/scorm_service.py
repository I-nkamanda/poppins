import os
import zipfile
import io
import markdown
import uuid
from datetime import datetime
from typing import Dict, Any

class ScormService:
    """
    SCORM 1.2 Package Generator (Multi-SCO)
    
    Converts chapter content into a SCORM 1.2 compliant ZIP package with multiple SCOs:
    1. Concept (concept.html)
    2. Exercise (exercise.html)
    3. Quiz (quiz.html) - Interactive with scoring
    4. Advanced Learning (advanced.html) - Subjective
    """
    
    @staticmethod
    def create_scorm_package(chapter_title: str, chapter_content: Dict[str, Any]) -> io.BytesIO:
        """
        Creates a SCORM 1.2 ZIP package in memory.
        """
        # 1. Generate HTML contents
        concept_html = ScormService._generate_concept_html(chapter_title, chapter_content)
        exercise_html = ScormService._generate_exercise_html(chapter_title, chapter_content)
        quiz_html = ScormService._generate_quiz_html(chapter_title, chapter_content)
        advanced_html = ScormService._generate_advanced_html(chapter_title, chapter_content)
        
        # 2. Generate Manifest (imsmanifest.xml)
        manifest_xml = ScormService._generate_manifest(chapter_title)
        
        # 3. Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add HTML files
            zip_file.writestr("concept.html", concept_html)
            zip_file.writestr("exercise.html", exercise_html)
            zip_file.writestr("quiz.html", quiz_html)
            zip_file.writestr("advanced.html", advanced_html)
            
            # Add Manifest
            zip_file.writestr("imsmanifest.xml", manifest_xml)
            
            # Add SCORM API Wrapper
            zip_file.writestr("scorm_api.js", ScormService._get_scorm_api_js())
            
            # Add CSS
            zip_file.writestr("style.css", ScormService._get_style_css())
            
        zip_buffer.seek(0)
        return zip_buffer

    @staticmethod
    def _generate_html_template(title: str, content_body: str, extra_script: str = "") -> str:
        """Common HTML template for all pages."""
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
    <script src="scorm_api.js"></script>
    {extra_script}
</head>
<body onload="initSCORM()" onunload="finishSCORM()">
    <div class="container">
        <header>
            <h1>{title}</h1>
        </header>
        
        <main>
            {content_body}
        </main>
        
        <footer>
            <div class="navigation">
                <p class="hint">Use the LMS navigation to move between sections.</p>
            </div>
        </footer>
    </div>
</body>
</html>"""

    @staticmethod
    def _generate_concept_html(title: str, content: Dict[str, Any]) -> str:
        md = markdown.Markdown(extensions=['fenced_code', 'tables'])
        body_content = md.convert(content.get('concept', {}).get('contents', ''))
        return ScormService._generate_html_template(f"{title} - Concept", body_content)

    @staticmethod
    def _generate_exercise_html(title: str, content: Dict[str, Any]) -> str:
        md = markdown.Markdown(extensions=['fenced_code', 'tables'])
        body_content = md.convert(content.get('exercise', {}).get('contents', ''))
        return ScormService._generate_html_template(f"{title} - Exercise", body_content)

    @staticmethod
    def _generate_quiz_html(title: str, content: Dict[str, Any]) -> str:
        quizzes = content.get('quiz', {}).get('quizes', [])
        
        quiz_items_html = ""
        answers_json = []
        
        for i, q in enumerate(quizzes, 1):
            options_html = ""
            for opt in q.get('options', []):
                options_html += f"""
                <label class="option-label">
                    <input type="radio" name="q{i}" value="{opt}">
                    {opt}
                </label>
                """
            
            quiz_items_html += f"""
            <div class="quiz-item" id="question-{i}">
                <p class="question-text"><strong>Q{i}. {q.get('question')}</strong></p>
                <div class="options">
                    {options_html}
                </div>
                <div class="feedback" id="feedback-{i}" style="display:none;"></div>
            </div>
            <hr>
            """
            answers_json.append({"index": i, "answer": q.get('answer'), "explanation": q.get('explanation')})

        # JavaScript for grading
        import json
        answers_str = json.dumps(answers_json, ensure_ascii=False)
        
        script = f"""
        <script>
        var correctAnswers = {answers_str};
        
        function submitQuiz() {{
            var score = 0;
            var total = correctAnswers.length;
            
            correctAnswers.forEach(function(item) {{
                var selected = document.querySelector('input[name="q' + item.index + '"]:checked');
                var feedbackEl = document.getElementById('feedback-' + item.index);
                feedbackEl.style.display = 'block';
                
                if (selected && selected.value === item.answer) {{
                    score++;
                    feedbackEl.className = 'feedback correct';
                    feedbackEl.innerHTML = '<strong>✓ Correct!</strong> ' + item.explanation;
                }} else {{
                    feedbackEl.className = 'feedback incorrect';
                    feedbackEl.innerHTML = '<strong>✗ Incorrect.</strong> The correct answer is: ' + item.answer + '<br><em>' + item.explanation + '</em>';
                }}
            }});
            
            var percentage = Math.round((score / total) * 100);
            alert("Quiz Completed! Score: " + percentage + "%");
            
            // Send score to LMS
            if (API != null) {{
                API.LMSSetValue("cmi.core.score.raw", percentage);
                API.LMSSetValue("cmi.core.lesson_status", percentage >= 80 ? "passed" : "completed");
                API.LMSCommit("");
            }}
        }}
        </script>
        """
        
        body_content = f"""
        <h2>Quiz</h2>
        <div id="quiz-container">
            {quiz_items_html}
            <button onclick="submitQuiz()" class="btn-primary">Submit Answers</button>
        </div>
        """
        
        return ScormService._generate_html_template(f"{title} - Quiz", body_content, script)

    @staticmethod
    def _generate_advanced_html(title: str, content: Dict[str, Any]) -> str:
        quizzes = content.get('advanced_learning', {}).get('quizes', [])
        
        if not quizzes:
            body_content = "<p>No advanced learning content available.</p>"
        else:
            items_html = ""
            for i, q in enumerate(quizzes, 1):
                model_answer = q.get('model_answer', '')
                model_answer_html = ""
                
                if model_answer:
                    # Convert markdown to HTML if needed
                    model_answer_html = f"""
                    <details class="model-answer">
                        <summary>📖 모범 답안 확인하기</summary>
                        <div class="model-answer-content">
                            {model_answer}
                        </div>
                    </details>
                    """
                
                items_html += f"""
                <div class="quiz-item">
                    <p><strong>Q{i}. {q.get('quiz')}</strong></p>
                    <textarea rows="5" class="text-input" placeholder="Write your thoughts here..."></textarea>
                    {model_answer_html}
                </div>
                <hr>
                """
            
            body_content = f"""
            <h2>Advanced Learning</h2>
            <p class="note"><em>Note: This section is for self-reflection. Your answers are not graded.</em></p>
            {items_html}
            <button onclick="alert('Your responses have been recorded (simulated).')" class="btn-primary">Save Responses</button>
            """
            
        return ScormService._generate_html_template(f"{title} - Advanced", body_content)

    @staticmethod
    def _generate_manifest(title: str) -> str:
        """Generates imsmanifest.xml with 4 items."""
        manifest_id = f"MANIFEST-{uuid.uuid4()}"
        org_id = f"ORG-{uuid.uuid4()}"
        
        # Resource IDs
        res_concept = f"RES-CONCEPT-{uuid.uuid4()}"
        res_exercise = f"RES-EXERCISE-{uuid.uuid4()}"
        res_quiz = f"RES-QUIZ-{uuid.uuid4()}"
        res_advanced = f"RES-ADVANCED-{uuid.uuid4()}"
        
        # Item IDs
        item_concept = f"ITEM-CONCEPT-{uuid.uuid4()}"
        item_exercise = f"ITEM-EXERCISE-{uuid.uuid4()}"
        item_quiz = f"ITEM-QUIZ-{uuid.uuid4()}"
        item_advanced = f"ITEM-ADVANCED-{uuid.uuid4()}"
        
        return f"""<?xml version="1.0" standalone="no" ?>
<manifest identifier="{manifest_id}" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                              http://www.imsproject.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">

  <organizations default="{org_id}">
    <organization identifier="{org_id}">
      <title>{title}</title>
      <item identifier="{item_concept}" identifierref="{res_concept}">
        <title>Concept</title>
      </item>
      <item identifier="{item_exercise}" identifierref="{res_exercise}">
        <title>Exercise</title>
      </item>
      <item identifier="{item_quiz}" identifierref="{res_quiz}">
        <title>Quiz</title>
      </item>
      <item identifier="{item_advanced}" identifierref="{res_advanced}">
        <title>Advanced Learning</title>
      </item>
    </organization>
  </organizations>

  <resources>
    <resource identifier="{res_concept}" type="webcontent" adlcp:scormtype="sco" href="concept.html">
      <file href="concept.html"/>
      <file href="style.css"/>
      <file href="scorm_api.js"/>
    </resource>
    <resource identifier="{res_exercise}" type="webcontent" adlcp:scormtype="sco" href="exercise.html">
      <file href="exercise.html"/>
      <file href="style.css"/>
      <file href="scorm_api.js"/>
    </resource>
    <resource identifier="{res_quiz}" type="webcontent" adlcp:scormtype="sco" href="quiz.html">
      <file href="quiz.html"/>
      <file href="style.css"/>
      <file href="scorm_api.js"/>
    </resource>
    <resource identifier="{res_advanced}" type="webcontent" adlcp:scormtype="sco" href="advanced.html">
      <file href="advanced.html"/>
      <file href="style.css"/>
      <file href="scorm_api.js"/>
    </resource>
  </resources>
</manifest>"""

    @staticmethod
    def _get_scorm_api_js() -> str:
        return """
var API = null;

function findAPI(win) {
    while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
        win = win.parent;
    }
    API = win.API;
}

function initSCORM() {
    findAPI(window);
    if ((API == null) && (window.opener != null) && (typeof(window.opener) != "undefined")) {
        findAPI(window.opener);
    }
    
    if (API != null) {
        API.LMSInitialize("");
        var status = API.LMSGetValue("cmi.core.lesson_status");
        if (status == "not attempted") {
            API.LMSSetValue("cmi.core.lesson_status", "incomplete");
            API.LMSCommit("");
        }
    }
}

function finishSCORM() {
    if (API != null) {
        API.LMSFinish("");
    }
}
"""

    @staticmethod
    def _get_style_css() -> str:
        return """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f9f9f9;
}
.container {
    background: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
h1, h2, h3 { color: #2c3e50; }
code {
    background: #f4f4f4;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
}
pre {
    background: #f4f4f4;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
}
.quiz-item {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    border: 1px solid #e9ecef;
}
.option-label {
    display: block;
    margin: 10px 0;
    cursor: pointer;
}
.btn-primary {
    display: block;
    width: 100%;
    padding: 15px;
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    margin-top: 30px;
    transition: background 0.2s;
}
.btn-primary:hover {
    background: #4338ca;
}
.feedback {
    margin-top: 15px;
    padding: 15px;
    border-radius: 5px;
}
.feedback.correct {
    background-color: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}
.feedback.incorrect {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
}
.text-input {
    width: 100%;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    margin-top: 10px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
}
.model-answer {
    margin-top: 15px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 0;
    background: #f9fafb;
}
.model-answer summary {
    padding: 12px 15px;
    cursor: pointer;
    font-weight: 500;
    color: #4f46e5;
    user-select: none;
    transition: background 0.2s;
}
.model-answer summary:hover {
    background: #f3f4f6;
}
.model-answer[open] summary {
    border-bottom: 1px solid #e5e7eb;
    background: #ffffff;
}
.model-answer-content {
    padding: 15px;
    background: #ffffff;
    color: #374151;
    line-height: 1.6;
    border-bottom-left-radius: 6px;
    border-bottom-right-radius: 6px;
}
.note {
    color: #6b7280;
    font-size: 0.9em;
    margin-bottom: 20px;
}
.hint {
    text-align: center;
    color: #9ca3af;
    font-size: 0.85em;
    margin-top: 40px;
}
"""
