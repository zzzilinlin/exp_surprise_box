#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 12:03:16 2023

"""
import os
import pandas as pd
import random
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from scipy.stats import pearsonr

# Specify the folder path containing TSV files
folder_path = 'exp_FINAL_data'

# Iterate through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.tsv'):
        # Extract base name without extension
        df_name = os.path.splitext(filename)[0]

        # Replace dots or other problematic characters in variable names
        safe_df_name = df_name.replace('.', '_')

        file_path = os.path.join(folder_path, filename)

        # Read the TSV file into a DataFrame
        df = pd.read_csv(file_path, sep='\t')

        # Assign to a global variable with a safe name
        globals()[safe_df_name] = df

# Drop rows with NaN values in the 'sens' column at the beginning
articles_nl = articles_nl_sql.dropna(subset=['text']).copy()

# Calculate percentage distribution
articles_nl['publisher'].value_counts(normalize=True)



# Seed
random.seed(42)

# Function to clean and tokenize sentences
def process_sentences(text):
  # Ensure that `text' is a string
    text_str = str(text)    
    # Replace various newline characters and extra spaces
    cleaned_text = text_str.replace('\n', ' ').replace('\r', ' ').replace('\r\n', ' ').replace('\\n', ' ')
    cleaned_text = ' '.join(cleaned_text.split())  # Remove extra spaces 
    sentences = sent_tokenize(cleaned_text)
    valid_sentences = [sen for sen in sentences if 4 < len(word_tokenize(sen)) < 51]
    return sentences, valid_sentences

# Apply the function to each row in the DataFrame
articles_nl[['all_sens', 'sens']] = articles_nl['text'].apply(process_sentences).apply(pd.Series)

# Create a DataFrame for sentences
df_senss = articles_nl.explode('sens')[['id', 'sens']].rename(columns={'id': 'sen_id', 'sens': 'sen_coding'})

# 594762->594579
df_sens = df_senss.dropna(subset=['sen_coding']).copy()

# Calculate the midpoint index
midpoint = len(df_sens) // 2

# Split the DataFrame into two halves
df_sens_1 = df_sens.iloc[:midpoint]
df_sens_2 = df_sens.iloc[midpoint:]

# Save each DataFrame to a separate CSV file for BERT predictions
df_sens_1.to_csv('exp_sens_1.csv', index=False)
df_sens_2.to_csv('exp_sens_2.csv', index=False)



# With predictions (computed on Colab)

# Read the CSV files into DataFrames
df1 = pd.read_csv('exp_FINAL_data/output_exp_sens_1.csv')
df2 = pd.read_csv('exp_FINAL_data/output_exp_sens_2.csv')

# Combine DataFrames into a single DataFrame
bert_combined = pd.concat([df1, df2], ignore_index=True)

# 1 is factual and formal
# Factual 0->1
bert_combined['y_fact'] = bert_combined['y_fact'].replace({0: 1, 1: 0})

# Formal 1
bert_combined_for = bert_combined.groupby('id', as_index=False)['y_for'].mean()

# Delete netural sentences; fact to opinion -> 0 to 1
bert_combined_no_2_sub = bert_combined.loc[bert_combined['y_fact'] != 2]
bert_combined_sub = bert_combined_no_2_sub.groupby('id', as_index=False)['y_fact'].mean()

text_score = pd.merge(bert_combined_for, bert_combined_sub, on=['id'], how='outer').rename(columns={"id":"news_id"})

# Check 'no fact score'
text_score['y_fact'].isna().sum()

# Save
text_score.to_csv(r'app_text_score.csv', index = False)
bert_combined_no_2_sub.to_csv(r'sen_score.csv', index = False)


# User files

# group 3 and group 4 -> recommendation
user_sql['group'] = user_sql['group'].replace({4: 1, 3: 1, 2: 0, 1: 0})

# Convert the 'timestamp' column to datetime
news_selected_sql['starttime'] = pd.to_datetime(news_selected_sql['starttime'])

# Extract date from the 'starttime' column
news_selected_sql['date'] = news_selected_sql['starttime'].dt.date

# Group by 'user_id' and count the unique dates
user_date_counts = news_selected_sql.groupby('user_id')['date'].nunique()

# Filter for users with more than 5 different dates and user_id larger than 35 (after pilot testing): n=121
filtered_users = user_date_counts[(user_date_counts > 5) & (user_date_counts.index > 35)]

# Filter 3 outliers who cheated the systems
filtered_user_info = user_sql[user_sql['id'].isin(filtered_users.index)]
filtered_user_info = filtered_user_info[filtered_user_info['sum_ratings'] <= 200]


### Attrition analysis
# Filter for users with more than 5 different dates and user_id larger than 35: n=121
filtered_users = user_date_counts[(user_date_counts.index > 35)]
# Filter 3 abusers
filtered_user_info = user_sql[user_sql['id'].isin(filtered_users.index)]
# Join on 'id'
filtered_user_info = user_sql[user_sql['id'].isin(filtered_users.index)].copy()
filtered_user_info = filtered_user_info.set_index('id').join(filtered_users).reset_index()
# Filter 3 outliers
filtered_user_info = filtered_user_info[filtered_user_info['sum_ratings'] <= 200]
# Save
filtered_user_info.to_csv(r'userinfo_attrition.csv', index = False)


### Serendipity
# Filter rows in news_info based on user_id being in filtered_user_info['id']
filtered_news_info = news_selected_sql[news_selected_sql['user_id'].isin(filtered_user_info['id'])]

# Stats
filtered_news_info['rating'].mean()
filtered_news_info['rating'].std()
filtered_news_info['rating2'].mean()
filtered_news_info['rating2'].std()

# Pearson correlation and p-value
r_value, p_value = pearsonr(filtered_news_info['rating'], filtered_news_info['rating2'])

print(f"Correlation (r): {r_value}")
print(f"P-value: {p_value:.10f}")

# Drop rows with NaN values in the 'mystery' column
filtered_news_info_subset = filtered_news_info[['user_id', 'mystery']].dropna()

# Grouping by 'user_id' and 'mystery'
filtered_news_info_subset = filtered_news_info_subset.groupby(['user_id', 'mystery']).size().reset_index(name='count')

# Pivot the DataFrame to have 'mystery' values as columns
filtered_news_info_subset_b = filtered_news_info_subset.pivot(index='user_id', columns='mystery', values='count').reset_index()

# Fill NaN values with 0
filtered_news_info_subset_b = filtered_news_info_subset_b.fillna(0)

# Calculate the ratio of mystery 1 to mystery 0
filtered_news_info_subset_b['ratio'] = filtered_news_info_subset_b[1.0] / (filtered_news_info_subset_b[0.0] + filtered_news_info_subset_b[1.0])

# Joining the two DataFrames on 'user_id' and 'id'
seren_joined_data = pd.merge(filtered_user_info, filtered_news_info_subset_b, left_on='id', right_on='user_id', how='inner')

# Save
seren_joined_data.to_csv('serendipity.csv', index=False)


### Ratings
# Convert 'time_spent' to datetime
filtered_news_info['time_spent'] = pd.to_datetime(filtered_news_info['time_spent'])

# Exclude less than 11 secs and nan/nat
filtered_news_info_subset_c = filtered_news_info[
    (filtered_news_info['time_spent'].dt.second >= 11) &
    ~filtered_news_info['time_spent'].isna()
]

# Drop rows with NaN values in the 'mystery' column
filtered_news_info_subset_c = filtered_news_info_subset_c.dropna(subset=['mystery'])
filtered_news_info_subset_c = filtered_news_info_subset_c[['news_id', 'user_id', 'rating', 'rating2', 'recommended','position','mystery']]

# Joining the two DataFrames on 'user_id' and 'id'
rate_joined_data = pd.merge(filtered_user_info, filtered_news_info_subset_c, left_on='id', right_on='user_id', how='inner')
rate_joined_data_b = pd.merge(rate_joined_data, text_score, on='news_id', how='inner')

# Check if the combination of 'news_id' and 'user_id' values is unique
is_unique_combination = not rate_joined_data_b.duplicated(subset=['user_id', 'news_id']).any()
print(f"Is the combination of 'user_id' and 'news_id' values unique? {is_unique_combination}")

rate_joined_data_b_subset = rate_joined_data_b[['user_id', 'y_for', 'y_fact', 'news_id']]

# Group by 'user_id' and calculate the standard deviation for 'y_for' and 'y_sub'
with_sd = rate_joined_data_b_subset.groupby('user_id').agg({
    'y_for': 'std',  # Calculate standard deviation for 'y_for' column
    'y_fact': 'std',  # Calculate standard deviation for 'y_sub' column
}).reset_index()

# Merge DataFrames on 'user_id'
diversity_data = pd.merge(seren_joined_data, with_sd, on='user_id', how='left')

# Save
diversity_data.to_csv('diversity.csv', index=False)
rate_joined_data_b.to_csv('rates.csv', index=False)


### Comments
# Clean up
user_comments = user_comments_sql[~(
    user_comments_sql['username'].str.contains('rcmdgt|cauvvr|prpahh|spugxu|rturbh', na=False) | # contains 'xx' or 'yy'
    user_comments_sql['username'].str.startswith('\n', na=False)  # starts with newline
)]

# Keep only rows where username matches expected pattern (like "rcmdgt")
user_comments = user_comments_sql[user_comments_sql['username'].str.match(r'^[a-z]{6}$', na=False)]

# group 3 and group 4 -> recommendation
user_comments['group'] = user_comments['group'].astype(float).astype('Int64')  # convert to numeric safely
user_comments['group'] = user_comments['group'].replace({4: 1, 3: 1, 2: 0, 1: 0})

# Define the prefix for comment columns
comment_prefix = 'eval_comments'

# Find comment columns
comment_cols = [col for col in user_comments.columns if col.startswith(comment_prefix)]

# Filter and select columns in one go
user_comments = (
    user_comments
    .loc[~user_comments[comment_cols].isna().all(axis=1), ['username', 'group', *comment_cols, 'id']]
)

# Save
user_comments.to_csv('comments.csv', index=False)
























