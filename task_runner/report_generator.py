"""
Report Generator - Genera reportes de ejecución
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class ReportGenerator:
    """Genera reportes de ejecución de tareas"""
    
    def __init__(self, reports_dir: str):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("ReportGenerator")
    
    def generate(
        self,
        tasks: List,
        execution_log: List[Dict],
        format: str = "all"
    ) -> Dict:
        """
        Genera reportes en múltiples formatos
        """
        self.logger.info("Generando reportes...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated = {}
        
        report_data = self._prepare_data(tasks, execution_log)
        
        if format in ["json", "all"]:
            json_path = self._generate_json(report_data, timestamp)
            generated["json"] = str(json_path)
        
        if format in ["html", "all"]:
            html_path = self._generate_html(report_data, timestamp)
            generated["html"] = str(html_path)
        
        if format in ["md", "all"]:
            md_path = self._generate_markdown(report_data, timestamp)
            generated["markdown"] = str(md_path)
        
        self.logger.info(f"Reportes generados: {generated}")
        
        return generated
    
    def _prepare_data(self, tasks: List, execution_log: List[Dict]) -> Dict:
        total = len(tasks)
        completed = len([t for t in tasks if t.status == "completed"])
        failed = len([t for t in tasks if t.status == "failed"])
        pending = len([t for t in tasks if t.status == "pending"])
        in_progress = len([t for t in tasks if t.status == "in_progress"])
        
        total_duration = 0
        for log in execution_log:
            if log.get("completed_at") and log.get("started_at"):
                start = datetime.fromisoformat(log["started_at"])
                end = datetime.fromisoformat(log["completed_at"])
                total_duration += (end - start).total_seconds()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "in_progress": in_progress,
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "total_duration_seconds": total_duration
            },
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                    "retry_count": t.retry_count,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "error_message": t.error_message,
                    "artifacts": t.artifacts
                }
                for t in tasks
            ],
            "execution_log": execution_log
        }
    
    def _generate_json(self, data: Dict, timestamp: str) -> Path:
        path = self.reports_dir / f"report_{timestamp}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path
    
    def _generate_html(self, data: Dict, timestamp: str) -> Path:
        path = self.reports_dir / f"report_{timestamp}.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Task Execution Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .completed {{ color: #10b981; }}
        .failed {{ color: #ef4444; }}
        .pending {{ color: #f59e0b; }}
        table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-completed {{ background: #d1fae5; color: #065f46; }}
        .badge-failed {{ background: #fee2e2; color: #991b1b; }}
        .badge-pending {{ background: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Task Orchestrator Report</h1>
        <p>Generated: {data['generated_at']}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total</h3>
            <div class="value">{data['summary']['total']}</div>
        </div>
        <div class="stat-card">
            <h3>Completed</h3>
            <div class="value completed">{data['summary']['completed']}</div>
        </div>
        <div class="stat-card">
            <h3>Failed</h3>
            <div class="value failed">{data['summary']['failed']}</div>
        </div>
        <div class="stat-card">
            <h3>Success Rate</h3>
            <div class="value">{data['summary']['success_rate']:.1f}%</div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Retries</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for task in data['tasks']:
            badge_class = f"badge-{task['status']}"
            html_content += f"""
            <tr>
                <td><strong>{task['id']}</strong></td>
                <td>{task['title']}</td>
                <td><span class="badge {badge_class}">{task['status']}</span></td>
                <td>{task['priority']}</td>
                <td>{task['retry_count']}</td>
            </tr>
"""
        
        html_content += """
        </tbody>
    </table>
</body>
</html>
"""
        
        path.write_text(html_content, encoding="utf-8")
        return path
    
    def _generate_markdown(self, data: Dict, timestamp: str) -> Path:
        path = self.reports_dir / f"report_{timestamp}.md"
        
        lines = [
            "# Task Execution Report",
            "",
            f"**Generated:** {data['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Total: {data['summary']['total']}",
            f"- Completed: {data['summary']['completed']}",
            f"- Failed: {data['summary']['failed']}",
            f"- Pending: {data['summary']['pending']}",
            f"- Success Rate: {data['summary']['success_rate']:.1f}%",
            "",
            "## Tasks",
            "",
        ]
        
        for task in data['tasks']:
            lines.extend([
                f"### {task['id']}: {task['title']}",
                "",
                f"- Status: {task['status']}",
                f"- Priority: {task['priority']}",
                f"- Retries: {task['retry_count']}",
                "",
            ])
        
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
