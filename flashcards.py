import streamlit as st
import json
import re
import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from response import openai_api_call
from fiber import FiberDBMS
from openai.types.chat import ChatCompletionMessageParam


def get_context_for_topic(dbms, topic):
    """Extracts keywords from a topic and queries the database for relevant context."""
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(topic)
    keywords = [word for word in words if word.lower() not in stop_words and word.isalpha()]
    
    if not keywords:
        return ""

    results = dbms.query(" ".join(keywords), top_n=10)
    
    if not results:
        return ""

    context = "Here is some relevant information from your documents:\n\n"
    for result in results:
        context += f"--- Start of content from {result['name']} ---\n"
        context += f"{result['content']}\n"
        context += f"--- End of content from {result['name']} ---\n\n"
    return context


def flashcards_page():
    st.title("🧠 Q&A Flashcard Generator")
    st.write("Generate interactive flashcards from your indexed documents to help you study effectively.")

    # Initialize session state for flashcards
    if 'flashcards' not in st.session_state:
        st.session_state.flashcards = []
    if 'current_card' not in st.session_state:
        st.session_state.current_card = 0
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'flashcard_mode' not in st.session_state:
        st.session_state.flashcard_mode = "generate"
    if 'flashcard_collections' not in st.session_state:
        st.session_state.flashcard_collections = {}
    if 'study_settings' not in st.session_state:
        st.session_state.study_settings = {
            'test_mode': 'Question to Answer',  # or 'Answer to Question'
            'show_feedback': True
        }
    if 'study_session' not in st.session_state:
        st.session_state.study_session = {
            'active': False,
            'current_question': 0,
            'user_answers': [],
            'scores': []
        }

    # Check if database is available, attempt to load from file if not found
    dbms = None
    if 'dbms' in st.session_state and isinstance(st.session_state.dbms, FiberDBMS) and not st.session_state.dbms.is_empty():
        dbms = st.session_state.dbms
    else:
        # Try to load from arcana_index.csv
        try:
            import os
            index_file = "arcana_index.csv"
            if os.path.exists(index_file):
                dbms = FiberDBMS()
                dbms.load_from_file(index_file)
                st.session_state.dbms = dbms
                if dbms.is_empty():
                    dbms = None
            else:
                dbms = None
        except Exception:
            dbms = None
    
    if dbms is None:
        st.warning("⚠️ No indexed files found. Please go to the 'Files' page and index your documents first.")
        st.info("💡 Flashcards work best when generated from your own study materials and documents.")
        return

    # Mode selection
    mode = st.radio(
        "Choose mode:",
        ["Generate New Flashcards", "Collections", "Study Mode", "Browse Existing Flashcards"],
        key='flashcard_mode_selector',
        horizontal=True,
    )

    if mode == "Generate New Flashcards":
        render_flashcard_generation(dbms)
    elif mode == "Collections":
        render_collections_mode()
    elif mode == "Study Mode":
        render_study_mode()
    else:
        render_flashcard_study_mode()


def render_flashcard_generation(dbms):
    st.subheader("📝 Generate Flashcards")
    
    # Input for topic
    topic = st.text_input("Enter the topic or subject for your flashcards:", 
                         placeholder="e.g., Biology, History, Mathematics")
    
    # Number of flashcards to generate
    num_cards = st.slider("Number of flashcards to generate:", min_value=5, max_value=50, value=10)
    
    # Difficulty level
    difficulty = st.selectbox("Difficulty level:", 
                             ["Basic", "Intermediate", "Advanced"])

    if st.button("🎯 Generate Flashcards", type="primary") and topic:
        with st.spinner(f"Generating {num_cards} flashcards about {topic}..."):
            # Get context from indexed documents
            context = get_context_for_topic(dbms, topic)
            
            if not context:
                st.warning("No relevant content found in your documents for this topic. Try a different topic or check your indexed files.")
                st.info("💡 Make sure your topic matches content in your indexed documents.")
                return
            
            # Show context preview
            with st.expander("📄 Context Found"):
                st.text(context[:500] + "..." if len(context) > 500 else context)
            
            # Generate flashcards using AI
            try:
                flashcards = generate_flashcards_from_context(context, topic, num_cards, difficulty)
                
                if flashcards and len(flashcards) > 0:
                    st.session_state.flashcards = flashcards
                    st.session_state.current_card = 0
                    st.session_state.show_answer = False
                    st.success(f"✅ Generated {len(flashcards)} flashcards successfully!")
                    
                    # Option to save to collection
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        collection_name = st.text_input("Save to collection (optional):", 
                                                       placeholder="Enter collection name to save these flashcards")
                    with col2:
                        if st.button("💾 Save", disabled=not collection_name):
                            st.session_state.flashcard_collections[collection_name] = {
                                'topic': topic,
                                'difficulty': difficulty,
                                'flashcards': flashcards.copy(),
                                'created_at': str(datetime.datetime.now())
                            }
                            st.success(f"Saved to collection: {collection_name}")
                    
                    # Show preview of generated flashcards
                    with st.expander("📋 Preview Generated Flashcards"):
                        for i, card in enumerate(flashcards, 1):
                            st.write(f"**Card {i}:**")
                            st.write(f"**Q:** {card['question']}")
                            st.write(f"**A:** {card['answer']}")
                            st.markdown("---")
                else:
                    st.error("❌ Failed to generate flashcards. This could be due to:")
                    st.write("• AI service connectivity issues")
                    st.write("• Insufficient context in your documents")
                    st.write("• Topic too specific or general")
                    st.info("💡 Try a different topic or check your indexed documents.")
                    
            except Exception as e:
                st.error(f"❌ Error during flashcard generation: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")


