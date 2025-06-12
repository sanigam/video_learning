import os
import google.generativeai as genai

class GoogleADKManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleADKManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the Google Gemini API client"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found")
        genai.configure(api_key=api_key)
        
        # Default model - can be overridden
        self._model_name = "gemini-1.5-flash"
    
    def set_model(self, model_name):
        """
        Set the model to use for generation
        
        Args:
            model_name (str): Name of the model (e.g., "gemini-1.5-flash", "gemini-1.5-pro")
        """
        self._model_name = model_name
        
    def get_model(self):
        """
        Get the current model name
        
        Returns:
            str: Current model name
        """
        return self._model_name
    
    def generate_text(self, prompt, system_prompt=None, response_format=None, temperature=0.5, max_tokens=None):
        """
        Generate text using Google Gemini Flash model
        
        Args:
            prompt (str): User prompt
            system_prompt (str, optional): System prompt to set context
            response_format (str, optional): Format for response (json, text)
            temperature (float, optional): Sampling temperature
            max_tokens (int, optional): Maximum tokens in response
            
        Returns:
            str: Generated text response
        """
        try:
            # Create generation configuration
            generation_config = genai.GenerationConfig(
                temperature=temperature
            )
            
            if max_tokens:
                generation_config.max_output_tokens = max_tokens
            
            # Set up the model with the current model setting
            model = genai.GenerativeModel(model_name=self._model_name)
            
            # Prepare the complete prompt with formatting instructions
            complete_prompt = prompt
            
            # For JSON format, add JSON formatting instruction
            if response_format == "json":
                complete_prompt = f"{prompt}\n\nFormat your entire response as a valid JSON object without any markdown formatting or code blocks. Do not include ```json or ``` tags."
            
            # Add system prompt if provided
            if system_prompt:
                # Use the system prompt with the appropriate formatting
                initial_message = f"System: {system_prompt}\n\nUser: {complete_prompt}"
                response = model.generate_content(
                    initial_message,
                    generation_config=generation_config
                )
            else:
                # Direct prompt without system context
                response = model.generate_content(
                    complete_prompt,
                    generation_config=generation_config
                )
            
            # Process the response
            response_text = response.text
            
            # If JSON format is requested, clean up the response
            if response_format == "json":
                # Remove code block markers if present
                if "```json" in response_text:
                    response_text = response_text.replace("```json", "").replace("```", "")
                elif "```" in response_text:
                    # Remove any other code block markers
                    response_text = response_text.split("```")[1]
                    if "```" in response_text:
                        response_text = response_text.split("```")[0]
                
                # Trim whitespace
                response_text = response_text.strip()
            
            return response_text
            
        except Exception as e:
            print(f"Error generating text with Gemini: {str(e)}")
            # Return a fallback response
            if response_format == "json":
                return '{"error": "Failed to generate response", "message": "' + str(e) + '"}'
            else:
                return f"Failed to generate response: {str(e)}"
