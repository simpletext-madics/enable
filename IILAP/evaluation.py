import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter
import itertools
import seaborn as sns
import os
import re
import math
from collections.abc import Iterable

with open('survey_and_chat_data.json', 'r') as f:
    data = json.load(f)

# Prepare lists to store rows for the DataFrames
survey_1_rows = []
survey_2_rows = []
chat_rows = []

# Iterate over the entries and extract relevant data for each DataFrame
for entry in data:
    survey_1_row = None  # Track only the first survey1 entry
    survey_2_row = {}
    chat_data = []
    long_texts = []  # List to store all long text inputs for the 'long_text' column
    chat_without_long_text = []  # Separate storage for chat messages without long text

    # Iterate over the entry's sub-elements
    for key, value in entry.items():
        if isinstance(value, list):
            for sub_entry in value:
                if 'survey1' in sub_entry and survey_1_row is None:
                    # Keep only the first survey1 and ignore others
                    survey_1_row = sub_entry['survey1']

                if 'survey2' in sub_entry:
                    survey_2_row.update(sub_entry['survey2'])

                if 'chat' in sub_entry:
                    # Ensure chat data is processed correctly
                    for chat in sub_entry['chat']:
                        if 'details' in chat and 'long_text_input' in chat['details']:
                            long_texts.append(chat['details']['long_text_input'])
                        else:
                            chat_without_long_text.append(chat)

    # Ensure that chat_rows gets a corresponding entry even if empty
    chat_rows.append({
        'chat': chat_without_long_text if chat_without_long_text else None,
        'long_text': long_texts if long_texts else None
    })

    # Append only the first survey1 entry
    survey_1_rows.append(survey_1_row if survey_1_row else {})

    # Append survey2 entry
    survey_2_rows.append(survey_2_row)

# Create DataFrames for each
survey_1_df = pd.DataFrame(survey_1_rows)
survey_2_df = pd.DataFrame(survey_2_rows)
chat_df = pd.DataFrame(chat_rows)

# Merge the three DataFrames on a common index
merged_df = pd.concat([survey_1_df, survey_2_df, chat_df], axis=1)

correct_quiz_answers = {
    "Q1": "A. James Chadwick",
    "Q2": "B. Themistocles",
    "Q3": "B. France",
    "Q4": "B. Mikhail Bulgakov",
    "Q5": "B. Athens and Sparta",
    "Q6": "B. Wassily Kandinsky",
    "Q7": "B. Life, Liberty, Property"
}
column_map = {
    "ai_use_ease": "ai_use_ease",
    "ai_use_clarity": "ai_use_clarity",
    "highlighted_info_use": "highlighted_info_use",
    "highlighted_info_trust": "helped me critically evaluate",
    "sources_trust_score": "noticed errors",
    "sources_reliability": "clicked",
    "clarity_helpful": "followup",
    "clarity_clear": "positive experience",
    "preference_for_highlighting": "use in school"
}

for internal_col, descriptive_col in column_map.items():
    if descriptive_col in merged_df.columns:
        merged_df[internal_col] = merged_df[internal_col].fillna(merged_df[descriptive_col])


# Remove these rows from the DataFrame
filtered_df = merged_df

# Display the new DataFrame without removed rows
print("Reports created")
columns_to_drop = [
    "helped me critically evaluate",
    "noticed errors",
    "clicked",
    "followup",
    "positive experience",
    "use in school",
    "long_text"
]

# Drop the columns if they exist in the DataFrame
filtered_df.drop(columns=[col for col in columns_to_drop if col in filtered_df.columns], inplace=True)
# Rename columns using the provided mapping
filtered_df.rename(columns=column_map, inplace=True)
correct_answers = {
    'source_misattribution': {
         'Q2(Battle of Salamis)',  'Q4(The Master and Margarita)', 'Q6(Blue Rider)' 
    },
    'correct_info_red': {
        'Q1(neutron)', 'Q3(most time zones)', 'Q5(city-states)', 'Q7(three natural rights)'
    },
    'wrong_info_green': {
        'Q2(Battle of Salamis)', 'Q3(most time zones)', 'Q6(Blue Rider)'
    },
    'wrong_credibility_score': {
        'Q1(neutron)', 'Q3(most time zones)', 'Q4(The Master and Margarita)'
    },
    'misinfo_in_unhighlighted': {
        'Q2(Battle of Salamis)', 'Q5(city-states)', 'Q7(three natural rights)'
    },
}