def render_flashcard_study_mode():
    if not st.session_state.flashcards:
        st.info("📚 No flashcards available. Please generate some flashcards first!")
        return
    
    st.subheader("🎓 Study Mode")
    
    total_cards = len(st.session_state.flashcards)
    current_idx = st.session_state.current_card
    
    # Progress indicator
    progress = (current_idx + 1) / total_cards
    st.progress(progress)
    st.write(f"Card {current_idx + 1} of {total_cards}")
    
    # Current flashcard
    current_card = st.session_state.flashcards[current_idx]
    
    # Question
    st.markdown(f"### 🤔 Question:")
    st.markdown(f"**{current_card['question']}**")
    
    # Show/Hide answer button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.show_answer:
            if st.button("🔍 Show Answer", key="show_answer_btn"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            st.markdown(f"### ✅ Answer:")
            st.markdown(f"**{current_card['answer']}**")
            
            # Self-assessment buttons
            st.markdown("### How well did you know this?")
            col_easy, col_medium, col_hard = st.columns(3)
            
            with col_easy:
                if st.button("😊 Easy", key="easy_btn"):
                    next_card()
            with col_medium:
                if st.button("🤔 Medium", key="medium_btn"):
                    next_card()
            with col_hard:
                if st.button("😅 Hard", key="hard_btn"):
                    next_card()
    
    # Navigation buttons
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button("⏮️ First", disabled=(current_idx == 0)):
            st.session_state.current_card = 0
            st.session_state.show_answer = False
            st.rerun()
    
    with nav_col2:
        if st.button("⏪ Previous", disabled=(current_idx == 0)):
            st.session_state.current_card = max(0, current_idx - 1)
            st.session_state.show_answer = False
            st.rerun()
    
    with nav_col3:
        if st.button("⏩ Next", disabled=(current_idx == total_cards - 1)):
            st.session_state.current_card = min(total_cards - 1, current_idx + 1)
            st.session_state.show_answer = False
            st.rerun()
    
    with nav_col4:
        if st.button("⏭️ Last", disabled=(current_idx == total_cards - 1)):
            st.session_state.current_card = total_cards - 1
            st.session_state.show_answer = False
            st.rerun()
    
    # Reset study session
    if st.button("🔄 Restart Study Session"):
        st.session_state.current_card = 0
        st.session_state.show_answer = False
        st.rerun()


def next_card():
    """Move to the next flashcard"""
    total_cards = len(st.session_state.flashcards)
    if st.session_state.current_card < total_cards - 1:
        st.session_state.current_card += 1
        st.session_state.show_answer = False
    else:
        st.session_state.current_card = 0  # Loop back to first card
        st.session_state.show_answer = False
        st.balloons()  # Celebrate completing all cards
    st.rerun()


def generate_flashcards_from_context(context, topic, num_cards, difficulty):
    """Generate flashcards using AI based on the provided context"""
    try:
        prompt = f"""
Based on the following content about {topic}, create exactly {num_cards} flashcards at a {difficulty.lower()} level.

Context:
{context}

Instructions:
- Create clear, specific questions that test understanding of the material
- Provide accurate, concise answers
- For {difficulty.lower()} level: {'basic recall and definitions' if difficulty == 'Basic' else 'application and analysis' if difficulty == 'Intermediate' else 'synthesis and evaluation'}
- Ensure questions are varied and cover different aspects of the topic
- Each flashcard must have both a question and an answer
- Return ONLY valid JSON - no other text

Return EXACTLY this JSON format:
[
  {{"question": "What is...?", "answer": "The answer is..."}},
  {{"question": "How does...?", "answer": "It works by..."}}
]
"""
        
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": prompt}
        ]
        
        response = openai_api_call(messages)
        
        if not response:
            st.error("No response from AI service")
            return None
        
        # Handle generator response from streaming API
        if hasattr(response, '__iter__') and not isinstance(response, str):
            # If response is a generator, collect all chunks
            response_text = ''.join(str(chunk) for chunk in response)
        else:
            response_text = str(response)
        
        # Debug: Show raw response (remove in production)
        with st.expander("🔍 Debug: Raw AI Response"):
            st.text(response_text[:500] + "..." if len(response_text) > 500 else response_text)
        
        # Clean the response text
        response_text = response_text.strip()
        
        # Try to extract JSON from the response
        flashcards = None
        
        # Method 1: Direct JSON parsing
        try:
            flashcards = json.loads(response_text)
            if isinstance(flashcards, list) and len(flashcards) > 0:
                # Validate structure
                valid_cards = []
                for card in flashcards:
                    if isinstance(card, dict) and 'question' in card and 'answer' in card:
                        # Clean the question and answer
                        question = str(card['question']).strip()
                        answer = str(card['answer']).strip()
                        if question and answer:
                            valid_cards.append({'question': question, 'answer': answer})
                
                if valid_cards:
                    st.success(f"✅ Successfully parsed {len(valid_cards)} flashcards via direct JSON")
                    return valid_cards[:num_cards]
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract JSON array pattern
        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                flashcards = json.loads(json_str)
                if isinstance(flashcards, list) and len(flashcards) > 0:
                    valid_cards = []
                    for card in flashcards:
                        if isinstance(card, dict) and 'question' in card and 'answer' in card:
                            question = str(card['question']).strip()
                            answer = str(card['answer']).strip()
                            if question and answer:
                                valid_cards.append({'question': question, 'answer': answer})
                    
                    if valid_cards:
                        st.success(f"✅ Successfully parsed {len(valid_cards)} flashcards via pattern matching")
                        return valid_cards[:num_cards]
            except json.JSONDecodeError as e:
                st.warning(f"JSON parsing failed: {str(e)}")
        
        # Method 3: Fallback text parsing
        lines = response_text.split('\n')
        flashcards = []
        current_card = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for question patterns
            if (line.startswith('Q:') or line.startswith('Question:') or 
                line.startswith('"question":') or 'question' in line.lower()):
                
                if current_card and 'question' in current_card and 'answer' in current_card:
                    flashcards.append(current_card)
                
                # Extract question
                if ':' in line:
                    question = line.split(':', 1)[1].strip()
                    question = question.strip('"').strip("'").strip()
                    current_card = {'question': question}
                
            # Look for answer patterns
            elif (line.startswith('A:') or line.startswith('Answer:') or 
                  line.startswith('"answer":') or 'answer' in line.lower()):
                
                if 'question' in current_card:
                    # Extract answer
                    if ':' in line:
                        answer = line.split(':', 1)[1].strip()
                        answer = answer.strip('"').strip("'").strip()
                        current_card['answer'] = answer
        
        # Add the last card if complete
        if current_card and 'question' in current_card and 'answer' in current_card:
            flashcards.append(current_card)
        
        if flashcards:
            st.success(f"✅ Successfully parsed {len(flashcards)} flashcards via text parsing")
            return flashcards[:num_cards]
        
        # If all methods fail, create some default cards based on the topic
        st.warning("AI response couldn't be parsed. Creating basic flashcards...")
        default_cards = [
            {
                "question": f"What is the main concept of {topic}?",
                "answer": f"The main concept relates to the key principles and ideas in {topic}."
            },
            {
                "question": f"Why is {topic} important?",
                "answer": f"{topic} is important because it helps us understand fundamental concepts in this field."
            }
        ]
        
        return default_cards[:num_cards]
            
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        st.info("Please try again with a different topic or check your internet connection.")
        return None


