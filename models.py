from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class GitHubUser(db.Model):
    __tablename__ = "git_hub_user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    followers = db.Column(db.Integer, nullable=False)
    public_repos = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(200))
    following = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200))
    bio = db.Column(db.Text)

    def __init__(self, username, followers, public_repos, name, avatar_url, following, location, bio):
        self.username = username
        self.followers = followers
        self.public_repos = public_repos
        self.name = name
        self.avatar_url = avatar_url
        self.following = following
        self.location = location
        self.bio = bio

class GitHubUserRepos(db.Model):
    __tablename__ = "git_hub_user_repos"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('git_hub_user.id'), nullable=False)
    repo_name = db.Column(db.String(200), nullable=False)
    commit_count = db.Column(db.Integer, nullable=False)
    issues_count = db.Column(db.Integer, nullable=False)
    languages = db.Column(db.String(200))
    stars = db.Column(db.Integer, nullable=False)
    watchers = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, repo_name, commit_count, issues_count, languages, stars, watchers):
        self.user_id = user_id
        self.repo_name = repo_name
        self.commit_count = commit_count
        self.issues_count = issues_count
        self.languages = languages
        self.stars = stars
        self.watchers = watchers