def parse_answers(cell):
    # If the cell is a string, split and clean
    if isinstance(cell, str):
        return set(ans.strip() for ans in cell.split(',') if ans.strip())
    
    # If it's a list-like but not a string
    elif isinstance(cell, Iterable) and not isinstance(cell, str):
        return set(str(ans).strip() for ans in cell if str(ans).strip())
    
    # If it's a null scalar (e.g., None, np.nan)
    elif cell is None or pd.isna(cell):
        return set()
    
    # Fallback: wrap single value in a set
    return {str(cell).strip()}
for col in correct_answers:
    if col in filtered_df.columns:
        filtered_df[col] = filtered_df[col].apply(parse_answers)
    else:
        print(f"⚠️ Warning: Column '{col}' not found in DataFrame.")
# Track per-row performance for each column
per_row_data = []

# Accumulate totals across all rows per column
column_totals = {col: {'tp': 0, 'fp': 0, 'fn': 0} for col in correct_answers}

# Evaluate each row in the DataFrame
for idx, row in filtered_df.iterrows():
    for col, correct_set in correct_answers.items():
        pred_set = row[col]
        tp = len(pred_set & correct_set)
        fp = len(pred_set - correct_set)
        fn = len(correct_set - pred_set)

        # Update running totals
        column_totals[col]['tp'] += tp
        column_totals[col]['fp'] += fp
        column_totals[col]['fn'] += fn

        # Row-level metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_row_data.append({
            'row': idx,
            'column': col,
            'TP': tp,
            'FP': fp,
            'FN': fn,
            'Precision': round(precision, 2),
            'Recall': round(recall, 2),
            'F1': round(f1, 2)
        })

# Create DataFrame for row-level analysis
per_row_df = pd.DataFrame(per_row_data)

# Create summary table with overall metrics
overall_data = []
for col, counts in column_totals.items():
    tp = counts['tp']
    fp = counts['fp']
    fn = counts['fn']
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    overall_data.append({
        'column': col,
        'Total TP': tp,
        'Total FP': fp,
        'Total FN': fn,
        'Precision': round(precision, 2),
        'Recall': round(recall, 2),
        'F1': round(f1, 2)
    })

overall_df = pd.DataFrame(overall_data)
participant_scores = per_row_df.groupby('row')['F1'].mean().reset_index()
participant_scores.rename(columns={'F1': 'Average F1'}, inplace=True)
# Ensure the index is named for merging
participant_scores.set_index('row', inplace=True)

# Add 'Average F1' column to filtered_df
filtered_df['participant_scores'] = participant_scores['Average F1']
short_labels = {
    "ai_use_ease": "AI was easy to use",
    "ai_use_clarity": "AI gave clear answers",
    "highlighted_info_use": "Highlights improved understanding",
    "helped me critically evaluate": "AI helped critical thinking",
    "noticed errors": "I noticed source or content errors",
    "clicked": "I checked the sources",
    "followup": "I asked follow-up questions",
    "clarity_clear": "Overall positive experience",
    "use in school": "Useful for academic use"
}
filtered_df = filtered_df.rename(columns=short_labels)


# Check for NaN or inf and convert to string
if isinstance(value, (int, float)):
    if math.isnan(value) or math.isinf(value):
        val_str = 'N/A'
    else:
        val_str = value
else:
    val_str = str(value)

# Step 1: Count event_type occurrences for each participant
def count_event_types(chat_list):
    return Counter(event.get('event_type') for event in chat_list if isinstance(event, dict))

# Step 2: Apply to your DataFrame
filtered_df['event_type_counts'] = filtered_df['chat'].apply(count_event_types)

# Step 3: Expand the counts into separate columns (one per event type)
event_type_df = filtered_df['event_type_counts'].apply(pd.Series).fillna(0).astype(int)

# Step 4: Merge back into the main DataFrame
filtered_df = pd.concat([filtered_df, event_type_df], axis=1)
# Function to convert seconds into minutes and seconds format
def seconds_to_minutes_seconds(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{int(minutes)}m {int(seconds)}s"

# Function to calculate the interaction time (time difference) between consecutive events in a chat
def calculate_interaction_time(chat_data):
    # Convert the timestamps to datetime
    timestamps = [datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S.%f') for event in chat_data]

    # Calculate time differences between consecutive events (in seconds)
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)]

    return time_diffs
def count_source_clicks(chat_data):
    # Count how many 'Source Click' events are present
    return sum(1 for event in chat_data if event['event_type'] == 'Source Click')

def count_highlight_change(chat_data):
    # Count how many 'Highlight Selection Change' events are present
    return sum(1 for event in chat_data if event['event_type'] == 'Highlight Selection Change')

