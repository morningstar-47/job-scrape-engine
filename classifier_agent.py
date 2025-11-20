# Agent classifier d'offres d'emploi
import os
import json
from groq import Groq
import pandas as pd
from dotenv import load_dotenv

class ClassifierAgent:
    load_dotenv()
    def __init__(self, job_offer_list, parsed_resume):
        self.client = Groq(api_key=os.getenv("GROQ_KEY"))
        self.job_offer_list = job_offer_list
        self.parsed_resume = parsed_resume
    
    def get_job_score(self):
        """
        Script to send the job offer list and parsed cv to LLM and 
        get the relevance score
        """
        # Get the context
        f = open('context_classifier.txt', 'r')
        context = f.read()
        f.close()

        # Get the user_prompt
        f = open('prompt_classifier.txt', 'r')
        user_prompt = f.read()
        f.close()

        # Get the Groq API response:
        scored_jobs = []
        for job in job_offer_list:
            get_score = self.client.chat.completions.create(
                messages = [
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_prompt+json.dumps(parsed_resume)+json.dumps(job)},
            ],
            model="openai/gpt-oss-120b",
            temperature=0.0,
            response_format={"type": "json_object"}
            )
            scored_jobs.append(json.loads(get_score.choices[0].message.content))

        return scored_jobs
    
    def write_excel(self):
        jobs_scored = self.get_job_score()
        df = pd.DataFrame(jobs_scored)
        df.to_excel('job_scored.xlsx', index=False)
        return jobs_scored
    
if __name__ == "__main__":
    #Get job_offer_list
    with open("exemple_job.json", "r", encoding="utf-8") as f:
        job_offer_list = json.load(f)
    
    #Get parsed_resume
    with open("parsed_cv.json", "r", encoding="utf-8") as f:
        parsed_resume = json.load(f)

    classifier_agent = ClassifierAgent(job_offer_list, parsed_resume)
    classifier_agent.write_excel()