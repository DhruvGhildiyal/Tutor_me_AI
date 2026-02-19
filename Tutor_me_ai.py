# install the libraries
!pip install gradio matplotlib textblob transformers torch google-generativeai fpdf
!pip install docx2txt
!pip install PyMuPDF

# main code
from google import genai
from google.genai import types
import gradio as gr
import os
import docx2txt
import fitz
import time
import datetime
import re

client = genai.Client(api_key="")  # ✅ Your Gemini API key here

chat_history = []

def clean_and_format_output(text):
    # Remove all markdown heading symbols like #, ##, ###
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = text.replace('\n', '<br>')
    return text

def ask_gemini(prompt, retries=3, delay=5):
    for _ in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text
        except Exception:
            time.sleep(delay)
    return "❌ Gemini API error."

def save_to_txt(content, prefix="AI_Output"):
    filename = f"{prefix}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def styled_output(text, font, size):
    return f"<div style='font-family:{font}; font-size:{size}px; white-space:pre-wrap;'>{clean_and_format_output(text)}</div>"

def generate_and_save(prompt, font, size, prefix="AI_Output"):
    result = ask_gemini(prompt)
    file_path = save_to_txt(result, prefix)
    return styled_output(result, font, size), file_path

def ask_ai_answer(question, font, size):
    answer = ask_gemini(question)
    chat_history.append(f"You: {question}\nAI: {answer}\n---")
    file_path = save_to_txt(answer, "Ask_AI")
    return styled_output(answer, font, size), file_path

def solve_assignment(file, mode, font, size):
    if file is None:
        return "⚠️ Upload a file.", None
    try:
        if file.name.endswith(".txt"):
            content = file.read().decode()
        elif file.name.endswith(".docx"):
            content = docx2txt.process(file.name)
        elif file.name.endswith(".pdf"):
            with fitz.open(file.name) as doc:
                content = "\n".join(page.get_text() for page in doc)
        else:
            return "❌ Unsupported file type.", None
        prompt = f"Solve each question in {mode} style:\n\n{content}"
        return generate_and_save(prompt, font, size, "Assignment_Solution")
    except Exception as e:
        return f"❌ Error: {e}", None

def generate_mcq(content, num_mcq, font, size):
    prompt = f"Generate {num_mcq} MCQs with 4 options and correct answers:\n{content}"
    return generate_and_save(prompt, font, size, "MCQs")

def generate_question_paper(subject, topic, marks, difficulty, font, size):
    prompt = f"""Generate an official exam paper:
Subject: {subject}
Topic: {topic}
Marks: {marks}
Difficulty: {difficulty}
Sections: MCQs, Short Answers, Long Answers"""
    return generate_and_save(prompt, font, size, "Question_Paper")

def explain_content(content, font, size):
    prompt = f"Explain this content simply:\n{content}"
    return generate_and_save(prompt, font, size, "Content_Explanation")

def save_notes_and_return(text, font, size):
    file_path = save_to_txt(text, "User_Notes")
    return styled_output(text, font, size), file_path

def study_tip(font, size):
    today = datetime.datetime.now().strftime("%d %B %Y")
    prompt = f"Motivational study tip for {today}:"
    return generate_and_save(prompt, font, size, "Daily_Tip")

def daily_quote(font, size):
    today = datetime.datetime.now().strftime("%d %B %Y")
    prompt = f"Short motivational quote for students on {today}:"
    return generate_and_save(prompt, font, size, "Daily_Quote")

def career_roadmap(profession, user_type, font, size):
    prompt = f"Career roadmap for {profession} (User type: {user_type}): Skills, Timeline, Courses."
    return generate_and_save(prompt, font, size, "Career_Roadmap")

def summarize_pdf(file, font, size):
    if file is None:
        return "⚠️ Upload a PDF.", None
    try:
        with fitz.open(file.name) as doc:
            content = "\n".join(page.get_text() for page in doc)
        prompt = f"Summarize these lecture notes:\n{content}"
        return generate_and_save(prompt, font, size, "PDF_Summary")
    except Exception as e:
        return f"❌ Error: {e}", None

def show_history(font, size):
    history_text = "\n\n".join(chat_history)
    return styled_output(history_text, font, size), None

def book_recommendations(subject, font, size):
    prompt = f"Recommend top books for learning {subject}. Include author, why the book is useful, and what topics it covers."
    return generate_and_save(prompt, font, size, "Book_Recommendations")