# Function to calculate the average time between consecutive 'Chat Submission' events
def avg_chat_submission_time(chat_data):
    # Filter "Chat Submission" events
    chat_submission_times = [event for event in chat_data if event['event_type'] == 'Chat Submission']

    # Calculate the time differences between consecutive "Chat Submission" events
    if len(chat_submission_times) < 2:
        return 0  # No second submission to compare with

    timestamps = [datetime.strptime(event['timestamp'], '%Y-%m-%d %H:%M:%S.%f') for event in chat_submission_times]
    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)]

    return sum(time_diffs) / len(time_diffs) if len(time_diffs) > 0 else 0

# Function to calculate the average time between "Source Click" and the next action
def avg_source_click_to_next_action(chat_data):
    source_click_times = []

    # Iterate through the events to find 'Source Click' events and the next event
    for i in range(len(chat_data) - 1):
        if chat_data[i]['event_type'] == 'Source Click':
            timestamp_source_click = datetime.strptime(chat_data[i]['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            timestamp_next_event = datetime.strptime(chat_data[i+1]['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            source_click_times.append((timestamp_next_event - timestamp_source_click).total_seconds())

    return sum(source_click_times) / len(source_click_times) if len(source_click_times) > 0 else 0

# Apply the functions to calculate values for each chat
filtered_df['total_interaction_time'] = filtered_df['chat'].apply(calculate_interaction_time).apply(sum)
filtered_df['avg_chat_submission_time'] = filtered_df['chat'].apply(avg_chat_submission_time)
filtered_df['avg_source_click_to_next_action'] = filtered_df['chat'].apply(avg_source_click_to_next_action)
filtered_df['num_source_clicks'] = filtered_df['chat'].apply(count_source_clicks)
filtered_df['num_highlight_changes'] = filtered_df['chat'].apply(count_highlight_change)


# Convert total_interaction_time, avg_chat_submission_time, and avg_source_click_to_next_action to minutes and seconds
filtered_df['total_interaction_time'] = filtered_df['total_interaction_time'].apply(seconds_to_minutes_seconds)
filtered_df['avg_chat_submission_time'] = filtered_df['avg_chat_submission_time'].apply(seconds_to_minutes_seconds)

filtered_df['avg_source_click_to_next_action'] = filtered_df['avg_source_click_to_next_action'].apply(seconds_to_minutes_seconds)

# Show the results
filtered_df[['total_interaction_time', 'avg_chat_submission_time', 'avg_source_click_to_next_action', 'num_source_clicks','num_highlight_changes']]
def calculate_quiz_score(chat_data):
    quiz_events = [event for event in chat_data if event.get('event_type') == 'Quiz answers']
    if not quiz_events:
        return None

    quiz_answers = quiz_events[-1].get('details', {})
    correct = 0
    total = len(correct_quiz_answers)

    for q_key, correct_answer in correct_quiz_answers.items():
        user_answer = quiz_answers.get(q_key)
        if user_answer and user_answer.strip() == correct_answer.strip():
            correct += 1
        # Else: incorrect or unanswered — counts as incorrect

    return round((correct / total) * 100, 2)
filtered_df['quiz_percentage_correct'] = filtered_df['chat'].apply(calculate_quiz_score)
filtered_df['quiz_percentage_correct']
c1=20
c2=20
c3=20
c4=20
c5=10
c6=10

def time_str_to_seconds(t):
    if isinstance(t, str):
        match = re.match(r"(?:(\d+)m)?\s*(\d+)s", t.strip())
        if match:
            minutes = int(match.group(1)) if match.group(1) else 0
            seconds = int(match.group(2))
            return minutes * 60 + seconds
    return 0  # Default if parsing fails
              
filtered_df['score_1'] = filtered_df['Source Click'].apply(lambda x: 1 if x >= 1 else 0) * c1

        
filtered_df['score_2'] = filtered_df['Chat Submission'].apply(lambda x: 1 if x >= 8 else 0) * c2

filtered_df['avg_chat_submission_time'] = filtered_df['avg_chat_submission_time'].apply(time_str_to_seconds)
       
filtered_df['score_3'] = filtered_df['avg_chat_submission_time'].apply(lambda x: 1 if x >= 20 else 0) * c3

        # avg_source_click_to_next_action (1 if >= 10, else 0) * c4
filtered_df['avg_source_click_to_next_action'] = filtered_df['avg_source_click_to_next_action'].apply(time_str_to_seconds)
filtered_df['score_4'] = filtered_df['avg_source_click_to_next_action'].apply(lambda x: 1 if x >= 10 else 0) * c4

        # quiz_percentage_correct * c5
filtered_df['score_5'] = filtered_df['quiz_percentage_correct'] * c5 / 100.0  # assuming it's in percent

        # errors_spotted * c6
filtered_df['score_6'] = filtered_df['participant_scores'] * c6

        # Step 4: Final score is the sum of all component scores
filtered_df['score'] = filtered_df[[f'score_{i}' for i in range(1, 7)]].sum(axis=1)

      
# Inputs
df = filtered_df.copy()  # Replace with your actual DataFrame

columns_to_analyze = [
    'name', 'familiarity', 'information_sources', 'ai_experience',
    'ai_usage', 'ai_frequency', 'ai_satisfaction',
    'source_misattribution', 'correct_info_red', 'wrong_info_green',
    'wrong_credibility_score', 'misinfo_in_unhighlighted',
    'AI was easy to use', 'AI gave clear answers',
    'Highlights improved understanding', 'AI helped critical thinking',
    'I noticed source or content errors', 'I checked the sources',
       'I asked follow-up questions', 'positive experience',
    'Useful for academic use','improvements', 'liked_disliked', 'thought_process', 'ai_reason',
    'participant_scores', 'Chat Submission', 'Source Click', 'Button Click', 
       'total_interaction_time', 'quiz_percentage_correct', 'score_1',
       'score_2', 'score_3', 'score_4', 'score_5', 'score_6', 'score'
]
list_only_columns = ['name', 'improvements', 'liked_disliked', 'thought_process', 'ai_reason']
score_columns = ['score_1', 'score_2', 'score_3', 'score_4', 'score_5', 'score_6', 'score', 'participant_scores']

special_eval_cols = [
    'source_misattribution', 'correct_info_red',
    'wrong_info_green', 'wrong_credibility_score',
    'misinfo_in_unhighlighted'
]

# Excel and chart setup
output_file = "reports/summary_participant_overview.xlsx"
writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
workbook = writer.book
chart_dir = "charts_temp"
os.makedirs(chart_dir, exist_ok=True)

for col in columns_to_analyze:
    sheet_name = col[:31]
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    if col in list_only_columns:
        worksheet.write(0, 0, f"{col} - Full Responses")
        raw_values = filtered_df[col].dropna().reset_index(drop=True)
        for i, val in enumerate(raw_values):
            # Convert list/dict to string if needed
            if isinstance(val, (list, dict)):
                val = str(val)
            worksheet.write(i + 1, 0, val)
        continue  # Skip the rest of the loop for these
        
    elif col == 'information_sources':
        # Ensure lists
        df['information_sources'] = df['information_sources'].apply(lambda x: x if isinstance(x, list) else [])
        all_sources = list(itertools.chain(*df['information_sources']))
        source_counts = Counter(all_sources)
        source_df = pd.DataFrame(source_counts.items(), columns=['Source', 'Count']).sort_values(by='Count', ascending=True)

        # Write table
        worksheet.write(0, 0, "Most Commonly Used Information Sources")
        source_df.to_excel(writer, sheet_name=sheet_name, startrow=1, index=False)

        # Plot chart
        plt.figure(figsize=(12, 6))
        bars = plt.barh(source_df['Source'], source_df['Count'], color='skyblue')
        for bar in bars:
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                     f'{int(bar.get_width())}', va='center', ha='left', fontsize=10)
        plt.xlabel('Count')
        plt.title('Most Commonly Used Information Sources')
        plt.tight_layout()
        chart_path = f"{chart_dir}/{col}_chart.png"
        plt.savefig(chart_path)
        plt.close()

        # Insert into Excel
        worksheet.insert_image(1, 4, chart_path, {"x_scale": 0.7, "y_scale": 0.7})

    elif col in special_eval_cols:
        # Write only summary from overall_df
        worksheet.write(0, 0, "Evaluation Metrics")
        subset_df = overall_df[overall_df['column'] == col]
        subset_df.to_excel(writer, sheet_name=sheet_name, startrow=1, index=False)

    elif col in score_columns:
        col_data = df[col].dropna()
    
        # --- Histogram with KDE ---
        plt.figure(figsize=(8, 4))
        sns.histplot(col_data, kde=True, bins=20, color='skyblue')
        plt.title(f'{col} Distribution')
        plt.xlabel(col)
        plt.ylabel('Frequency')
        plt.tight_layout()
        hist_path = f"{chart_dir}/{col}_hist_kde.png"
        plt.savefig(hist_path)
        plt.close()
        worksheet.insert_image(1, 4, hist_path, {"x_scale": 0.7, "y_scale": 0.7})
    
        # --- Boxplot ---
        plt.figure(figsize=(6, 3))
        sns.boxplot(x=col_data, color='lightgreen')
        plt.title(f'Boxplot of {col}')
        plt.xlabel(col)
        plt.tight_layout()
        box_path = f"{chart_dir}/{col}_boxplot.png"
        plt.savefig(box_path)
        plt.close()
        worksheet.insert_image(18, 4, box_path, {"x_scale": 0.7, "y_scale": 0.7})
    
        # --- Summary Statistics ---
        worksheet.write(0, 0, f"{col} Summary Statistics")
        summary = col_data.describe()
        median = col_data.median()
        summary_df = pd.DataFrame(summary).reset_index()
        summary_df.columns = ['Metric', 'Value']
        summary_df = pd.concat([summary_df, pd.DataFrame([{'Metric': 'median', 'Value': median}])], ignore_index=True)
        summary_df.to_excel(writer, sheet_name=sheet_name, startrow=1, index=False)


    else:
        # Generic value counts/statistics/plot
        col_data = df[col].dropna()
        counts = col_data.value_counts()
        percentages = col_data.value_counts(normalize=True) * 100
        summary = col_data.describe()

        worksheet.write(0, 0, f"{col} Value Counts")
        counts_df = counts.reset_index()
        counts_df.columns = [col, "Count"]
        counts_df.to_excel(writer, sheet_name=sheet_name, startrow=1, index=False)

        worksheet.write(len(counts_df)+3, 0, f"{col} Percentages")
        perc_df = percentages.reset_index()
        perc_df.columns = [col, "Percentage"]
        perc_df.to_excel(writer, sheet_name=sheet_name, startrow=len(counts_df)+4, index=False)

        worksheet.write(len(counts_df)+len(perc_df)+6, 0, f"{col} Summary Stats")
        summary_df = pd.DataFrame(summary).reset_index()
        summary_df.columns = ["Metric", "Value"]
        summary_df.to_excel(writer, sheet_name=sheet_name, startrow=len(counts_df)+len(perc_df)+7, index=False)

        # Plot
        plt.figure(figsize=(6, 4))
        sns.barplot(x=counts.index.astype(str), y=counts.values, hue=counts.index.astype(str), legend=False, palette="pastel")
        plt.title(f"{col} Distribution")
        plt.ylabel("Count")
        plt.xlabel(col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        chart_path = f"{chart_dir}/{col}_chart.png"
        plt.savefig(chart_path)
        plt.close()

        worksheet.insert_image(1, 4, chart_path, {"x_scale": 0.7, "y_scale": 0.7})

# Save Excel
writer.close()
print(f"✅ Summary report saved: {output_file}")

# Create a new Excel writer for per-participant reports
participant_output_file = "reports/per_participant_report.xlsx"
participant_writer = pd.ExcelWriter(participant_output_file, engine='xlsxwriter')
workbook = participant_writer.book

# Loop through each participant
for idx, row in filtered_df.iterrows():
    sheet_name = f"Participant_{idx}"
    worksheet = workbook.add_worksheet(sheet_name)
    participant_writer.sheets[sheet_name] = worksheet

    # 1. Write participant full row info
    worksheet.write(0, 0, "Participant Data")
    for i, (col_name, value) in enumerate(row.items()):
        if isinstance(value, (int, float)):
            if math.isnan(value) or math.isinf(value):
                val_str = 'N/A'
            else:
                val_str = value
        else:
            val_str = str(value)
        worksheet.write(i + 1, 0, col_name)
        worksheet.write(i + 1, 1, val_str)

    # 2. Add per-question performance metrics from per_row_df
    worksheet.write(len(row) + 3, 0, "Per-Question Performance")

    # Filter relevant rows from per_row_df
    participant_perf = per_row_df[per_row_df['row'] == idx].drop(columns=['row'])
    participant_perf.reset_index(drop=True, inplace=True)

    # Write table headers
    for j, col in enumerate(participant_perf.columns):
        worksheet.write(len(row) + 4, j, col)

    # Write table values with safe handling of NaN/inf
    for i, data_row in participant_perf.iterrows():
        for j, value in enumerate(data_row):
            if isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    worksheet.write(len(row) + 5 + i, j, 'N/A')
                else:
                    worksheet.write(len(row) + 5 + i, j, value)
            else:
                worksheet.write(len(row) + 5 + i, j, str(value))

# Save the file
participant_writer.close()
print(f"✅ Per-participant report saved: {participant_output_file}")
