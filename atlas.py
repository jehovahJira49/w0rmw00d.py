"""
ATLAS - Personal AI Assistant
A conversational AI with memory, learning capabilities, and task assistance
Voice-activated by saying "Atlas"
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import random
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

try:
    import speech_recognition as sr  # type: ignore
    SPEECH_AVAILABLE = True
except ImportError:
    sr = None  # type: ignore
    SPEECH_AVAILABLE = False
    print("Warning: speech_recognition not installed. Install with: pip install SpeechRecognition")

try:
    import pyttsx3  # type: ignore
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None  # type: ignore
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not installed. Install with: pip install pyttsx3")


class Atlas:
    """Personal AI Assistant with memory and learning capabilities"""
    
    def __init__(self, name: str = "Atlas", voice_mode: bool = True):
        self.name = name
        self.voice_mode = voice_mode
        self.listening = False
        self.activated = False
        self.user_name = None
        self.memory_file = "atlas_memory.json"
        self.conversation_history: List[Dict[str, str]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.tasks: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Any] = {}
        
        # Initialize speech components
        if self.voice_mode and SPEECH_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                # Adjust recognizer settings for better accuracy
                self.recognizer.energy_threshold = 300  # Minimum audio energy to consider for recording
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8  # Seconds of silence to consider end of phrase
                
                # List available microphones
                print("\nAvailable microphones:")
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"  [{index}] {name}")
                
                # Use default microphone
                self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                print("\n🎤 Calibrating microphone for ambient noise...")
                print("Please be quiet for a moment...")
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print(f"✓ Microphone calibrated! Energy threshold: {self.recognizer.energy_threshold}")
                print("You can now speak to Atlas!\n")
            except Exception as e:
                print(f"Error initializing microphone: {e}")
                self.recognizer = None
                self.microphone = None
                self.voice_mode = False
        else:
            self.recognizer = None
            self.microphone = None
        
        # Initialize text-to-speech
        if self.voice_mode and TTS_AVAILABLE:
            self.tts_engine = pyttsx3.init()
            # Set voice properties
            self.tts_engine.setProperty('rate', 175)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        else:
            self.tts_engine = None
        
        # Load existing memory if available
        self.load_memory()
        
        # Personality traits
        self.personality = {
            "helpful": True,
            "friendly": True,
            "curious": True,
            "analytical": True
        }
        
    def load_memory(self):
        """Load persistent memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_name = data.get('user_name')
                    self.conversation_history = data.get('conversation_history', [])
                    self.user_preferences = data.get('user_preferences', {})
                    self.tasks = data.get('tasks', [])
                    self.knowledge_base = data.get('knowledge_base', {})
                print(f"[{self.name}] Memory loaded successfully.")
            except Exception as e:
                print(f"[{self.name}] Error loading memory: {e}")
    
    def save_memory(self):
        """Save persistent memory to file"""
        try:
            data = {
                'user_name': self.user_name,
                'conversation_history': self.conversation_history[-100:],  # Keep last 100 conversations
                'user_preferences': self.user_preferences,
                'tasks': self.tasks,
                'knowledge_base': self.knowledge_base,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.name}] Error saving memory: {e}")
    
    def remember_conversation(self, user_input: str, ai_response: str):
        """Store conversation in memory"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'atlas': ai_response
        })
        self.save_memory()
    
    def learn_preference(self, key: str, value: Any):
        """Learn and store user preferences"""
        self.user_preferences[key] = value
        self.save_memory()
        return f"Got it! I'll remember that you prefer {key}: {value}"
    
    def add_task(self, task: str, priority: str = "medium"):
        """Add a task to the task list"""
        new_task = {
            'id': len(self.tasks) + 1,
            'task': task,
            'priority': priority,
            'status': 'pending',
            'created': datetime.now().isoformat()
        }
        self.tasks.append(new_task)
        self.save_memory()
        return f"Task added: {task} (Priority: {priority})"
    
    def list_tasks(self, filter_status: Optional[str] = None):
        """List all tasks, optionally filtered by status"""
        if not self.tasks:
            return "You have no tasks yet."
        
        filtered_tasks = self.tasks
        if filter_status:
            filtered_tasks = [t for t in self.tasks if t['status'] == filter_status]
        
        if not filtered_tasks:
            return f"No {filter_status} tasks found."
        
        output = "\n=== Your Tasks ===\n"
        for task in filtered_tasks:
            status_icon = "✓" if task['status'] == 'completed' else "○"
            output += f"{status_icon} [{task['priority'].upper()}] {task['task']}\n"
        return output
    
    def complete_task(self, task_id: int):
        """Mark a task as completed"""
        for task in self.tasks:
            if task['id'] == task_id:
                task['status'] = 'completed'
                task['completed'] = datetime.now().isoformat()
                self.save_memory()
                return f"Task completed: {task['task']}"
        return "Task not found."
    
    def add_knowledge(self, topic: str, info: str):
        """Add to knowledge base"""
        self.knowledge_base[topic] = {
            'info': info,
            'added': datetime.now().isoformat()
        }
        self.save_memory()
        return f"Knowledge added about: {topic}"
    
    def recall_knowledge(self, topic: str):
        """Retrieve knowledge from knowledge base"""
        if topic in self.knowledge_base:
            return self.knowledge_base[topic]['info']
        return f"I don't have any information about '{topic}' yet."
    
    def greet(self):
        """Generate a personalized greeting"""
        hour = datetime.now().hour
        
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 18:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        if self.user_name:
            return f"{time_greeting}, {self.user_name}! I'm {self.name}, your personal AI assistant. How can I help you today?"
        else:
            return f"{time_greeting}! I'm {self.name}, your personal AI assistant. What's your name?"
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate appropriate response"""
        user_input_lower = user_input.lower().strip()
        
        # Deactivate command
        if user_input_lower in ['sleep', 'deactivate', 'standby']:
            self.activated = False
            return f"Going to sleep. Say '{self.name}' to wake me up again!"
        
        # Set user name
        if not self.user_name and len(user_input.split()) <= 3:
            self.user_name = user_input.strip()
            self.save_memory()
            return f"Nice to meet you, {self.user_name}! I'm here to help you with tasks, remember things, and learn your preferences. Try saying 'help' to see what I can do!"
        
        # Help command
        if 'help' in user_input_lower:
            return self.show_help()
        
        # Task management
        if 'add task' in user_input_lower or 'new task' in user_input_lower:
            task = user_input.lower().replace('add task', '').replace('new task', '').strip()
            priority = 'high' if 'urgent' in user_input_lower or 'important' in user_input_lower else 'medium'
            return self.add_task(task, priority)
        
        if 'show tasks' in user_input_lower or 'list tasks' in user_input_lower:
            return self.list_tasks()
        
        if 'complete task' in user_input_lower:
            try:
                task_id = int(''.join(filter(str.isdigit, user_input)))
                return self.complete_task(task_id)
            except:
                return "Please specify the task ID number to complete."
        
        # Preference learning
        if 'i prefer' in user_input_lower or 'i like' in user_input_lower:
            parts = user_input_lower.split('prefer' if 'prefer' in user_input_lower else 'like')
            if len(parts) > 1:
                pref = parts[1].strip()
                return self.learn_preference('general_preference', pref)
        
        # Knowledge base
        if 'remember that' in user_input_lower or 'note that' in user_input_lower:
            topic = user_input.split('that')[0].strip()
            info = user_input.split('that')[1].strip()
            return self.add_knowledge(topic, info)
        
        if 'what do you know about' in user_input_lower:
            topic = user_input_lower.replace('what do you know about', '').strip().rstrip('?')
            return self.recall_knowledge(topic)
        
        # Memory recall
        if 'my name' in user_input_lower:
            if self.user_name:
                return f"Your name is {self.user_name}!"
            return "I don't know your name yet. What should I call you?"
        
        # Conversation history
        if 'what did we talk about' in user_input_lower or 'previous conversation' in user_input_lower:
            if len(self.conversation_history) > 1:
                last_conv = self.conversation_history[-2]
                return f"Previously, you said: '{last_conv['user']}' and I responded: '{last_conv['atlas']}'"
            return "This is our first conversation!"
        
        # Exit
        if user_input_lower in ['exit', 'quit', 'bye', 'goodbye']:
            return f"Goodbye, {self.user_name if self.user_name else 'friend'}! I'll remember our conversation. See you next time!"
        
        # Default conversational responses
        return self.generate_response(user_input)
    
    def generate_response(self, user_input: str) -> str:
        """Generate contextual conversational responses"""
        responses = [
            f"I understand you're saying: '{user_input}'. Could you tell me more?",
            f"Interesting! I've noted that down. Would you like me to remember this?",
            f"Thanks for sharing that with me, {self.user_name if self.user_name else 'friend'}!",
            f"I'm learning more about you. What else would you like to discuss?",
            f"Got it! Is there anything specific you'd like me to help you with?",
        ]
        return random.choice(responses)
    
    def speak(self, text: str):
        """Speak text using text-to-speech"""
        print(f"\n{self.name}: {text}")
        if self.tts_engine and TTS_AVAILABLE:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"[TTS Error: {e}]")
    
    def listen_for_wake_word(self) -> bool:
        """Listen for the wake word 'Atlas'"""
        if not self.recognizer or not self.microphone or not SPEECH_AVAILABLE:
            return False
        
        try:
            with self.microphone as source:
                print(f"[🎤 Listening for '{self.name}'... Speak clearly!]")
                # Listen with adjusted parameters for better detection
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=4)
            
            print("[Processing speech...]")
            text = self.recognizer.recognize_google(audio).lower()
            print(f"[✓ Heard: '{text}']")
            
            if self.name.lower() in text:
                print(f"[✓ Wake word '{self.name}' detected!]")
                return True
            else:
                print(f"[✗ Wake word not found in: '{text}']")
                
        except Exception as e:
            error_name = type(e).__name__
            if "WaitTimeoutError" in error_name:
                print("[⏱ Timeout - No speech detected]")
            elif "UnknownValueError" in error_name:
                print("[✗ Could not understand audio - try speaking louder]")
            else:
                print(f"[Listen Error: {e}]")
        
        return False
    
    def listen_for_command(self) -> str:
        """Listen for user command after wake word"""
        if not self.recognizer or not self.microphone or not SPEECH_AVAILABLE:
            return ""
        
        try:
            with self.microphone as source:
                print("[🎤 Listening for your command... Speak now!]")
                # Longer timeout for commands
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)
            
            print("[Processing your command...]")
            text = self.recognizer.recognize_google(audio)
            print(f"[✓ You said: '{text}']")
            return text
            
        except Exception as e:
            error_name = type(e).__name__
            if "UnknownValueError" in error_name:
                msg = "I didn't catch that. Could you repeat more clearly?"
                print(f"[✗ {msg}]")
                self.speak(msg)
            elif "WaitTimeoutError" in error_name:
                print("[⏱ Timeout - No command heard]")
            else:
                print(f"[Listen Error: {e}]")
            return ""
    
    def show_help(self) -> str:
        """Display available commands"""
        help_text = f"""
=== {self.name} - Personal AI Assistant ===

Voice Mode: {'ENABLED' if self.voice_mode else 'DISABLED'}
Wake Word: Say "{self.name}" to activate

Available Commands:
  • help - Show this help message
  
Task Management:
  • add task [task description] - Add a new task
  • show tasks - List all tasks
  • complete task [task_id] - Mark task as complete
  
Memory & Learning:
  • i prefer [preference] - Teach me your preferences
  • remember that [topic] [info] - Add to knowledge base
  • what do you know about [topic] - Recall knowledge
  
Conversation:
  • my name - Ask me your name
  • what did we talk about - Recall previous conversation
  • sleep/deactivate - Return to listening for wake word
  • exit/bye - End conversation

Just talk to me naturally - I'm learning from every conversation!
"""
        return help_text
    
    def run(self):
        """Main conversation loop with voice activation"""
        print("=" * 60)
        print(f"  {self.name.upper()} - Your Personal AI Assistant")
        print("=" * 60)
        
        if self.voice_mode and SPEECH_AVAILABLE:
            print(f"\n🎤 VOICE MODE ACTIVATED")
            print(f"Say '{self.name}' to wake me up!")
            print("Or type 'text' to switch to text mode")
            print("=" * 60)
            
            # Voice mode main loop
            while True:
                try:
                    # Check for text input override
                    import select
                    import sys
                    
                    # Listen for wake word
                    if not self.activated:
                        if self.listen_for_wake_word():
                            self.activated = True
                            response = f"Yes, how can I help you, {self.user_name if self.user_name else 'there'}?"
                            self.speak(response)
                        continue
                    
                    # If activated, listen for command
                    if self.activated:
                        user_input = self.listen_for_command()
                        
                        if not user_input:
                            continue
                        
                        response = self.process_input(user_input)
                        self.speak(response)
                        
                        # Remember the conversation
                        self.remember_conversation(user_input, response)
                        
                        # Exit condition
                        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                            break
                        
                        # Auto-deactivate after response unless in continuous mode
                        if not self.activated:
                            self.speak(f"Say '{self.name}' when you need me again.")
                        
                except KeyboardInterrupt:
                    print(f"\n\n{self.name}: Goodbye! Memory saved.")
                    self.save_memory()
                    break
                except Exception as e:
                    print(f"\n{self.name}: I encountered an error: {e}")
        
        else:
            # Text mode fallback
            print(f"\n💬 TEXT MODE")
            print(self.greet())
            print("\nType 'help' for available commands or just chat with me!")
            print("=" * 60)
            
            while True:
                try:
                    user_input = input(f"\n{self.user_name if self.user_name else 'You'}: ").strip()
                    
                    if not user_input:
                        continue
                    
                    response = self.process_input(user_input)
                    print(f"\n{self.name}: {response}")
                    
                    # Remember the conversation
                    self.remember_conversation(user_input, response)
                    
                    # Exit condition
                    if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                        break
                        
                except KeyboardInterrupt:
                    print(f"\n\n{self.name}: Goodbye! Memory saved.")
                    self.save_memory()
                    break
                except Exception as e:
                    print(f"\n{self.name}: I encountered an error: {e}")


