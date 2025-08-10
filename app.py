from flask import Flask, render_template_string, request, jsonify
from ai21 import AI21Client
from ai21.models.chat import ChatMessage
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize AI21 client
client = AI21Client(api_key=os.getenv("AI21_API_KEY"))

# Global variable to store chat context
chat_context = {
    "domain": None,
    "personal_data": None,
    "messages": []
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Risk Mirror Analyzer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        .menu {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
        }
        .menu button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .menu button:hover {
            background-color: #2980b9;
        }
        .form-container {
            display: none;
            margin-top: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .submit-btn {
            background-color: #2ecc71;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .submit-btn:hover {
            background-color: #27ae60;
        }
        .chat-container {
            display: none;
            margin-top: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            background-color: #fafafa;
        }
        .chat-message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 4px;
            max-width: 80%;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        .bot-message {
            background-color: #f1f1f1;
            margin-right: auto;
        }
        .chat-input {
            display: flex;
            margin-top: 10px;
        }
        .chat-input input {
            flex-grow: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
        }
        .chat-input button {
            padding: 8px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
        }
        .back-btn {
            margin-top: 10px;
            padding: 8px 15px;
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Risk Mirror Analyzer</h1>
        
        <div id="main-menu">
            <div class="menu">
                <button onclick="showForm('finance')">Finance Risk Analyzer</button>
                <button onclick="showForm('health')">Health Risk Analyzer</button>
            </div>
        </div>
        
        <div id="finance-form" class="form-container">
            <h2>Financial Risk Assessment</h2>
            <form id="financeForm" onsubmit="submitForm(event, 'finance')">
                <div class="form-group">
                    <label for="age">What is your age?</label>
                    <input type="number" id="age" required>
                </div>
                <div class="form-group">
                    <label for="income">What is your annual income?</label>
                    <input type="text" id="income" required>
                </div>
                <div class="form-group">
                    <label for="net_worth">What is your current net worth?</label>
                    <input type="text" id="net_worth" required>
                </div>
                <div class="form-group">
                    <label for="time_horizon">What is your investment time horizon (years)?</label>
                    <input type="number" id="time_horizon" required>
                </div>
                <div class="form-group">
                    <label for="goals">What are your primary investment goals? (e.g., retirement, buying home)</label>
                    <input type="text" id="goals" required>
                </div>
                <div class="form-group">
                    <label for="tolerance">How would you describe your risk tolerance?</label>
                    <select id="tolerance" required>
                        <option value="conservative">Conservative</option>
                        <option value="moderate">Moderate</option>
                        <option value="aggressive">Aggressive</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="savings_rate">What percentage of your income do you typically invest/save?</label>
                    <input type="number" id="savings_rate" required>
                </div>
                <button type="submit" class="submit-btn">Analyze My Risk</button>
            </form>
        </div>
        
        <div id="health-form" class="form-container">
            <h2>Health Risk Assessment</h2>
            <form id="healthForm" onsubmit="submitForm(event, 'health')">
                <div class="form-group">
                    <label for="h_age">What is your age?</label>
                    <input type="number" id="h_age" required>
                </div>
                <div class="form-group">
                    <label for="height">What is your height (in cm)?</label>
                    <input type="number" id="height" required>
                </div>
                <div class="form-group">
                    <label for="weight">What is your weight (in kg)?</label>
                    <input type="number" id="weight" required>
                </div>
                <div class="form-group">
                    <label for="exercise">How often do you exercise per week?</label>
                    <input type="text" id="exercise" required>
                </div>
                <div class="form-group">
                    <label for="conditions">Do you have any chronic conditions? (yes/no)</label>
                    <input type="text" id="conditions" required>
                </div>
                <div class="form-group">
                    <label for="smoking">Do you smoke? (yes/no)</label>
                    <input type="text" id="smoking" required>
                </div>
                <div class="form-group">
                    <label for="stress">How would you rate your stress levels? (1-10)</label>
                    <input type="number" id="stress" min="1" max="10" required>
                </div>
                <div class="form-group">
                    <label for="sleep">How many hours of sleep do you get on average?</label>
                    <input type="number" id="sleep" required>
                </div>
                <button type="submit" class="submit-btn">Analyze My Risk</button>
            </form>
        </div>
        
        <div id="chat-container" class="chat-container">
            <div id="chat-messages"></div>
            <div class="chat-input">
                <input type="text" id="user-input" placeholder="Type your message...">
                <button onclick="sendMessage()">Send</button>
            </div>
            <button class="back-btn" onclick="backToMenu()">Back to Main Menu</button>
        </div>
    </div>

    <script>
        function showForm(domain) {
            document.getElementById('main-menu').style.display = 'none';
            document.getElementById('finance-form').style.display = 'none';
            document.getElementById('health-form').style.display = 'none';
            document.getElementById(domain + '-form').style.display = 'block';
        }
        
        function submitForm(event, domain) {
            event.preventDefault();
            
            // Collect form data
            const formData = {};
            const form = document.getElementById(domain + 'Form');
            const inputs = form.querySelectorAll('input, select');
            
            inputs.forEach(input => {
                const key = input.id.startsWith('h_') ? input.id.substring(2) : input.id;
                formData[key] = input.value;
            });
            
            // Show loading state
            form.querySelector('button').textContent = 'Analyzing...';
            form.querySelector('button').disabled = true;
            
            // Send data to server
            fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    domain: domain,
                    data: formData
                })
            })
            .then(response => response.json())
            .then(data => {
                // Show chat interface
                document.getElementById(domain + '-form').style.display = 'none';
                document.getElementById('chat-container').style.display = 'block';
                
                // Display initial analysis
                addBotMessage(data.analysis);
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during analysis');
                form.querySelector('button').textContent = 'Analyze My Risk';
                form.querySelector('button').disabled = false;
            });
        }
        
        function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            
            if (message) {
                // Add user message to chat
                addUserMessage(message);
                input.value = '';
                
                // Send to server
                fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message
                    })
                })
                .then(response => response.json())
                .then(data => {
                    addBotMessage(data.response);
                })
                .catch(error => {
                    console.error('Error:', error);
                    addBotMessage("Sorry, I encountered an error processing your request.");
                });
            }
        }
        
        function addUserMessage(message) {
            const chat = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message user-message';
            messageDiv.textContent = message;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function addBotMessage(message) {
            const chat = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message bot-message';
            messageDiv.textContent = message;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function backToMenu() {
            document.getElementById('chat-messages').innerHTML = '';
            document.getElementById('chat-container').style.display = 'none';
            document.getElementById('main-menu').style.display = 'block';
        }
        
        // Allow pressing Enter to send message
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    domain = data['domain']
    personal_data = data['data']
    
    # Store in global context
    chat_context['domain'] = domain
    chat_context['personal_data'] = personal_data
    chat_context['messages'] = []
    
    # Generate system prompt based on domain
    if domain == 'finance':
        system_prompt = """You are a financial risk assessment expert. Analyze the following personal financial data and:
        1. Calculate a personalized risk score (1-10)
        2. Identify key risk factors
        3. Provide specific recommendations
        4. Suggest appropriate investment strategies
        
        Present this as a clear "Risk Mirror" report with sections for each component."""
    else:
        system_prompt = """You are a health risk assessment expert. Analyze the following personal health data and:
        1. Calculate a personalized health risk score (1-10)
        2. Identify key health risk factors
        3. Provide specific recommendations for improvement
        4. Suggest lifestyle changes
        
        Present this as a clear "Risk Mirror" report with sections for each component."""
    
    # Format user data for prompt
    user_data = "\n".join([f"{k}: {v}" for k, v in personal_data.items()])
    
    # Get analysis from AI21
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_data)
    ]
    
    response = client.chat.completions.create(
        messages=messages,
        model="jamba-large",
        max_tokens=1024,
    )
    
    analysis = response.choices[0].message.content
    
    # Store initial messages in context
    chat_context['messages'] = messages
    chat_context['messages'].append(ChatMessage(role="assistant", content=analysis))
    
    return jsonify({"analysis": analysis})

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    # Add user message to context
    chat_context['messages'].append(ChatMessage(role="user", content=user_message))
    
    # Get response from AI21
    response = client.chat.completions.create(
        messages=chat_context['messages'],
        model="jamba-large",
        max_tokens=1024,
    )
    
    bot_response = response.choices[0].message.content
    
    # Add bot response to context
    chat_context['messages'].append(ChatMessage(role="assistant", content=bot_response))
    
    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)