def render_collections_mode():
    st.subheader("📚 Flashcard Collections")
    
    if not st.session_state.flashcard_collections:
        st.info("No collections saved yet. Generate some flashcards and save them to create collections!")
        return
    
    # Display existing collections
    st.write("**Saved Collections:**")
    
    for collection_name, collection_data in st.session_state.flashcard_collections.items():
        with st.expander(f"📖 {collection_name} ({len(collection_data['flashcards'])} cards)"):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Topic:** {collection_data['topic']}")
                st.write(f"**Difficulty:** {collection_data['difficulty']}")
                st.write(f"**Created:** {collection_data['created_at'][:16]}")
            
            with col2:
                if st.button(f"📖 Load for Browsing", key=f"load_{collection_name}"):
                    st.session_state.flashcards = collection_data['flashcards'].copy()
                    st.session_state.current_card = 0
                    st.session_state.show_answer = False
                    st.success(f"Loaded {collection_name} for browsing!")
                
                if st.button(f"🎓 Load for Study", key=f"study_{collection_name}"):
                    st.session_state.flashcards = collection_data['flashcards'].copy()
                    st.session_state.study_session = {
                        'active': True,
                        'current_question': 0,
                        'user_answers': [],
                        'scores': [],
                        'total_questions': len(collection_data['flashcards'])
                    }
                    st.success(f"Loaded {collection_name} for study mode!")
                    st.rerun()
            
            with col3:
                if st.button(f"🗑️", key=f"delete_{collection_name}", help="Delete collection"):
                    if st.session_state.get(f"confirm_delete_{collection_name}", False):
                        del st.session_state.flashcard_collections[collection_name]
                        st.success(f"Deleted {collection_name}")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{collection_name}"] = True
                        st.warning("Click again to confirm deletion")
            
            # Show preview of cards in collection
            if st.checkbox(f"Preview cards", key=f"preview_{collection_name}"):
                for i, card in enumerate(collection_data['flashcards'][:3], 1):  # Show first 3 cards
                    st.write(f"**Card {i}:** {card['question']}")
                if len(collection_data['flashcards']) > 3:
                    st.write(f"... and {len(collection_data['flashcards']) - 3} more cards")


