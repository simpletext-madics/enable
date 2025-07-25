import datetime
import difflib
import json
import os
import random
import re

import gradio as gr
import pandas as pd

def save_data():
    file_path = "survey_and_chat_data.json"

    try:
        # Read existing data from the file if it exists
        try:
            with open(file_path, "r") as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []  # Start fresh if file doesn't exist or is empty

        # Create a new entry with all the data combined under "entry"
        new_entry = {"entry": all_data}

        # Append new entry if it's not a duplicate
        if new_entry not in existing_data:
            existing_data.append(new_entry)

        # Write updated data back to the file
        with open(file_path, "w") as file:
            json.dump(existing_data, file, indent=4)

        # Clear temporary storage after saving to avoid duplicates
        all_data.clear()

        return "Data appended successfully!", gr.update(visible=False)

    except Exception as e:
        return f"Error saving data: {e}", gr.update(visible=True)


def safe_load_json(s):
    # First, try to fix missing quotes
    fixed = fix_missing_quotes(s)
    # Optionally, you can add additional cleaning steps here (e.g., stripping control characters)
    fixed = fixed.strip()
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        print("Offending string:", fixed)
        return None
def fix_missing_quotes(s):
    s_fixed = re.sub(r"([{,]\s*)([a-zA-Z0-9_]+)\s*:", r'\1"\2":', s)
    return s_fixed

def save_interactions():
    with open("interaction_log.json", "w") as log_file:
        json.dump(interaction_log, log_file, indent=4)

def log_interaction(event_type, details):
    interaction_entry = {
        "timestamp": str(datetime.datetime.now()),
        "event_type": event_type,
        "details": details,
    }
    interaction_log.append(interaction_entry)
    save_interactions()

all_data = []
interaction_log = []


qa_data = pd.read_csv("data_annotation_new_2.csv", encoding="utf-8", delimiter=",")

qa_data.columns = qa_data.columns.str.strip()
qa_data["question"] = qa_data["question"].str.strip('",')
qa_data["answer"] = qa_data["answer"].str.strip('",')
qa_data["confirmed_parts"] = qa_data["confirmed_parts"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)
qa_data["false_claim_parts"] = qa_data["false_claim_parts"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)

qa_data["confirmed_sources"] = qa_data["confirmed_sources"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)
qa_data["false_claim_sources"] = qa_data["false_claim_sources"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)

qa_data["confirmed_sources_names"] = qa_data["confirmed_sources_names"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)
qa_data["fake_sources_names"] = qa_data["fake_sources_names"].apply(
    lambda x: safe_load_json(x) if isinstance(x, str) else x
)


qa_pairs = qa_data.to_dict(orient="records")
source_questions = [
    "Q1(neutron)",
    "Q2(Battle of Salamis)",
    "Q3(most time zones)",
    "Q4(The Master and Margarita)",
    "Q5(city-states)",
    "Q6(Blue Rider)",
    "Q7(three natural rights)",
]

filename = "source_credibility_2.json"

with open(filename, "r") as file:
    source_credibility = json.load(file)


suggested_questions = [
            "Which scientist is credited with the discovery of the neutron?",
            "Who led the Athenian navy at the Battle of Salamis?",
            "Which country has the most time zones (including overseas territories)?",
            "Who wrote *The Master and Margarita*, a novel banned in the Soviet Union for decades?",
            "The Peloponnesian War was primarily fought between which two Greek city-states?",
            "Which artist is considered a major figure in the Blue Rider movement (Der Blaue Reiter)?",
            "According to John Locke, what are the three natural rights?",
            "Who was James Chadwick?",
            "Who was Ernest Rutherford?",
            "Who was  Pericles?",
            "Who was  Themistocles?",
            "Russia timezones",
            "France timezones",
            "Who was  Boris Pasternak?",
            "Who was Mikhail Bulgakov?",
            "Athens and Corinth",
            "Athens and Sparta",
            "Who was  Wassily Kandinsky?",
            "Who was  Gustav Klimt?",
            "Liberty, Equality, Brotherhood",
            "Life, Liberty, Property",
        ]

