import json
import time

from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from models import StructuredBusinessAnalysis
from core.logging import SystemLogger


class LLM():

    def __init__(self, model_name: str, local_api_key: str, local_api_base: str):
        self.model_name = model_name
        self.local_api_key = local_api_key
        self.local_api_base = local_api_base
        
        # We might not need the legacy loggers but keeping for compatibility
        self.logger = SystemLogger('./logs/basic_log.txt', './logs/rag_log.txt', './logs/hyde_log.txt')

        kwargs = {
            "model": self.model_name,
            "openai_api_key": self.local_api_key,
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        if self.local_api_base:
            kwargs["openai_api_base"] = self.local_api_base
            
        self.llm = ChatOpenAI(**kwargs)

    def generate_company_report(self, company_name: str, region: str, retrieved_data: List[Dict[str, str]]) -> StructuredBusinessAnalysis:
        """
        Generates a structured business analysis report using the provided context.
        """
        
        # Format the context
        context_str = ""
        for i, data in enumerate(retrieved_data):
            context_str += f"\nSource {i+1}:\nTitle: {data.get('title', 'N/A')}\nURL: {data.get('href', 'N/A')}\nContent Snippet/Scraped:\n{data.get('scraped_content', 'N/A')}\n"

        # Set up JSON parser based on our Pydantic model
        parser = JsonOutputParser(pydantic_object=StructuredBusinessAnalysis)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert business analyst. Your task is to extract and synthesize information about a target company operating in a specified region based only on the provided context.\n\n{format_instructions}"),
            ("user", "Target Company: {company_name}\nRegion: {region}\n\nContext Retrieved from Web:\n{context}")
        ])

        chain = prompt_template | self.llm | parser

        try:
            print(f"\nSending reporting task to local LLM for {company_name}...")
            
            start_time = time.time()
            
            # Pass the required fields to invoke
            response = chain.invoke({
                "company_name": company_name,
                "region": region,
                "context": context_str,
                "format_instructions": parser.get_format_instructions()
            })
            
            duration = time.time() - start_time
            print(f"Report generated in {duration:.2f} seconds.")
            
            # Since parser usually returns a dict matching the schema, let's wrap it in the Pydantic object
            return StructuredBusinessAnalysis(**response)

        except Exception as e:
            print(f"\nAn error occurred generating the report: {e}")
            raise e
