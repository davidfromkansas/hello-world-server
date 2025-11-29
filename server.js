const express = require('express');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Anthropic client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || 'your-api-key-here',
});

app.get('/', async (req, res) => {
  try {
    const response = await anthropic.messages.create({
      model: "claude-3-haiku-20240307",
      max_tokens: 1000,
      messages: [{
        role: "user",
        content: "what does my calendar look like for next week?"
      }]
    });
    res.send(response.content[0].text);
    console.log(response);
  } catch (error) {
    res.send('Error: ' + error.message);
  }
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});