def survey1(
    name,
    familiarity,
    information_sources,
    ai_experience,
    ai_usage,
    ai_frequency,
    ai_satisfaction,
    ai_reason,
):
    errors = []
    if not name:
        errors.append("Please specify your name.")
    if not familiarity:
        errors.append(
            "Please state your full name"
        )
    if not information_sources:
        errors.append(
            "Please select how you usually find information when researching a topic."
        )
    if not ai_experience:
        errors.append(
            "Please specify your prior experience with AI systems in professional or academic settings."
        )
    if not ai_usage:
        errors.append("Please specify if you have used an AI chat interface before.")
    if ai_usage == "Yes" and not ai_frequency:
        errors.append("Please specify how frequently you use AI chat interfaces.")
    if not ai_satisfaction:
        errors.append("Please rate your overall experience using AI chat interfaces.")
    if not ai_reason:
        errors.append(
            "Please explain why you chose your rating for AI chat interfaces."
        )

    # If there are any errors, return error messages and keep the form visible
    if errors:
        return (
            "Please correct the errors above.",
            gr.update(visible=True),  # Hide the chat section
            gr.update(visible=False),  # Hide the send button initially
        )

    # Save all the data
    all_data.append(
        {
            "survey1": {
                "name": name,
                "familiarity": familiarity,
                "information_sources": information_sources,
                "ai_experience": ai_experience,
                "ai_usage": ai_usage,
                "ai_frequency": ai_frequency,
                "ai_satisfaction": ai_satisfaction,
                "ai_reason": ai_reason,
            }
        }
    )

    # Hide the survey fields and show the next step (chat)
    return (
        "Survey 1 complete. Please proceed to the chat.",
        gr.update(value="", visible=False),
        gr.update(visible=True),
    )

def survey2(
    source_misattribution,
    correct_info_red,
    wrong_info_green,
    wrong_credibility_score,
    misinfo_in_unhighlighted,
    ai_use_ease,
    ai_use_clarity,
    highlighted_info_use,
    highlighted_info_trust,
    sources_trust_score,
    sources_reliability,
    clarity_helpful,
    clarity_clear,
    preference_for_highlighting,
    improvements,
    liked_disliked,
    thought_process,
):
    errors = []

    # Validation for each field
    if not ai_use_ease:
        errors.append("Please select your ai_use_ease.")
    if not ai_use_clarity:
        errors.append("Please select your highest level of ai_use_clarity")
    if not highlighted_info_use:
        errors.append("Please provide your occupation or current field of study.")

    if not highlighted_info_trust:
        errors.append("Please specify whether your native language is English.")
    if not sources_trust_score:
        errors.append(
            "Please select your general familiarity with technology and digital tools."
        )
    if not sources_reliability:
        errors.append(
            "Please select how you usually find information when researching a topic."
        )
    if not clarity_helpful:
        errors.append(
            "Please specify your prior experience with AI systems in professional or academic settings."
        )
    if not clarity_clear:
        errors.append("Please specify if you have used an AI chat interface before.")
    if not preference_for_highlighting:
        errors.append("Please rate your overall experience using AI chat interfaces.")
    if not improvements:
        errors.append(
            "Please specify your prior experience with AI systems in professional or academic settings."
        )
    if not liked_disliked:
        errors.append(
            "Please explain why you chose your rating for AI chat interfaces."
        )
    if not thought_process:
        errors.append(
            "Please explain why you chose your rating for AI chat interfaces."
        )

    # If there are any errors, return error messages and keep the form visible
    if errors:
        return (
            "Please answer the question about whether the AI provided useful information for your research.",
            gr.update(visible=True),
            gr.update(visible=False),
        )

    # Save feedback data, including the new question
    all_data.append(
        {
            "survey2": {
                "source_misattribution": source_misattribution,
                "correct_info_red": correct_info_red,
                "wrong_info_green": wrong_info_green,
                "wrong_credibility_score": wrong_credibility_score,
                "misinfo_in_unhighlighted": misinfo_in_unhighlighted,
                "ai_use_ease": ai_use_ease,
                "ai_use_clarity": ai_use_clarity,
                "highlighted_info_use": highlighted_info_use,
                "highlighted_info_trust": highlighted_info_trust,
                "sources_trust_score": sources_trust_score,
                "sources_reliability": sources_reliability,
                "clarity_helpful": clarity_helpful,
                "clarity_clear": clarity_clear,
                "preference_for_highlighting": preference_for_highlighting,
                "improvements": improvements,
                "liked_disliked": liked_disliked,
                "thought_process": thought_process,
            }
        }
    )

    # Save the data automatically after feedback
    save_status, _ = save_data()

    # Return everything, ensuring the thank-you message is displayed
    return (
        f"Survey 2 complete. {save_status}",
        gr.update(visible=False),  # Hide the feedback form
        gr.update(visible=True),  #
    )

