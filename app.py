from flask import Flask, render_template_string, request, jsonify
from ai21 import AI21Client
from ai21.models.chat import ChatMessage
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize AI21 client
client = AI21Client(api_key=os.getenv("AI21_API_KEY"))

# Initialize MongoDB
mongo_client = MongoClient(os.getenv("MONGODB_URL"))
db = mongo_client[os.getenv("DB_NAME")]
assessments_collection = db.assessments
users_collection = db.users

# Global chat context for the session
chat_context = {
    "domain": None,
    "personal_data": None,
    "messages": [],
    "user_id": None,
    "assessment_id": None
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>MUFG GenAI | Risk Mirror Analyzer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-red: #E60012;
            --primary-dark: #1A1A1A;
            --secondary-gray: #2D2D2D;
            --accent-blue: #0066CC;
            --text-light: #FFFFFF;
            --text-gray: #B0B0B0;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --gradient-primary: linear-gradient(135deg, #E60012, #FF4444);
            --gradient-secondary: linear-gradient(135deg, #0066CC, #0080FF);
            --shadow-primary: 0 8px 32px rgba(230, 0, 18, 0.3);
            --shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 50%, #1A1A1A 100%);
            min-height: 100vh; color: var(--text-light); overflow-x: hidden;
        }
        .background-pattern {
            position: fixed; top:0; left:0; width:100%; height:100%;
            background-image:
                radial-gradient(circle at 25% 25%, rgba(230,0,18,0.1) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(0,102,204,0.1) 0%, transparent 50%);
            z-index:-1;
        }
        .container { max-width:1200px; margin:0 auto; padding:20px; position:relative; z-index:1; }
        .header { text-align:center; margin-bottom:40px; position:relative; }
        .logo-section {
            display:flex; align-items:center; justify-content:center; gap:20px; margin-bottom:20px;
        }
        .mufg-logo {
            background: var(--gradient-primary); color:white; padding:12px 24px;
            border-radius:12px; font-weight:700; font-size:24px; letter-spacing:-0.5px; box-shadow: var(--shadow-primary);
        }
        .genai-badge {
            background: var(--glass-bg); backdrop-filter: blur(10px); border:1px solid var(--glass-border);
            padding:8px 16px; border-radius:25px; font-size:14px; font-weight:500; color: var(--text-gray);
        }
        h1 {
            font-size:3.5rem; font-weight:700;
            background:linear-gradient(135deg, var(--primary-red), #FF6B6B, var(--accent-blue));
            background-clip:text; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin-bottom:10px; text-align:center;
        }
        .pulse { animation:pulse 2s infinite; }
        @keyframes pulse { 0%{transform:scale(1);} 50%{transform:scale(1.05);} 100%{transform:scale(1);} }
        .subtitle { font-size:1.2rem; color:var(--text-gray); font-weight:300; margin-bottom:40px; }
        .main-menu { display:flex; justify-content:center; gap:30px; flex-wrap:wrap; }
        .analyzer-card {
            background: var(--glass-bg); backdrop-filter: blur(20px); border:1px solid var(--glass-border);
            border-radius:24px; padding:40px 30px; width:300px; text-align:center; cursor:pointer;
            transition: all 0.4s cubic-bezier(0.4,0,0.2,1); position:relative; overflow:hidden;
        }
        .analyzer-card::before {
            content:''; position:absolute; top:0; left:0; right:0; bottom:0;
            background:var(--gradient-primary); opacity:0; transition: opacity 0.4s ease; z-index:-1;
        }
        .analyzer-card:hover::before { opacity:0.1; }
        .analyzer-card:hover { transform:translateY(-10px); box-shadow: var(--shadow-glass); border-color:var(--primary-red); }
        .card-icon {
            font-size:4rem; margin-bottom:20px;
            background: var(--gradient-primary); background-clip:text; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        }
        .card-title { font-size:1.5rem; font-weight:600; margin-bottom:15px; color:var(--text-light); }
        .card-description { color: var(--text-gray); font-size:0.95rem; line-height:1.5; }
        .form-container {
            display:none; max-width:800px; margin:0 auto; background:var(--glass-bg); backdrop-filter:blur(20px);
            border:1px solid var(--glass-border); border-radius:24px; padding:40px; box-shadow: var(--shadow-glass);
        }
        .form-header { text-align:center; margin-bottom:40px; }
        .form-header h2 { font-size:2.5rem; font-weight:600; color:var(--text-light); margin-bottom:10px; }
        .form-header p { color: var(--text-gray); font-size:1.1rem; }
        .form-grid {
            display:grid; grid-template-columns:repeat(auto-fit, minmax(300px,1fr)); gap:25px; margin-bottom:30px;
        }
        .form-group { position:relative; }
        .form-group label { display:block; margin-bottom:8px; font-weight:500; color:var(--text-light); font-size:0.95rem; }
        .form-group input, .form-group select, .form-group textarea {
            width:100%; padding:16px 20px; background: rgba(255,255,255,0.08); border:1px solid var(--glass-border);
            border-radius:12px; color: var(--text-light); font-size:1rem; transition: all 0.3s ease; backdrop-filter:blur(10px);
        }
        .form-group textarea { resize:vertical; min-height:100px; }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline:none; border-color:var(--primary-red); box-shadow:0 0 0 3px rgba(230,0,18,0.1); background:rgba(255,255,255,0.12);
        }
        .form-group input::placeholder, .form-group textarea::placeholder { color: var(--text-gray); }
        .submit-btn {
            background: var(--gradient-primary); color:white; border:none; padding:18px 40px; border-radius:12px;
            font-size:1.1rem; font-weight:600; cursor:pointer; transition: all 0.3s ease; box-shadow: var(--shadow-primary);
            display:flex; align-items:center; justify-content:center; gap:10px; margin:0 auto;
        }
        .submit-btn:hover { transform:translateY(-2px); box-shadow:0 12px 40px rgba(230,0,18,0.4);}
        .submit-btn:disabled { opacity:0.6; cursor:not-allowed; transform:none; }
        .chat-container {
            display:none; max-width:900px; margin:0 auto; background:var(--glass-bg); backdrop-filter:blur(20px);
            border:1px solid var(--glass-border); border-radius:24px; overflow:hidden; box-shadow: var(--shadow-glass);
        }
        .chat-header { background: var(--gradient-primary); padding:20px 30px; text-align:center;}
        .chat-header h3 { font-size:1.5rem; font-weight:600; margin-bottom:5px;}
        .chat-header p { opacity:0.9; font-size:0.95rem;}
        .chat-messages { height:500px; overflow-y:auto; padding:30px; background:rgba(0,0,0,0.2);}
        .chat-message { margin-bottom:20px; display:flex; align-items:flex-start; gap:15px;}
        .message-avatar { width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0;}
        .user-avatar { background: var(--gradient-secondary); margin-left:auto; order:2;}
        .bot-avatar { background: var(--gradient-primary);}
        .message-content { max-width:70%; padding:16px 20px; border-radius:16px; font-size:0.95rem; line-height:1.5;}
        .user-message .message-content { background: var(--accent-blue); color:white; margin-left:auto;}
        .bot-message .message-content { background: var(--glass-bg); backdrop-filter: blur(10px); border:1px solid var(--glass-border); color: var(--text-light);}
        .chat-input-container { padding:20px 30px; background: rgba(0,0,0,0.3); }
        .chat-input { display: flex; gap:12px; align-items:center;}
        .chat-input input {
            flex-grow:1; padding:16px 20px; background:rgba(255,255,255,0.08); border:1px solid var(--glass-border); border-radius:12px; color:var(--text-light); font-size:1rem;
        }
        .chat-input input:focus { outline:none; border-color:var(--primary-red); box-shadow:0 0 0 3px rgba(230,0,18,0.1);}
        .send-btn { background: var(--gradient-primary); border:none; padding:16px 20px; border-radius:12px; color:white; cursor:pointer; transition: all 0.3s ease;}
        .send-btn:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(230,0,18,0.3);}
        .back-btn { margin-top:20px; background:rgba(255,255,255,0.1); border:1px solid var(--glass-border); color:var(--text-light); padding:12px 24px; border-radius:8px; cursor:pointer; transition:all 0.3s ease; display:flex; align-items:center; gap:8px; justify-content:center;}
        .back-btn:hover { background:rgba(255,255,255,0.15); transform:translateY(-1px);}
        .loading-animation { display:inline-block; width:20px; height:20px; border:2px solid rgba(255,255,255,0.3); border-radius:50%; border-top-color:white; animation:spin 1s linear infinite;}
        @keyframes spin { to{ transform:rotate(360deg);} }
        .full-width { grid-column:1/-1;}
        @media(max-width:768px){
            .container{padding:15px;}
            h1{font-size:2.5rem;}
            .main-menu{flex-direction:column; align-items:center;}
            .analyzer-card{width:100%; max-width:400px;}
            .form-container{padding:20px;}
            .form-grid{grid-template-columns:1fr;}
        }
        .chat-messages::-webkit-scrollbar{width:8px;}
        .chat-messages::-webkit-scrollbar-track{background:rgba(255,255,255,0.1);border-radius:4px;}
        .chat-messages::-webkit-scrollbar-thumb{background:var(--primary-red);border-radius:4px;}
        .chat-messages::-webkit-scrollbar-thumb:hover{background:#FF4444;}
    </style>
</head>
<body>
    <div class="background-pattern"></div>
    <div class="container">
        <div class="header">
            <div class="logo-section">
                <div class="mufg-logo">MUFG</div>
                <div class="genai-badge">
                    <i class="fas fa-robot"></i> GenAI Hackathon
                </div>
            </div>
            <h1 class="pulse">Risk Mirror Analyzer</h1>
            <p class="subtitle">AI-Powered Personalized Risk Assessment Platform</p>
        </div>
        <div id="main-menu">
            <div class="main-menu">
                <div class="analyzer-card" onclick="showForm('finance')">
                    <div class="card-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h3 class="card-title">Financial Risk Analyzer</h3>
                    <p class="card-description">
                        Get comprehensive insights into your financial health and investment strategies with AI-powered analysis
                    </p>
                </div>
                <div class="analyzer-card" onclick="showForm('health')">
                    <div class="card-icon">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <h3 class="card-title">Health Risk Analyzer</h3>
                    <p class="card-description">
                        Evaluate your health risks and receive personalized recommendations for a healthier lifestyle
                    </p>
                </div>
            </div>
        </div>
        <!-- FINANCIAL FORM -->
        <div id="finance-form" class="form-container">
            <div class="form-header">
                <h2><i class="fas fa-chart-line"></i> Financial Risk Assessment</h2>
                <p>Analyze your financial profile and get personalized investment recommendations</p>
            </div>
            <form id="financeForm" onsubmit="submitForm(event, 'finance')">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="name"><i class="fas fa-user"></i> Full Name</label>
                        <input type="text" id="name" required placeholder="Enter your full name">
                    </div>
                    <div class="form-group">
                        <label for="age"><i class="fas fa-birthday-cake"></i> Age</label>
                        <input type="number" id="age" required placeholder="35" min="18" max="100">
                    </div>
                    <div class="form-group">
                        <label for="income"><i class="fas fa-dollar-sign"></i> Annual Income ($)</label>
                        <input type="number" id="income" required placeholder="75000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="net_worth"><i class="fas fa-piggy-bank"></i> Net Worth ($)</label>
                        <input type="number" id="net_worth" required placeholder="250000">
                    </div>
                    <div class="form-group">
                        <label for="assets"><i class="fas fa-home"></i> Total Assets ($)</label>
                        <input type="number" id="assets" required placeholder="500000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="liabilities"><i class="fas fa-credit-card"></i> Total Liabilities ($)</label>
                        <input type="number" id="liabilities" required placeholder="250000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="monthly_expenses"><i class="fas fa-receipt"></i> Monthly Expenses ($)</label>
                        <input type="number" id="monthly_expenses" required placeholder="4000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="emergency_fund"><i class="fas fa-shield-alt"></i> Emergency Fund ($)</label>
                        <input type="number" id="emergency_fund" required placeholder="20000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="investment_portfolio"><i class="fas fa-chart-pie"></i> Investment Portfolio ($)</label>
                        <input type="number" id="investment_portfolio" required placeholder="150000" min="0">
                    </div>
                    <div class="form-group">
                        <label for="time_horizon"><i class="fas fa-clock"></i> Investment Time Horizon (Years)</label>
                        <input type="number" id="time_horizon" required placeholder="10" min="1" max="50">
                    </div>
                    <div class="form-group">
                        <label for="tolerance"><i class="fas fa-balance-scale"></i> Risk Tolerance</label>
                        <select id="tolerance" required>
                            <option value="">Select your risk tolerance</option>
                            <option value="conservative">Conservative (Low Risk, Stable Returns)</option>
                            <option value="moderate">Moderate (Balanced Risk/Return)</option>
                            <option value="aggressive">Aggressive (High Risk, High Potential Returns)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="savings_rate"><i class="fas fa-percent"></i> Monthly Savings Rate (%)</label>
                        <input type="number" id="savings_rate" required placeholder="20" min="0" max="100">
                    </div>
                    <div class="form-group full-width">
                        <label for="goals"><i class="fas fa-target"></i> Investment Goals</label>
                        <textarea id="goals" required placeholder="e.g., retirement planning, home purchase, children's education, wealth building"></textarea>
                    </div>
                    <div class="form-group full-width">
                        <label for="current_debts"><i class="fas fa-file-invoice-dollar"></i> Current Debts (Details)</label>
                        <textarea id="current_debts" placeholder="Describe your current debts: mortgage, car loans, credit cards, etc."></textarea>
                    </div>
                </div>
                <button type="submit" class="submit-btn">
                    <i class="fas fa-analytics"></i> Analyze My Financial Risk
                </button>
            </form>
        </div>
        <!-- HEALTH FORM -->
        <div id="health-form" class="form-container">
            <div class="form-header">
                <h2><i class="fas fa-heartbeat"></i> Health Risk Assessment</h2>
                <p>Comprehensive health analysis with personalized wellness recommendations</p>
            </div>
            <form id="healthForm" onsubmit="submitForm(event, 'health')">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="h_name"><i class="fas fa-user"></i> Full Name</label>
                        <input type="text" id="h_name" required placeholder="Enter your full name">
                    </div>
                    <div class="form-group">
                        <label for="h_age"><i class="fas fa-birthday-cake"></i> Age</label>
                        <input type="number" id="h_age" required placeholder="35" min="1" max="120">
                    </div>
                    <div class="form-group">
                        <label for="gender"><i class="fas fa-venus-mars"></i> Gender</label>
                        <select id="gender" required>
                            <option value="">Select gender</option>
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="height"><i class="fas fa-ruler-vertical"></i> Height (cm)</label>
                        <input type="number" id="height" required placeholder="175" min="50" max="250">
                    </div>
                    <div class="form-group">
                        <label for="weight"><i class="fas fa-weight"></i> Weight (kg)</label>
                        <input type="number" id="weight" required placeholder="70" min="20" max="300">
                    </div>
                    <div class="form-group">
                        <label for="blood_pressure"><i class="fas fa-heartbeat"></i> Blood Pressure</label>
                        <input type="text" id="blood_pressure" placeholder="120/80" pattern="[0-9]{2,3}/[0-9]{2,3}">
                    </div>
                    <div class="form-group">
                        <label for="cholesterol"><i class="fas fa-vial"></i> Cholesterol Level (mg/dL)</label>
                        <input type="number" id="cholesterol" placeholder="180" min="100" max="400">
                    </div>
                    <div class="form-group">
                        <label for="blood_sugar"><i class="fas fa-tint"></i> Blood Sugar (mg/dL)</label>
                        <input type="number" id="blood_sugar" placeholder="100" min="50" max="300">
                    </div>
                    <div class="form-group">
                        <label for="exercise"><i class="fas fa-dumbbell"></i> Exercise Frequency</label>
                        <select id="exercise" required>
                            <option value="">Select exercise frequency</option>
                            <option value="none">No regular exercise</option>
                            <option value="light">1-2 times per week (light)</option>
                            <option value="moderate">3-4 times per week (moderate)</option>
                            <option value="heavy">5+ times per week (intense)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="diet"><i class="fas fa-apple-alt"></i> Diet Quality</label>
                        <select id="diet" required>
                            <option value="">Rate your diet</option>
                            <option value="poor">Poor (fast food, processed)</option>
                            <option value="average">Average (mixed diet)</option>
                            <option value="good">Good (balanced, some healthy choices)</option>
                            <option value="excellent">Excellent (whole foods, balanced)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="smoking"><i class="fas fa-smoking-ban"></i> Smoking Status</label>
                        <select id="smoking" required>
                            <option value="">Select smoking status</option>
                            <option value="never">Never smoked</option>
                            <option value="former">Former smoker</option>
                            <option value="occasional">Occasional smoker</option>
                            <option value="regular">Regular smoker</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="alcohol"><i class="fas fa-wine-glass"></i> Alcohol Consumption</label>
                        <select id="alcohol" required>
                            <option value="">Select alcohol consumption</option>
                            <option value="none">None</option>
                            <option value="light">Light (1-3 drinks/week)</option>
                            <option value="moderate">Moderate (4-10 drinks/week)</option>
                            <option value="heavy">Heavy (10+ drinks/week)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="stress"><i class="fas fa-brain"></i> Stress Level (1-10)</label>
                        <input type="number" id="stress" min="1" max="10" required placeholder="Rate 1-10" title="1 = Very Low, 10 = Very High">
                    </div>
                    <div class="form-group">
                        <label for="sleep"><i class="fas fa-bed"></i> Average Sleep Hours</label>
                        <input type="number" id="sleep" required placeholder="7" min="3" max="12" step="0.5">
                    </div>
                    <div class="form-group">
                        <label for="family_history"><i class="fas fa-users"></i> Family Medical History</label>
                        <select id="family_history" required>
                            <option value="">Select family history</option>
                            <option value="none">No known conditions</option>
                            <option value="heart">Heart disease</option>
                            <option value="diabetes">Diabetes</option>
                            <option value="cancer">Cancer</option>
                            <option value="multiple">Multiple conditions</option>
                        </select>
                    </div>
                    <div class="form-group full-width">
                        <label for="conditions"><i class="fas fa-stethoscope"></i> Current Medical Conditions</label>
                        <textarea id="conditions" placeholder="List any current medical conditions, medications, or health concerns"></textarea>
                    </div>
                    <div class="form-group full-width">
                        <label for="health_goals"><i class="fas fa-bullseye"></i> Health Goals</label>
                        <textarea id="health_goals" placeholder="Describe your health and wellness goals"></textarea>
                    </div>
                </div>
                <button type="submit" class="submit-btn">
                    <i class="fas fa-user-md"></i> Analyze My Health Risk
                </button>
            </form>
        </div>
        <!-- CHAT CONTAINER -->
        <div id="chat-container" class="chat-container">
            <div class="chat-header">
                <h3><i class="fas fa-robot"></i> AI Risk Consultant</h3>
                <p>Your personalized analysis is ready. Ask questions for deeper insights!</p>
            </div>
            <div id="chat-messages" class="chat-messages"></div>
            <div class="chat-input-container">
                <div class="chat-input">
                    <input type="text" id="user-input" placeholder="Ask me anything about your risk analysis...">
                    <button class="send-btn" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button>
                </div>
                <button class="back-btn" onclick="backToMenu()">
                    <i class="fas fa-arrow-left"></i> Back to Main Menu
                </button>
            </div>
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
            const formData = {};
            const form = document.getElementById(domain + 'Form');
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                let key = input.id;
                if (key.startsWith('h_')) key = key.substring(2);
                formData[key] = input.value;
            });
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalContent = submitBtn.innerHTML;
            submitBtn.innerHTML = '<div class="loading-animation"></div> Analyzing...';
            submitBtn.disabled = true;
            fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain: domain, data: formData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    document.getElementById(domain + '-form').style.display = 'none';
                    document.getElementById('chat-container').style.display = 'block';
                    addBotMessage(data.analysis);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during analysis. Please try again.');
            })
            .finally(() => {
                submitBtn.innerHTML = originalContent;
                submitBtn.disabled = false;
            });
        }
        function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (message) {
                addUserMessage(message);
                input.value = '';
                fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => { addBotMessage(data.response); })
                .catch(error => {
                    console.error('Error:', error);
                    addBotMessage("I apologize, but I encountered an error processing your request. Please try again.");
                });
            }
        }
        function addUserMessage(message) {
            const chat = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message user-message';
            messageDiv.innerHTML = `
                <div class="message-avatar user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="message-content">${message}</div>
            `;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        function addBotMessage(message) {
            const chat = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message bot-message';
            messageDiv.innerHTML = `
                <div class="message-avatar bot-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">${message.replace(/\\n/g, '<br>')}</div>
            `;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        function backToMenu() {
            document.getElementById('chat-messages').innerHTML = '';
            document.getElementById('chat-container').style.display = 'none';
            document.getElementById('main-menu').style.display = 'block';
        }
        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { sendMessage(); }
        });
        // Animate cards on load
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.analyzer-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.opacity = '0'; card.style.transform = 'translateY(30px)'; card.style.transition = 'all 0.6s ease';
                    setTimeout(() => { card.style.opacity = '1'; card.style.transform = 'translateY(0)'; }, 100);
                }, index * 200);
            });
        });
    </script>