with gr.Blocks(css="""
#welcome-overlay {position: fixed;top: 0;left: 0;right: 0;bottom: 0;background: rgba(0,0,0,0.85);color: white;display: flex;align-items: center;justify-content: center;flex-direction: column;font-size: 24px;z-index: 1000;animation: fadeOut 2s ease-out 3s forwards;}
@keyframes fadeOut {to {opacity: 0;visibility: hidden;}}
button:hover {box-shadow: 0 0 20px #3b82f6;transition: 0.3s;}
.font-panel {position: fixed;top: 10px;right: 20px;background: linear-gradient(145deg, #e0f7fa, #b2ebf2);padding: 8px;border-radius: 8px;box-shadow: 0 2px 15px rgba(0,0,0,0.2);z-index: 999;max-width: 150px;font-size: 12px;}
""") as app:

    gr.HTML("""<div id="welcome-overlay"><div style="animation: bounce 2s infinite;">🎓 Welcome to Tutor Me AI!</div><div style="margin-top:10px; font-size:16px;">Empowering your study journey...</div></div><style>@keyframes bounce {0%,100% {transform: translateY(0);}50% {transform: translateY(-15px);}}</style>""")

    with gr.Row():
        font_choice = gr.Dropdown(choices=["Poppins", "Roboto", "Open Sans", "Arial", "Courier New", "Georgia", "Times New Roman"], value="Poppins", label="Font Style")
        font_size = gr.Slider(minimum=12, maximum=28, step=1, value=18, label="Font Size")

    with gr.Tab("Ask AI"):
        q = gr.Textbox(label="Your Question")
        out1, file1 = gr.HTML(), gr.File()
        gr.Button("Ask AI").click(ask_ai_answer, inputs=[q, font_choice, font_size], outputs=[out1, file1])

    with gr.Tab("Assignment Solver"):
        file_in = gr.File()
        mode = gr.Dropdown(["Short", "Long", "Simplified", "Direct"], value="Short", label="Answer Style")
        out2, file2 = gr.HTML(), gr.File()
        gr.Button("Solve Assignment").click(solve_assignment, inputs=[file_in, mode, font_choice, font_size], outputs=[out2, file2])

    with gr.Tab("MCQ Generator"):
        mcq_text = gr.Textbox(label="Paste Content")
        num = gr.Slider(1, 20, 5, label="Number of MCQs")
        out3, file3 = gr.HTML(), gr.File()
        gr.Button("Generate MCQs").click(generate_mcq, inputs=[mcq_text, num, font_choice, font_size], outputs=[out3, file3])

    with gr.Tab("Question Paper"):
        sub = gr.Textbox(label="Subject")
        top = gr.Textbox(label="Topic")
        marks = gr.Number(value=100, label="Marks")
        diff = gr.Dropdown(["Easy", "Medium", "Hard", "Mixed"], value="Medium", label="Difficulty")
        out4, file4 = gr.HTML(), gr.File()
        gr.Button("Generate Paper").click(generate_question_paper, inputs=[sub, top, marks, diff, font_choice, font_size], outputs=[out4, file4])

    with gr.Tab("Content Explainer"):
        cont = gr.Textbox(label="Paste Content")
        out5, file5 = gr.HTML(), gr.File()
        gr.Button("Explain").click(explain_content, inputs=[cont, font_choice, font_size], outputs=[out5, file5])

    with gr.Tab("Notes"):
        notes = gr.Textbox(label="Write Notes")
        out6, file6 = gr.HTML(), gr.File()
        gr.Button("Save Notes").click(save_notes_and_return, inputs=[notes, font_choice, font_size], outputs=[out6, file6])

    with gr.Tab("Daily Tip & Quote"):
        out7, file7 = gr.HTML(), gr.File()
        gr.Button("Get Tip").click(study_tip, inputs=[font_choice, font_size], outputs=[out7, file7])
        out8, file8 = gr.HTML(), gr.File()
        gr.Button("Get Quote").click(daily_quote, inputs=[font_choice, font_size], outputs=[out8, file8])

    with gr.Tab("Career Roadmap"):
        prof = gr.Textbox(label="Profession")
        typ = gr.Dropdown(["Student", "Working Professional", "Free Learner"], value="Student", label="You Are")
        out9, file9 = gr.HTML(), gr.File()
        gr.Button("Generate Roadmap").click(career_roadmap, inputs=[prof, typ, font_choice, font_size], outputs=[out9, file9])

    with gr.Tab("PDF Notes Summarizer"):
        pdf_file = gr.File(label="Upload Lecture PDF")
        out10, file10 = gr.HTML(), gr.File()
        gr.Button("Summarize PDF").click(summarize_pdf, inputs=[pdf_file, font_choice, font_size], outputs=[out10, file10])

    with gr.Tab("Chat History"):
        out11 = gr.HTML()
        gr.Button("Show History").click(show_history, inputs=[font_choice, font_size], outputs=[out11])

    with gr.Tab("Book Recommendations"):
        subject = gr.Textbox(label="Enter Subject Name")
        out12, file12 = gr.HTML(), gr.File()
        gr.Button("Get Book Recommendations").click(book_recommendations, inputs=[subject, font_choice, font_size], outputs=[out12, file12])

if __name__ == "__main__":
    app.launch()