def get_trust_score(source_name):
    source_name = source_name.strip()  # Ensure no leading/trailing spaces
    print(f"Checking credibility for: '{source_name}'")  # Debugging output

    # Check if the source is in the dictionary
    if source_name in source_credibility:
        credibility = source_credibility[source_name]

        # Assign scores based on credibility levels
        if credibility == "High":
            return "Trusted source"
        elif credibility in ["Medium", "Medium to High"]:
            return "Medium credibility"
        else:
            return "Low credibility"
    else:
        return "Unknown credibility"

def highlight_answer(answer, qa, highlight_types):
    source_numbers = []
    current_index = 1
    source_buttons_html = ""

    for highlight_type in highlight_types:
        if highlight_type == "Confirmed":
            for part, link, source_name in zip(
                qa["confirmed_parts"],
                qa["confirmed_sources"],
                qa["confirmed_sources_names"],
            ):
                trust_score = get_trust_score(source_name)
                # Adding tooltip to the highlighted text
                answer = answer.replace(
                    part,
                    f'<span class="source highlighted" data-source-id="{current_index}" data-source-name="{source_name}" data-link="{link}" style="background-color: lightgreen;" title="Source: {source_name} | Trust: {trust_score}">{part}</span>[{current_index}]',
                )
                source_numbers.append((source_name, link, trust_score, "Confirmed"))
                current_index += 1

        elif highlight_type == "Potential misinformation":
            for part, link, source_name in zip(
                qa["false_claim_parts"],
                qa["false_claim_sources"],
                qa["fake_sources_names"],
            ):
                trust_score = get_trust_score(source_name)
                # Adding tooltip to the highlighted text
                answer = answer.replace(
                    part,
                    f'<span class="source highlighted" data-source-id="{current_index}" data-source-name="{source_name}" data-link="{link}" style="background-color: lightcoral;" title="Source: {source_name} | Trust: {trust_score}">{part}</span>[{current_index}]',
                )
                source_numbers.append((source_name, link, trust_score, "Disagree"))
                current_index += 1

    # Generate the sources section with clickable buttons and trust scores
    sources_section = ""
    if source_numbers:
        sources_section = "<div><strong>Sources:</strong><br>"
        for i, (source_name, link, trust_score, status) in enumerate(source_numbers):
            # Font color based on source type
            if status == "Confirmed":
                font_color = "green"  # Green for confirmed sources

            else:
                font_color = "red"  # Red for fake sources

            sources_section += f"<button id='source_{i}' onclick='document.getElementById(\"link_{i}\").style.display = \"block\";' style='color: {font_color};'>{i+1}. {source_name} (Source credibility: {trust_score})</button>"
            sources_section += f"<div id='link_{i}' style='display:none;'><a href='{link}' target='_blank'>{link}</a></div><br>"

    return answer, source_numbers, sources_section


def chatbot_conversation(user_input, history=None, highlight_types=None):
    if history is None:
        history = []
    if highlight_types is None:
        highlight_types = []

    bot_response, source_numbers, sources_section = get_closest_answer(
        user_input, highlight_types
    )
    history.append((user_input, bot_response))

    log_interaction(
        "Chat Submission",
        {
            "user_input": user_input,
            "bot_response": bot_response,
            "highlight_types": highlight_types,
        },
    )

    return history, history, sources_section