</body>
</html>
"""

def calculate_financial_risk_score(data):
    score = 5.0 # base
    try:
        age = int(data.get('age', 35))
        if age < 30: score += 0.5
        elif age > 55: score -= 0.5
        income = float(data.get('income', 0))
        expenses = float(data.get('monthly_expenses', 0)) * 12
        if income > 0 and expenses > 0:
            ratio = expenses / income
            if ratio > 0.8: score += 1.0
            elif ratio < 0.5: score -= 0.5
        emergency_fund = float(data.get('emergency_fund', 0))
        monthly_expenses = float(data.get('monthly_expenses', 0))
        if monthly_expenses > 0:
            months_covered = emergency_fund / monthly_expenses
            if months_covered < 3: score += 1.0
            elif months_covered > 6: score -= 0.5
        liabilities = float(data.get('liabilities', 0))
        if income > 0:
            debt_ratio = liabilities / income
            if debt_ratio > 0.4: score += 1.0
            elif debt_ratio < 0.2: score -= 0.3
        tolerance = data.get('tolerance', 'moderate')
        time_horizon = int(data.get('time_horizon', 10))
        if tolerance == 'aggressive' and time_horizon < 5: score += 0.8
        elif tolerance == 'conservative' and time_horizon > 20: score += 0.3
        savings_rate = float(data.get('savings_rate', 10))
        if savings_rate < 10: score += 0.7
        elif savings_rate > 20: score -= 0.5
    except (ValueError, TypeError):
        pass
    return max(1.0, min(10.0, score))

def calculate_health_risk_score(data):
    score = 5.0
    try:
        height = float(data.get('height', 170)) / 100
        weight = float(data.get('weight', 70))
        bmi = weight / (height ** 2)
        if bmi < 18.5 or bmi > 30: score += 1.5
        elif bmi > 25: score += 0.8
        elif 18.5 <= bmi <= 24.9: score -= 0.5
        age = int(data.get('age', 35))
        if age > 65: score += 1.0
        elif age > 50: score += 0.5
        elif age < 30: score -= 0.3
        exercise = data.get('exercise', 'none')
        if exercise == 'none': score += 1.2
        elif exercise == 'light': score += 0.3
        elif exercise in ['moderate','heavy']: score -= 0.5
        smoking = data.get('smoking', 'never')
        if smoking == 'regular': score += 2.0
        elif smoking == 'occasional': score += 1.0
        elif smoking == 'former': score += 0.3
        alcohol = data.get('alcohol', 'none')
        if alcohol == 'heavy': score += 1.0
        elif alcohol == 'moderate': score += 0.3
        stress = int(data.get('stress', 5))
        if stress >= 8: score += 1.0
        elif stress >= 6: score += 0.5
        elif stress <= 3: score -= 0.3
        sleep = float(data.get('sleep', 7))
        if sleep < 6 or sleep > 9: score += 0.8
        elif 7 <= sleep <= 8: score -= 0.3
        family_history = data.get('family_history', 'none')
        if family_history == 'multiple': score += 1.0
        elif family_history in ['heart','diabetes','cancer']: score += 0.5
        diet = data.get('diet', 'average')
        if diet == 'poor': score += 0.8
        elif diet == 'excellent': score -= 0.5
    except (ValueError, TypeError):
        pass
    return max(1.0, min(10.0, score))

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        domain = data['domain']
        personal_data = data['data']
        user_id = f"{personal_data.get('name', 'user')}_{int(datetime.now().timestamp())}"
        if domain == 'finance':
            risk_score = calculate_financial_risk_score(personal_data)
            risk_category = "High Risk" if risk_score > 7 else "Moderate Risk" if risk_score > 4 else "Low Risk"
            system_prompt = f"""You are an elite financial risk assessment expert working for MUFG's GenAI division.

