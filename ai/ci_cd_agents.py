"""
Self-Evolving Code CI/CD Agents

This module implements AI agents that can automatically improve source code
through CI/CD pipelines. The agents analyze code, suggest improvements,
and create automated pull requests for code enhancements.
"""

import asyncio
import subprocess
import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import tempfile
import shutil
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysis:
    """Results of code analysis"""
    file_path: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class CodeImprovement:
    """A code improvement suggestion"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    current_code: str
    suggested_code: str
    confidence: float
    category: str  # 'bug_fix', 'optimization', 'style', 'security'

@dataclass
class PullRequest:
    """Pull request data"""
    title: str
    description: str
    branch_name: str
    improvements: List[CodeImprovement]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = 'draft'  # 'draft', 'open', 'merged', 'closed'

class CodeAnalyzer:
    """
    AI-powered code analyzer that identifies issues and suggests improvements
    """

    def __init__(self, project_root: str, language: str = 'python'):
        self.project_root = Path(project_root)
        self.language = language

        # Analysis patterns for different languages
        self.patterns = self._load_analysis_patterns()

        # Code quality thresholds
        self.thresholds = {
            'complexity': 10,
            'lines_per_function': 50,
            'duplicate_lines': 5,
            'test_coverage': 80
        }

    def _load_analysis_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load analysis patterns for code issues"""
        return {
            'python': [
                {
                    'pattern': r'print\(',
                    'issue': 'debug_print',
                    'suggestion': 'Remove debug print statements',
                    'category': 'style'
                },
                {
                    'pattern': r'except:\s*$',
                    'issue': 'bare_except',
                    'suggestion': 'Specify exception types in except clauses',
                    'category': 'bug_fix'
                },
                {
                    'pattern': r'if\s+.*:\s*$',
                    'issue': 'missing_else',
                    'suggestion': 'Consider adding else clause for clarity',
                    'category': 'style'
                }
            ],
            'javascript': [
                {
                    'pattern': r'console\.log\(',
                    'issue': 'debug_console',
                    'suggestion': 'Remove debug console.log statements',
                    'category': 'style'
                },
                {
                    'pattern': r'var\s+',
                    'issue': 'var_usage',
                    'suggestion': 'Use let/const instead of var',
                    'category': 'style'
                }
            ]
        }

    async def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a single file for issues and improvements"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analysis = CodeAnalysis(file_path=file_path)
            lines = content.split('\n')

            # Basic metrics
            analysis.metrics = {
                'total_lines': len(lines),
                'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
                'empty_lines': len([l for l in lines if not l.strip()]),
                'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0
            }

            # Pattern-based analysis
            for i, line in enumerate(lines, 1):
                for pattern_info in self.patterns.get(self.language, []):
                    if re.search(pattern_info['pattern'], line):
                        issue = {
                            'line': i,
                            'type': pattern_info['issue'],
                            'description': pattern_info['suggestion'],
                            'category': pattern_info['category'],
                            'code': line.strip()
                        }
                        analysis.issues.append(issue)

            # Generate suggestions
            analysis.suggestions = await self._generate_suggestions(analysis.issues, content)

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return CodeAnalysis(file_path=file_path, issues=[{'error': str(e)}])

    async def _generate_suggestions(self, issues: List[Dict[str, Any]],
                                  content: str) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on issues"""
        suggestions = []

        # Group issues by type
        issue_counts = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Generate suggestions based on patterns
        if issue_counts.get('debug_print', 0) > 0:
            suggestions.append({
                'type': 'cleanup',
                'description': f'Remove {issue_counts["debug_print"]} debug print statements',
                'priority': 'medium'
            })

        if issue_counts.get('bare_except', 0) > 0:
            suggestions.append({
                'type': 'robustness',
                'description': f'Fix {issue_counts["bare_except"]} bare except clauses',
                'priority': 'high'
            })

        # Complexity analysis (simplified)
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
        if len(functions) > 10:
            suggestions.append({
                'type': 'refactor',
                'description': f'Consider breaking down {len(functions)} functions into smaller modules',
                'priority': 'medium'
            })

        return suggestions

class CodeImprover:
    """
    AI agent that generates code improvements and fixes
    """

    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer
        self.improvement_templates = self._load_improvement_templates()

    def _load_improvement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load templates for code improvements"""
        return {
            'debug_print': {
                'pattern': r'print\((.*?)\)',
                'replacement': '# print(\\1)  # Commented out debug statement'
            },
            'bare_except': {
                'pattern': r'except:\s*$',
                'replacement': 'except Exception as e:'
            },
            'var_usage': {
                'pattern': r'\bvar\s+',
                'replacement': 'const '
            }
        }

    async def generate_improvements(self, analysis: CodeAnalysis) -> List[CodeImprovement]:
        """Generate specific code improvements"""
        improvements = []

        try:
            with open(analysis.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            for issue in analysis.issues:
                improvement = await self._create_improvement(issue, lines, analysis.file_path)
                if improvement:
                    improvements.append(improvement)

        except Exception as e:
            logger.error(f"Failed to generate improvements for {analysis.file_path}: {e}")

        return improvements

    async def _create_improvement(self, issue: Dict[str, Any], lines: List[str],
                                file_path: str) -> Optional[CodeImprovement]:
        """Create a specific improvement for an issue"""
        try:
            line_num = issue.get('line', 1) - 1  # Convert to 0-based
            if line_num >= len(lines):
                return None

            current_code = lines[line_num]
            issue_type = issue.get('type', 'unknown')

            # Get improvement template
            template = self.improvement_templates.get(issue_type)
            if not template:
                return None

            # Generate suggested code
            suggested_code = re.sub(template['pattern'], template['replacement'], current_code)

            # Skip if no change
            if suggested_code == current_code:
                return None

            return CodeImprovement(
                file_path=file_path,
                line_number=line_num + 1,
                issue_type=issue_type,
                description=issue.get('description', 'Code improvement'),
                current_code=current_code,
                suggested_code=suggested_code,
                confidence=0.8,
                category=issue.get('category', 'style')
            )

        except Exception as e:
            logger.debug(f"Failed to create improvement: {e}")
            return None

class CICDAgent:
    """
    CI/CD agent that orchestrates code analysis and improvement
    """

    def __init__(self, project_root: str, github_token: Optional[str] = None):
        self.project_root = Path(project_root)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        self.analyzer = CodeAnalyzer(str(project_root))
        self.improver = CodeImprover(self.analyzer)

        # CI/CD state
        self.active_prs: Dict[str, PullRequest] = {}
        self.analysis_cache: Dict[str, CodeAnalysis] = {}

    async def run_analysis(self, files: Optional[List[str]] = None) -> Dict[str, CodeAnalysis]:
        """Run code analysis on specified files or all tracked files"""
        if files is None:
            files = self._get_tracked_files()

        results = {}
        for file_path in files:
            if self._should_analyze_file(file_path):
                analysis = await self.analyzer.analyze_file(file_path)
                results[file_path] = analysis
                self.analysis_cache[file_path] = analysis

        return results

    async def generate_improvements(self, analysis_results: Dict[str, CodeAnalysis]) -> List[CodeImprovement]:
        """Generate improvements from analysis results"""
        all_improvements = []

        for analysis in analysis_results.values():
            improvements = await self.improver.generate_improvements(analysis)
            all_improvements.extend(improvements)

        # Sort by confidence and category priority
        category_priority = {'security': 3, 'bug_fix': 2, 'optimization': 1, 'style': 0}
        all_improvements.sort(key=lambda x: (
            category_priority.get(x.category, 0),
            x.confidence
        ), reverse=True)

        return all_improvements

    async def create_improvement_pr(self, improvements: List[CodeImprovement],
                                   title: str = None, description: str = None) -> Optional[PullRequest]:
        """Create a pull request with code improvements"""
        if not improvements:
            return None

        try:
            # Create branch
            branch_name = f"ai-improvements-{int(datetime.now().timestamp())}"
            await self._create_branch(branch_name)

            # Apply improvements
            applied_improvements = []
            for improvement in improvements:
                if await self._apply_improvement(improvement):
                    applied_improvements.append(improvement)

            if not applied_improvements:
                return None

            # Commit changes
            await self._commit_changes(f"AI-generated improvements: {title or 'Code enhancements'}")

            # Create PR
            pr_title = title or f"🤖 AI Code Improvements ({len(applied_improvements)} changes)"
            pr_description = description or self._generate_pr_description(applied_improvements)

            pr = PullRequest(
                title=pr_title,
                description=pr_description,
                branch_name=branch_name,
                improvements=applied_improvements
            )

            # Create GitHub PR if token available
            if self.github_token:
                pr_url = await self._create_github_pr(pr)
                if pr_url:
                    pr.status = 'open'

            self.active_prs[branch_name] = pr
            return pr

        except Exception as e:
            logger.error(f"Failed to create improvement PR: {e}")
            return None

    async def _create_branch(self, branch_name: str):
        """Create a new git branch"""
        cmd = ['git', 'checkout', '-b', branch_name]
        result = await self._run_command(cmd, cwd=self.project_root)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create branch: {result.stderr}")

    async def _apply_improvement(self, improvement: CodeImprovement) -> bool:
        """Apply a single improvement to the codebase"""
        try:
            with open(improvement.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if improvement.line_number <= len(lines):
                lines[improvement.line_number - 1] = improvement.suggested_code + '\n'

                with open(improvement.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                return True

        except Exception as e:
            logger.debug(f"Failed to apply improvement to {improvement.file_path}: {e}")

        return False

    async def _commit_changes(self, message: str):
        """Commit the applied changes"""
        # Stage changes
        await self._run_command(['git', 'add', '.'], cwd=self.project_root)

        # Commit
        await self._run_command(['git', 'commit', '-m', message], cwd=self.project_root)

    async def _create_github_pr(self, pr: PullRequest) -> Optional[str]:
        """Create a GitHub pull request"""
        try:
            # This would use GitHub CLI or API
            # For now, just log the intent
            logger.info(f"Would create PR: {pr.title}")
            return f"https://github.com/example/repo/pull/{hash(pr.title) % 1000}"
        except Exception as e:
            logger.error(f"Failed to create GitHub PR: {e}")
            return None

    def _generate_pr_description(self, improvements: List[CodeImprovement]) -> str:
        """Generate PR description from improvements"""
        description = "## 🤖 AI-Generated Code Improvements\n\n"

        # Group by category
        categories = {}
        for imp in improvements:
            cat = imp.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(imp)

        for category, imps in categories.items():
            description += f"### {category.title()} ({len(imps)} changes)\n"
            for imp in imps[:5]:  # Limit to 5 per category
                description += f"- **{imp.file_path}:{imp.line_number}**: {imp.description}\n"
            if len(imps) > 5:
                description += f"- ... and {len(imps) - 5} more\n"
            description += "\n"

        description += "### Files Changed\n"
        files_changed = set(imp.file_path for imp in improvements)
        for file in sorted(files_changed):
            description += f"- `{file}`\n"

        return description

    def _get_tracked_files(self) -> List[str]:
        """Get list of files tracked by git"""
        try:
            result = subprocess.run(['git', 'ls-files'], cwd=self.project_root,
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return [f for f in result.stdout.split('\n') if f.strip()]
        except Exception as e:
            logger.error(f"Failed to get tracked files: {e}")
        return []

    def _should_analyze_file(self, file_path: str) -> bool:
        """Check if a file should be analyzed"""
        # Skip certain files
        skip_patterns = [
            r'\.git/',
            r'__pycache__/',
            r'\.pyc$',
            r'\.log$',
            r'node_modules/',
            r'\.min\.js$'
        ]

        for pattern in skip_patterns:
            if re.search(pattern, file_path):
                return False

        # Check file extension
        supported_exts = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp'}
        return Path(file_path).suffix in supported_exts

    async def _run_command(self, cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a shell command asynchronously"""
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'active_prs': len(self.active_prs),
            'analyzed_files': len(self.analysis_cache),
            'total_improvements': sum(len(pr.improvements) for pr in self.active_prs.values())
        }

# Convenience functions
async def create_ci_cd_agent(project_root: str, github_token: Optional[str] = None) -> CICDAgent:
    """Factory function to create CI/CD agent"""
    return CICDAgent(project_root, github_token)

async def run_ai_code_improvement(project_root: str, files: Optional[List[str]] = None,
                                github_token: Optional[str] = None) -> Optional[PullRequest]:
    """Run full AI code improvement pipeline"""
    agent = await create_ci_cd_agent(project_root, github_token)

    # Analyze code
    analysis_results = await agent.run_analysis(files)

    # Generate improvements
    improvements = await agent.generate_improvements(analysis_results)

    if not improvements:
        logger.info("No improvements found")
        return None

    # Create PR with improvements
    pr = await agent.create_improvement_pr(improvements)

    return pr

# Example usage and testing
async def test_ci_cd_agent():
    """Test the CI/CD agent"""
    agent = CICDAgent("./")  # Current directory

    # Run analysis on this file
    results = await agent.run_analysis(["ai/ci_cd_agents.py"])

    print(f"Analyzed {len(results)} files")
    for file_path, analysis in results.items():
        print(f"{file_path}: {len(analysis.issues)} issues, {len(analysis.suggestions)} suggestions")

    # Generate improvements
    improvements = await agent.generate_improvements(results)
    print(f"Generated {len(improvements)} improvements")

    for imp in improvements[:3]:  # Show first 3
        print(f"- {imp.category}: {imp.description}")

if __name__ == "__main__":
    asyncio.run(test_ci_cd_agent())
