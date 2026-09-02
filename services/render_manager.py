"""
Polynomial Studio — Render Manager

Manages background rendering jobs with status tracking.
Jobs are persisted to disk so they survive server restarts.
"""
import os
import json
import uuid
import threading
import time
import logging
from datetime import datetime

import config as cfg
from services.manim_renderer import generate_manim_scene, render_scene

logger = logging.getLogger("polynomial_studio")

JOBS_FILE = os.path.join(cfg.RENDER_DIR, "jobs.json")

class RenderJob:
    """Represents a single rendering job."""

    def __init__(self, job_id: str, config: dict):
        self.job_id = job_id
        self.config = config
        self.status = "pending"  # pending | generating | rendering | complete | failed
        self.progress = 0
        self.video_path = None
        self.video_filename = None
        self.error = None
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.duration = 0

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "video_path": self.video_path,
            "video_filename": self.video_filename,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
        }


class RenderManager:
    """Singleton-style manager for render jobs."""

    def __init__(self):
        self._jobs: dict[str, RenderJob] = {}
        self._lock = threading.Lock()
        self._load_jobs()

    def submit_job(
        self,
        polynomials: list[dict],
        render_config: dict,
        theme: dict,
        animation_options: dict,
        output_video_dir: str,
        scene_dir: str,
    ) -> str:
        """
        Submit a new render job. Returns job_id.
        The actual rendering happens in a background thread.
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = RenderJob(job_id, {
            "polynomials": polynomials,
            "render_config": render_config,
            "theme": theme,
            "animation_options": animation_options,
        })

        with self._lock:
            self._jobs[job_id] = job
            self._save_jobs()

        thread = threading.Thread(
            target=self._execute_job,
            args=(job_id, polynomials, render_config, theme, animation_options, output_video_dir, scene_dir),
            daemon=True,
        )
        thread.start()

        return job_id

    def get_job_status(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                return job.to_dict()
            return None

    def _save_jobs(self):
        """Persist all jobs to disk (called with lock held)."""
        try:
            data = {jid: job.to_dict() for jid, job in self._jobs.items()}
            os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
            with open(JOBS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")

    def _load_jobs(self):
        """Load jobs from disk on startup."""
        if not os.path.isfile(JOBS_FILE):
            return
        try:
            with open(JOBS_FILE, "r") as f:
                data = json.load(f)
            for jid, status_dict in data.items():
                job = RenderJob(jid, {})
                job.status = status_dict.get("status", "pending")
                job.progress = status_dict.get("progress", 0)
                job.video_path = status_dict.get("video_path")
                job.video_filename = status_dict.get("video_filename")
                job.error = status_dict.get("error")
                job.created_at = status_dict.get("created_at", datetime.now().isoformat())
                job.completed_at = status_dict.get("completed_at")
                job.duration = status_dict.get("duration", 0)
                # Jobs that were mid-render when the server died are dead
                if job.status in ("pending", "generating", "rendering"):
                    job.status = "failed"
                    job.error = "Server restarted during render."
                    job.progress = 0
                self._jobs[jid] = job
            logger.info(f"Loaded {len(self._jobs)} jobs from disk.")
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")

    def _execute_job(
        self,
        job_id: str,
        polynomials: list[dict],
        render_config: dict,
        theme: dict,
        animation_options: dict,
        output_video_dir: str,
        scene_dir: str,
    ):
        """Execute a render job in a background thread."""
        job = self._jobs.get(job_id)
        if not job:
            return

        try:
            # Step 1: Generate Manim scene
            job.status = "generating"
            job.progress = 10
            with self._lock:
                self._save_jobs()

            scene_path = generate_manim_scene(
                polynomials=polynomials,
                render_config=render_config,
                theme=theme,
                animation_options=animation_options,
                output_dir=scene_dir,
            )
            job.progress = 30

            # Step 2: Render
            job.status = "rendering"
            job.progress = 40

            timeout = cfg.RENDER_TIMEOUT

            result = render_scene(
                scene_path=scene_path,
                render_config=render_config,
                output_dir=cfg.RENDER_DIR,
                timeout=timeout,
            )

            job.duration = result.get("duration", 0)

            if result["success"]:
                video_path = result["video_path"]

                # Copy video to our standard output directory
                final_filename = f"polynomial_animation_{job_id}.mp4"
                final_path = os.path.join(output_video_dir, final_filename)

                if os.path.abspath(video_path) != os.path.abspath(final_path):
                    import shutil
                    shutil.copy2(video_path, final_path)

                job.video_path = final_path
                job.video_filename = final_filename
                job.status = "complete"
                job.progress = 100
                job.completed_at = datetime.now().isoformat()
                logger.info(f"Job {job_id} completed: {final_filename}")
            else:
                job.status = "failed"
                job.error = result.get("error", "Unknown rendering error")
                job.progress = 0
                logger.error(f"Job {job_id} failed: {job.error}")

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.progress = 0
            logger.error(f"Job {job_id} exception: {e}")

        # Persist final state
        with self._lock:
            self._save_jobs()


# Global singleton
render_manager = RenderManager()
