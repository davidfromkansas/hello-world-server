"""
Tool functions and schemas for Claude API integration.
"""
import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Tool schemas for Claude API
google_calendar_tool_schema = {
    "name": "get_calendar_events",
    "description": "Get calendar events for a specified date range",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format"
            },
            "end_date": {
                "type": "string", 
                "description": "End date in YYYY-MM-DD format"
            }
        },
        "required": ["start_date", "end_date"]
    }
}

get_today_date_tool_schema = {
    "name": "get_today_date",
    "description": "Get today's current date and time",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

# Add more tool schemas here as needed
available_tools = [
    google_calendar_tool_schema,
    get_today_date_tool_schema
]

def handle_tool_call(tool_name, tool_input):
    """
    Handle tool function calls based on tool name and input.
    
    Args:
        tool_name (str): Name of the tool to execute
        tool_input (dict): Input parameters for the tool
        
    Returns:
        dict: Tool execution result
    """
    if tool_name == "get_calendar_events":
        return get_calendar_events(tool_input)
    elif tool_name == "get_today_date":
        return get_today_date(tool_input)
    
    # Add more tool handlers here
    return {"error": f"Unknown tool: {tool_name}"}

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_google_calendar():
    """
    Authenticate with Google Calendar API.
    
    Returns:
        service: Authenticated Google Calendar service object
    """
    creds = None
    
    # Check if token.json exists (stored credentials)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need credentials.json file with OAuth 2.0 client info
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # Use port 3000 to match one of your redirect URIs
                creds = flow.run_local_server(port=3000)
            else:
                raise FileNotFoundError("credentials.json not found. Please download from Google Cloud Console.")
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

def get_calendar_events(tool_input):
    """
    Get upcoming calendar events from Google Calendar.
    
    Args:
        tool_input (dict): Contains start_date and end_date
        
    Returns:
        dict: Calendar events data
    """
    try:
        start_date = tool_input.get("start_date")
        end_date = tool_input.get("end_date")
        
        # Parse dates
        start_datetime = datetime.fromisoformat(start_date).isoformat() + 'Z'
        end_datetime = datetime.fromisoformat(end_date).isoformat() + 'Z'
        
        # Authenticate and get service
        service = authenticate_google_calendar()
        
        # Get events from primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_datetime,
            timeMax=end_datetime,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for response
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'title': event.get('summary', 'No title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
            })
        
        return {
            "events": formatted_events,
            "total_events": len(formatted_events),
            "date_range": f"{start_date} to {end_date}"
        }
        
    except HttpError as error:
        return {
            "error": f"Google Calendar API error: {error}",
            "events": [],
            "total_events": 0
        }
    except FileNotFoundError as error:
        return {
            "error": str(error),
            "events": [],
            "total_events": 0,
            "setup_required": "Please set up Google Calendar API credentials"
        }
    except Exception as error:
        return {
            "error": f"Unexpected error: {error}",
            "events": [],
            "total_events": 0
        }

def get_today_date(tool_input):
    """
    Get today's current date and time.
    
    Args:
        tool_input (dict): Empty dict (no parameters needed)
        
    Returns:
        dict: Current date and time information
    """
    now = datetime.now()
    
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "iso_format": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.year,
        "timestamp": int(now.timestamp())
    }