def get_random_question():
            # Return a randomly selected question from the list
            return random.choice(suggested_questions)

def track_highlight_change(highlight_types):
    log_interaction(
        "Highlight Selection Change", {"selected_highlight_types": highlight_types}
    )


# Track button clicks
def track_button_click(button_name):
    log_interaction(
        "Button Click",
        {
            "button_name": button_name,
            "message": f"User clicked on the {button_name} button.",
        },
    )


# Track source clicks
def track_source_click(source_id):
    log_interaction(
        "Source Click",
        {"source_id": source_id, "message": f"User clicked on source {source_id}."},
    )
    return f""

def get_closest_answer(user_input, highlight_types):
    print("User input:", user_input)
    
    questions = [qa["question"] for qa in qa_pairs]
    print("Known questions:", questions)

    closest_question = difflib.get_close_matches(user_input, questions, n=1)
    print("Closest match found:", closest_question)

    if closest_question:
        index = questions.index(closest_question[0])
        print("Match index in qa_pairs:", index)
        
        qa = qa_pairs[index]
        print("Matched QA pair:", qa)

        highlighted_answer, source_numbers, sources_section = highlight_answer(
            qa["answer"], qa, highlight_types
        )

        print("Highlighted answer:", highlighted_answer)
        print("Sources:", source_numbers)
        print("Sources section:", sources_section)

        return highlighted_answer, source_numbers, sources_section
    else:
        print("No close match found.")
        return (
            "Sorry, I don't have an answer for that, but I can help with topics in history, science, geography, literature, and philosophy! Try asking questions like who discovered the neutron, who led the Athenian navy at Salamis, or which country has the most time zones. You can also explore individual figures like James Chadwick, Themistocles, or Mikhail Bulgakov—check out the suggestions on the right!",
            [],
            "",
        )

def handle_quiz_submission(q1, q2, q3, q4, q5, q6, q7):
    # Store answers in a dictionary
    answers = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5, "Q6": q6, "Q7": q7}

    # Log the interaction
    log_interaction("Quiz answers", answers)

    # Load previous interaction log
    with open("interaction_log.json", "r") as file:
        interaction_log = json.load(file)

    # Append this session's data to a larger collection (assumed global or session-level)
    all_data.append({"chat": interaction_log})

    return (
        f"Quiz answers saved successfully at {str(datetime.datetime.now())}",
        gr.update(visible=False),
        gr.update(visible=True),
    )