def render_study_mode():
    st.subheader("🎯 AI-Powered Study Mode")
    
    if not st.session_state.flashcards:
        st.warning("No flashcards loaded! Please load a collection or generate new flashcards first.")
        return
    
    # Study Settings
    with st.expander("⚙️ Study Settings"):
        col1, col2 = st.columns(2)
        with col1:
            test_mode = st.selectbox(
                "Test Mode:",
                ["Question to Answer", "Answer to Question"],
                index=0 if st.session_state.study_settings['test_mode'] == 'Question to Answer' else 1
            )
            st.session_state.study_settings['test_mode'] = test_mode
        
        with col2:
            show_feedback = st.checkbox(
                "Show AI Feedback",
                value=st.session_state.study_settings['show_feedback']
            )
            st.session_state.study_settings['show_feedback'] = show_feedback
    
    # Start study session if not active
    if not st.session_state.study_session['active']:
        st.info("Click 'Start Study Session' to begin AI-powered testing!")
        if st.button("🚀 Start Study Session", type="primary"):
            st.session_state.study_session = {
                'active': True,
                'current_question': 0,
                'user_answers': [],
                'scores': [],
                'total_questions': len(st.session_state.flashcards)
            }
            st.rerun()
        return
    
    # Active study session
    session = st.session_state.study_session
    current_idx = session['current_question']
    
    if current_idx >= len(st.session_state.flashcards):
        # Study session complete
        render_study_results()
        return
    
    # Progress
    progress = (current_idx + 1) / session['total_questions']
    st.progress(progress)
    st.write(f"Question {current_idx + 1} of {session['total_questions']}")
    
    # Current question
    current_card = st.session_state.flashcards[current_idx]
    
    if st.session_state.study_settings['test_mode'] == 'Question to Answer':
        prompt_text = current_card['question']
        correct_answer = current_card['answer']
        st.markdown(f"### 🤔 Question:")
    else:
        prompt_text = current_card['answer']
        correct_answer = current_card['question']
        st.markdown(f"### 🎯 Given Answer:")
    
    st.markdown(f"**{prompt_text}**")
    
    # User input
    user_answer = st.text_area(
        "Your answer:" if st.session_state.study_settings['test_mode'] == 'Question to Answer' else "What was the question?",
        key=f"answer_{current_idx}",
        height=100
    )
    
    # Submit answer
    if st.button("✅ Submit Answer", disabled=not user_answer.strip()):
        with st.spinner("Getting AI feedback..."):
            # Get AI feedback
            feedback = get_ai_feedback(user_answer, correct_answer, prompt_text)
            
            # Store answer and feedback
            session['user_answers'].append({
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'prompt': prompt_text,
                'feedback': feedback
            })
            
            # Display feedback
            if st.session_state.study_settings['show_feedback']:
                if "correct" in feedback.lower() or "right" in feedback.lower():
                    st.success(f"✅ {feedback}")
                else:
                    st.error(f"❌ {feedback}")
                    st.info(f"**Correct answer:** {correct_answer}")
            
            # Move to next question
            session['current_question'] += 1
            st.session_state.study_session = session
            
            if session['current_question'] < session['total_questions']:
                if st.button("➡️ Next Question"):
                    st.rerun()
            else:
                if st.button("🏁 Finish Study Session"):
                    st.rerun()


