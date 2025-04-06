# ai_service.py
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import logging
from utils import ai_operation_handler
from ai.error_handling import agent_error_handler, story_continuation_fallback

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Get provider configuration from environment
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "")

class AIService:
    def __init__(self):
        # Initialize the appropriate LLM based on the provider
        if AI_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI
            model_name = AI_MODEL_NAME or "gpt-3.5-turbo"
            self.llm = ChatOpenAI(model_name=model_name, temperature=0.7)
            logger.info(f"Using OpenAI provider with model: {model_name}")
        
        elif AI_PROVIDER == "ollama":
            from langchain_community.llms import Ollama
            model_name = AI_MODEL_NAME or "mistral:7b-instruct"
            base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            self.llm = Ollama(model=model_name, base_url=base_url, temperature=0.7)
            logger.info(f"Using Ollama provider with model: {model_name}")
        
        elif AI_PROVIDER == "huggingface":
            from langchain_community.llms import HuggingFaceEndpoint
            model_name = AI_MODEL_NAME or "mistralai/Mistral-7B-Instruct-v0.2"
            api_key = os.getenv("HF_API_TOKEN")
            self.llm = HuggingFaceEndpoint(
                endpoint_url=f"https://api-inference.huggingface.co/models/{model_name}",
                huggingfacehub_api_token=api_key,
                temperature=0.7,
                max_new_tokens=500
            )
            logger.info(f"Using HuggingFace provider with model: {model_name}")

        elif AI_PROVIDER == "deep_seek":
            from langchain_deepseek import ChatDeepSeek
            api_key = os.getenv("DEEPSEEK_API_KEY")
            model_name = AI_MODEL_NAME or "deep_seek_v3"
            self.llm = ChatDeepSeek(
                    model="...",
                    temperature=0.7,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                    api_key=api_key,
                )
            logger.info(f"Using DeepSeek provider with model: {model_name}")       
        else:
            raise ValueError(f"Unsupported AI provider: {AI_PROVIDER}")
    
    @ai_operation_handler
    async def generate_story_introduction(self, genre: str, theme: str, setting: str) -> str:
        """Generate an engaging introduction for a new story"""
        prompt = ChatPromptTemplate.from_template("""
        You are a creative science fiction writer crafting an interactive story.
        
        Write an engaging introduction for an interactive science fiction story with the following details:
        - Genre: {genre}
        - Theme: {theme}
        - Setting: {setting}
        
        The introduction should be 2-3 paragraphs, set the scene vividly, and end with an intriguing situation
        that invites the reader to make a decision about what happens next.
        
        Write in second person perspective (using "you") to make it immersive.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({"genre": genre, "theme": theme, "setting": setting})
        return result
    
    @ai_operation_handler
    @agent_error_handler(fallback_factory=story_continuation_fallback)
    async def generate_story_continuation(
        self,
        story_context: Dict[str, Any],
        user_input: str
    ) -> str:
        """Generate the next part of the story based on user input"""
        # Extract story context
        genre = story_context.get("genre", "science fiction")
        theme = story_context.get("theme", "exploration")
        setting = story_context.get("setting", "")
        
        # Get recent sections for context
        previous_sections = story_context.get("previous_sections", [])
        recent_sections = previous_sections[-3:] if len(previous_sections) > 3 else previous_sections
        context_text = "\n\n".join(recent_sections)
        
        prompt = ChatPromptTemplate.from_template("""
        You are a creative science fiction writer continuing an interactive story based on reader choices.
        
        STORY DETAILS:
        - Genre: {genre}
        - Theme: {theme}
        - Setting: {setting}
        
        PREVIOUS STORY CONTENT:
        {context_text}
        
        USER DECISION/INPUT:
        {user_input}
        
        Continue the story based on the user's input. Write 2-3 paragraphs that follow naturally from 
        the previous content and incorporate the user's decision. Use second person perspective (using "you").
        End with a situation that invites another decision.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = await chain.ainvoke({
            "genre": genre,
            "theme": theme,
            "setting": setting,
            "context_text": context_text,
            "user_input": user_input
        })
        
        return result
    
    @ai_operation_handler
    async def generate_story_suggestions(
        self,
        story_context: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for what the user might do next"""
        # Get latest section
        previous_sections = story_context.get("previous_sections", [])
        latest_section = previous_sections[-1] if previous_sections else ""
        
        prompt = ChatPromptTemplate.from_template("""
        You suggest compelling choices for interactive fiction.
        
        Based on the following latest part of an interactive science fiction story, 
        suggest 3 interesting choices the reader could make to continue the story.
        
        LATEST STORY CONTENT:
        {latest_section}
        
        Provide exactly 3 short, distinct suggestions. Each should be 1 sentence long,
        start with a verb, and offer a clear direction. Format as a simple list, each on a new line.
        The list should ONLY contain the suggestions, with no numbering or bullets.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        
        suggestions_text = await chain.ainvoke({"latest_section": latest_section})
        
        # Parse suggestions from response
        suggestions = [line.strip() for line in suggestions_text.split('\n') if line.strip()]
        
        # Ensure we always have exactly 3 suggestions
        while len(suggestions) < 3:
            suggestions.append(f"Explore the {['area', 'surroundings', 'environment'][len(suggestions) % 3]}.")
        
        return suggestions[:3]

# Create a singleton instance
ai_service = AIService()