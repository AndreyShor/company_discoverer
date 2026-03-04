import os
import time
from typing import List, Optional
from datetime import datetime

class SystemLogger:
    def __init__(self, basic_log_path: str, rag_log_path: str, hyde_log_path: str):
        self.basic_log_path = basic_log_path
        self.rag_log_path = rag_log_path
        self.hyde_log_path = hyde_log_path
        self.basic_counter = 0
        self.rag_counter = 0
        self.hyde_counter = 0

        self._initialize_log_file(self.basic_log_path, 'basic')
        self._initialize_log_file(self.rag_log_path, 'rag')
        self._initialize_log_file(self.hyde_log_path, 'hyde')


    def log_basic(self, query: str, response: str, durationResponse: float):
        """ Log the basic query and response """

        self.basic_counter += 1
        formatted_query = self._format_text(query)
        formatted_response = self._format_text(response)
        timestamp = self._current_timestamp()
        log_entry = (
            f"///////// Record {self.basic_counter} ////////////\n"
            f"Timestamp: {timestamp}\n\n"
            f"//////// Query:\n\n"
            f"{formatted_query}\n\n"
            f"//////// System Response:\n\n"
            f"{formatted_response}\n\n"
            f"//////// Time Taken to Response: {durationResponse:.2f} seconds\n\n"
        )
        with open(self.basic_log_path, 'a') as f:
            f.write(log_entry)

    def log_rag(self, query: str, docs: Optional[List[str]], response: str, durationResponse: float, durationRAG: float):
        """ Log the RAG query and response """

        self.rag_counter += 1
        formatted_query = self._format_text(query)
        formatted_response = self._format_text(response)
        timestamp = self._current_timestamp()
        log_entry = (
            f"///////// Record {self.rag_counter} ////////////\n"
            f"Timestamp: {timestamp}\n\n"
            f"//////// Query:\n\n"
            f"{formatted_query}\n\n"
            f"//////// Vector Addition\n\n"
        )

        if docs and isinstance(docs, list):
            for text in docs:
                formatted_vector = self._format_text(text)
                log_entry += f"//// Vector Addition \n\n{formatted_vector}\n\n"
        else:
            log_entry += "(No vector additions)\n\n"

        
        totalTime = durationResponse + durationRAG

        log_entry += (
            f"//////// System Response:\n\n"
            f"{formatted_response}\n\n"
            f"//////// Time for RAG generation: {durationRAG:.2f} seconds\n\n"
            f"//////// Time Taken to Response: {durationResponse:.2f} seconds\n\n"
            f"//////// Total Time: {totalTime:.2f} seconds\n\n"

        )
        with open(self.rag_log_path, 'a') as f:
            f.write(log_entry)

    def log_hyde(
        self,
        query: str,
        agent_addition: str,
        docs: Optional[List[str]],
        response: str,
        durationResponse: float,
        durationRAG: float,
        durationAgent: float,
    ):
        """ Log the HyDE query and response """
        self.hyde_counter += 1
        formatted_query = self._format_text(query)
        formatted_agent = self._format_text(agent_addition)
        formatted_response = self._format_text(response)
        timestamp = self._current_timestamp()

        log_entry = (
            f"///////// Record {self.hyde_counter} ////////////\n"
            f"Timestamp: {timestamp}\n\n"
            f"//////// Query:\n\n{formatted_query}\n\n"
            f"//////// Agent Addition:\n\n{formatted_agent}\n\n"
            f"//////// Vector Additions:\n\n"
        )

        if docs and isinstance(docs, list):
            for text in docs:
                formatted_vector = self._format_text(text)
                log_entry += f"//// Vector Addition \n\n{formatted_vector}\n\n"
        else:
            log_entry += "(No vector additions)\n\n"

        totalTime = durationResponse + durationAgent + durationRAG

        log_entry += (
            f"//////// System Response:\n\n{formatted_response}\n\n"
            f"//////// Time for Agent Answering: {durationAgent:.2f} seconds\n\n"
            f"//////// Time for RAG generation: {durationRAG:.2f} seconds\n\n"
            f"//////// Time Taken to respond: {durationResponse:.2f} seconds\n\n"
            f"//////// Total Time: {totalTime:.2f} seconds\n\n"
        )

        with open(self.hyde_log_path, 'a') as f:
            f.write(log_entry)


    def _initialize_log_file(self, path: str, mode: str):
        """ Initialize the log file """

        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write('')
        else:
            with open(path, 'r') as f:
                content = f.read()
                if mode == 'basic':
                    self.basic_counter = content.count('///////// Record')
                elif mode == 'rag':
                    self.rag_counter = content.count('///////// Record')
                elif mode == 'hyde':
                    self.hyde_counter = content.count('///////// Record')

    def _format_text(self, text: str, max_length: int = 500) -> str:
        """ Format text to fit within a specified line length """

        text = text.replace('\n', ' ').strip()
        words = text.split()
        lines = []
        line = ''
        for word in words:
            if len(line) + len(word) + 1 <= max_length:
                line += (' ' if line else '') + word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return '\n'.join(lines)

    def _current_timestamp(self) -> str:
        """ Get the current timestamp in a readable format """
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')