def render_study_results():
    st.subheader("📊 Study Session Results")
    
    session = st.session_state.study_session
    total_questions = len(session['user_answers'])
    
    if total_questions == 0:
        st.warning("No answers recorded!")
        return
    
    # Calculate score
    correct_count = 0
    for answer_data in session['user_answers']:
        feedback = answer_data['feedback'].lower()
        if "correct" in feedback or "right" in feedback:
            correct_count += 1
    
    score_percentage = (correct_count / total_questions) * 100
    
    # Display overall results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", total_questions)
    with col2:
        st.metric("Correct Answers", correct_count)
    with col3:
        st.metric("Score", f"{score_percentage:.1f}%")
    
    # Performance indicator
    if score_percentage >= 80:
        st.success(f"🎉 Excellent work! You scored {score_percentage:.1f}%")
    elif score_percentage >= 60:
        st.warning(f"👍 Good job! You scored {score_percentage:.1f}%")
    else:
        st.error(f"📚 Keep studying! You scored {score_percentage:.1f}%")
    
    # Detailed results
    with st.expander("📋 Detailed Results"):
        for i, answer_data in enumerate(session['user_answers'], 1):
            st.write(f"**Question {i}:**")
            st.write(f"**Prompt:** {answer_data['prompt']}")
            st.write(f"**Your Answer:** {answer_data['user_answer']}")
            st.write(f"**Correct Answer:** {answer_data['correct_answer']}")
            
            feedback = answer_data['feedback'].lower()
            if "correct" in feedback or "right" in feedback:
                st.success(f"**Feedback:** {answer_data['feedback']}")
            else:
                st.error(f"**Feedback:** {answer_data['feedback']}")
            st.markdown("---")
    
    # Reset session
    if st.button("🔄 Start New Study Session"):
        st.session_state.study_session = {
            'active': False,
            'current_question': 0,
            'user_answers': [],
            'scores': []
        }
        st.rerun()


def get_ai_feedback(user_answer, correct_answer, prompt):
    """Get AI feedback comparing user answer to correct answer"""
    try:
        feedback_prompt = f"""
Compare the user's answer to the correct answer and provide brief feedback in one line.

Prompt: {prompt}
User's Answer: {user_answer}
Correct Answer: {correct_answer}

Instructions:
- If the user's answer is essentially correct (covers the main points), start with "Correct!" 
- If the user's answer is wrong or incomplete, start with "Incorrect." and briefly explain what was missing
- Keep feedback to one line, be encouraging but accurate
- Focus on the key concepts that were right or wrong

Feedback:"""
        
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": feedback_prompt}
        ]
        
        response = openai_api_call(messages)
        
        if response:
            # Handle generator response
            if hasattr(response, '__iter__') and not isinstance(response, str):
                feedback = ''.join(str(chunk) for chunk in response)
            else:
                feedback = str(response)
            
            return feedback.strip()
        else:
            return "Unable to get AI feedback at this time."
            
    except Exception as e:
        return f"Error getting feedback: {str(e)}"