with gr.Blocks() as demo:
#Survey 1, questions and options
    with gr.Group() as survey1_group:
        gr.Markdown(
            "# Questionnaire 1: General Information and Prior Experience",
            elem_id="naslov",
        )  

        name_input = gr.Textbox(label="Full name")

        familiarity_input = gr.Dropdown(
            [
                "Select your experience level",
                "Very experienced",
                "Moderately experienced",
                "Beginner",
                "Not experienced at all",
            ],
            label="General familiarity with technology and digital tools",
            value="Select your experience level",
            interactive=True,
        )

        information_sources_input = gr.CheckboxGroup(
            [
                "Search engines (e.g., Google, Bing)",
                "Online databases (e.g., Google Scholar, academic journals)",
                "AI chat interfaces (e.g., ChatGPT, Siri, etc.)",
                "Social media platforms (e.g., Facebook, Twitter, Reddit)",
                "Asking friends, colleagues, or family members",
                "Books or printed materials",
                "Online forums or communities (e.g., Quora, StackExchange)",
                "Other ",
            ],
            label="How do you usually find information when researching a topic?",
        )

        ai_experience_input = gr.Dropdown(
            ["Select an option", "Yes, regularly", "Yes, occasionally", "No"],
            label="Prior experience with AI systems in professional or academic settings",
            value="Select an option",
            interactive=True,
        )

        ai_usage_input = gr.Dropdown(
            ["Select an option", "Yes", "No"],
            label="Have you ever used an AI chat interface (e.g., ChatGPT, Siri, or other virtual assistants)?",
            value="Select an option",
            interactive=True,
        )

        ai_frequency_input = gr.Dropdown(
            ["Daily", "Weekly", "Monthly", "Rarely"],
            label="If you answered 'Yes' to the previous question, how frequently do you use AI chat interfaces?",
            visible=False,
        )

        ai_satisfaction_input = gr.Dropdown(
            [
                "Select your satisfaction level",
                "Very Satisfied",
                "Satisfied",
                "Neutral",
                "Dissatisfied",
                "Very Dissatisfied",
            ],
            label="How would you rate your overall experience using AI chat interfaces?",
            value="Select your satisfaction level",
            interactive=True,
        )

        ai_reason_input = gr.Textbox(
            label="Can you explain why you chose your answer to the previous question?"
        )
    
        warning_msg = gr.Markdown(
            "## ⚠️ The study is only available to participants over the age of 18. For more details review [Terms and Conditions](https://drive.google.com/file/d/1Ccp_JGhuDUOyR99w3VgrGlN2H5dkmrbo/view?usp=sharing)",
            visible=False,
            elem_id="message",
        )

        # Survey 1 submit button
        survey1_button = gr.Button("Complete Survey", interactive=True)
        survey1_status = gr.Textbox(visible=False, interactive=False)

    

    # Chat section (initially hidden)
    with gr.Group(visible=False) as chat_group:
        with gr.Row(elem_id="row"):
            gr.Markdown(
                """
                # Instructions

                On this page, you will answer a series of general knowledge questions with the help of the chatbot.

                - You can ask the chatbot about any quiz question or its possible answers.
                - You can click on source name to display the source
                - The chatbot can help you understand, verify, or explore your answers.
                - For additional inspiration, use the **"Generate a Question"** section to discover related or follow-up questions.

                Use the chatbot to think critically and confidently before submitting your responses.
                """,
                elem_id="desc",
            )
            with gr.Row(elem_id="styled-button"):
                # Output textbox where the suggested question will appear
                output_text = gr.Textbox(label="Generate a Question", interactive=False)
                button = gr.Button("Generate a Question", elem_id="but")
                button.click(get_random_question, outputs=output_text)

        with gr.Row():
            chat_input = gr.Textbox(
                label="Enter a message to the chatbot",
                visible=False,
            )
            chat_output = gr.Textbox(
                label="Chatbot response", interactive=False, visible=False
            )
            chat_button = gr.Button("Send", visible=False)
            with gr.Column(elem_id="chatbot-container", scale=1):
                chatbot = gr.Chatbot(height=300)
                sources_output = gr.HTML()

                highlight_types = gr.CheckboxGroup(
                    ["Confirmed", "Potential misinformation"],
                    label="Highlight Types",
                    value=["Confirmed", "Potential misinformation"],
                )

                with gr.Row(elem_id="chatbot-controls"):
                    user_input = gr.Textbox(
                        elem_id="chatbot-user-input", label="Your Message", lines=1
                    )
                    submit_button = gr.Button(
                        "Send", elem_id="submit-button", scale=00
                    )  # Small submit button