Analyze the following personal financial data and provide a comprehensive "Risk Mirror" report that includes:

🎯 EXECUTIVE SUMMARY
- Overall Financial Risk Score: {risk_score:.1f}/10 (calculated)
- Risk Category: {risk_category}
- Key Financial Health Assessment

📊 COMPREHENSIVE FINANCIAL ANALYSIS
1. Liquidity Risk - Emergency fund adequacy and cash flow stability
2. Debt Risk - Debt-to-income ratios and repayment capacity
3. Investment Risk - Portfolio diversification and risk tolerance alignment
4. Income Risk - Income stability and growth potential
5. Retirement Risk - Long-term financial security assessment

💡 PERSONALIZED FINANCIAL RECOMMENDATIONS
- Immediate action items for risk mitigation
- Investment strategy optimization
- Debt management strategies
- Emergency fund planning
- Retirement planning adjustments

📈 MUFG WEALTH INSIGHTS
- Risk-adjusted portfolio recommendations
- Tax-efficient investment strategies
- Long-term wealth building opportunities
- Financial technology integration suggestions

Present this as a professional, comprehensive financial analysis leveraging MUFG's expertise in wealth management and risk assessment. Be specific with numbers and actionable recommendations."""
        else:
            risk_score = calculate_health_risk_score(personal_data)
            risk_category = "High Risk" if risk_score > 7 else "Moderate Risk" if risk_score > 4 else "Low Risk"
            system_prompt = f"""You are an elite health risk assessment expert working for MUFG's GenAI wellness division.

Analyze the following personal health data and provide a comprehensive "Risk Mirror" report that includes:

🎯 EXECUTIVE SUMMARY
- Overall Health Risk Score: {risk_score:.1f}/10 (calculated)
- Risk Category: {risk_category}
- Key Health Assessment Summary

📊 COMPREHENSIVE HEALTH ANALYSIS
1. Cardiovascular Risk - Heart health and circulation assessment
2. Metabolic Risk - BMI, diabetes, and metabolic syndrome indicators
3. Lifestyle Risk - Exercise, sleep, and stress factor analysis
4. Behavioral Risk - Smoking, alcohol, and dietary habit evaluation
5. Genetic Risk - Family history and hereditary factor assessment

💡 PERSONALIZED HEALTH RECOMMENDATIONS
- Immediate lifestyle modifications
- Exercise and nutrition optimization plans
- Preventive care and screening schedules
- Stress management strategies
- Sleep hygiene improvements

📈 MUFG WELLNESS INSIGHTS
- Evidence-based health optimization strategies
- Technology-assisted health monitoring recommendations
- Long-term wellness investment planning
- Corporate wellness program integration

Present this as a professional, comprehensive health analysis leveraging MUFG's commitment to employee and client wellness. Include specific, actionable health recommendations."""
        chat_context['domain'] = domain
        chat_context['personal_data'] = personal_data
        chat_context['messages'] = []
        chat_context['user_id'] = user_id
        user_data_text = "\n".join([f"📋 {k.replace('_', ' ').title()}: {v}" for k, v in personal_data.items() if v])
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Please analyze my {domain} profile:\n\n{user_data_text}")
        ]
        response = client.chat.completions.create(
            messages=messages,
            model="jamba-large",
            max_tokens=2048,
            temperature=0.7
        )
        analysis = response.choices[0].message.content
        chat_context['messages'] = messages
        chat_context['messages'].append(ChatMessage(role="assistant", content=analysis))
        assessment_data = {
            "user_id": user_id,
            "domain": domain,
            "personal_data": personal_data,
            "risk_score": risk_score,
            "analysis": analysis,
            "timestamp": datetime.now(),
            "chat_history": []
        }
        result = assessments_collection.insert_one(assessment_data)
        chat_context['assessment_id'] = str(result.inserted_id)
        user_data_doc = {
            "user_id": user_id,
            "name": personal_data.get('name', ''),
            "domain": domain,
            "created_at": datetime.now(),
            "last_assessment": str(result.inserted_id)
        }
        users_collection.insert_one(user_data_doc)
        return jsonify({"analysis": analysis, "risk_score": risk_score})
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message']
        chat_context['messages'].append(ChatMessage(role="user", content=user_message))
        response = client.chat.completions.create(
            messages=chat_context['messages'],
            model="jamba-large",
            max_tokens=1024,
            temperature=0.7
        )
        bot_response = response.choices[0].message.content
        chat_context['messages'].append(ChatMessage(role="assistant", content=bot_response))
        if chat_context.get('assessment_id'):
            assessments_collection.update_one(
                {"_id": chat_context['assessment_id']},
                {
                    "$push": {
                        "chat_history": {
                            "user_message": user_message,
                            "bot_response": bot_response,
                            "timestamp": datetime.now()
                        }
                    }
                }
            )
        return jsonify({"response": bot_response})
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"response": f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."})

@app.route('/history/<user_id>')
def get_user_history(user_id):
    try:
        assessments = list(assessments_collection.find(
            {"user_id": user_id},
            {"_id": 1, "domain": 1, "risk_score": 1, "timestamp": 1}
        ).sort("timestamp", -1))
        return jsonify({"history": assessments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)