class AtlasGUI:
    """GUI window for Atlas AI Assistant"""
    
    def __init__(self, atlas_instance):
        self.atlas = atlas_instance
        self.window = tk.Tk()
        self.window.title("ATLAS - Personal AI Assistant")
        self.window.geometry("800x600")
        self.window.configure(bg='#1e1e1e')
        
        # Set window icon (optional)
        try:
            self.window.iconbitmap('atlas_icon.ico')
        except:
            pass
        
        self.setup_ui()
        self.listening_thread = None
        self.running = True
        
    def setup_ui(self):
        """Setup the GUI interface"""
        # Title Frame
        title_frame = tk.Frame(self.window, bg='#2d2d2d', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 ATLAS",
            font=('Consolas', 24, 'bold'),
            bg='#2d2d2d',
            fg='#00ff00'
        )
        title_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(
            title_frame,
            text="● Ready",
            font=('Consolas', 12),
            bg='#2d2d2d',
            fg='#00ff00'
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Chat Display Area
        chat_frame = tk.Frame(self.window, bg='#1e1e1e')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            bg='#0d0d0d',
            fg='#00ff00',
            insertbackground='#00ff00',
            selectbackground='#2d5016',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input Frame
        input_frame = tk.Frame(self.window, bg='#2d2d2d')
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.input_field = tk.Entry(
            input_frame,
            font=('Consolas', 12),
            bg='#0d0d0d',
            fg='#00ff00',
            insertbackground='#00ff00',
            relief=tk.FLAT
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_field.bind('<Return>', self.send_message)
        
        send_button = tk.Button(
            input_frame,
            text="Send",
            font=('Consolas', 11, 'bold'),
            bg='#00ff00',
            fg='#000000',
            relief=tk.FLAT,
            command=self.send_message,
            cursor='hand2',
            padx=20
        )
        send_button.pack(side=tk.RIGHT)
        
        # Control Frame
        control_frame = tk.Frame(self.window, bg='#2d2d2d')
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        if self.atlas.voice_mode and SPEECH_AVAILABLE:
            self.voice_button = tk.Button(
                control_frame,
                text="🎤 Start Listening",
                font=('Consolas', 10),
                bg='#2d5016',
                fg='#00ff00',
                relief=tk.FLAT,
                command=self.toggle_voice,
                cursor='hand2'
            )
            self.voice_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = tk.Button(
            control_frame,
            text="Clear Chat",
            font=('Consolas', 10),
            bg='#4d2d2d',
            fg='#ff5555',
            relief=tk.FLAT,
            command=self.clear_chat,
            cursor='hand2'
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        help_button = tk.Button(
            control_frame,
            text="Help",
            font=('Consolas', 10),
            bg='#2d4d4d',
            fg='#5599ff',
            relief=tk.FLAT,
            command=self.show_help,
            cursor='hand2'
        )
        help_button.pack(side=tk.LEFT, padx=5)
        
        # Initial greeting
        self.add_message("ATLAS", self.atlas.greet())
        
        # Auto-start voice listening if available
        if self.atlas.voice_mode and SPEECH_AVAILABLE:
            self.add_message("SYSTEM", "🎤 Voice mode is active! Say 'Atlas' to give commands.")
            # Start listening automatically after a short delay
            self.window.after(1000, self.auto_start_listening)
        
    def add_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "ATLAS":
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            self.chat_display.insert(tk.END, f"ATLAS: ", 'atlas')
            self.chat_display.insert(tk.END, f"{message}\n\n", 'message')
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
            self.chat_display.insert(tk.END, f"{sender}: ", 'user')
            self.chat_display.insert(tk.END, f"{message}\n\n", 'message')
        
        # Configure tags
        self.chat_display.tag_config('timestamp', foreground='#666666')
        self.chat_display.tag_config('atlas', foreground='#00ff00', font=('Consolas', 11, 'bold'))
        self.chat_display.tag_config('user', foreground='#5599ff', font=('Consolas', 11, 'bold'))
        self.chat_display.tag_config('message', foreground='#cccccc')
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        """Send message to Atlas"""
        message = self.input_field.get().strip()
        
        if not message:
            return
        
        # Display user message
        user_name = self.atlas.user_name if self.atlas.user_name else "You"
        self.add_message(user_name, message)
        
        # Clear input field
        self.input_field.delete(0, tk.END)
        
        # Process message in separate thread to keep GUI responsive
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        """Process message and get response from Atlas"""
        response = self.atlas.process_input(message)
        
        # Update GUI from main thread
        self.window.after(0, self.add_message, "ATLAS", response)
        
        # Speak if voice mode enabled
        if self.atlas.tts_engine and TTS_AVAILABLE:
            try:
                self.atlas.tts_engine.say(response)
                self.atlas.tts_engine.runAndWait()
            except:
                pass
        
        # Save conversation
        self.atlas.remember_conversation(message, response)
        
        # Check for exit
        if message.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            self.window.after(2000, self.window.quit)
    
    def toggle_voice(self):
        """Toggle voice listening mode"""
        if not self.listening_thread or not self.listening_thread.is_alive():
            # Start listening
            self.listening_thread = threading.Thread(target=self.voice_listen_loop, daemon=True)
            self.listening_thread.start()
            if hasattr(self, 'voice_button'):
                self.voice_button.config(text="🎤 Listening...", bg='#ff5555')
            self.update_status("● Listening for 'Atlas'...", '#ff5555')
        else:
            # Stop listening
            self.running = False
            if hasattr(self, 'voice_button'):
                self.voice_button.config(text="🎤 Start Listening", bg='#2d5016')
            self.update_status("● Ready", '#00ff00')
    
    def auto_start_listening(self):
        """Automatically start voice listening when GUI opens"""
        if self.atlas.voice_mode and SPEECH_AVAILABLE and self.atlas.recognizer:
            self.toggle_voice()
    
    def voice_listen_loop(self):
        """Voice listening loop"""
        self.running = True
        
        while self.running:
            try:
                if self.atlas.listen_for_wake_word():
                    self.window.after(0, self.update_status, "● Activated! Listening for command...", '#ffff00')
                    self.window.after(0, self.add_message, "SYSTEM", "Wake word detected!")
                    
                    command = self.atlas.listen_for_command()
                    
                    if command:
                        self.window.after(0, self.add_message, self.atlas.user_name or "You", command)
                        response = self.atlas.process_input(command)
                        self.window.after(0, self.add_message, "ATLAS", response)
                        
                        if self.atlas.tts_engine:
                            try:
                                self.atlas.tts_engine.say(response)
                                self.atlas.tts_engine.runAndWait()
                            except:
                                pass
                        
                        self.atlas.remember_conversation(command, response)
                    
                    self.window.after(0, self.update_status, "● Listening for 'Atlas'...", '#00ff00')
                    
            except Exception as e:
                print(f"Voice error: {e}")
                
        self.window.after(0, self.update_status, "● Ready", '#00ff00')
    
    def update_status(self, text, color):
        """Update status label"""
        self.status_label.config(text=text, fg=color)
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.add_message("SYSTEM", "Chat cleared.")
    
    def show_help(self):
        """Display help information"""
        help_text = self.atlas.show_help()
        self.add_message("ATLAS", help_text)
    
    def run(self):
        """Run the GUI"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.atlas.save_memory()
        self.window.destroy()


if __name__ == "__main__":
    # Check if voice mode is available
    voice_enabled = SPEECH_AVAILABLE and TTS_AVAILABLE
    
    if not voice_enabled:
        print("\n⚠️  Voice mode unavailable. Install dependencies:")
        print("   pip install SpeechRecognition pyttsx3 pyaudio")
        print("\nStarting in TEXT mode...\n")
    
    # Create Atlas instance
    atlas = Atlas("Atlas", voice_mode=voice_enabled)
    
    # Create and run GUI
    gui = AtlasGUI(atlas)
    gui.run()
