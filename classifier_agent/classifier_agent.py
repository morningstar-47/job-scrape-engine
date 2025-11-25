# Agent classifier d'offres d'emploi
import os
import json
from groq import Groq
import pandas as pd
from dotenv import load_dotenv
from utils import travel_time_from_cities
from sheets_writer import write_google_sheet
from get_cv_parser import get_json_from_parser

TITRE_FEUILLE = "Personnalized Job Offers"
CHEMIN_CREDS = 'classifier_agent/credentials.json'

class ClassifierAgent:
    load_dotenv()
    def __init__(self, job_offer_list, parsed_resume):
        self.client = Groq(api_key=os.getenv("GROQ_KEY"))
        self.job_offer_list = job_offer_list
        self.parsed_resume = parsed_resume
    
    def get_best_travel_time(self, job, parsed_resume):
        time_by_transport_mean = []
        for transport_mean in ["WALK", "DRIVE", "TRANSIT", "BICYCLE"]:
            minutes = travel_time_from_cities(api_key=os.getenv("GOOGLE_MAPS_API_KEY"), 
                                              origin_city=job["job_city"], 
                                              origin_country=job["job_country"], 
                                              destination_city=parsed_resume["adress_city"], 
                                              destination_country=parsed_resume["adress_country"], 
                                              travel_mode=transport_mean)
            time_by_transport_mean.append(minutes)
        return min(time_by_transport_mean)
    
    def get_job_score(self):
        """
        Script to send the job offer list and parsed cv to LLM and 
        get the relevance score
        """
        # Get the context
        f = open('classifier_agent/context_classifier.txt', 'r')
        context = f.read()
        f.close()

        # Get the user_prompt
        f = open('classifier_agent/prompt_classifier.txt', 'r')
        user_prompt = f.read()
        f.close()

        # Get the Groq API response:
        scored_jobs = []
        for job in job_offer_list:
            distance = self.get_best_travel_time(job, parsed_resume)
            get_score = self.client.chat.completions.create(
                messages = [
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_prompt+json.dumps(parsed_resume)+json.dumps(job)+json.dumps(distance)},
            ],
            model="openai/gpt-oss-120b",
            temperature=0.0,
            response_format={"type": "json_object"}
            )
            scored_jobs.append(json.loads(get_score.choices[0].message.content))

        return scored_jobs
    
    def write_excel(self):
        jobs_scored = self.get_job_score()
        df = pd.DataFrame(jobs_scored).sort_values("score", ascending=False)
        df["status"] = "pending"
        success = write_google_sheet(df, TITRE_FEUILLE, CHEMIN_CREDS, "A1")
        if success:
            df.to_excel("job_scored.xlsx", index=False)
            return jobs_scored
        else:
            print("Erreur dans l'écriture de google sheet")
    
if __name__ == "__main__":
    #Get job_offer_list
    with open("classifier_agent/exemple_job.json", "r", encoding="utf-8") as f:
        job_offer_list = json.load(f)
    
    #Get parsed_resume
    parsed_resume = get_json_from_parser()

    classifier_agent = ClassifierAgent(job_offer_list, parsed_resume)
    classifier_agent.write_excel()