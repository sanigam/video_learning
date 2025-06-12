import os
from utils.google_adk_manager import GoogleADKManager

class ChatAssistantAgent:
    def __init__(self):
        """Initialize the ChatAssistantAgent class."""
        self.adk_manager = GoogleADKManager()
        
    def generate_response(self, user_query, context):
        """
        Generate a response to the user's query about video content.
        
        Args:
            user_query (str): User's question
            context (dict): Context information including transcript and video info
            
        Returns:
            str: Generated response
        """
        transcript = context.get('transcript', '')
        video_info = context.get('video_info', {})
        summary = context.get('summary')
        # Ensure summary is a dictionary, not None
        if summary is None:
            summary = {}
        chat_history = context.get('chat_history', [])
        
        # Check if there's a transcript
        if not transcript:
            return "To answer your question about the video, I'll need to process a video first. Could you please go to the Video Processing section and input a YouTube URL?"
        
        # Format chat history for the prompt
        formatted_messages = []
        for msg in chat_history[-5:]:  # Include only the last 5 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            formatted_messages.append({"role": role, "content": content})
        
        # System prompt for chat assistant
        system_prompt = """
        You are an expert educational assistant specializing in helping users understand video content.
        Your task is to answer questions about the video accurately and helpfully.
        
        When responding:
        1. Be concise and clear in your explanations
        2. Reference specific parts of the video content when relevant
        3. If the answer isn't in the transcript, acknowledge that and provide general information if possible
        4. Maintain a helpful, friendly, and educational tone
        """
        
        # Prepare context for the message
        # Handle summary content safely
        summary_text = "Not available"
        if summary and 'summary_text' in summary:
            summary_text = summary.get('summary_text')
        
        key_points = ["Not available"]
        if summary and 'key_points' in summary:
            key_points = summary.get('key_points')
            if not key_points or not isinstance(key_points, list):
                key_points = ["No key points available"]
        
        context_message = f"""
        Video Title: {video_info.get('title', 'Unknown')}
        Video Channel: {video_info.get('channel', 'Unknown')}
        
        Video Summary:
        {summary_text}
        
        Key Points:
        {', '.join(key_points)}
        
        Relevant part of transcript:
        {transcript[:2000] if len(transcript) > 0 else 'Transcript not available'}
        """
        
        try:
            # Prepare messages for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if available
            if formatted_messages:
                messages.extend(formatted_messages)
            
            # Add context and user query
            messages.append({"role": "user", "content": f"{context_message}\n\nUser Question: {user_query}"})
            
            # Use Google ADK API to generate response
            response_text = self.adk_manager.generate_text(
                prompt=f"{context_message}\n\nUser Question: {user_query}",
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            # Return the generated response
            return response_text
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your question: {str(e)}. Could you try asking in a different way?"
