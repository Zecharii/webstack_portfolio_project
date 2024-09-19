from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import os
import base64
from models import db, GitHubUser, GitHubUserRepos
from config import Config
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# Fetch GitHub user data
def fetch_github_user_data(username):
    url = f'https://api.github.com/users/{username}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Fetch GitHub user repositories data
def fetch_github_user_repos(username):
    url = f'https://api.github.com/users/{username}/repos'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Save user data to the database
def save_user_to_db(data):
    user = GitHubUser(
        username=data['login'],
        followers=data['followers'],
        public_repos=data['public_repos'],
        name=data.get('name'),
        avatar_url=data.get('avatar_url'),
        bio=data.get('bio'),
        location=data.get('location'),
        following=data.get('following', 0)
    )
    db.session.add(user)
    db.session.commit()
    return user

# Save repository data to the database
def save_repos_to_db(user_id, repos_data):
    for repo_data in repos_data:
        repo_name = repo_data['name']
        commit_url = repo_data['commits_url'].replace('{/sha}', '')
        commits_response = requests.get(commit_url)
        commits_count = len(commits_response.json()) if commits_response.status_code == 200 else 0

        issues_count = repo_data['open_issues_count']
        languages_url = repo_data['languages_url']
        languages_response = requests.get(languages_url)
        languages = ', '.join(languages_response.json().keys()) if languages_response.status_code == 200 else 'N/A'
        stars = repo_data['stargazers_count']
        watchers = repo_data['watchers_count']

        repo = GitHubUserRepos(
            user_id=user_id,
            repo_name=repo_name,
            commit_count=commits_count,
            issues_count=issues_count,
            languages=languages,
            stars=stars,
            watchers=watchers
        )
        db.session.add(repo)
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analytics', methods=['POST'])
def analytics():
    username = request.form['username']

    # Check if user data exists in the database
    user = GitHubUser.query.filter_by(username=username).first()

    if not user:
        user_data = fetch_github_user_data(username)
        if user_data:
            user = save_user_to_db(user_data)
        else:
            flash('GitHub user not found. Please check the username and try again.', 'error')
            return redirect(url_for('index'))

    # Check if repo data exists in the database
    repos = GitHubUserRepos.query.filter_by(user_id=user.id).all()

    if not repos:
        repos_data = fetch_github_user_repos(username)
        if repos_data:
            save_repos_to_db(user.id, repos_data)
            repos = GitHubUserRepos.query.filter_by(user_id=user.id).all()
        else:
            flash('An error occurred while fetching repository data from GitHub. Please try again later.', 'error')
            return redirect(url_for('index'))

    # Generate plots and visualizations
    plot_url = generate_plot(user)
    donut_chart_url = generate_donut_chart(repos)
    pie_chart_url = generate_pie_chart(repos)
    issues_heatmap_url = issues_heatmap(repos)
    commits_heatmap_url = commits_heatmap(repos)

    return render_template('analytics.html', username=username, name=user.name, avatar_url=user.avatar_url, bio=user.bio, 
                           location=user.location, followers=user.followers, following=user.following, public_repos=user.public_repos,
                           plot_url=plot_url, pie_chart_url=pie_chart_url, donut_chart_url=donut_chart_url, issues_heatmap_url=issues_heatmap_url, commits_heatmap_url=commits_heatmap_url, repos=repos)

# Generate plot for user data
def generate_plot(user):
    plt.figure(figsize=(8, 4))
    plt.bar(['Following', 'Followers', 'Public Repos'], [user.following, user.followers, user.public_repos])
    plt.title(f'GitHub Stats for {user.username}')
    plt.xlabel('Metrics')
    plt.ylabel('Counts')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url

# Generate donut chart for repo languages
def generate_donut_chart(repos):
    language_counts = {}
    for repo in repos:
        for lang in repo.languages.split(', '):
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

    if language_counts:
        plt.figure(figsize=(8, 4))
        plt.pie(language_counts.values(), labels=language_counts.keys(), autopct='%1.1f%%', wedgeprops=dict(width=0.3))
        plt.title('Top Languages by Repo Count')
        # Add a circle at the center to make it a donut chart
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        donut_chart_url = base64.b64encode(img.getvalue()).decode()
        return donut_chart_url
    return None

def generate_pie_chart(repos):
    language_counts = {}
    for repo in repos:
        for lang in repo.languages.split(', '):
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

    if language_counts:
        plt.figure(figsize=(8, 4))
        plt.pie(language_counts.values(), labels=language_counts.keys(), autopct='%1.1f%%')
        plt.title('Top Languages by Repo')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        pie_chart_url = base64.b64encode(img.getvalue()).decode()
        return pie_chart_url
    return None

# Generate heatmap for repo issues
def issues_heatmap(repos):
    if repos:
        issues_data = pd.DataFrame({
            'Repo': [repo.repo_name for repo in repos],
            'Issues': [repo.issues_count for repo in repos]
        })
        plt.figure(figsize=(8, 4))
        sns.heatmap(issues_data.set_index('Repo'), annot=True, fmt="d", cmap='YlGnBu')
        plt.title('Heatmap of Issues by Repo Count')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        issues_heatmap_url = base64.b64encode(img.getvalue()).decode()
        return issues_heatmap_url
    return None

# Generate heatmap for repo commits
def commits_heatmap(repos):
    if repos:
        commits_data = pd.DataFrame({
            'Repo': [repo.repo_name for repo in repos],
            'Commits': [repo.commit_count for repo in repos]
        })
        plt.figure(figsize=(8, 4))
        sns.heatmap(commits_data.set_index('Repo'), annot=True, fmt="d", cmap='YlGnBu')
        plt.title('Heatmap of Commits by Repo Count')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        commits_heatmap_url = base64.b64encode(img.getvalue()).decode()
        return commits_heatmap_url
    return None


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True)
