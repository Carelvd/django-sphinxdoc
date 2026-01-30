"""
VCS:Git

This provide a class that wraps the underlying git calls executed through subprocess intoa  convenient class.

There are some libraries that also perform this including :

GitPython
python-gitlab
"""
import subprocess
import logging
import os
from pathlib import Path
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger(__name__)

class Repository:
    """Git repository management utility class."""
    
    def __init__(self, repo, path, branch=None, credentials = getattr(settings, "VERSION_CONTROL_CREDENTIALS", {}).get("git", None), timeout = 300):
        """
        Initialize Git repository manager.
        
        Args:
            repo_url (str): Repository URL (HTTPS, SSH, or Git protocol)
            target_path (Path): Local directory for the repository
            branch (str, optional): Branch or tag to checkout
        """
        self.repo = repo
        self.path = Path(path)
        self.branch = branch
        self.credentials = credentials
        self.timeout = timeout        
        # Note : self.is_ssh -> self.encrypted
        
    @property
    def encrypted(self):
        return self.repo.startswith('git@') or self.repo.startswith('ssh://')
    
    @property
    def repository(self):
        repo = urlparse(self.repo)
        try:
            # token = getattr(settings, f'SPHINXDOC_{repo.hostname.split('.')[-2].upper()}_TOKEN', self.credentials[repo.hostname])
            token = self.credentials[repo.hostname]
        except KeyError as e:
            raise ValueError(f"Sphinxdoc requires that you assign `VERSION_CONTROL_CREDENTIALS` for {repo.hostname} in your `settings.py` file.")
        if repo.scheme in ('http','https'):
            return f"{repo.scheme}://:{token}@{repo.netloc}{repo.path}"
        else :
            return self.repo

    @property
    def environment(self):
        """\
        Environment

        Prepare a copy of the Django environment for Git operations based upon authentication method.
        
        Returns:
            dict: Environment with necessary variables for Git operations
        """
        env = os.environ.copy()
        
        if self.encrypted:
            # SSH authentication - use system SSH keys
            ssh_key = getattr(settings, 'SPHINXDOC_SSH_KEY_PATH', None)
            if ssh_key:
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key} -o StrictHostKeyChecking=no'
        # else:
        #     # HTTPS authentication - use access token if available
        #     token = getattr(settings, 'SPHINXDOC_GITHUB_TOKEN', None)
        #     if token:
        #         # Modify URL to include token
        #         parsed = urlparse(self.repo)
        #         if parsed.scheme in ('http', 'https'):
        #             self.repo = f"{parsed.scheme}://:{token}@{parsed.netloc}{parsed.path}"        
        return env
    
    @property
    def accessible(self):
        """
        Accessibility

        Confirms whether or not the remote server hosting the repository is accessiible.
        
        Returns:
            bool: True if repository is accessible
        """
        try:
            env = self.environment
            result = subprocess.run(
                ['git', 'ls-remote', self.repository],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.timeout
            )
            print(result)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.error(f"Error checking repository accessibility: {e}")
            return False
    
    # def validate_repository_accessibility(self):
    #     """Validate if repository URL is accessible."""
    #     if not self.repo:
    #         return True
    #     try:
    #         # Check if repository exists and is accessible
    #         result = subprocess.run(
    #             ['git', 'ls-remote', self.repo],
    #             capture_output=True,
    #             text=True,
    #             timeout=30
    #         )
    #         return result.returncode == 0
    #     except (subprocess.TimeoutExpired, FileNotFoundError):
    #         return False   

    @property
    def default_branch(self):
        """\
        Default Branch

        Get the default branch of the repository.
        
        Returns:
            str or None: Default branch name
        """
        try:
            env = self.environment()
            result = subprocess.run(
                ['git', 'ls-remote', '--symref', self.repo, 'HEAD'],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            print(result)
            if result.returncode == 0:
                # Parse output to get default branch
                for line in result.stdout.split('\n'):
                    if line.startswith('ref: refs/heads/'):
                        return line.split('/')[-1].split('\t')[0]
            
            return None
        except Exception as e:
            logger.error(f"Error getting default branch: {e}")
            return None
    
    @property
    def current_branch(self):
        """\
        Get the current branch of the cloned repository.
        
        Returns:
            str or None: Current branch name
        """
        if not self.path.exists() or not (self.path / '.git').exists():
            return None
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting current branch: {e}")
            return None

    @property
    def cloned(self):
        """\
        Cloned
        
        Asserts whether or not the repository has been cloned.
        """
        return self.path.exists() and (self.path/'.git').exists() and (self.path/'.git').is_dir()

    # def clone_repository(self):
    #     """Clone repository to source_path."""
    #     if not self.repo:
    #         logger.warning(f"Project {self.slug} has no repository URL")
    #         return False
    #     try:
    #         # Ensure parent directory exists
    #         self.source_path.mkdir(parents=True, exist_ok=True)            
    #         # Prepare clone command
    #         cmd = ['git', 'clone', '--recurse-submodules']
    #         if branch:= self.branch:
    #             cmd.extend(['--branch', branch, '--single-branch'])
    #         cmd.extend([self.repo, str(self.source_root)])
    #         # Execute clone
    #         result = subprocess.run(
    #             cmd,
    #             capture_output=True,
    #             text=True,
    #             timeout=300  # 5 minutes timeout
    #         )
    #         if result.returncode == 0:
    #             self.updated = timezone.now()
    #             self.save(update_fields=['updated'])
    #             logger.info(f"Successfully cloned repository for project {self.slug}")
    #             return True
    #         else:
    #             logger.error(f"Failed to clone repository for project {self.slug}: {result.stderr}")
    #             return False      
    #     except subprocess.TimeoutExpired:
    #         logger.error(f"Clone timeout for project {self.slug}")
    #         return False
    #     except Exception as e:
    #         logger.error(f"Error cloning repository for project {self.slug}: {e}")
    #         return False
    
    def clone(self, timeout = None):
        """\
        Clone

        Clone the repository.
        
        Args:
            timeout (int): Timeout in seconds
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if self.path.exists() and (self.path / '.git').exists():
            return False, "Repository already exists"        
        try:
            # Ensure parent directory exists
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Prepare clone command
            cmd = ['git', 'clone', '--recurse-submodules']            
            if self.branch:
                cmd.extend(['--branch', self.branch, '--single-branch'])            
            cmd.extend([self.repository, str(self.path)])
            print("Executing Clone Operation")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=self.environment,
                timeout=timeout or self.timeout
            )
            print(result)
            if result.returncode == 0:
                logger.info(f"Successfully cloned repository to {self.path}")
                return True, "Repository cloned successfully"
            else:
                error_msg = f"Failed to clone repository: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"Clone operation timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error cloning repository: {e}"
            logger.error(error_msg)
            return False, error_msg

    def pull(self, timeout=180):
        """\
        Pull

        Pull latest changes from the repository.
        
        Args:
            timeout (int): Timeout in seconds
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.path.exists() or not (self.path / '.git').exists():
            return False, "Repository is not cloned"        
        try:
            cmd = ['git', 'pull', 'origin']
            if self.branch:
                cmd.append(self.branch)
            else:
                cmd.append('HEAD')
            result = subprocess.run(
                cmd,
                cwd=str(self.path),
                capture_output=True,
                text=True,
                env=self.environment,
                timeout=timeout
            )
            if result.returncode == 0:
                logger.info(f"Successfully pulled changes to {self.path}")
                return True, "Repository updated successfully"
            else:
                error_msg = f"Failed to pull changes: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = f"Pull operation timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error pulling changes: {e}"
            logger.error(error_msg)
            return False, error_msg

    # def update_repository(self):
    #     """Update repository with latest changes."""
    #     if not self.is_cloned:
    #         logger.warning(f"Repository for project {self.slug} is not cloned")
    #         return False
    #     try:
    #         # Pull latest changes
    #         cmd = ['git', 'pull', 'origin']
    #         if self.branch:
    #             cmd.append(self.branch)
    #         else:
    #             cmd.append('HEAD')
    #         result = subprocess.run(
    #             cmd,
    #             cwd=str(self.repo_dir),
    #             capture_output=True,
    #             text=True,
    #             timeout=180  # 3 minutes timeout
    #         )
    #         if result.returncode == 0:
    #             self.last_sync = timezone.now()
    #             self.save(update_fields=['last_sync'])
    #             logger.info(f"Successfully updated repository for project {self.slug}")
    #             return True
    #         else:
    #             logger.error(f"Failed to update repository for project {self.slug}: {result.stderr}")
    #             return False 
    #     except subprocess.TimeoutExpired:
    #         logger.error(f"Update timeout for project {self.slug}")
    #         return False
    #     except Exception as e:
    #         logger.error(f"Error updating repository for project {self.slug}: {e}")
    #         return False
    
    def latest_commit(self):
        """\
        Latest Commit

        Get the hash of the last commit.
        
        Returns:
            str or None: Commit hash
        """
        if not self.path.exists() or not (self.path / '.git').exists():
            return None
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            return None
        except Exception as e:
            logger.error(f"Error getting last commit hash: {e}")
            return None

    def has_changes(self):
        """
        Check if repository has uncommitted changes.
        
        Returns:
            bool: True if there are uncommitted changes
        """
        if not self.path.exists() or not (self.path / '.git').exists():
            return False
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(self.path),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking repository status: {e}")
            return False

