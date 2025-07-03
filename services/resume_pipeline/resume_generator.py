import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT = (
    "You are a helpful assistant that rewrites a resume to match a job description." 
    "Return the improved resume in plain text."
)

def generate_resume(resume_text: str, job_requirements: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f"Resume:\n{resume_text}\n\nJob requirements:\n{job_requirements}"},
    ]
    resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return resp.choices[0].message.content.strip()