#quiz section
            with gr.Column(elem_id="summary", scale=1):  
                gr.Markdown("## General Knowledge Quiz")

                q1 = gr.Radio(
                    ["A. James Chadwick", "B. Ernest Rutherford"],
                    label="1. Which scientist is credited with the discovery of the neutron?",
                )

                q2 = gr.Radio(
                    ["A. Pericles", "B. Themistocles"],
                    label="2. Who led the Athenian navy at the Battle of Salamis?",
                )
                q3 = gr.Radio(
                    ["A. Russia", "B. France"],
                    label="3. Which country has the most time zones (including overseas territories)?",
                )

                q4 = gr.Radio(
                    ["A. Boris Pasternak", "B. Mikhail Bulgakov"],
                    label="4. Who wrote *The Master and Margarita*, a novel banned in the Soviet Union for decades?",
                )

                q5 = gr.Radio(
                    ["A. Athens and Corinth", "B. Athens and Sparta"],
                    label="5. The Peloponnesian War was primarily fought between which two Greek city-states?",
                )

                q6 = gr.Radio(
                    ["A. Gustav Klimt", "B. Wassily Kandinsky"],
                    label="6. Which artist is considered a major figure in the Blue Rider movement (Der Blaue Reiter)?",
                )

                q7 = gr.Radio(
                    ["A. Liberty, Equality, Brotherhood", "B. Life, Liberty, Property"],
                    label="7. According to John Locke, what are the three natural rights?",
                )

                send_button = gr.Button("Submit summary and finish")
                long_text_output = gr.HTML()

        # different style settings 
        demo.css = """
        /* Chatbot Controls Row Styles */
    #chatbot-controls {
      display: flex;
      background-color: #FFA500;
      flex-direction: row-reverse;
      border-radius: 5px;

      gap: 0px;/* Make controls row a flex container */
    }

    /* Chatbot Column Styles */
    #chatbot-container {
      border: 2px solid #808080; /* Grey border */
      border-radius: 10px;
      box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
      gap: 10px;
      background-color: white;

    }
    #message{
        background-color: #D35400;
        font-weight: bold; 
        color:white !important;
        }
    #row{
    display:flex-box;
            flex-direction: row;

    }
    
    div.svelte-1nguped {
            background-color: white;

      }
    div.svelte-1xp0cw7 {
        flex-direction: row-reverse;
    }

    #summary{
    padding-left: 10px;
    padding-right: 10px;
    }
    @media (prefers-color-scheme: dark) {
                #component-2920,#summary,#chatbot-container,#desc,#naslov,#terms{ 
                    background-color:var(--neutral-800);
                    color: var(--col-dark);
                }
                div.svelte-1nguped>*:not(.absolute) {
                      
                        background-color: #27272a;
                    }
               #thanks
               {
               color:white;
               }
            }


    /* User Input Textbox Style */
    #chatbot-user-input {
      background-color: #FFA500; /* Orange background */
      color: white; /* white text */
      border:no-border;
    }
    #chatbot-user-input span{
      color:white;
    }
    div.svelte-633qhp{
      border: none;

    }
    .gradio-container.gradio-container-5-21-0 .contain #chatbot-controls{
    flex-direction:row
    }


    #desc{
      padding-bottom:20px;
    }
    /* Submit Button Style */
    #submit-button {
      min-width: 50px;
      background-color:#FFA500; /* Grey button */
      color: white;
      border-radius: 5px;
      align-self:center;
    justify-content: flex-end;
}
#styled-button {
    display: flex;
    align-items: center !important;
}

#but {
width: 100px;
flex:none;
min-width: none;
}
div.svelte-1nguped{
  border:none;
}


        """

    #Pop quiz, initially hidden
    with gr.Group(visible=False) as survey2_group:
        gr.Markdown("## Pop Quiz")
        source_misattribution = gr.CheckboxGroup(
            source_questions,
            label="The chatbot made a mistake in source attribution (select the questions where this happened):",
        )

        correct_info_red = gr.CheckboxGroup(
            source_questions,
            label="The chatbot highlighted correct information in red (select the questions where this happened):",
        )

        wrong_info_green = gr.CheckboxGroup(
            source_questions,
            label="The chatbot highlighted incorrect information in green (select the questions where this happened):",
        )

        wrong_credibility_score = gr.CheckboxGroup(
            source_questions,
            label="The chatbot gave a wrong credibility score to some sources (select applicable questions):",
        )

        misinfo_in_unhighlighted = gr.CheckboxGroup(
            source_questions,
            label="Some misinformation was present in unhighlighted text (select the questions where this applies):",
        )
        #Post study survey, initially hidden
        gr.Markdown("## Post-Study Survey: AI Chat Interface Experience")
        ai_use_ease = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="I found it easy to use the AI chat interface during the study.",
        )
        ai_use_clarity = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="The AI chat interface provided clear responses to my questions.",
        )
        highlighted_info_use = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="Highlighted information helped me understand the information better.",
        )
        highlighted_info_trust = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="The system helped me critically evaluate the information.",
        )
        sources_trust_score = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="I noticed errors or inconsistencies in the sources or content presented.",
        )
        sources_reliability = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="I clicked on the sources to verify their credibility.",
        )
        clarity_helpful = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="I asked follow-up questions or challenged the AI’s answers. ",
        )
        clarity_clear = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="I had a positive overall experience using the system. ",
        )
        preference_for_highlighting = gr.Radio(
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"],
            label="This tool would be useful in academic or classroom settings.",
        )
        liked_disliked = gr.Textbox(label="What did you like most about the system?")
        improvements = gr.Textbox(label="What would you improve or change? ")
        thought_process = gr.Textbox(
            label="What would help you engage more critically with the information"
        )

        feedback_button = gr.Button("Submit Feedback & Data")
        feedback_output = gr.Textbox(visible=False, interactive=False)
    # thank you window
    with gr.Group(visible=False) as thanks:
        gr.HTML(
            """
        <style>
            /* Default light mode styles */
            .thank-you-container {
                text-align: center;
                padding: 50px;
            }

            .thank-you-container h1 {
                font-size: 50px;
                color: #4CAF50;
                margin-bottom: 20px;
            }

            .thank-you-container p {
                font-size: 24px;
                max-width: 700px;
                margin: auto;
                color: #333;
            }

            .thank-you-container .message {
                font-size: 20px;
                color: #555;
                margin-top: 20px;
            }

            /* Dark mode styles using media query */
            @media (prefers-color-scheme: dark) {
                body {
                    background-color: #121212;
                    color: white;
                }

                .thank-you-container h1 {
                    color: #4CAF50;
                }

                .thank-you-container p {
                    color: #ddd;  /* Lighter text color in dark mode */
                }

                .thank-you-container .message {
                    color: #bbb;  /* Lighter message color */
                }
            }
        </style>
        <div class="thank-you-container">
            <h1>🎉 THANK YOU! 🎉</h1>
            <p>Your time and effort are greatly appreciated!  
            </p>
            <p class="message">
                Wishing you all the best! 😊
            </p>
        </div>
        """
        )

    survey1_button.click(
        fn=survey1,
        inputs=[
            name_input,
            familiarity_input,
            information_sources_input,
            ai_experience_input,
            ai_usage_input,
            ai_frequency_input,
            ai_satisfaction_input,
            ai_reason_input,
        ],
        outputs=[survey1_status, survey1_group, chat_group],
    )

    feedback_button.click(
        fn=survey2,
        inputs=[
            source_misattribution,
            correct_info_red,
            wrong_info_green,
            wrong_credibility_score,
            misinfo_in_unhighlighted,
            ai_use_ease,
            ai_use_clarity,
            highlighted_info_use,
            highlighted_info_trust,
            sources_trust_score,
            sources_reliability,
            clarity_helpful,
            clarity_clear,
            preference_for_highlighting,
            improvements,
            liked_disliked,
            thought_process,
        ],  
        outputs=[feedback_output, survey2_group, thanks],
    )
    user_input.submit(
        chatbot_conversation,
        inputs=[user_input, gr.State(), highlight_types],
        outputs=[chatbot, gr.State(), sources_output],
    )
    submit_button.click(
        chatbot_conversation,
        inputs=[user_input, gr.State(), highlight_types],
        outputs=[chatbot, gr.State(), sources_output],
    )
    send_button.click(
        handle_quiz_submission,
        inputs=[q1, q2, q3, q4, q5, q6, q7],
        outputs=[long_text_output, chat_group, survey2_group],
    )
    highlight_types.change(track_highlight_change, inputs=[highlight_types], outputs=[])
    send_button.click(track_button_click, inputs=[send_button], outputs=[])

    sources_output.click(track_source_click, inputs=[gr.HTML()], outputs=[gr.HTML()])
    # agree_checkbox.change(enable_button, agree_checkbox, survey1_button)


demo.launch(share=True, inbrowser=False)
