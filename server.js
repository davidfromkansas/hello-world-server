const express = require('express');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Anthropic client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || 'your-api-key-here',
});

// Store messages in memory (simple chat)
let messages = [];

app.use(express.json());
app.use(express.static('public'));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/messages', (req, res) => {
  res.json(messages);
});

app.post('/messages', async (req, res) => {
  const { username, message } = req.body;
  
  if (!username || !message) {
    return res.status(400).json({ error: 'Username and message required' });
  }
  
  const userMessage = {
    id: Date.now(),
    username,
    message,
    timestamp: new Date().toISOString()
  };
  
  messages.push(userMessage);
  console.log('New message:', userMessage);
  
  // Get AI response from Claude using the user's message
  try {
    const response = await anthropic.messages.create({
      model: "claude-3-haiku-20240307",
      max_tokens: 1000,
      messages: [{
        role: "user",
        content: message
      }]
    });
    
    const aiMessage = {
      id: Date.now() + 1,
      username: "Claude",
      message: response.content[0].text,
      timestamp: new Date().toISOString()
    };
    
    messages.push(aiMessage);
    console.log('AI response:', aiMessage);
    
  } catch (error) {
    console.error('AI Error:', error);
    const errorMessage = {
      id: Date.now() + 1,
      username: "Claude",
      message: "Sorry, I'm having trouble connecting right now. Please check your API key.",
      timestamp: new Date().toISOString()
    };
    messages.push(errorMessage);
  }
  
  res.json(userMessage);
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});